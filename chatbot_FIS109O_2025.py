
import streamlit as st
import csv
import os
import re
from datetime import datetime

# --- OpenAI >= 1.0 client ---
try:
    from openai import OpenAI
except Exception as _e:
    OpenAI = None

# ---------- PROMPT PEDAGÓGICO ----------
PEDAGOGICAL_PROMPT = """
Eres FIS109O Assistant, un asistente académico para estudiantes de Odontología en el curso Física para Odontología (FIS109O) de la Pontificia Universidad Católica de Chile.

Tu función principal es explicar con claridad y rigor los contenidos del curso: mecánica, fluidos, electricidad, ondas y radiación, enfocados en su aplicación clínica. Usas analogías relevantes como palancas mandibulares, irrigadores dentales, presión en jeringas, entre otros.

Formato de ecuaciones (OBLIGATORIO):
- Para matemáticas en línea usa: $ ... $ o \\( ... \\)
- Para ecuaciones en bloque usa: \\[ ... \\]  (o $$ ... $$)
- No uses Markdown (negritas/cursivas) para notación matemática.
- Escribe vectores con flecha: \\vec{v}, \\vec{F}, etc.
- Escribe vectores unitarios cartesianos como: \\hat{x}, \\hat{y}, \\hat{z}.
- No uses corchetes literales "[" y "]" para delimitar ecuaciones.
- No dejes expresiones LaTeX sin $ o \\[ \\].

Te comunicas en español neutro, con matices chilenos, en un tono académico, claro, respetuoso y cercano. Apoyas el aprendizaje paso a paso, fomentas el pensamiento crítico, y ayudas a resolver dudas conceptuales y ejercicios. Si no sabes algo o si una pregunta excede tu alcance, sugiere al estudiante consultar con el equipo docente. Nunca inventas información.
"""

# ---------- CONFIG INICIAL ----------
st.set_page_config(page_title="Chatbot FIS109O", page_icon="🦷")
st.title("🦷 Chatbot Educativo - Física para Odontología")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Falta OPENAI_API_KEY en Settings → Secrets.")
    st.stop()

client = None
if OpenAI is not None:
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    except Exception as e:
        st.error(f"No se pudo inicializar el cliente OpenAI: {e}")
        st.stop()
else:
    st.error("La librería openai>=1.0 no está disponible. Agrega 'openai>=1.40.0' en requirements.txt y vuelve a desplegar.")
    st.stop()

LISTA_ESTUDIANTES = [
    "ana.perez@uc.cl",
    "jperez5@uc.cl",
    "mmendez@uc.cl",
    "camila.rojas@uc.cl",
    "luis.gomez@uc.cl",
    "francisco.torres@uc.cl",
    "sofia.vidal@uc.cl",
    "alejandro.varas@uc.cl",
]

st.markdown("Este chatbot responde preguntas de contenidos del curso FIS109O - Física para Odontología. Por favor, ingresa tu correo UC para comenzar.")
st.warning("🔒 Toda pregunta enviada será registrada con fines educativos y podrá ser revisada por el equipo docente del curso.")

correo = st.text_input("Correo UC:")

# ---------- Utilidades ----------
LATEX_CMD_PATTERN = re.compile(r"\\[A-Za-z]+")  # para heurística de rescate

def latex_transform(expr: str) -> str:
    # --- Unicode -> LaTeX ---
    expr = expr.replace("θ", r"\theta").replace("Θ", r"\Theta")
    expr = re.sub(r"(\d+)\s*[°º∘]", r"\1^{\\circ}", expr)

    # --- funciones trigonométricas "desnudas" -> \sin, \cos, \tan ---
    expr = re.sub(r"(?<!\\)\b(sin|cos|tan)\b", r"\\\1", expr)

    # --- Mapeos unitarios i, j, k -> x, y, z ---
    expr = re.sub(r"\\mathbf\{\s*i\s*\}", r"\\hat{x}", expr)
    expr = re.sub(r"\\mathbf\{\s*j\s*\}", r"\\hat{y}", expr)
    expr = re.sub(r"\\mathbf\{\s*k\s*\}", r"\\hat{z}", expr)
    expr = re.sub(r"(\\hat\{\s*i\s*\}|\\hat\s+i\b|\\hat\{\s*\\imath\s*\}|\\vec\{\s*i\s*\}|\\vec\s+i\b)", r"\\hat{x}", expr)
    expr = re.sub(r"(\\hat\{\s*j\s*\}|\\hat\s+j\b|\\hat\{\s*\\jmath\s*\}|\\vec\{\s*j\s*\}|\\vec\s+j\b)", r"\\hat{y}", expr)
    expr = re.sub(r"(\\hat\{\s*k\s*\}|\\hat\s+k\b|\\vec\{\s*k\s*\}|\\vec\s+k\b)", r"\\hat{z}", expr)

    # --- Unitarios con x,y,z explícitos ---
    expr = re.sub(r"\\mathbf\{\s*([xyzXYZ])\s*\}", lambda m: f"\\hat{{{m.group(1).lower()}}}", expr)
    expr = re.sub(r"\\hat\s+([A-Za-z])", r"\\hat{\1}", expr)

    # --- Vectores generales ---
    expr = re.sub(r"\\mathbf\{\s*([A-Za-z])\s*\}", r"\\vec{\1}", expr)
    expr = re.sub(r"\\vec\s+([A-Za-z])", r"\\vec{\1}", expr)

    return expr

