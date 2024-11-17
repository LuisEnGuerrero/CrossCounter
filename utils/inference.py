import streamlit as st
from PIL import Image, ImageDraw
from utils.yoloconnect import get_image_inference, get_video_inference
from ultralytics import YOLO

# Cargar el modelo YOLOv8
model_path = "models/best.pt"
try:
    model = YOLO(model_path, verbose=False)
    # st.write("Modelo cargado correctamente!")
except Exception as e:
    st.error(f"Error al cargar el modelo: {e}")
    st.stop()


def process_image(image_path):
    """
    Procesa una imagen utilizando la lógica definida en yoloconnect.

    Args:
        image_path (str): Ruta de la imagen.

    Returns:
        dict: Resultados de detecciones en formato esperado.
    """
    detections = get_image_inference(image_path)
    return {"predictions": detections}


def process_video(video_path):
    """
    Procesa un video utilizando la lógica definida en yoloconnect.

    Args:
        video_path (str): Ruta del video.

    Returns:
        dict: Incluye la ruta al video procesado y conteo total de detecciones.
    """
    return get_video_inference(video_path)

