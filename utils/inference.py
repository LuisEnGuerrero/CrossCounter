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
    Procesa una imagen con el modelo YOLOv8.

    Args:
        image_path (str): Ruta de la imagen a procesar.

    Returns:
        dict: Resultados de las detecciones en formato esperado.
    """
    # Realizar la inferencia
    results = model(image_path)

    # Estructurar los resultados en el formato esperado
    detections = []
    for result in results:
        for box in result.boxes:
            # Asegurarse de que las coordenadas se convierten correctamente
            st.write("recibimos box.xyxy: ", box.xyxy) # box.xyxy: tensor([[  0.0000,  63.0000,  99.0000,  99.0000]])
            xyxy = box.xyxy[0].cpu().numpy()  # Obtener el array del primer elemento
            detections.append({
                "name": result.names[int(box.cls)],
                "confidence": float(box.conf),
                "xmin": int(xyxy[0]),  # Extraer xmin
                "ymin": int(xyxy[1]),  # Extraer ymin
                "xmax": int(xyxy[2]),  # Extraer xmax
                "ymax": int(xyxy[3]),  # Extraer ymax
            })

    return {"predictions": detections}


def process_video(video_path):
    """
    Procesa un video con el modelo YOLOv8.

    Args:
        video_path (str): Ruta del video a procesar.

    Returns:
        dict: Resultados de las detecciones en el video.
    """
    # Realizar la inferencia
    results = model(video_path)

    # Estructurar los resultados en el formato esperado
    detections = []
    for result in results:
        for box in result.boxes:
            detections.append({
                "name": result.names[int(box.cls)],
                "confidence": float(box.conf),
                "xmin": int(box.xyxy[0].cpu().numpy()),  # Convertir tensor a escalar
                "ymin": int(box.xyxy[1].cpu().numpy()),  # Convertir tensor a escalar
                "xmax": int(box.xyxy[2].cpu().numpy()),  # Convertir tensor a escalar
                "ymax": int(box.xyxy[3].cpu().numpy()),  # Convertir tensor a escalar
            })

    return {"predictions": detections}
