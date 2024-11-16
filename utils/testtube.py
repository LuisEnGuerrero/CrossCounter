import streamlit as st
from utils.yoloconnect import get_image_inference
from utils.mongodb import save_inference_result
from pytube import YouTube
import yt_dlp
from yt_dlp.utils import DownloadError
import validators
import requests
from urllib.parse import urlparse, parse_qs
import tempfile
import os
import math
import subprocess
import shutil
import cv2
from moviepy.video.io.VideoFileClip import VideoFileClip
import googleapiclient.discovery
import googleapiclient.errors
import isodate


# Obtener la API de YouTube desde los secretos de Streamlit Cloud
YOUTUBE_API_KEY = st.secrets["YOUTUBE"]["YOUTUBE_API_KEY"]


# Función para obtener información del video desde la API de YouTube
def get_youtube_video_info(youtube_url):
    video_id = youtube_url.split("v=")[-1]  # Extraemos el ID del video de la URL
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    
    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=video_id
    )
    
    response = request.execute()
    
    if response["items"]:
        video_info = response["items"][0]
        title = video_info["snippet"]["title"]
        # description = video_info["snippet"]["description"]
        duration = video_info["contentDetails"]["duration"]
        view_count = video_info["statistics"]["viewCount"]
        
        # Duración en segundos (convertir el formato ISO 8601)
        duration_seconds = parse_duration(duration)
        
        return {
            "title": title,
            # "description": description,
            "duration_seconds": duration_seconds,
            "view_count": view_count,
        }
    else:
        return None


def estimate_video_size_in_mb(duration_seconds, bitrate_mbps=5):
    """
    Estima el tamaño del video en MB basado en la duración y un bitrate promedio.
    :param duration_seconds: Duración del video en segundos.
    :param bitrate_mbps: Tasa de bits promedio en Mbps (por defecto, 5 Mbps para HD).
    :return: Tamaño estimado en MB.
    """
    # Convertimos el bitrate a bits por segundo y calculamos el tamaño
    size_in_mb = (bitrate_mbps * duration_seconds) / 8  # Dividimos por 8 para pasar de bits a bytes
    return size_in_mb


# Función para convertir duración en formato ISO 8601 a segundos
def parse_duration(duration):
    duration_obj = isodate.parse_duration(duration)
    return int(duration_obj.total_seconds())


