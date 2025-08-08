
import streamlit as st
import openai
import csv
import os
import re
from datetime import datetime

# ---------- PROMPT PEDAGÓGICO (SIN INTERPOLACIÓN) ----------
PEDAGOGICAL_PROMPT = """
Eres FIS109O Assistant, un asistente académico para estudiantes de Odontología en el curso Física para Odontología (FIS109O) de la Pontificia Universidad Católica de Chile.

Tu función principal es explicar con claridad y rigor los contenidos del curso: mecánica, fluidos, electricidad, ondas y radiación, enfocados en su aplicación clínica. Usas analogías relevantes como palancas mandibulares, irrigadores dentales, presión en jeringas, entre otros.

Formato de ecuaciones (OBLIGATORIO):
- Para matemáticas en línea usa: $ ... $
- Para ecuaciones en bloque usa: \[ ... \]  (o $$ ... $$)
- No uses Markdown (negritas/cursivas) para notación matemática.
- No uses corchetes literales "[" y "]" para delimitar ecuaciones.
- No dejes expresiones LaTeX sin $ o \[ \].

Te comunicas en español neutro, con matices chilenos, en un tono académico, claro, respetuoso y cercano. Apoyas el aprendizaje paso a paso, fomentas el pensamiento crítico, y ayudas a resolver dudas conceptuales y ejercicios. Si no sabes algo o si una pregunta excede tu alcance, sugiere al estudiante consultar con el equipo docente. Nunca inventas información.
"""

# ---------- CONFIG INICIAL ----------
st.set_page_config(page_title="Chatbot FIS109O", page_icon="🦷")
st.title("🦷 Chatbot Educativo - Física para Odontología")

# API KEY
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Lista blanca
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

# ---------- Utilidades de render matemático ----------
def contiene_latex(s: str) -> bool:
    return bool(re.search(r"\\(vec|frac|sqrt|hat|bar|overline|underline|cdot|times|sin|cos|tan|alpha|beta|gamma|theta|pi|sum|int|partial)\\b|[\\^_]", s))

def preprocess_nonmath_segment(seg: str) -> str:
    # **v** -> $\mathbf{v}$  (solo una letra)
    seg = re.sub(r"\*\*([A-Za-z])\*\*", r"$\\mathbf{\1}$", seg)
    # *v* -> $\mathit{v}$  (opcional, solo una letra)
    seg = re.sub(r"(?<!\*)\*([A-Za-z])\*(?!\*)", r"$\\mathit{\1}$", seg)
    # v_x -> $v_{x}$  (fuera de entornos matemáticos)
    seg = re.sub(r"\b([A-Za-z])_([A-Za-z0-9]+)\b", r"$\1_{\2}$", seg)
    # Heurística: "vector v " -> "vector $v$ "
    seg = re.sub(r"(?i)(vector)\s+([a-zA-Z])(\b)", r"\1 $\2$\3", seg)
    return seg

def render_segmento_texto_con_parentesis(texto: str):
    # Divide por paréntesis y procesa cada segmento no-matemático; \(...\) no se usa, pero detectamos () con LaTeX "desnudo"
    partes = re.split(r"(\([^()]*\))", texto)
    if len(partes) == 1:
        st.write(preprocess_nonmath_segment(texto) if texto else "")
        return
    buffer_txt = ""
    for p in partes:
        if re.fullmatch(r"\([^()]*\)", p or ""):
            interior = p[1:-1]
            if contiene_latex(interior):
                if buffer_txt:
                    st.write(preprocess_nonmath_segment(buffer_txt)); buffer_txt = ""
                st.latex(interior.strip())
            else:
                buffer_txt += p
        else:
            buffer_txt += p
    if buffer_txt:
        st.write(preprocess_nonmath_segment(buffer_txt))

def render_with_math(texto:str):
    # Normaliza patrón de bloque con corchetes aislados a \[...\]
    texto = re.sub(r"(?ms)^\[\s*\n(.*?)\n\s*\]$", r"\\[\1\\]", texto)

    lineas = texto.split("\n")
    en_bloque_corchetes = False
    acumulador = []

    def render_line(linea):
        linea = linea.strip()
        # Bloques completos en una línea: \[...\] o $$...$$
        if re.fullmatch(r"\\\[.*\\\]", linea) or re.fullmatch(r"\$\$.*\$\$", linea):
            st.latex(re.sub(r"^\\\[|\\\]$|^\$\$|\$\$$", "", linea).strip()); return
        # Línea solo $...$
        if re.fullmatch(r"\$.*\$", linea):
            st.latex(linea.strip("$")); return

        # Inline: separar por $...$, $$...$$ o \[...\]
        partes = re.split(r"(\$\$.*?\$\$|\$.*?\$|\\\[.*?\\\])", linea)
        if len(partes) > 1:
            buffer_txt = ""
            for p in partes:
                if re.fullmatch(r"\$\$.*?\$\$|\$.*?\$|\\\[.*?\\\]", p):
                    if buffer_txt:
                        render_segmento_texto_con_parentesis(buffer_txt); buffer_txt = ""
                    st.latex(re.sub(r"^\\\[|\\\]$|^\$\$|\$\$|^\$|\$$", "", p).strip())
                else:
                    buffer_txt += p
            if buffer_txt:
                render_segmento_texto_con_parentesis(buffer_txt)
        else:
            # Si no hay delimitadores LaTeX, revisar si hay \[...\] incrustado
            m = re.search(r"\\\[(.*?)\\\]", linea)
            if m:
                antes = linea[:m.start()]; dentro = m.group(1); despues = linea[m.end():]
                if antes: render_segmento_texto_con_parentesis(antes)
                st.latex(dentro.strip())
                if despues: render_segmento_texto_con_parentesis(despues)
            else:
                # Procesar texto normal aplicando heurísticas (negritas, subíndices, etc.)
                st.write(preprocess_nonmath_segment(linea))

    for ln in lineas:
        s = ln.strip()
        # Soportar bloque estilo:
        # [
        #   <latex>
        # ]
        if not en_bloque_corchetes and s == "[":
            en_bloque_corchetes = True; acumulador = []; continue
        if en_bloque_corchetes:
            if s == "]":
                bloque = "\n".join(acumulador).strip()
                st.latex(bloque)
                en_bloque_corchetes = False; acumulador = []
            else:
                acumulador.append(ln)
        else:
            render_line(ln)

    if en_bloque_corchetes and acumulador:
        st.write(preprocess_nonmath_segment("\n".join(acumulador)))

# ---------- Lógica principal ----------
if correo:
    correo = correo.lower().strip()
    if correo not in LISTA_ESTUDIANTES:
        st.warning("Este correo no está autorizado para usar el chatbot.")
        st.stop()

    pregunta = st.text_area("Escribe tu pregunta sobre contenidos del curso:", height=150)

    if st.button("Preguntar") and pregunta.strip() != "":
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
                registro = [now, correo, pregunta, respuesta]
                with open("registro_chat_fis109o.csv", "a", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f); writer.writerow(registro)

            except Exception as e:
                st.error(f"Ocurrió un error: {e}")

    # Botón de descarga solo visible para el docente
    if correo == "alejandro.varas@uc.cl" and os.path.exists("registro_chat_fis109o.csv"):
        with open("registro_chat_fis109o.csv", "rb") as f:
            st.download_button(
                label="📥 Descargar registro de interacciones (.csv)",
                data=f,
                file_name="registro_chat_fis109o.csv",
                mime="text/csv"
            )

else:
    st.info("Por favor, ingresa tu correo UC para comenzar.")
