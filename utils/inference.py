from datetime import datetime
import streamlit as st
from ultralytics import YOLO
from pathlib import Path
import os
import cv2
from PIL import Image
from utils.helpers import (
    get_youtube_video_metadata,
    download_youtube_video, 
    generate_inference_id,
    resize_frame_proportionally,
    is_large_video,
    )
import tempfile
import base64
from pytube import YouTube

from utils.mongodb import save_inference_result_video



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


def process_video(video_path, frame_interval=103, total_frames=None):
    """
    Procesa un video utilizando YOLO.

    Args:
        video_path (str): Ruta del video.
        frame_interval (int): Procesar cada n-ésimo frame.
        total_frames (int): Total de frames en el video (para mostrar progreso).

    Returns:
        dict: Incluye conteo total de detecciones y conteos por frame.
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
    motorcycle_count_per_frame = []
    
    # Crear un contenedor vacío para mostrar los frames procesados
    image_container = st.empty()  

    # Crear barra de progreso única
    progress_bar = st.progress(0)

    app_name = "AI-MotorCycle CrossCounter TalentoTECH"  # Nombre de la aplicación


    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_motorcycle_count = 0  # Contador de motocicletas por frame


        if frame_count % frame_interval == 0:
            # Convertir frame a formato PIL para la inferencia
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            # Realizar inferencia en el frame
            results = model(img)

            # frame_motorcycle_count = 0
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

            # Actualizar el contador total de motocicletas
            total_motorcycle_count += frame_motorcycle_count

            # Acumular resultados por frame
            motorcycle_count_per_frame.append({
                "timestamp": datetime.now(),
                "motorcycle_count": frame_motorcycle_count,
            })

        # Añadir título y contador total al frame
        motos_text = f"Motos encontradas: {total_motorcycle_count}"
        cv2.putText(frame, app_name, (10, height - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, motos_text, (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Mostrar en un cuadro de imagen pequeño el frame procesado dentro de un container de Streamlit
        frame_small = resize_frame_proportionally(frame, scale=0.5)

        if image_container:
            image_container.image(frame_small, channels="BGR", caption=f"Frame {frame_count}")

        # Escribir el frame procesado en el video de salida
        out.write(frame)

        frame_count += 1

        # Actualizar la barra de progreso
        progress_bar.progress(frame_count / total_frames)

    cap.release()
    out.release()

    # Leer el video procesado como binario
    with open(output_path, "rb") as file:
        video_data = file.read()
        encoded_video = base64.b64encode(video_data).decode()

    return {
        "inference_id": inference_id,
        "processed_video_path": output_path,
        "encoded_video": encoded_video,
        "total_motos": total_motorcycle_count,
        "motorcycle_count_per_frame": motorcycle_count_per_frame,
    }



def process_youtube_video(youtube_url, frame_interval=99, max_segment_duration=200):
    """
    Procesa un video de YouTube dividiéndolo en segmentos si es necesario.

    Args:
        youtube_url (str): URL del video de YouTube.
        frame_interval (int): Procesar cada n-ésimo frame.
        max_segment_duration (int): Duración máxima de un segmento en segundos.

    Returns:
        dict: Resultados de la inferencia.
    """
    # Obtener información del video
    video_info = get_youtube_video_metadata(youtube_url)
    duration = video_info["duration"]
  
    # Validar tamaño y decidir si segmentar
    is_large = is_large_video(youtube_url)
    if not is_large and duration <= max_segment_duration:
        video_path = download_youtube_video(youtube_url)
        return process_youtube_video_inference(video_path, frame_interval)

    # Descargar y procesar por segmentos
    inference_id = generate_inference_id()
    total_motorcycle_count = 0
    motorcycle_count_per_frame = []
    processed_video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name

    for start_time in range(0, int(duration), max_segment_duration):
        end_time = min(start_time + max_segment_duration, duration)

        # Descargar el segmento del video
        segment_url = f"{youtube_url}#t={start_time},{end_time}"
        segment_path = download_youtube_video(segment_url)

        # Verificar que el segmento se descargó correctamente
        if not os.path.exists(segment_path) or os.path.getsize(segment_path) == 0:
            raise ValueError(f"El segmento del video no se descargó correctamente: {segment_url}")

        # Procesar el segmento
        segment_result = process_youtube_video_inference(segment_path, frame_interval)
        total_motorcycle_count += segment_result["total_motos"]
        motorcycle_count_per_frame.extend(segment_result["motorcycle_count_per_frame"])

        # Combinar el video procesado
        with open(segment_result["processed_video_path"], "rb") as segment_file:
            with open(processed_video_path, "ab") as final_video:
                final_video.write(segment_file.read())

        # Limpiar recursos temporales
        os.remove(segment_path)
        os.remove(segment_result["processed_video_path"])

    # Guardar resultados en MongoDB
    save_inference_result_video(inference_id, motorcycle_count_per_frame)

    return {
        "inference_id": inference_id,
        "total_motos": total_motorcycle_count,
        "processed_video_path": processed_video_path,
    }


def process_youtube_video_inference(video_path, frame_interval=33, total_frames=None):
    """
    Procesa un video de YouTube y realiza la inferencia de motocicletas.

    Args:
        video_path (str): Ruta del video.
        frame_interval (int): Intervalo de frames a procesar.
        total_frames (int): Total de frames en el video (para mostrar progreso).

    Returns:
        dict: Resultados de la inferencia.
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
    motorcycle_count_per_frame = []

    # Crear un contenedor vacío para mostrar los frames procesados
    image_container = st.empty()

    # Crear barra de progreso única
    progress_bar = st.progress(0)

    app_name = "AI-MotorCycle CrossCounter TalentoTECH"  # Nombre de la aplicación

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_motorcycle_count = 0  # Contador de motocicletas por frame

        if frame_count % frame_interval == 0:
            # Convertir frame a formato PIL para la inferencia
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            # Realizar inferencia en el frame
            results = model(img)

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

            # Actualizar el contador total de motocicletas
            total_motorcycle_count += frame_motorcycle_count

            # Acumular resultados por frame
            motorcycle_count_per_frame.append({
                "timestamp": datetime.now(),
                "motorcycle_count": frame_motorcycle_count,
            })

        # Añadir título y contador total al frame
        motos_text = f"Motos encontradas: {total_motorcycle_count}"
        cv2.putText(frame, app_name, (10, height - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, motos_text, (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Mostrar en un cuadro de imagen pequeño el frame procesado dentro de un container de Streamlit
        frame_small = resize_frame_proportionally(frame, scale=0.5)

        # Mostrar el frame procesado en el contenedor de imagen
        if image_container:
            image_container.image(frame, channels="BGR", use_container_width=True)

        # Escribir el frame procesado en el video de salida
        out.write(frame)


        frame_count += 1

        # Actualizar la barra de progreso
        progress_value = min(frame_count / total_frames, 1.0)
        progress_bar.progress(progress_value)

    cap.release()
    out.release()

    # Leer el video procesado como binario
    with open(output_path, "rb") as file:
        video_data = file.read()
        encoded_video = base64.b64encode(video_data).decode()

    return {
        "inference_id": inference_id,
        "total_motos": total_motorcycle_count,
        "motorcycle_count_per_frame": motorcycle_count_per_frame,
        "processed_video_path": output_path
    }

