import streamlit as st
import torch
from PIL import Image
import cv2
import tempfile
import os
from ultralytics import YOLO  # Si usas YOLOv8

# Cargar el modelo YOLOv8
model_path = "models/best.pt"
try:
    model = YOLO(model_path, verbose=False)
    st.write("Modelo cargado correctamente!")
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

    detections = []  # Asegúrate de tener una lista vacía para las detecciones

    for result in results:
        print("Resultado individual:", result)

        # Verifica si result tiene el atributo 'boxes'
        if hasattr(result, 'boxes'):
            for box in result.boxes:
                print("Contenido de box:", box)  # Depuración: Imprimir el contenido de la caja
                # Verifica que box.xyxy sea un tensor con 4 elementos
                if hasattr(box, 'xyxy') and box.xyxy.shape[-1] == 4:
                    xyxy = box.xyxy[0]  # Acceder a la primera fila si es un tensor 2D
                    detection = {
                        "name": model.names[int(box.cls.item())],  # Convertir a nombre de clase
                        "confidence": float(box.conf.item()),      # Convertir a valor flotante
                        "xmin": int(xyxy[0].item()),               # Coordenada X mínima
                        "ymin": int(xyxy[1].item()),               # Coordenada Y mínima
                        "xmax": int(xyxy[2].item()),               # Coordenada X máxima
                        "ymax": int(xyxy[3].item())                # Coordenada Y máxima
                    }
                    detections.append(detection)
                else:
                    print(f"Error: box.xyxy no tiene 4 elementos, contiene: {len(box.xyxy)} elementos!")
        else:
            print("Error: 'result' no tiene el atributo 'boxes'.")

    # Para depurar, puedes imprimir las detecciones después
    st.write("Detecciones obtenidas:", detections)

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

            # Procesar solo un frame de cada nueve
            if frame_count % 9 == 0:
                # Realizar inferencia en el frame
                results = model(frame)
                for result in results:
                    for box in result.boxes:
                        label = f'{model.names[int(box.cls.item())]} {box.conf.item():.2f}'
                        xyxy = box.xyxy[0]  # Acceder a la primera fila si es un tensor 2D
                        cv2.rectangle(frame, (int(xyxy[0].item()), int(xyxy[1].item())), (int(xyxy[2].item()), int(xyxy[3].item())), (0, 255, 0), 2)
                        cv2.putText(frame, label, (int(xyxy[0].item()), int(xyxy[1].item()) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # Mostrar el frame procesado
                st.image(frame, channels="BGR", caption=f"Frame {frame_count}")

                # Guardar los resultados en MongoDB
                detections = []
                for result in results:
                    if hasattr(result, 'boxes'):
                        for box in result.boxes:
                            if hasattr(box, 'xyxy') and box.xyxy.shape[-1] == 4:
                                xyxy = box.xyxy[0]
                                detection = {
                                    "name": model.names[int(box.cls.item())],
                                    "confidence": float(box.conf.item()),
                                    "xmin": int(xyxy[0].item()),
                                    "ymin": int(xyxy[1].item()),
                                    "xmax": int(xyxy[2].item()),
                                    "ymax": int(xyxy[3].item())
                                }
                                detections.append(detection)
            save_inference_result(detections)

        # Escribir el frame procesado en el video de salida
        out.write(frame)
        frame_count += 1

    cap.release()
    out.release()

    # Devolver la ruta del video procesado
    return {"video_path": temp_video_output.name}
