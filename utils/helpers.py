import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
from ultralytics import YOLO
import os
import subprocess
from googleapiclient.discovery import build
from datetime import datetime
import cv2
import tempfile
from PIL import Image
import requests
import yt_dlp
import isodate

# Obtener la API de YouTube desde los secretos de Streamlit Cloud
YOUTUBE_API_KEY = st.secrets["YOUTUBE"]["YOUTUBE_API_KEY"]

# Cargar el modelo YOLOv8
model_path = "models/best.pt"
try:
    model = YOLO(model_path, verbose=False)
except Exception as e:
    st.error(f"Error al cargar el modelo: {e}")
    st.stop()

def get_youtube_video_metadata(youtube_url):
    """
    Obtiene metadatos de un video de YouTube utilizando la API de YouTube.

    Args:
        youtube_url (str): URL del video de YouTube.

    Returns:
        dict: Metadatos del video (título, duración en segundos, tamaño estimado, etc.).

    Raises:
        RuntimeError: Si ocurre algún error al obtener los datos del video.
    """
    try:
        # Extraer el ID del video desde la URL
        if "v=" in youtube_url:
            video_id = youtube_url.split("v=")[1].split("&")[0]
        else:
            raise ValueError("URL de YouTube no válida.")

        # Construir cliente de la API de YouTube
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

        # Obtener información del video
        request = youtube.videos().list(part="snippet,contentDetails", id=video_id)
        response = request.execute()

        # Validar que el video existe
        if not response["items"]:
            raise ValueError("El video no fue encontrado en YouTube.")

        # Extraer datos del video
        video_data = response["items"][0]
        title = video_data["snippet"]["title"]
        duration_iso = video_data["contentDetails"]["duration"]  # Duración en formato ISO 8601

        # Convertir duración ISO 8601 a segundos
        duration_seconds = isodate.parse_duration(duration_iso).total_seconds()

        # Estimar el tamaño del video (esto es una aproximación basada en bitrate promedio)
        average_bitrate = 2 * 1024  # 2 Mbps promedio
        filesize_approx = (duration_seconds * average_bitrate) / 8  # Convertir a bytes

        # Retornar los metadatos del video
        return {
            "title": title,
            "duration": duration_seconds,
            "video_id": video_id,
            "filesize_approx": filesize_approx,
            "total_frames": int(duration_seconds * 30),  # Suponiendo 30 FPS
        }

    except Exception as e:
        # Manejar errores y lanzar excepciones con un mensaje descriptivo
        raise RuntimeError(f"Error al obtener los metadatos del video: {e}")

#  función para descargar un video de YouTube
def download_youtube_video(youtube_url):
    """
    Descarga un video de YouTube utilizando yt-dlp.

    Args:
        youtube_url (str): URL del video de YouTube.

    Returns:
        str: Ruta al archivo descargado.
    """
    output_template = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name

    # Comprobar los formatos disponibles antes de descargar
    try:
        with YoutubeDL() as ydl:
            info = ydl.extract_info(youtube_url, download=False)
        
        # Seleccionar el mejor formato disponible sin necesidad de ffmpeg
        best_format = next(
            (fmt for fmt in info.get("formats", []) if fmt.get("ext") in ["mp4", "webm", "avi"] and fmt.get("vcodec") != "none" and fmt.get("acodec") != "none"),
            None
        )
        
        if not best_format:
            raise RuntimeError("No se encontró un formato compatible para este video.")

    except Exception as e:
        raise RuntimeError(f"Error al obtener información del video: {e}")

    metadata = get_youtube_video_metadata(youtube_url)
    video_id = metadata["video_id"]

    # Descargar el video utilizando el formato encontrado
    ydl_opts = {
        "format": best_format['format_id'],
        "outtmpl": output_template,
        "quiet": False,  # Cambiar a False temporalmente para depuración
        "postprocessors": [],  # No usar postprocesadores que requieran ffmpeg
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
            # st.text(f"Descargando video: {ydl.process_info['downloaded_bytes'] / 1024 / 1024:.2f} MB")
        
        # Verificar que el archivo se haya descargado correctamente
        if not os.path.exists(output_template):
            raise RuntimeError("El archivo de video no existe después de la descarga.")
        if os.path.getsize(output_template) == 0:
            raise RuntimeError("El video descargado está vacío o no se descargó correctamente.")
        
        return output_template
    except Exception as e:
        raise RuntimeError(f"Error al descargar el video: {e}")


# función para segmentar un video
def segment_video(video_path, segment_duration=200):
    """
    Divide un video en segmentos más pequeños.

    Args:
        video_path (str): Ruta del video original.
        segment_duration (int): Duración máxima de cada segmento en segundos.

    Returns:
        list: Lista de rutas a los segmentos generados.
    """
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_duration = total_frames / fps

    segments = []
    start_time = 0

    while start_time < total_duration:
        end_time = min(start_time + segment_duration, total_duration)
        segment_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name

        out = cv2.VideoWriter(
            segment_path,
            cv2.VideoWriter_fourcc(*'mp4v'),
            fps,
            (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))),
        )

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_time * fps)
        while cap.get(cv2.CAP_PROP_POS_MSEC) < end_time * 1000:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)

        out.release()
        segments.append(segment_path)
        start_time = end_time

    cap.release()
    return segments


