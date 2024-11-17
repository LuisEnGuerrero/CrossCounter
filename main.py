import streamlit as st
from views.html import (
    anchor_html, header_html, logo_separator_html,
    qr_code_html, about_section_html, team_section_html, documentation_html
)
from utils.visualization import show_statistics, draw_detections
from utils.inference import process_image, process_video
from utils.mongodb import save_inference_result
from pathlib import Path
import os

# Configuración de la página
st.set_page_config(
    page_title="AI·MotorCycle CrossCounter",
    layout="wide",
    page_icon="🛵",
)

# Cargar estilos CSS
def load_css(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

st.markdown(
    f"""
    <style>
        {load_css("views/styless.md")}
    </style>
    """,
    unsafe_allow_html=True
)

# Mostrar introducción
def load_markdown(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

intro_content = load_markdown("views/intro.md")
st.markdown(intro_content)

# Renderizar secciones principales
st.markdown(anchor_html(), unsafe_allow_html=True)
st.markdown(header_html(), unsafe_allow_html=True)

# Selección de modo de inferencia
inference_mode = st.sidebar.selectbox(
    "Selecciona el modo de inferencia", ("Imagen", "Video")
)

# Inferencia de Imágenes
if inference_mode == "Imagen":
    st.markdown(logo_separator_html(), unsafe_allow_html=True)
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
            image_with_boxes = draw_detections(original_image, detections)

            # Guardar en MongoDB
            save_inference_result({
                "type": "image",
                "inference_id": detections.get("inference_id", "unknown"),
                "motorcycle_count": len(detections["predictions"]),
            })

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
            save_inference_result({
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

# Sección de Estadísticas
st.header("Estadísticas de Conteo de Motocicletas")
show_statistics()

# Sección 'Acerca de'
st.markdown(about_section_html(), unsafe_allow_html=True)

# Sección del Equipo
st.markdown(team_section_html(), unsafe_allow_html=True)

# Sección de Documentación
st.markdown(documentation_html(), unsafe_allow_html=True)

# Pie de Página
st.markdown(logo_separator_html(), unsafe_allow_html=True)
