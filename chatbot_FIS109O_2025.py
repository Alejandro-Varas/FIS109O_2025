
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

correo = st.text_input("Correo UC:")

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

Te comunicas en español neutro, con matices chilenos, en un tono académico, claro, respetuoso y cercano. Apoyas el aprendizaje paso a paso, fomentas el pensamiento crítico, y ayudas a resolver dudas conceptuales y ejercicios.

Si no sabes algo o si una pregunta excede tu alcance, sugiere al estudiante consultar con el equipo docente. Nunca inventas información.
"""},
                        {"role": "user", "content": pregunta}
                    ]
                )
                respuesta = response["choices"][0]["message"]["content"]
                st.success("Respuesta del Chatbot:")

                for linea in respuesta.split("\n"):
                    if re.fullmatch(r"\$\$.*\$\$", linea) or re.fullmatch(r"\$.*\$", linea):
                        st.latex(linea.strip("$"))
                    else:
                        partes = re.split(r"(\$.*?\$)", linea)
                        if len(partes) > 1:
                            texto_buffer = ""
                            for parte in partes:
                                if parte.startswith("$") and parte.endswith("$"):
                                    if texto_buffer:
                                        st.write(texto_buffer)
                                        texto_buffer = ""
                                    st.latex(parte.strip("$"))
                                else:
                                    texto_buffer += parte
                            if texto_buffer:
                                st.write(texto_buffer)
                        else:
                            st.write(linea)

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                registro = [now, correo, pregunta, respuesta]

                with open("registro_chat_fis109o.csv", "a", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(registro)

            except Exception as e:
                st.error(f"Ocurrió un error: {e}")
else:
    st.info("Por favor, ingresa tu correo UC para comenzar.")
