import streamlit as st
from pytube import YouTube
import yt_dlp
import validators
import requests
import tempfile
import os
import math
import subprocess
import ffmpeg

# Obtener la API de YouTube desde los secretos de Streamlit Cloud
YOUTUBE_API_KEY = st.secrets["YOUTUBE"]["YOUTUBE_API_KEY"]

def verificar_ffmpeg(temp_video_path):
    """
    Verifica si FFmpeg está instalado y accesible en el sistema.
    """
    # Suponiendo que ya tienes un archivo de video descargado en alguna variable o ruta, como temp_video_path
    if 'temp_video_path' in locals() and os.path.exists(temp_video_path):
        try:
            # Intentar hacer una prueba en el archivo de video descargado
            ffmpeg.probe(temp_video_path)  # Verifica que FFmpeg puede acceder al archivo
            st.write("FFmpeg está instalado y funcionando correctamente.")
        except ffmpeg.Error as e:
            st.error(f"Error al ejecutar FFmpeg en el archivo: {e}")
    else:
        st.error("No se encontró un archivo de video válido para procesar.")


def download_youtube_video_with_yt_dlp(url):
    """
    Descarga un video de YouTube usando yt_dlp y devuelve la ruta al archivo descargado.
    """
    try:
        # Crear un directorio temporal para la descarga
        temp_dir = tempfile.mkdtemp()
        
        # Opciones de descarga
        ydl_opts = {
            'format': 'mp4/bestvideo+bestaudio/best',  # Descargar en el mejor formato disponible
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),  # Ruta de salida
            'noplaylist': True,  # Asegurarse de descargar solo un video
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info_dict)
        
        return video_path  # Ruta del video descargado
    except Exception as e:
        raise RuntimeError(f"Error al descargar el video: {e}")



def is_valid_youtube_url(youtube_url):
    """
    Verifica si la URL de YouTube es válida usando la API de YouTube.
    """
    from urllib.parse import urlparse, parse_qs
    import requests

    # Extraer el ID del video de la URL
    parsed_url = urlparse(youtube_url)
    query_params = parse_qs(parsed_url.query)
    video_id = query_params.get('v')
    
    if not video_id:
        return False, "La URL no contiene un ID de video válido."
    
    video_id = video_id[0]

    # Validar el video usando la API de YouTube
    api_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={YOUTUBE_API_KEY}&part=status"
    response = requests.get(api_url)
    
    if response.status_code != 200:
        return False, f"Error al validar el video: {response.status_code}"
    
    data = response.json()
    if "items" not in data or len(data["items"]) == 0:
        return False, "El video no existe o no es accesible."
    
    return True, "URL válida."

def download_youtube_video(youtube_url):
    """
    Descarga un video de YouTube y retorna la ruta del archivo temporal.
    """
    try:
        yt = YouTube(youtube_url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
        if stream is None:
            raise Exception("No se encontró un stream adecuado para el video.")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video_file:
            stream.download(output_path=temp_video_file.name.rsplit('/', 1)[0], 
                            filename=temp_video_file.name.rsplit('/', 1)[1])
            return temp_video_file.name
    except Exception as e:
        raise Exception(f"Error al descargar el video: {e}")


def get_video_info(video_path_or_url, is_youtube=False):
    """
    Obtiene información sobre la duración y peso del video.
    
    Args:
        video_path_or_url (str): Ruta local del video o URL de YouTube.
        is_youtube (bool): True si el video es de YouTube, False si es un archivo local.
    
    Returns:
        dict: Información del video (duración en segundos, tamaño en MB, etc.).
    """
    if is_youtube:
        # Obtener información de un video de YouTube usando yt_dlp
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "format": "best",  # Mejor calidad
            "simulate": True,  # Solo simula, no descarga
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_path_or_url, download=False)
                return {
                    "duration": info.get("duration"),  # En segundos
                    "filesize": info.get("filesize_approx", 0) / (1024 * 1024),  # En MB
                    "title": info.get("title"),
                }
        except Exception as e:
            raise ValueError(f"No se pudo obtener la información del video de YouTube: {e}")
    else:
        # Obtener información de un archivo local usando ffprobe
        try:
            command = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration,size",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path_or_url,
            ]
            output = subprocess.check_output(command).decode("utf-8").strip().split("\n")
            duration = float(output[0])  # Duración en segundos
            size_mb = float(output[1]) / (1024 * 1024)  # Tamaño en MB
            return {
                "duration": duration,
                "filesize": size_mb,
                "title": os.path.basename(video_path_or_url),  # Nombre del archivo
            }
        except Exception as e:
            raise ValueError(f"No se pudo obtener la información del archivo de video: {e}")


def split_video(video_path, output_dir, max_size_mb=300):
    """
    Divide un video en partes más pequeñas basadas en un tamaño máximo aproximado.
    
    Args:
        video_path (str): Ruta del video.
        output_dir (str): Directorio donde se guardarán las partes.
        max_size_mb (int): Tamaño máximo aproximado por cada parte (en MB).
    
    Returns:
        list: Lista de rutas de los videos divididos.
    """
    # Obtener información del video
    video_info = get_video_info(video_path, is_youtube=False)
    duration = video_info["duration"]  # En segundos
    total_size_mb = video_info["filesize"]

    # Calcular el número de partes necesarias
    num_parts = math.ceil(total_size_mb / max_size_mb)
    part_duration = duration / num_parts  # Duración aproximada de cada parte en segundos

    # Crear el directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)

    # Dividir el video en partes
    part_paths = []
    for i in range(num_parts):
        start_time = i * part_duration
        output_path = os.path.join(output_dir, f"part_{i + 1}.mp4")
        command = [
            "ffmpeg",
            "-i", video_path,
            "-ss", str(int(start_time)),
            "-t", str(int(part_duration)),
            "-c", "copy",
            output_path,
        ]
        subprocess.run(command, check=True)
        part_paths.append(output_path)

    return part_paths