def display_youtube_info(youtube_url):
    """
    Extrae información básica de un video de YouTube utilizando yt_dlp.

    Args:
        youtube_url (str): URL del video de YouTube.

    Returns:
        dict: Información estructurada del video (título, duración, autor, tamaño aproximado).
    """
    try:
        # Extraer metadatos del video
        ydl_opts = {"quiet": True, "dump_single_json": True}
        with YoutubeDL(ydl_opts) as ydl:
            yt = ydl.extract_info(youtube_url, download=False)

        # Manejar datos opcionales
        title = yt.get("title", "Título no disponible")
        duration = yt.get("duration", 0)  # Duración en segundos
        if duration is None:
            st.error("No se pudo obtener la duración del video.")
            return {}
        uploader = yt.get("uploader", "Autor no disponible")
        filesize_approx = None  # Inicializamos en None

        # Obtener el tamaño aproximado del archivo
        formats = yt.get("formats", [])
        for fmt in formats:
            if fmt.get("filesize"):
                filesize_approx = fmt["filesize"]
                break

        # Devolver información estructurada
        return {
            "title": title,
            "duration": duration,
            "author": uploader,
            "filesize_approx": filesize_approx,
        }

    except Exception as e:
        st.error(f"Error al extraer información del video: {e}")
        return {}
        

def update_progress(bar, processed_frames, total_frames):
    """
    Actualiza la barra de progreso en Streamlit.

    Args:
        processed_frames (int): Número de frames procesados hasta ahora.
        total_frames (int): Total de frames en el video.
    """
    progress = int((processed_frames / total_frames) * 100)
    bar.progress(progress)


    # Limpiar la barra al finalizar
    if progress == 100:
        st.empty()

# función para generar un ID de inferencia único
def generate_inference_id():
    """
    Genera un ID único basado en la fecha y hora actual.

    Returns:
        str: ID único en formato ISO 8601.
    """
    return datetime.now().isoformat()