def preprocess_nonmath_segment(seg: str) -> str:
    # **v** -> $\vec{v}$  (solo una letra)
    seg = re.sub(r"\*\*([A-Za-z])\*\*", r"$\\vec{\1}$", seg)
    # v_x -> $v_{x}$
    seg = re.sub(r"\b([A-Za-z])_([A-Za-z0-9]+)\b", r"$\1_{\2}$", seg)
    # "vector v" -> "vector \vec{v}"
    seg = re.sub(r"(?i)(vector)\s+([a-zA-Z])(\b)", r"\1 $\\vec{\2}$\3", seg)
    # ( x ) -> $(x)$  (incluye θ)
    seg = re.sub(r"\(\s*([A-Za-zθΘ])\s*\)", r"$(\1)$", seg)
    return seg

def render_with_math(texto: str):
    # Normalizar saltos de línea
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")

    # Normalizar bloques [...] -> \[...\] (multi-línea y una línea)
    texto = re.sub(r"(?s)\[\s*\n(.*?)\n\s*\]", r"\\[\1\\]", texto)
    texto = re.sub(r"\[\s*([^\[\]\n]+?)\s*\]", r"\\[\1\\]", texto)

    # Quitar líneas sueltas con "[" o "]"
    texto = re.sub(r"(?m)^\s*\[\s*\]\s*$", "", texto)
    texto = re.sub(r"(?m)^\s*\[\s*$", "", texto)
    texto = re.sub(r"(?m)^\s*\]\s*$", "", texto)

    for ln in texto.split("\n"):
        if not ln.strip():
            st.write("")
            continue

        # Fragmentar por delimitadores: $$...$$, $...$, \[...\], \(...\)
        partes = re.split(r"(\$\$.*?\$\$|\$.*?\$|\\\[.*?\\\]|\\\([^\)]+\\\))", ln)
        if len(partes) > 1:
            for p in partes:
                if re.fullmatch(r"\$\$.*?\$\$|\$.*?\$|\\\[.*?\\\]|\\\([^\)]+\\\)", p or ""):
                    contenido = re.sub(r"^\\\[|\\\]$|^\$\$|\$\$$|^\\\(|\\\)$|^\$|\$$", "", p).strip()
                    st.latex(latex_transform(contenido))
                elif p:
                    st.write(preprocess_nonmath_segment(p))
            continue

        # Heurística: si tiene comandos LaTeX, rendérizalo como bloque
        if LATEX_CMD_PATTERN.search(ln):
            st.latex(latex_transform(ln.strip()))
        else:
            st.write(preprocess_nonmath_segment(ln))

# ---------- Lógica principal ----------
if correo:
    correo = correo.lower().strip()
    if correo not in LISTA_ESTUDIANTES:
        st.warning("Este correo no está autorizado para usar el chatbot.")
        st.stop()

    pregunta = st.text_area("Escribe tu pregunta sobre contenidos del curso:", height=150)

    if st.button("Preguntar") and pregunta.strip():
        with st.spinner("Pensando..."):
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": PEDAGOGICAL_PROMPT},
                        {"role": "user", "content": pregunta}
                    ]
                )
                respuesta = resp.choices[0].message.content
                st.success("Respuesta del Chatbot:")
                render_with_math(respuesta)

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open("registro_chat_fis109o.csv", "a", encoding="utf-8", newline="") as f:
                    csv.writer(f).writerow([now, correo, pregunta, respuesta])
            except Exception as e:
                st.error(f"Ocurrió un error: {e}")

    if correo == "alejandro.varas@uc.cl" and os.path.exists("registro_chat_fis109o.csv"):
        with open("registro_chat_fis109o.csv", "rb") as f:
            st.download_button("📥 Descargar registro de interacciones (.csv)", f, "registro_chat_fis109o.csv", "text/csv")
else:
    st.info("Por favor, ingresa tu correo UC para comenzar.")
