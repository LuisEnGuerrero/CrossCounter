import streamlit as st
from ultralytics import YOLO
from pathlib import Path
import os
import cv2
from PIL import Image
from utils.helpers import (
    update_progress, 
    download_youtube_video, 
    segment_video, 
    display_youtube_info, 
    generate_inference_id,
    )
import tempfile


# Cargar el modelo YOLOv8
model_path = "models/best.pt"
try:
    model = YOLO(model_path, verbose=False)
except Exception as e:
    st.error(f"Error al cargar el modelo: {e}")
    st.stop()


def process_image(image_path):
    """
    Procesa una imagen utilizando el modelo YOLO.

    Args:
        image_path (str): Ruta de la imagen.

    Returns:
        dict: Resultados de detecciones en formato esperado.
    """
    results = model(image_path)

    detections = []
    for result in results:
        for box in result.boxes:
            cls = result.names[int(box.cls[0])]
            conf = box.conf[0]
            x_min, y_min, x_max, y_max = box.xyxy[0].tolist()
            detections.append({
                "name": cls,
                "confidence": float(conf),
                "xmin": float(x_min),
                "ymin": float(y_min),
                "xmax": float(x_max),
                "ymax": float(y_max),
            })
    
    return {"predictions": detections}


def process_video(video_path, frame_interval=99, total_frames=None):
    """
    Procesa un video utilizando YOLO.

    Args:
        video_path (str): Ruta del video.
        frame_interval (int): Procesar cada n-ésimo frame.
        total_frames (int): Total de frames en el video (para mostrar progreso).

    Returns:
        dict: Incluye la ruta al video procesado y conteo total de detecciones.
    """
    inference_id = generate_inference_id()  # Generar ID único
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    output_path = temp_output.name

    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    total_motorcycle_count = 0
    frame_count = 0

    # Crear barra de progreso única
    progress_bar = st.progress(0)


    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            # Convertir frame a formato PIL para la inferencia
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            # Realizar inferencia en el frame
            results = model(img)

            frame_motorcycle_count = 0
            for result in results:
                for box in result.boxes:
                    cls = result.names[int(box.cls[0])]
                    if cls == "motorcycle":
                        conf = box.conf[0]
                        x_min, y_min, x_max, y_max = map(int, box.xyxy[0].tolist())
                        # Dibujar detección en el frame
                        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                        cv2.putText(frame, f"{cls} {conf:.2f}", (x_min, y_min - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        frame_motorcycle_count += 1

                # Acumular el conteo total de motocicletas
                total_motorcycle_count += frame_motorcycle_count

        # Escribir el frame procesado en el video de salida
        out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

        if total_frames:
            update_progress(progress_bar, frame_count, total_frames)

        frame_count += 1

    cap.release()
    out.release()

    return {
        "inference_id": inference_id,
        "processed_video_path": output_path,
        "total_motos": total_motorcycle_count,
    }


def process_youtube_video(youtube_url):
    """
    Procesa un video de YouTube para inferencia.

    Args:
        youtube_url (str): URL del video de YouTube.

    Returns:
        dict: Resultados de la inferencia.
    """
    info = display_youtube_info(youtube_url)
    video_size = info["filesize_approx"]

    if video_size <= 200 * 1024 * 1024:  # Inferencia directa
        temp_path = download_youtube_video(youtube_url)
        return process_video(temp_path)
    else:  # Segmentación y procesamiento por partes
        temp_path = download_youtube_video(youtube_url, output_path="temp_large.mp4")
        segment_paths = segment_video(temp_path)
        results = []

        for segment in segment_paths:
            partial_result = process_video(segment)
            results.append(partial_result)
            os.remove(segment)  # Eliminar segmento procesado para liberar espacio

        return results[-1]  # Devuelve el último segmento procesado
    