# Añade una marca de agua y un contador total de motocicletas a un video.
def add_watermark_and_counter(video_path, total_motorcycle_count):
    """
    Añade una marca de agua y un contador total de motocicletas a un video.

    Args:
        video_path (str): Ruta del video.
        total_motorcycle_count (int): Conteo total de motocicletas detectadas.

    Returns:
        str: Ruta del video procesado con la marca de agua y el contador.
    """
    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    output_path = video_path.replace(".mp4", "_watermarked.mp4")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    app_name = "AI-MotorCycle CrossCounter TalentoTECH"  # Nombre de la aplicación

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Añadir título y contador total al frame
        motos_text = f"Motos encontradas: {total_motorcycle_count}"
        cv2.putText(frame, app_name, (10, height - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.putText(frame, motos_text, (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Escribir el frame procesado en el video de salida
        out.write(frame)

    cap.release()
    out.release()

    return output_path

# función para redimensionar un frame de forma proporcional
def resize_frame_proportionally(frame, scale=0.5):
    """
    Redimensiona un frame de forma proporcional.

    Args:
        frame (numpy.ndarray): El frame original.
        scale (float): El factor de escala (por defecto 0.5 para reducir al 50%).

    Returns:
        numpy.ndarray: El frame redimensionado.
    """
    # Obtener las dimensiones originales del frame
    original_height, original_width = frame.shape[:2]

    # Calcular las nuevas dimensiones
    new_width = int(original_width * scale)
    new_height = int(original_height * scale)

    # Redimensionar el frame
    resized_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

    return resized_frame


def get_video_duration_and_size(video_path):
    """
    Calcula la duración y el tamaño de un video.

    Args:
        video_path (str): Ruta al archivo de video.

    Returns:
        tuple: Duración en segundos y tamaño en MB.
    """
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    duration_seconds = total_frames / fps
    video_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    cap.release()
    return duration_seconds, video_size_mb

#   función para procesar un segmento de video
def process_video_segment(cap, start_frame, end_frame, frame_interval, inference_id):
    """
    Procesa un segmento de video utilizando el modelo YOLO.

    Args:
        cap (cv2.VideoCapture): Objeto de captura del video.
        start_frame (int): Frame inicial del segmento.
        end_frame (int): Frame final del segmento.
        frame_interval (int): Intervalo de frames a procesar.
        inference_id (str): ID único para la inferencia.

    Returns:
        dict: Resultados del segmento procesado, incluyendo el conteo total y la ruta del video.
    """
    # Establecer el punto inicial del segmento
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    segment_motorcycle_count = 0
    frame_results = []
    processed_video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name

    # Crear el escritor de video
    out = cv2.VideoWriter(
        processed_video_path,
        cv2.VideoWriter_fourcc(*'mp4v'),
        cap.get(cv2.CAP_PROP_FPS),
        (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))),
    )

    # Inicializar variables para mostrar progreso
    frame_count = start_frame
    total_frames_in_segment = end_frame - start_frame
    progress_bar = st.progress(0)

    # Nombre de la aplicación
    app_name = "AI-MotorCycle CrossCounter TalentoTECH"

    while cap.isOpened():
        frame_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)

        # Detener si se alcanza el final del segmento
        if frame_pos >= end_frame:
            break

        ret, frame = cap.read()
        if not ret:
            break

        frame_motorcycle_count = 0

        # Procesar frame solo si cumple con el intervalo
        if int(frame_pos) % frame_interval == 0:
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            results = model(img)

            # Detecciones y anotaciones en el frame
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

            # Actualizar conteo total de motocicletas en el segmento
            segment_motorcycle_count += frame_motorcycle_count

            # Guardar resultados del frame
            frame_results.append({
                "timestamp": datetime.now(),
                "motorcycle_count": frame_motorcycle_count,
            })

        # Añadir título y contador total al frame
        motos_text = f"Motos encontradas: {segment_motorcycle_count}"
        cv2.putText(frame, app_name, (10, frame.shape[0] - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.putText(frame, motos_text, (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Escribir el frame en el video de salida
        out.write(frame)

        # Actualizar progreso
        progress = (frame_pos - start_frame + 1) / total_frames_in_segment
        progress_bar.progress(min(progress, 1.0))

        frame_count += 1

    cap.release()
    out.release()

    # Retornar resultados del segmento procesado
    return {
        "motorcycle_count": segment_motorcycle_count,
        "frame_results": frame_results,
        "processed_video_path": processed_video_path,
    }


def is_large_video(video_url, max_size_mb=200):
    """
    Verifica si el tamaño del video supera el límite permitido.

    Args:
        video_url (str): URL del video de YouTube.
        max_size_mb (int): Tamaño máximo permitido en MB.

    Returns:
        bool: True si el video es grande, False en caso contrario.
    """
    ydl_opts = {"quiet": True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)

    # Si no hay información de tamaño, estima con duración y un bitrate promedio
    filesize = info.get("filesize")
    if not filesize:
        duration = info.get("duration", 0)  # en segundos
        estimated_size = (2.4 * 1024 * 1024) * duration / 8  # 5 Mbps bitrate
        filesize = estimated_size

    return filesize > max_size_mb * 1024 * 1024

