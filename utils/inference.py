from PIL import Image, ImageDraw
from utils.yoloconnect import get_image_inference, get_video_inference
from ultralytics import YOLO

# Cargar el modelo YOLO
model = YOLO("models/best.pt")  # Cambiar según el modelo

def process_image(image_path):
    """
    Procesa una imagen cargada para realizar inferencias con YOLO.
    Dibuja las detecciones directamente en la imagen.
    
    Args:
        image_file: Archivo de imagen cargado por el usuario.
    
    Returns:
        dict: Contiene la imagen con detecciones y el conteo total de motocicletas.
    """
    # Realizar la inferencia
    results = model(image_path)

    # Estructurar los resultados en el formato esperado
    detections = []
    for result in results:
        for box in result.boxes:
            detections.append({
                "name": result.names[int(box.cls)],
                "confidence": float(box.conf),
                "xmin": int(box.xyxy[0]),
                "ymin": int(box.xyxy[1]),
                "xmax": int(box.xyxy[2]),
                "ymax": int(box.xyxy[3]),
            })

    return {"predictions": detections}