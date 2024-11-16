import streamlit as st
from pytube import YouTube
import yt_dlp
import validators
import requests
import tempfile
import os

# Obtener la API de YouTube desde los secretos de Streamlit Cloud
YOUTUBE_API_KEY = st.secrets["YOUTUBE"]["YOUTUBE_API_KEY"]


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

