import torch
import streamlit as st
from PIL import Image
import cv2
import tempfile
import os
from ultralytics import YOLO  # Si usas YOLOv8

# Cargar el modelo YOLOv8
model_path = "models/best.pt"
try:
    model = YOLO(model_path)
except Exception as e:
    st.error(f"Error al cargar el modelo: {e}")
    st.stop()


def get_image_inference(image_path: str):
    """
    Realiza inferencia en una imagen usando el modelo YOLOv8 entrenado localmente.
    """
    img = Image.open(image_path)
    results = model(img)

    # Convertir los resultados a un formato de diccionario
    detections = []
    for result in results:
        for box in result.boxes:
            detection = {
                "xmin": box.xyxy[0].item(),
                "ymin": box.xyxy[1].item(),
                "xmax": box.xyxy[2].item(),
                "ymax": box.xyxy[3].item(),
                "confidence": box.conf.item(),
                "class": int(box.cls.item()),
                "name": model.names[int(box.cls.item())]
            }
            detections.append(detection)
    
    return detections

def get_video_inference(video_path: str, fps: int = 5):
    """
    Realiza inferencia en video usando el modelo YOLOv8 entrenado localmente.
    """
    # Abrir el video
    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    # Crear un archivo temporal para el video de salida
    temp_video_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    out = cv2.VideoWriter(temp_video_output.name, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Realizar inferencia en el frame
        results = model(frame)
        for *box, conf, cls in results.xyxy[0]:
            label = f'{model.names[int(cls)]} {conf:.2f}'
            cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 255, 0), 2)
            cv2.putText(frame, label, (int(box[0]), int(box[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Escribir el frame procesado en el video de salida
        out.write(frame)

    cap.release()
    out.release()

    # Devolver la ruta del video procesado
    return {"video_path": temp_video_output.name}
