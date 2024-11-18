import streamlit as st
from views.html import (
    anchor_html, header_html, logo_separator_html,
    qr_code_html, about_section_html, team_section_html, documentation_html, meta_html
)
from utils.visualization import show_statistics, draw_detections, show_inspected_data
from utils.inference import process_image, process_video, process_youtube_video
from utils.helpers import display_youtube_info
from utils.mongodb import save_inference_result_image, save_inference_result_video
from datetime import datetime
from pathlib import Path
import cv2
from dotenv import dotenv_values
import os
from PIL import Image
import base64

# Configuración de la página
st.set_page_config(
    page_title="AI·MotorCycle CrossCounter",
    layout="wide",
    page_icon="🛵",
)

# Cargar configuraciones de API
config = dotenv_values(".env")  # Cambiar según el entorno
YOUTUBE_API_KEY = config.get("YOUTUBE_API_KEY")

# Obtener la API de YouTube desde los secretos de Streamlit Cloud
YOUTUBE_API_KEY = st.secrets["YOUTUBE"]["YOUTUBE_API_KEY"]

# Cargar estilos CSS
def load_css(file_path):
    with open(file_path) as file:
        st.markdown(f"<style>{file.read()}</style>", unsafe_allow_html=True)

# Mostrar introducción
def load_markdown(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

load_css("views/styless.css")

# Renderizar secciones principales
st.markdown(meta_html(), unsafe_allow_html=True)
st.markdown(anchor_html(), unsafe_allow_html=True)
st.markdown(header_html(), unsafe_allow_html=True)

# Selección de modo de inferencia
inference_mode = st.sidebar.selectbox(
    "Selecciona el modo de inferencia", ("Imagen", "Video", "YouTube")
)

# Mostrar la imagen del logo en la barra lateral
st.sidebar.image('media/logox512.jpg', use_column_width=True)

# Inferencia en imágenes
if inference_mode == "Imagen":
    st.subheader("Cargar una Imagen")
    uploaded_image = st.file_uploader("Elige una imagen", type=["jpg", "jpeg", "png"])

    if uploaded_image:
        with st.spinner("Procesando la imagen..."):
            # Guardar imagen temporal
            temp_path = Path(f"temp_{uploaded_image.name}")
            with open(temp_path, "wb") as f:
                f.write(uploaded_image.read())

            # Procesar imagen
            detections = process_image(temp_path)

            # Dibujar detecciones
            original_image = Image.open(temp_path)
            image_with_boxes = draw_detections(original_image, detections["predictions"])

            # Guardar en MongoDB
            # st.write(detections) # identificar el formato de las detecciones
            inference_id = datetime.now().isoformat()  # Genera una marca de tiempo única como ID
            # convertir infecence_id a string
            # inference_id = str(inference_id)
            save_inference_result_image({
                "type": "image",
                "inference_id": detections.get("inference_id", inference_id),
                "motorcycle_count": len(detections["predictions"]),
            })

            # Mostrar la imagen procesada
            st.image(
                image_with_boxes,
                caption="Imagen con detecciones",
                use_container_width=True
            )
            st.success(f"Inferencia completada. Total de motocicletas detectadas: {len(detections['predictions'])}")


# Inferencia de Videos
elif inference_mode == "Video":
    st.subheader("Cargar un Video")
    uploaded_video = st.file_uploader("Elige un video", type=["mp4", "avi", "mov"])

    if uploaded_video:
        with st.spinner("Procesando el video..."):
            # Guardar video temporal
            temp_path = Path(f"temp_{uploaded_video.name}")
            with open(temp_path, "wb") as f:
                f.write(uploaded_video.read())

            # Obtener la cantidad total de frames para calcular el progreso
            cap = cv2.VideoCapture(str(temp_path))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()

            # Crear barra de progreso
            # progress_bar = st.progress(0)

            # Procesar video
            results = process_video(temp_path, frame_interval=99, total_frames=total_frames)

            # Guardar en MongoDB
            save_inference_result_video({
                "type": "video",
                "inference_id": results.get("inference_id", "unknown"),
                "motorcycle_count": results.get("total_motos", 0),
            })
            

            # Mostrar enlace de descarga del video procesado
            st.success(f"Inferencia completada. Total de motocicletas detectadas: {results.get('total_motos', 0)}")
            if "encoded_video" in results:
                st.download_button(
                    label="Descargar video procesado",
                    data=base64.b64decode(results["encoded_video"]),
                    file_name="video_procesado.mp4",
                    mime="video/mp4"
                )


# Inferencia en videos de YouTube
elif inference_mode == "YouTube":
    st.subheader("Procesar un Video de YouTube")
    youtube_url = st.text_input("Ingrese la URL del video de YouTube:")

    if youtube_url:
        with st.spinner("Obteniendo información del video..."):
            try:
                info = display_youtube_info(youtube_url)
                st.write(f"**Título:** {info['title']}")
                st.write(f"**Autor:** {info['author']}")
                st.write(f"**Duración:** {info['duration'] // 60} minutos {info['duration'] % 60} segundos")

                with st.spinner("Procesando el video de YouTube..."):
                    results = process_youtube_video(youtube_url)

                st.success(f"Inferencia completada. Total de motocicletas detectadas: {results.get('total_motos', 0)}")
                if "processed_video_path" in results:
                    st.markdown(
                        f"[Descargar video procesado]({results['processed_video_path']})",
                        unsafe_allow_html=True
                    )


            except Exception as e:
                st.error(f"Error procesando el video de YouTube: {e}")



# Sección de Estadísticas
st.header("Estadísticas de Conteo de Motocicletas")
show_statistics()
show_inspected_data() 
st.markdown(logo_separator_html(), unsafe_allow_html=True)

# Sección 'Acerca de'
st.markdown(about_section_html(), unsafe_allow_html=True)

# Sección del Equipo
st.markdown(team_section_html(), unsafe_allow_html=True)
st.markdown(logo_separator_html(), unsafe_allow_html=True)

# Sección de Introducción
intro_content = load_markdown("views/intro.md")
st.markdown(intro_content)

# Sección de Documentación
st.markdown(documentation_html(), unsafe_allow_html=True)

# Pie de Página
st.markdown(logo_separator_html(), unsafe_allow_html=True)
