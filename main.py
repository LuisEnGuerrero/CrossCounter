import uuid
import streamlit as st
from views.html import (
    anchor_html, header_html, logo_separator_html,
    qr_code_html, about_section_html, team_section_html, documentation_html, meta_html
)
from utils.visualization import show_statistics, draw_detections, show_inspected_data
from utils.inference import (
    process_image, 
    process_video, 
    process_youtube_video,
    process_youtube_video_inference,
)
from utils.helpers import (
    get_youtube_video_metadata,
    download_youtube_video,
)
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

# Mostrar Contenido Markdown
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
st.sidebar.image('media/logox512.jpg', use_container_width=True)

# Inferencia en imágenes
if inference_mode == "Imagen":
    st.subheader("Cargar una Imagen")

    # Restablecer estado al cambiar de modo de inferencia
    if "image_uploaded" not in st.session_state:
        st.session_state.image_uploaded = None  # Inicializar estado

    # Cargar nueva imagen
    uploaded_image = st.file_uploader("Elige una imagen", type=["jpg", "jpeg", "png"])

    # Detectar si se cargó una nueva imagen
    if uploaded_image and uploaded_image != st.session_state.image_uploaded:
        st.session_state.image_uploaded = uploaded_image  # Actualizar estado con la nueva imagen

        # Crear un contenedor vacío para mostrar los frames procesados
        image_container = st.empty()  

        temp_path = Path(f"temp_{uploaded_image.name}")

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

            # Generar campos necesarios para guardar en MongoDB
            inference_id = str(datetime.now().isoformat())  # Marca de tiempo única
            detection_id = str(uuid.uuid4())  # Generar un ID único para la detección
            timestamp = datetime.now()  # Fecha y hora de la inferencia


            # Guardar en MongoDB
            # st.write(detections) # identificar el formato de las detecciones
            save_inference_result_image({
                "type": "image",
                "inference_id": inference_id,
                "detection_id": detection_id,
                "motorcycle_count": len(detections["predictions"]),
                "timestamp": timestamp,
            })

            # Mostrar el frame procesado en el contenedor de imagen
            if image_container:
            # Mostrar la imagen procesada
                image_container.image(
                    image_with_boxes,
                    caption="Imagen con detecciones",
                    use_container_width=True
                )
                st.success(f"Inferencia completada. Total de motocicletas detectadas: {len(detections['predictions'])}")

                # Eliminar archivo temporal
        try:
            temp_path.unlink()  # Eliminar archivo temporal
            # st.info("Imagen temporal eliminada correctamente.")
        except FileNotFoundError:
            st.warning("No se encontró la imagen temporal para eliminar.")
        except Exception as e:
            st.error(f"Error al intentar eliminar la imagen temporal: {e}")



# Inferencia de Videos
elif inference_mode == "Video":
    st.subheader("Cargar un Video")
    uploaded_video = st.file_uploader("Elige un video", type=["mp4", "avi", "mov"])

    # Verificar si hay un video procesado previamente
    if "processed_video" not in st.session_state:
        st.session_state["processed_video"] = None

    if uploaded_video:
        if st.session_state["processed_video"] != uploaded_video.name:
            with st.spinner("Procesando el video..."):
                # Guardar video temporal
                temp_path = Path(f"temp_{uploaded_video.name}")
                with open(temp_path, "wb") as f:
                    f.write(uploaded_video.read())

                # Obtener la cantidad total de frames para calcular el progreso
                cap = cv2.VideoCapture(str(temp_path))
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.release()

                # Procesar video
                results = process_video(temp_path, frame_interval=101, total_frames=total_frames)

                # Guardar en MongoDB
                save_inference_result_video(
                    inference_id=results["inference_id"],
                    motorcycle_count_per_frame=results["motorcycle_count_per_frame"],
                )

                # Mostrar enlace de descarga del video procesado
                st.success(f"Inferencia completada. Total de motocicletas detectadas: {results.get('total_motos', 0)}")
                if "encoded_video" in results:
                    st.download_button(
                        label="Descargar video procesado",
                        data=base64.b64decode(results["encoded_video"]),
                        file_name="video_procesado.mp4",
                        mime="video/mp4"
                    )

                # Actualizar estado
                st.session_state["processed_video"] = uploaded_video.name

                # Eliminar archivo temporal
                try:
                    temp_path.unlink()
                    # st.info("Video temporal eliminado correctamente.")
                except Exception as e:
                    st.error(f"Error al eliminar el archivo temporal: {e}")
        else:
            print("El video ya ha sido procesado. Carga un nuevo video para realizar otra inferencia.")
            

# Inferencia en videos de YouTube
elif inference_mode == "YouTube":
    st.subheader("Procesar un Video de YouTube")
    youtube_url = st.text_input("Introduce la URL del video de YouTube")

    # Inicializar el estado de sesión para YouTube si no existe
    if "YouTube" not in st.session_state:
        st.session_state["YouTube"] = {
            "video_processed": False,
            "video_path": None,
            "results": None,
            "processing": False,
            "progress": 0,
        }

    # Mostrar barra de progreso si el procesamiento está en curso
    if st.session_state["YouTube"]["processing"]:
        st.progress(st.session_state["YouTube"]["progress"])

    if youtube_url:
        if st.button("Iniciar Inferencia") and not st.session_state["YouTube"]["processing"]:
            st.session_state["YouTube"]["processing"] = True
            st.session_state["YouTube"]["progress"] = 0  # Reiniciar barra de progreso

            with st.spinner("Procesando el video de YouTube..."):
                try:
                    # Descargar y procesar el video
                    video_metadata = get_youtube_video_metadata(youtube_url)
                    is_large = video_metadata["filesize_approx"] > 200 * 1024

                    if is_large:
                        st.warning("El video es grande y será procesado en segmentos.")
                        results = process_youtube_video(youtube_url)
                    else:
                        video_path = download_youtube_video(youtube_url)
                        if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
                            raise ValueError("El video descargado está vacío o no existe.")

                        results = process_youtube_video_inference(video_path)

                    # Actualizar el estado en la sesión
                    st.session_state["YouTube"]["processing"] = False
                    st.session_state["YouTube"]["video_processed"] = True
                    st.session_state["YouTube"]["video_path"] = results["processed_video_path"]
                    st.session_state["YouTube"]["results"] = results

                    # Mostrar mensaje de éxito
                    st.success(f"Inferencia completada. Total de motocicletas detectadas: {results['total_motos']}")

                except Exception as e:
                    st.session_state["YouTube"]["processing"] = False
                    st.error(f"Error al procesar el video de YouTube: {e}")

    # Mostrar el video procesado si ya fue procesado correctamente
    if st.session_state["YouTube"]["video_processed"]:
        st.video(st.session_state["YouTube"]["video_path"])
        st.write("Resultados de la Inferencia:")
        st.json(st.session_state["YouTube"]["results"])

        # Botón para descargar el video procesado
        with open(st.session_state["YouTube"]["video_path"], "rb") as f:
            st.download_button(
                label="Descargar video procesado",
                data=f,
                file_name="video_procesado_youtube.mp4",
                mime="video/mp4"
            )


# Sección de Estadísticas
st.header("Estadísticas de Conteo de Motocicletas")
show_statistics()
# show_inspected_data() # Mostrar datos almacenados en MongoDB
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
