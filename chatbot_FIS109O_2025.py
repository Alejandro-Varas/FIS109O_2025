import streamlit as st
import openai
import csv
import os
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

st.markdown("Este chatbot responde preguntas relacionadas con el curso FIS109O - Física para Odontología. Por favor, ingresa tu correo UC para comenzar.")

correo = st.text_input("Correo UC:")

if correo:
    correo = correo.lower().strip()
    if correo not in lista_estudiantes:
        st.warning("Este correo no está autorizado para usar el chatbot.")
        st.stop()

    pregunta = st.text_area("Escribe tu pregunta:", height=150)

    if st.button("Preguntar") and pregunta.strip() != "":
        with st.spinner("Pensando..."):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": f"""
Eres FIS109O Assistant, el asistente académico del curso Física para Odontología (FIS109O) de la Pontificia Universidad Católica de Chile. Respondes en español neutro, con un tono académico, claro y respetuoso. Apoyas el aprendizaje con ejemplos clínicos y nunca inventas información. Si no sabes algo, sugieres consultar con el profesor o ayudantes.
"""},
                        {"role": "user", "content": pregunta}
                    ]
                )
                respuesta = response["choices"][0]["message"]["content"]
                st.success("Respuesta del Chatbot:")
                st.write(respuesta)

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                registro = [now, correo, pregunta, respuesta]

                with open("registro_chat_fis109o.csv", "a", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(registro)

            except Exception as e:
                st.error(f"Ocurrió un error: {e}")
else:
    st.info("Por favor, ingresa tu correo UC para comenzar.")