# Función para dividir el video en segmentos
def process_video_segments(youtube_url, max_size_mb=200):
    st.write("Obteniendo información del video...")
    video_info = get_youtube_video_info(youtube_url)
    
    if not video_info:
        st.error("No se pudo obtener información del video. Verifica la URL.")
        return

    duration_seconds = video_info["duration_seconds"]
    video_size = estimate_video_size_in_mb(duration_seconds)
    
    st.write(f"Tamaño estimado del video: {video_size:.2f} MB")    # Inicializar contador total de motocicletas
    total_motorcycle_count = 0

    # Si el tamaño del video es mayor a max_size_mb, lo dividimos
    if video_size > max_size_mb:
        st.write(f"El video es grande ({video_size:.2f} MB). Se procederá a dividirlo en segmentos.")
        
        # Dividir el video en segmentos
        segment_duration = calculate_segment_duration(youtube_url, max_size_mb)
        output_dir = tempfile.mkdtemp()
        segments = split_video_into_segments(youtube_url, segment_duration, output_dir)

        st.write(f"Video dividido en {len(segments)} segmentos.")
        processed_segments = []

        # Realizar inferencia en cada segmento
        for i, segment in enumerate(segments):
            st.write(f"Procesando segmento {i + 1} de {len(segments)}...")
            with st.spinner(f"Realizando inferencia en el segmento {i + 1}..."):
                cap = cv2.VideoCapture(segment)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")

                temp_part_output = tempfile.NamedTemporaryFile(delete=False, suffix=f"_part_{i + 1}.mp4")
                out = cv2.VideoWriter(temp_part_output.name, fourcc, 30, (width, height))

                frame_count = 0
                image_container = st.empty()

                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    if frame_count % 30 == 0:  # Cambia a un valor más razonable, como 30 frames
                        results = get_image_inference(frame)
                        motorcycle_count = 0

                        for prediction in results:
                            if prediction["name"] == "motorcycle":
                                x = int(prediction["xmin"])
                                y = int(prediction["ymin"])
                                w = int(prediction["xmax"] - x)
                                h = int(prediction["ymax"] - y)
                                confidence = prediction["confidence"]
                                motorcycle_count += 1

                                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                                cv2.putText(frame, f"{confidence:.2f}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 2)

                        total_motorcycle_count += motorcycle_count
                        save_inference_result(results)

                    # Añadir texto al frame
                    app_name = "AI MotorCycle CrossCounter TalentoTECH"
                    motos_text = f"Motos encontradas: {total_motorcycle_count}"
                    cv2.putText(frame, app_name, (10, height - 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                    cv2.putText(frame, motos_text, (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

                    image_container.image(frame, channels="BGR", caption=f"Frame {frame_count}")
                    out.write(frame)
                    frame_count += 1

                cap.release()
                out.release()

                # Guardar cada segmento procesado
                # processed_segments.append(temp_part_output.name)

                # Eliminar el archivo temporal del segmento original
                os.remove(segment)

        st.success("Inferencia en video completada.")
        st.write(f"Total de motos encontradas: {total_motorcycle_count}")
        return processed_segments

    else:
        # Si el video es pequeño, se procesa entero
        st.write(f"El video tiene un tamaño adecuado ({video_size:.2f} MB). Procesando completo...")
        return process_full_video(youtube_url)



# Función para realizar la inferencia en el video completo
def process_full_video(video_path):
    st.write("Procesando video completo...")
    cap = cv2.VideoCapture(video_path)

    # Configuración del video de salida
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # Crear un archivo temporal para el video procesado
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    out = cv2.VideoWriter(temp_output.name, fourcc, fps, (width, height))

    frame_count = 0
    total_motorcycle_count = 0
    image_container = st.empty()

    with st.spinner("Realizando inferencia en el video completo..."):
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Procesar solo algunos frames (para optimización)
            if frame_count % 101 == 0:
                results = get_image_inference(frame)
                motorcycle_count = 0

                # Dibujar detecciones y contar motocicletas
                for prediction in results:
                    if prediction["name"] == "motorcycle":
                        x, y = prediction["xmin"], prediction["ymin"]
                        w, h = (
                            prediction["xmax"] - x,
                            prediction["ymax"] - y,
                        )
                        confidence = prediction["confidence"]
                        motorcycle_count += 1

                        # Dibujar el rectángulo y la confianza en el frame
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                        cv2.putText(
                            frame,
                            f"{confidence:.2f}",
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.3,
                            (0, 255, 0),
                            2,
                        )

                total_motorcycle_count += motorcycle_count
                save_inference_result(results)

            # Añadir texto al frame
            app_name = "AI MotorCycle CrossCounter TalentoTECH"
            motos_text = f"Motos encontradas: {total_motorcycle_count}"
            cv2.putText(
                frame,
                app_name,
                (10, height - 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 0, 0),
                2,
            )
            cv2.putText(
                frame,
                motos_text,
                (10, height - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )

            # Mostrar el frame procesado y escribir en el video de salida
            image_container.image(frame, channels="BGR", caption=f"Frame {frame_count}")
            out.write(frame)
            frame_count += 1

    cap.release()
    out.release()

    st.success("Inferencia en video completada.")
    st.write(f"Total de motos encontradas: {total_motorcycle_count}")

    # Botón de descarga para el video procesado
    with open(temp_output.name, "rb") as file:
        st.download_button(
            label="Descargar video procesado",
            data=file,
            file_name="video_procesado_completo.mp4",
            mime="video/mp4",
        )

    # Eliminar archivo temporal después de la descarga
    os.remove(temp_output.name)



def is_valid_youtube_url(youtube_url):
    """
    Verifica si la URL de YouTube es válida.
    """
    try:
        parsed_url = urlparse(youtube_url)
        if parsed_url.netloc in ["www.youtube.com", "youtube.com", "youtu.be"]:
            query_params = parse_qs(parsed_url.query)
            return "v" in query_params or parsed_url.path.startswith("/")
        return False
    except Exception:
        return False


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


def split_video_into_segments(video_path, segment_duration=60, output_dir="segments"):
    """
    Divide un video en segmentos más pequeños usando MoviePy.
    
    Args:
        video_path (str): Ruta al archivo de video.
        segment_duration (int): Duración de cada segmento en segundos.
        output_dir (str): Carpeta donde se guardarán los segmentos.

    Returns:
        list: Lista de rutas a los segmentos generados.
    """
    # Validar si el archivo existe
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"El archivo de video '{video_path}' no existe.")
    
    # Crear el directorio de salida si no existe
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        # Cargar el video
        video = VideoFileClip(video_path)
        video_duration = video.duration  # Duración total del video en segundos
        total_segments = math.ceil(video_duration / segment_duration)

        segment_paths = []

        for i in range(total_segments):
            start_time = i * segment_duration
            end_time = min((i + 1) * segment_duration, video_duration)

            # Crear segmento
            segment = video.subclip(start_time, end_time)
            segment_path = os.path.join(output_dir, f"segment_{str(i + 1).zfill(2)}.mp4")
            segment.write_videofile(segment_path, codec="libx264", audio_codec="aac")

            segment_paths.append(segment_path)

        return segment_paths

    except Exception as e:
        raise RuntimeError(f"Error al dividir el video: {e}")

    finally:
        # Asegurar que el video se cierre
        if 'video' in locals():
            video.close()
    

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
    
    except DownloadError as de:
        # Limpieza del directorio en caso de error específico de yt_dlp
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"Error al descargar el video (yt_dlp): {de}")
    
    except Exception as e:
        # Limpieza del directorio en caso de cualquier otro error
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"Error al descargar el video: {e}")
    

def calculate_segment_duration(video_path, max_size_mb=200):
    """
    Calcula la duración recomendada de los segmentos en función del bitrate del video.

    Args:
        video_path (str): Ruta al archivo de video.
        max_size_mb (int): Tamaño máximo permitido por segmento en MB.

    Returns:
        int: Duración recomendada de cada segmento en segundos.
    """
    try:
        # Usar cv2 para capturar propiedades del video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError("No se pudo abrir el video para obtener información.")

        # Obtener el bitrate (bits por segundo)
        bitrate = cap.get(cv2.CAP_PROP_BITRATE)  # Bitrate en bits/segundo
        if bitrate <= 0:
            raise RuntimeError("No se pudo obtener el bitrate del video.")

        # Convertir el bitrate a MB/s
        bitrate_mb_per_second = bitrate / (8 * 1024 * 1024)  # De bits/s a MB/s

        # Calcular la duración máxima en segundos para no superar el tamaño máximo
        max_duration = max_size_mb / bitrate_mb_per_second

        cap.release()
        return int(max_duration)  # Redondear a segundos enteros

    except Exception as e:
        raise RuntimeError(f"Error al calcular la duración del segmento: {e}")
    
