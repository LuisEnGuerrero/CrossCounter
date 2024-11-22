from datetime import datetime
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
    add_watermark_and_counter,
    get_youtube_video_metadata,
    resize_frame_proportionally,
    )
import tempfile
import base64

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


def process_youtube_video(youtube_url):
    """
    Procesa un video de YouTube y almacena los resultados de inferencia en MongoDB.

    Args:
        youtube_url (str): URL del video de YouTube.

    Returns:
        dict: Resultados de la inferencia.
    """
    inference_id = generate_inference_id()
    info = get_youtube_video_metadata(youtube_url)
    video_size = info.get("filesize_approx")
    total_frames = info.get("total_frames")

    if not video_size:
        info = display_youtube_info(youtube_url)
        video_size = info.get("filesize_approx")
        st.write(f"Tamaño del video: {video_size}Mb")

    if video_size and video_size <= 200 * 1024 * 1024 * 128:
        temp_path = download_youtube_video(youtube_url)
        results = process_youtube_video_inference(temp_path, frame_interval=33, total_frames=total_frames)

        # Añadir la marca de agua y el contador total al video
        total_motorcycle_count = results["total_motos"]
        final_video_path = add_watermark_and_counter(temp_path, total_motorcycle_count)

        # Guardar resultado en MongoDB
        save_inference_result_video(inference_id, results["motorcycle_count_per_frame"])

        # Guardar el estado del video procesado
        st.session_state["processed_video"] = final_video_path

        # Proporcionar un botón de descarga para el video procesado
        st.download_button(
            label="Descargar video procesado",
            data=open(final_video_path, "rb").read(),
            file_name="video_procesado.mp4",
            mime="video/mp4"
        )
        # eliminar archivos temporales
        os.remove(temp_path)
        os.remove(final_video_path)
    else:
        temp_path = download_youtube_video(youtube_url, output_path="temp_large.mp4")
        segment_paths = segment_video(temp_path)
        st.warning(f"El video se ha segmentado debido a su tamaño, en {len(segment_paths)} segmentos.")

        total_motorcycle_count = 0
        all_frame_data = []

        for segment in segment_paths[:-1]:
            segment_results = process_video(segment, frame_interval=33, total_frames=total_frames)
            total_motorcycle_count += segment_results["total_motos"]
            all_frame_data.extend(segment_results["motorcycle_count_per_frame"])
            os.remove(segment)

        # Procesar el último segmento y añadir la marca de agua
        last_segment = segment_paths[-1]
        last_segment_results = process_video(last_segment, frame_interval=33, total_frames=total_frames)
        total_motorcycle_count += last_segment_results["total_motos"]
        all_frame_data.extend(last_segment_results["motorcycle_count_per_frame"])

        # Añadir la marca de agua y el contador total al último segmento
        final_video_path = add_watermark_and_counter(last_segment, total_motorcycle_count)

        # Guardar resultado en MongoDB
        save_inference_result_video(inference_id, all_frame_data)

        # Guardar el estado del video procesado
        st.session_state["processed_video"] = final_video_path

        # Proporcionar un botón de descarga para el video procesado
        st.download_button(
            label="Descargar video procesado",
            data=open(final_video_path, "rb").read(),
            file_name="video_procesado.mp4",
            mime="video/mp4"
        )
        os.remove(last_segment)
        os.remove(final_video_path)
        

    return {"inference_id": inference_id, "total_motos": total_motorcycle_count, "processed_video_path": st.session_state["processed_video"]}


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

            # Guardar el frame temporalmente para procesarlo como imagen
            temp_frame_path = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
            img.save(temp_frame_path)

            # Realizar inferencia en el frame
            results = process_image(temp_frame_path)

            for detection in results["predictions"]:
                if detection["name"] == "motorcycle":
                    x_min, y_min, x_max, y_max = int(detection["xmin"]), int(detection["ymin"]), int(detection["xmax"]), int(detection["ymax"])
                    conf = detection["confidence"]
                    # Dibujar detección en el frame
                    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                    cv2.putText(frame, f"{detection['name']} {conf:.2f}", (x_min, y_min - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    frame_motorcycle_count += 1

            # Actualizar el contador total de motocicletas
            total_motorcycle_count += frame_motorcycle_count

            # Acumular resultados por frame
            motorcycle_count_per_frame.append({
                "timestamp": datetime.now(),
                "motorcycle_count": frame_motorcycle_count,
            })

            # Mostrar el frame procesado en el contenedor de imagen
            if image_container:
                image_container.image(frame, channels="BGR", use_container_width=True)

            # Eliminar el frame temporal
            os.remove(temp_frame_path)

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
        progress_value = min(frame_count / total_frames, 1.0)
        progress_bar.progress(progress_value)


    cap.release()
    out.release()

    return {
        "inference_id": inference_id,
        "total_motos": total_motorcycle_count,
        "motorcycle_count_per_frame": motorcycle_count_per_frame,
        "processed_video_path": output_path
    }

