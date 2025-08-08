
import streamlit as st
import openai
import csv
import os
import re
from datetime import datetime

st.set_page_config(page_title="Chatbot FIS109O", page_icon="🦷")
st.title("🦷 Chatbot Educativo - Física para Odontología")

openai.api_key = st.secrets["OPENAI_API_KEY"]

lista_estudiantes = [
    "ana.perez@uc.cl",
    "jperez5@uc.cl",
    "mmendez@uc.cl",
    "camila.rojas@uc.cl",
    "luis.gomez@uc.cl",
    "francisco.torres@uc.cl",
    "sofia.vidal@uc.cl",
    "alejandro.varas@uc.cl"
]

st.markdown("Este chatbot responde preguntas de contenidos del curso FIS109O - Física para Odontología. Por favor, ingresa tu correo UC para comenzar.")
st.warning("🔒 Toda pregunta enviada será registrada con fines educativos y podrá ser revisada por el equipo docente del curso.")

correo = st.text_input("Correo UC:")

def contiene_latex(s: str) -> bool:
    return bool(re.search(r"\\(vec|frac|sqrt|hat|bar|overline|underline|cdot|times|sin|cos|tan|alpha|beta|gamma|theta|pi|sum|int|partial)\b|[\^_]", s))

def render_segmento_texto_con_parentesis(texto: str):
    # Divide por paréntesis y renderiza como LaTeX si dentro hay comandos típicos
    partes = re.split(r"(\([^()]*\))", texto)  # conserva ( ... )
    if len(partes) == 1:
        st.write(texto if texto else "")
        return
    buffer_txt = ""
    for p in partes:
        if re.fullmatch(r"\([^()]*\)", p or ""):
            # quitar paréntesis exteriores
            interior = p[1:-1]
            if contiene_latex(interior):
                if buffer_txt:
                    st.write(buffer_txt); buffer_txt = ""
                st.latex(interior.strip())
            else:
                buffer_txt += p
        else:
            buffer_txt += p
    if buffer_txt:
        st.write(buffer_txt)

def render_with_math(texto:str):
    lineas = texto.split("\n")
    en_bloque_corchetes = False
    acumulador = []

    def render_line(linea):
        linea = linea.strip()
        # Bloques completos en una línea: \[...\] o $$...$$
        if re.fullmatch(r"\\\[.*\\\]", linea) or re.fullmatch(r"\$\$.*\$\$", linea):
            st.latex(re.sub(r"^\\\[|\\\]$|^\$\$|\$\$$", "", linea).strip()); return
        # Línea sólo $...$
        if re.fullmatch(r"\$.*\$", linea):
            st.latex(linea.strip("$")); return
        # Inline: separar por $...$, $$...$$ o \[...\]
        partes = re.split(r"(\$\$.*?\$\$|\$.*?\$|\\\[.*?\\\])", linea)
        if len(partes) > 1:
            buffer_txt = ""
            for p in partes:
                if re.fullmatch(r"\$\$.*?\$\$|\$.*?\$|\\\[.*?\\\]", p):
                    if buffer_txt:
                        # procesar posibles paréntesis con LaTeX en el texto acumulado
                        render_segmento_texto_con_parentesis(buffer_txt)
                        buffer_txt = ""
                    st.latex(re.sub(r"^\\\[|\\\]$|^\$\$|\$\$|^\$|\$$", "", p).strip())
                else:
                    buffer_txt += p
            if buffer_txt:
                render_segmento_texto_con_parentesis(buffer_txt)
        else:
            # Si no hay delimitadores LaTeX, revisar si hay paréntesis con LaTeX dentro
            if contiene_latex(linea):
                # Intentar detectar bloques \[ ... \] dentro de la línea
                m = re.search(r"\\\[(.*?)\\\]", linea)
                if m:
                    antes = linea[:m.start()]; dentro = m.group(1); despues = linea[m.end():]
                    if antes: render_segmento_texto_con_parentesis(antes)
                    st.latex(dentro.strip())
                    if despues: render_segmento_texto_con_parentesis(despues)
                else:
                    render_segmento_texto_con_parentesis(linea)
            else:
                st.write(linea)

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
        st.write("\n".join(acumulador))

if correo:
    correo = correo.lower().strip()
    if correo not in lista_estudiantes:
        st.warning("Este correo no está autorizado para usar el chatbot.")
        st.stop()

    pregunta = st.text_area("Escribe tu pregunta sobre contenidos del curso:", height=150)

    if st.button("Preguntar") and pregunta.strip() != "":
        with st.spinner("Pensando..."):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": f"""
Eres FIS109O Assistant, un asistente académico para estudiantes de Odontología en el curso Física para Odontología (FIS109O) de la Pontificia Universidad Católica de Chile.

Tu función principal es explicar con claridad y rigor los contenidos del curso: mecánica, fluidos, electricidad, ondas y radiación, enfocados en su aplicación clínica. Usas analogías relevantes como palancas mandibulares, irrigadores dentales, presión en jeringas, entre otros.

Formato de ecuaciones (OBLIGATORIO):
- Para matemáticas en línea usa: $ ... $
- Para ecuaciones en bloque usa: \[ ... \]  (o $$ ... $$)
- No uses corchetes literales "[" y "]" para delimitar ecuaciones.
- No dejes expresiones LaTeX sin $ o \[ \].

Te comunicas en español neutro, con matices chilenos, en un tono académico, claro, respetuoso y cercano. Apoyas el aprendizaje paso a paso, fomentas el pensamiento crítico, y ayudas a resolver dudas conceptuales y ejercicios. Si no sabes algo o si una pregunta excede tu alcance, sugiere al estudiante consultar con el equipo docente. Nunca inventas información.
"""},
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
