
import streamlit as st
import openai
import csv
import os
from datetime import datetime

# CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Chatbot FIS109O", page_icon="🦷")
st.title("🦷 Chatbot Educativo - Física para Odontología")

# API Key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# LISTA BLANCA DE CORREOS UC (modifica esta lista con tus estudiantes reales)
lista_estudiantes = [
    "alejandro.varas@uc.cl",
    "caguilarc9@estudiante.uc.cl",
    "alarconvd@estudiante.uc.cl",
    "valalvarezz@estudiante.uc.cl",
    "fran.aranibar@estudiante.uc.cl",
    "alonso.araya@estudiante.uc.cl",
    "karayat@estudiante.uc.cl",
    "valentina.arriaza@estudiante.uc.cl",
    "trinidadarrieta@estudiante.uc.cl",
    "dastorgac@estudiante.uc.cl",
    "cbarbanoa@estudiante.uc.cl",
    "vicentecampana@estudiante.uc.cl",
    "mcharpentier@estudiante.uc.cl",
    "julieta.chepillo@estudiante.uc.cl",
    "fcidm@estudiante.uc.cl",
    "acorreag6@estudiante.uc.cl",
    "dan.cruz@estudiante.uc.cl",
    "adelrioconcha@estudiante.uc.cl",
    "benja.diaz.massardo@estudiante.uc.cl",
    "hans.diethelm@estudiante.uc.cl",
    "vdingemans@estudiante.uc.cl",
    "agarn@estudiante.uc.cl",
    "sofiagomezr@estudiante.uc.cl",
    "pgutierrz@estudiante.uc.cl",
    "fherrerah@estudiante.uc.cl",
    "agustin.jimenez@estudiante.uc.cl",
    "elamr@estudiante.uc.cl",
    "francisca.lepem@estudiante.uc.cl",
    "rafaella.lertora@estudiante.uc.cl",
    "alonso.llantn@estudiante.uc.cl",
    "bbenjalopez@estudiante.uc.cl",
    "moana.maltry@estudiante.uc.cl",
    "ignacio.mancilla@estudiante.uc.cl",
    "amartinezlobos@estudiante.uc.cl",
    "julieta.maturana@estudiante.uc.cl",
    "amendezi@estudiante.uc.cl",
    "angelina.meta@estudiante.uc.cl",
    "smuov@estudiante.uc.cl",
    "bolivaresf@estudiante.uc.cl",
    "nicole.orellana@estudiante.uc.cl",
    "maiteosorioriquelme@estudiante.uc.cl",
    "maite.pe@estudiante.uc.cl",
    "sofia.pavez@estudiante.uc.cl",
    "constanza.p@estudiante.uc.cl",
    "sofiapinop@estudiante.uc.cl",
    "gaspar.pizaro@estudiante.uc.cl",
    "matias.pulgar@estudiante.uc.cl",
    "vquitral@estudiante.uc.cl",
    "estephania.reinoso.h@estudiante.uc.cl",
    "frepetto@estudiante.uc.cl",
    "mrevecoperez@estudiante.uc.cl",
    "mreyesp8@estudiante.uc.cl",
    "ers477@estudiante.uc.cl",
    "saromang@estudiante.uc.cl",
    "juan.romero@estudiante.uc.cl",
    "valeronderos06@estudiante.uc.cl",
    "javi.rozasortega@estudiante.uc.cl",
    "martisalneira@estudiante.uc.cl",
    "catalinasalinas@estudiante.uc.cl",
    "mfsalinas2@uc.cl",
    "r.santana@estudiante.uc.cl",
    "isantosr@estudiante.uc.cl",
    "florencia.serra@uc.cl",
    "vsubercaseaux@estudiante.uc.cl",
    "javieratagle@estudiante.uc.cl",
    "emiliaturrieta@estudiante.uc.cl",
    "ijurzuac@estudiante.uc.cl",
    "sebastianvaldebenito@estudiante.uc.cl",
    "mvallejoc@estudiante.uc.cl",
    "dvillegasf@estudiante.uc.cl",
    "valentina.wall@estudiante.uc.cl"
]

# INSTRUCCIONES
st.markdown("Este chatbot responde preguntas relacionadas con el curso FIS109O - Física para Odontología. Por favor, ingresa tu correo UC para comenzar.")

# IDENTIFICACIÓN
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
                        {"role": "system", "content": "Eres un tutor experto en Física para Odontología. Responde con ejemplos clínicos cuando sea posible, de forma clara, rigurosa y pedagógica."},
                        {"role": "user", "content": pregunta}
                    ]
                )
                respuesta = response["choices"][0]["message"]["content"]
                st.success("Respuesta del Chatbot:")
                st.write(respuesta)

                # GUARDAR EN CSV
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                registro = [now, correo, pregunta, respuesta]

                with open("registro_chat_fis109o.csv", "a", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(registro)

            except Exception as e:
                st.error(f"Ocurrió un error: {e}")
else:
    st.info("Por favor, ingresa tu correo UC para comenzar.")
