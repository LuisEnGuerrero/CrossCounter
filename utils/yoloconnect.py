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
    print("Modelo cargado correctamente:", model)
except Exception as e:
    st.error(f"Error al cargar el modelo: {e}")
    st.stop()


def get_image_inference(image_path: str):
    """
    Realiza inferencia en una imagen usando el modelo YOLOv8 entrenado localmente.
    """
    img = Image.open(image_path)
    results = model(img)


    # Depuración: imprime el contenido de los resultados
    print("Resultados de la inferencia:", results)


    try:
        detections = []  # Asegúrate de tener una lista vacía para las detecciones

        # Verifica si 'results' es iterable (en caso de que no lo sea)
        if isinstance(results, list):  
            for result in results:
                print("Resultado individual:", result)

                # Verifica si result tiene el atributo 'boxes'
                if hasattr(result, 'boxes'):
                    for box in result.boxes:
                        print("Contenido de box:", box)  # Depuración: Imprimir el contenido de la caja
                        # Verifica que box.xyxy sea un tensor con 4 elementos
                        if hasattr(box, 'xyxy') and len(box.xyxy) == 4:
                            detection = {
                                "name": model.names[int(box.cls.item())],  # Convertir a nombre de clase
                                "confidence": float(box.conf.item()),      # Convertir a valor flotante
                                "xmin": int(box.xyxy[0].cpu().item()),     # Coordenada X mínima
                                "ymin": int(box.xyxy[1].cpu().item()),     # Coordenada Y mínima
                                "xmax": int(box.xyxy[2].cpu().item()),     # Coordenada X máxima
                                "ymax": int(box.xyxy[3].cpu().item())      # Coordenada Y máxima
                            }
                            detections.append(detection)
                        else:
                            print("Error: box.xyxy no tiene 4 elementos o no existe.")
                else:
                    print("Error: 'result' no tiene el atributo 'boxes'.")
        else:
            print("Error: 'results' no es una lista.")

    except AttributeError as e:
        print("Error al acceder a las cajas detectadas:", e)

    # Para depurar, puedes imprimir las detecciones después
    print("Detecciones obtenidas:", detections)

   
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
        for result in results:
            for box in result.boxes:
                label = f'{model.names[int(box.cls.item())]} {box.conf.item():.2f}'
                cv2.rectangle(frame, (int(box.xyxy[0].item()), int(box.xyxy[1].item())), (int(box.xyxy[2].item()), (int(box.xyxy[3].item())), (0, 255, 0), 2))
                cv2.putText(frame, label, (int(box.xyxy[0].item()), int(box.xyxy[1].item()) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Escribir el frame procesado en el video de salida
        out.write(frame)

    cap.release()
    out.release()

    # Devolver la ruta del video procesado
    return {"video_path": temp_video_output.name}
