import streamlit as st
from pytube import YouTube
from yt_dlp import YoutubeDL
from pathlib import Path
import os
from googleapiclient.discovery import build


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

    return {
        "title": title,
        "duration": duration_seconds,
        "video_id": video_id,
    }


def download_youtube_video(youtube_url, output_path="temp_youtube.mp4"):
    """
    Descarga un video de YouTube.

    Args:
        youtube_url (str): URL del video de YouTube.
        output_path (str): Ruta para guardar el video descargado.

    Returns:
        str: Ruta del archivo descargado.
    """
    metadata = get_youtube_video_metadata(youtube_url)
    video_id = metadata["video_id"]

    # Descargar video con yt-dlp
    ydl_opts = {"format": "best", "outtmpl": output_path}
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

    return output_path


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
    ydl_opts = {
        "format": "best",
        "outtmpl": f"{output_dir}/segment_%(part)d.mp4",
        "max_filesize": segment_duration * 1024 * 1024,
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_path])
    return sorted(Path(output_dir).glob("segment_*.mp4"))


def display_youtube_info(youtube_url):
    """
    Muestra información básica de un video de YouTube.

    Args:
        youtube_url (str): URL del video de YouTube.

    Returns:
        dict: Información del video (título, duración, autor, tamaño aproximado).
    """
    metadata = get_youtube_video_metadata(youtube_url)
    return {
        "title": metadata["title"],
        "duration": int(metadata["duration"]),
        "video_id": metadata["video_id"],
    }


def update_progress(processed_frames, total_frames):
    """
    Actualiza la barra de progreso en Streamlit.

    Args:
        processed_frames (int): Número de frames procesados hasta ahora.
        total_frames (int): Total de frames en el video.
    """
    progress = int((processed_frames / total_frames) * 100)
    st.progress(progress)

    # Limpiar la barra al finalizar
    if progress == 100:
        st.empty()
