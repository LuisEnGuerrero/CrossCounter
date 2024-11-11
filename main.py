import streamlit as st

# Configuración inicial de la página de Streamlit
st.set_page_config(page_title="IAMotorCycle CrossCounter", layout="wide")

from PIL import Image, ImageDraw
import os
from utils.yoloconnect import get_video_inference, get_image_inference
import tempfile
from utils.mongodb import save_inference_result, get_inference_statistics
import pandas as pd

st.title("Detección y Conteo de Motocicletas")

# Obtener las variables de entorno desde los secretos de Streamlit Cloud
MONGO_URI = st.secrets["MONGO"]["MONGO_URI"]
ROBOFLOW_API_KEY = st.secrets["ROBOFLOW"]["ROBOFLOW_API_KEY"]
ROBOFLOW_MODEL_ID = st.secrets["ROBOFLOW"]["ROBOFLOW_MODEL_ID"]
ROBOFLOW_API_URL = st.secrets["ROBOFLOW"]["ROBOFLOW_API_URL"]

# Seleccionar modo de inferencia: Imagen o Video
inference_mode = st.sidebar.selectbox("Selecciona el modo de inferencia", ("Imagen", "Video"))

# Sección para inferencia de imágenes
if inference_mode == "Imagen":
    st.subheader("Cargar una imagen")
    
    # Subir imagen
    uploaded_image = st.file_uploader("Elige una imagen", type=["jpg", "jpeg", "png"])

    if uploaded_image is not None:
        # Mostrar imagen original
        image = Image.open(uploaded_image)
        st.image(image, caption="Imagen Original", use_container_width=True)

        # Guardar la imagen temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_image_file:
            image.save(temp_image_file.name)
            temp_image_path = temp_image_file.name
            st.write(f"Imagen guardada temporalmente en: {temp_image_path}")

        # Realizar inferencia
        if st.button("Realizar inferencia"):
            with st.spinner("Realizando inferencia en la imagen..."):
                results = get_image_inference(temp_image_path)
                st.success("Inferencia completada.")

                # Guardar los resultados en MongoDB
                save_inference_result(results)

            # Visualizar resultados de inferencia
            st.subheader("Resultados de Inferencia")
            st.json(results)

            # Dibujar detecciones en la imagen
            image_with_boxes = image.copy()
            draw = ImageDraw.Draw(image_with_boxes)
            motorcycle_count = 0
            
            for prediction in results['predictions']:
                if prediction['class'] == 'motorcycle':
                    x, y, w, h = prediction['x'], prediction['y'], prediction['width'], prediction['height']
                    confidence = prediction['confidence']
                    motorcycle_count += 1
                    
                    # Dibuja el rectángulo en torno a la detección
                    top_left = (x - w / 2, y - h / 2)
                    bottom_right = (x + w / 2, y + h / 2)
                    draw.rectangle([top_left, bottom_right], outline="red", width=2)
                    draw.text(top_left, f"{confidence:.2f}", fill="red")
            
            st.write(f"Total de motocicletas detectadas: {motorcycle_count}")
            st.image(image_with_boxes, caption="Imagen con detecciones", use_container_width=True)

# Sección para inferencia de video
elif inference_mode == "Video":
    st.subheader("Cargar un video")
    
    # Subir video
    uploaded_video = st.file_uploader("Elige un video", type=["mp4", "avi", "mov"])

    if uploaded_video is not None:
        # Guardar el video temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video_file:
            temp_video_file.write(uploaded_video.read())
            temp_video_path = temp_video_file.name
            st.write(f"Video guardado temporalmente en: {temp_video_path}")

        # Realizar inferencia en el video
        if st.button("Realizar inferencia en video"):
            with st.spinner("Realizando inferencia en el video..."):
                results = get_video_inference(temp_video_path, fps=5, method="object-detection")
                st.success("Inferencia en video completada.")

                # Guardar los resultados en MongoDB
                save_inference_result(results)

            # Visualizar resultados de inferencia
            st.subheader("Resultados de Inferencia")
            st.json(results)

            # Descargar el video procesado (si está disponible en los resultados)
            signed_url = results.get("signed_url", None)
            if signed_url:
                st.markdown(f"[Descargar video procesado]({signed_url})")

        # Nota adicional para casos de error de cuota agotada
        if results.get("status_info") == "quota exhausted error":
            st.error("Error de cuota agotada. Considera aumentar el límite en Roboflow.")

# Gráfico de estadísticas
st.header("Estadísticas de Conteo de Motocicletas")
statistics = get_inference_statistics()

if statistics:
    # Convertir estadísticas a DataFrame para su uso en gráficos
    data = pd.DataFrame(statistics)
    data["_id"] = data["_id"].apply(lambda x: f"{x['day']} - {x['hour']}h")
    data = data.rename(columns={"total_motos": "Cantidad de Motocicletas", "_id": "Fecha y Hora"})
    data = data.set_index("Fecha y Hora")

    # Crear el gráfico
    st.line_chart(data)
    st.write(data)
else:
    st.write("No hay datos de estadísticas disponibles.")
    