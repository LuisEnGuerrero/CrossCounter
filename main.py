import streamlit as st
from views.html import (
    anchor_html, header_html, logo_separator_html,
    qr_code_html, about_section_html, team_section_html, documentation_html
)
from utils.visualization import show_statistics, draw_detections
from utils.inference import process_image, process_video
from utils.mongodb import save_inference_result_image
from datetime import datetime
from pathlib import Path
from pytube import YouTube
from yt_dlp import YoutubeDL
from dotenv import dotenv_values
import os
from PIL import Image

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
st.markdown(anchor_html(), unsafe_allow_html=True)
st.markdown(header_html(), unsafe_allow_html=True)

# Selección de modo de inferencia
inference_mode = st.sidebar.selectbox(
    "Selecciona el modo de inferencia", ("Imagen", "Video", "YouTube")
)

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
    st.markdown(logo_separator_html(), unsafe_allow_html=True)
    st.subheader("Cargar un Video")
    uploaded_video = st.file_uploader("Elige un video", type=["mp4", "avi", "mov"])

    if uploaded_video:
        with st.spinner("Procesando el video..."):
            # Guardar video temporal
            temp_path = Path(f"temp_{uploaded_video.name}")
            with open(temp_path, "wb") as f:
                f.write(uploaded_video.read())

            # Procesar video
            results = process_video(temp_path)

            # Guardar en MongoDB
            save_inference_result_image({
                "type": "video",
                "inference_id": results.get("inference_id", "unknown"),
                "motorcycle_count": results.get("total_motos", 0),
            })

            # Mostrar enlace de descarga del video procesado
            st.success(f"Inferencia completada. Total de motocicletas detectadas: {results.get('total_motos', 0)}")
            if "processed_video_path" in results:
                st.markdown(
                    f"[Descargar video procesado]({results['processed_video_path']})",
                    unsafe_allow_html=True
                )


# Inferencia en videos de YouTube
elif inference_mode == "YouTube":
    st.markdown(logo_separator_html(), unsafe_allow_html=True)
    st.subheader("Procesar un Video de YouTube")
    youtube_url = st.text_input("Ingrese la URL del video de YouTube:")

    if youtube_url:
        with st.spinner("Obteniendo información del video..."):
            try:
                # Obtener información básica del video
                yt = YouTube(youtube_url)
                st.write(f"**Título:** {yt.title}")
                st.write(f"**Duración:** {yt.length // 60} minutos {yt.length % 60} segundos")
                st.write(f"**Autor:** {yt.author}")

                # Decidir inferencia directa o segmentada
                if yt.filesize_approx <= 200 * 1024 * 1024:  # Inferencia directa
                    st.info("El video es menor a 200MB. Se procesará directamente.")
                    temp_path = Path(f"temp_youtube.mp4")
                    yt.streams.get_highest_resolution().download(filename=temp_path)

                    # Procesar el video directamente
                    results = process_video(temp_path)

                    # Mostrar resultados
                    st.success(f"Inferencia completada. Total de motocicletas detectadas: {results.get('total_motos', 0)}")
                    if "processed_video_path" in results:
                        st.markdown(
                            f"[Descargar video procesado]({results['processed_video_path']})",
                            unsafe_allow_html=True
                        )

                else:  # Segmentación del video
                    st.warning("El video es mayor a 200MB. Será segmentado y procesado por partes.")
                    ydl_opts = {"format": "best", "outtmpl": "segment_%(part)d.mp4"}
                    with YoutubeDL(ydl_opts) as ydl:
                        ydl.download([youtube_url])

                    segment_paths = sorted(Path(".").glob("segment_*.mp4"))
                    for segment in segment_paths:
                        with st.spinner(f"Procesando segmento: {segment.name}"):
                            results = process_video(segment)

                            # Guardar resultados parciales
                            save_inference_result_image({
                                "type": "youtube_segment",
                                "inference_id": results.get("inference_id", "unknown"),
                                "motorcycle_count": results.get("total_motos", 0),
                            })
                            os.remove(segment)

                    st.success("Segmentos procesados. Descarga el último segmento procesado:")
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
