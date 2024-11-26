import streamlit as st
from yt_dlp import YoutubeDL
from pathlib import Path
import os
from googleapiclient.discovery import build
from datetime import datetime
import cv2
import tempfile
import requests
import yt_dlp

# Obtener la API de YouTube desde los secretos de Streamlit Cloud
YOUTUBE_API_KEY = st.secrets["YOUTUBE"]["YOUTUBE_API_KEY"]


def get_youtube_video_metadata(youtube_url):
    """
    Obtiene metadatos de un video de YouTube utilizando la API de YouTube.

    Args:
        youtube_url (str): URL del video de YouTube.

    Returns:
        dict: Metadatos del video (título, duración en segundos, tamaño estimado, etc.).
    """
    # Extraer el ID del video desde la URL
    video_id = youtube_url.split("v=")[1].split("&")[0]

    # Construir cliente de la API de YouTube
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    # Obtener información del video
    request = youtube.videos().list(part="snippet,contentDetails", id=video_id)
    response = request.execute()

    if not response["items"]:
        raise ValueError("El video no fue encontrado.")

    video_data = response["items"][0]
    title = video_data["snippet"]["title"]
    duration_iso = video_data["contentDetails"]["duration"]  # Formato ISO 8601

    # Convertir duración ISO 8601 a segundos
    import isodate
    duration_seconds = isodate.parse_duration(duration_iso).total_seconds()

    # Estimar el tamaño del video (esto es solo una estimación)
    average_bitrate = 5 * 1024 * 1024  # 5 Mbps
    filesize_approx = (duration_seconds * average_bitrate) / 8  # Convertir a bytes

    return {
            "title": title,
            "duration": duration_seconds,
            "video_id": video_id,
            "filesize_approx": filesize_approx,
            "total_frames" : int(duration_seconds * 30),  # Asumir 30 FPS
        }

#  función para descargar un video de YouTube
def download_youtube_video(youtube_url, output_path="temp_youtube.mp4"):
    """
    Descarga un video de YouTube usando yt-dlp.

    Args:
        youtube_url (str): URL del video de YouTube.
        output_path (str): Ruta para guardar el video descargado.

    Returns:
        str: Ruta del archivo descargado.
    """
    ydl_opts = {
        "format": "best",
        "outtmpl": output_path or "%(title)s.%(ext)s",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.download([youtube_url])
        if isinstance(result, list):
            return result[0]  # Ruta del archivo descargado
        return result


def segment_video(video_path, segment_duration=200, output_dir="segments"):
    """
    Divide un video en segmentos más pequeños.

    Args:
        video_path (str): Ruta del video original.
        segment_duration (int): Duración máxima de cada segmento en MB.
        output_dir (str): Directorio donde guardar los segmentos.

    Returns:
        list: Lista de rutas a los segmentos generados.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Abrir el video original
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Calcular el tamaño de un frame en bytes
    frame_size = width * height * 3  # 3 bytes por píxel (RGB)

    # Calcular el número de frames por segmento
    segment_frames = int((segment_duration * 1024 * 1024) / frame_size)

    segment_paths = []
    segment_index = 0
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % segment_frames == 0:
            if frame_count > 0:
                out.release()
            segment_index += 1
            segment_path = os.path.join(output_dir, f"segment_{segment_index}.mp4")
            segment_paths.append(segment_path)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(segment_path, fourcc, fps, (width, height))

        out.write(frame)
        frame_count += 1

    cap.release()
    out.release()

    return sorted(Path(output_dir).glob("segment_*.mp4"))


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
def process_video_segment(cap, start_frame, end_frame, frame_interval):
    """
    Procesa un segmento del video.

    Args:
        cap (cv2.VideoCapture): Objeto de captura del video.
        start_frame (int): Frame inicial del segmento.
        end_frame (int): Frame final del segmento.
        frame_interval (int): Intervalo de frames a procesar.

    Returns:
        dict: Resultados del segmento procesado.
    """
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    segment_motorcycle_count = 0
    frame_results = []
    processed_video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    out = cv2.VideoWriter(
        processed_video_path,
        cv2.VideoWriter_fourcc(*'mp4v'),
        cap.get(cv2.CAP_PROP_FPS),
        (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    )

    while cap.isOpened():
        frame_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
        if frame_pos >= end_frame:
            break

        ret, frame = cap.read()
        if not ret:
            break

        if int(frame_pos) % frame_interval == 0:
            # Procesar frame
            frame_motorcycle_count = 0
            # (Aquí debes incluir la lógica de detección y marcaje usando YOLO)
            # Actualizar resultados
            segment_motorcycle_count += frame_motorcycle_count
            frame_results.append({
                "timestamp": datetime.now(),
                "motorcycle_count": frame_motorcycle_count,
            })

        out.write(frame)

    cap.release()
    out.release()
    
    return {
        "motorcycle_count": segment_motorcycle_count,
        "frame_results": frame_results,
        "processed_video_path": processed_video_path,
    }

# función para obtener información de un video de YouTube
def get_video_info(youtube_url):
    """
    Obtiene información de un video de YouTube usando la API de YouTube.

    Args:
        youtube_url (str): URL del video de YouTube.
        api_key (str): Clave de la API de YouTube.

    Returns:
        dict: Información del video (tamaño, duración, título, etc.).
    """
    # Extraer el ID del video de la URL
    video_id = youtube_url.split("v=")[-1].split("&")[0]
    api_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={YOUTUBE_API_KEY}&part=contentDetails,snippet"

    response = requests.get(api_url)
    if response.status_code != 200:
        raise ValueError(f"Error al obtener información del video: {response.json()}")

    video_data = response.json()["items"][0]
    duration = video_data["contentDetails"]["duration"]
    title = video_data["snippet"]["title"]

    # Convertir la duración de ISO 8601 a segundos
    def parse_duration(duration):
        import isodate
        return isodate.parse_duration(duration).total_seconds()

    return {
        "video_id": video_id,
        "title": title,
        "duration": parse_duration(duration),  # En segundos
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
    info = yt_dlp.YoutubeDL({"quiet": True}).extract_info(video_url, download=False)
    return info.get("filesize", 0) > max_size_mb * 1024 * 1024
