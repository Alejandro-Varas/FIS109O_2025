
import streamlit as st
import openai
import csv
import os
import re
from datetime import datetime

# ---------- PROMPT PEDAGÓGICO ----------
PEDAGOGICAL_PROMPT = """
Eres FIS109O Assistant, un asistente académico para estudiantes de Odontología en el curso Física para Odontología (FIS109O) de la Pontificia Universidad Católica de Chile.

Tu función principal es explicar con claridad y rigor los contenidos del curso: mecánica, fluidos, electricidad, ondas y radiación, enfocados en su aplicación clínica. Usas analogías relevantes como palancas mandibulares, irrigadores dentales, presión en jeringas, entre otros.

Formato de ecuaciones (OBLIGATORIO):
- Para matemáticas en línea usa: $ ... $
- Para ecuaciones en bloque usa: \[ ... \]  (o $$ ... $$)
- No uses Markdown (negritas/cursivas) para notación matemática.
- Escribe vectores con flecha: \vec{v}, \vec{F}, etc.
- Escribe vectores unitarios cartesianos como: \hat{x}, \hat{y}, \hat{z}.
- No uses corchetes literales "[" y "]" para delimitar ecuaciones.
- No dejes expresiones LaTeX sin $ o \[ \].

Te comunicas en español neutro, con matices chilenos, en un tono académico, claro, respetuoso y cercano. Apoyas el aprendizaje paso a paso, fomentas el pensamiento crítico, y ayudas a resolver dudas conceptuales y ejercicios. Si no sabes algo o si una pregunta excede tu alcance, sugiere al estudiante consultar con el equipo docente. Nunca inventas información.
"""

# ---------- CONFIG INICIAL ----------
st.set_page_config(page_title="Chatbot FIS109O", page_icon="🦷")
st.title("🦷 Chatbot Educativo - Física para Odontología")

openai.api_key = st.secrets["OPENAI_API_KEY"]

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
def latex_transform(expr: str) -> str:
    # Unitarios cartesianos
    expr = re.sub(r"\\mathbf\{\s*([xyzXYZ])\s*\}", lambda m: f"\\hat{{{m.group(1).lower()}}}", expr)
    expr = re.sub(r"\\hat\s+([A-Za-z])", r"\\hat{\1}", expr)
    # Vectores generales
    expr = re.sub(r"\\mathbf\{\s*([A-Za-wA-W])\s*\}", r"\\vec{\1}", expr)
    expr = re.sub(r"\\vec\s+([A-Za-z])", r"\\vec{\1}", expr)
    return expr

def preprocess_nonmath_segment(seg: str) -> str:
    seg = re.sub(r"\*\*([A-Za-z])\*\*", r"$\\vec{\1}$", seg)
    seg = re.sub(r"\b([A-Za-z])_([A-Za-z0-9]+)\b", r"$\1_{\2}$", seg)
    seg = re.sub(r"(?i)(vector)\s+([a-zA-Z])(\b)", r"\1 $\\vec{\2}$\3", seg)
    seg = re.sub(r"\(\s*([A-Za-z])\s*\)", r"$(\1)$", seg)
    return seg

def render_with_math(texto: str):
    texto = re.sub(r"(?ms)^\[\s*\n(.*?)\n\s*\]$", r"\\[\1\\]", texto)
    lineas = texto.split("\n")
    en_bloque_corchetes = False
    acumulador = []
    for ln in lineas:
        s = ln.strip()
        if not en_bloque_corchetes and s == "[":
            en_bloque_corchetes = True
            acumulador = []
            continue
        if en_bloque_corchetes:
            if s == "]":
                bloque = "\n".join(acumulador).strip()
                st.latex(latex_transform(bloque))
                en_bloque_corchetes = False
            else:
                acumulador.append(ln)
        else:
            partes = re.split(r"(\$\$.*?\$\$|\$.*?\$|\\\[.*?\\\])", ln)
            if len(partes) > 1:
                for p in partes:
                    if re.fullmatch(r"\$\$.*?\$\$|\$.*?\$|\\\[.*?\\\]", p):
                        st.latex(latex_transform(re.sub(r"^\\\[|\\\]$|^\$\$|\$\$$", "", p).strip()))
                    else:
                        st.write(preprocess_nonmath_segment(p))
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
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": PEDAGOGICAL_PROMPT},
                        {"role": "user", "content": pregunta}
                    ]
                )
                respuesta = response["choices"][0]["message"]["content"]
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
