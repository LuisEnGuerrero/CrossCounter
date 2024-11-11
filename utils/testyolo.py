import os
from dotenv import load_dotenv
from yoloconnect import get_video_inference, get_image_inference

# Cargar las variables de entorno desde la raíz
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Archivo de prueba de video e imagen
VIDEO_PATH = "./media/D02_20240914083802.mp4"
IMAGE_PATH = "./media/scene00199test.jpg"

def test_video_inference():
    # Realiza inferencia en un video usando Object Detection
    print("Ejecutando inferencia en video...")
    video_results = get_video_inference(VIDEO_PATH, fps=5, method="object-detection")
    print("Resultados de inferencia en video:", video_results)

def test_image_inference():
    # Realiza inferencia en una imagen usando la API Hosted Inference
    print("Ejecutando inferencia en imagen...")
    image_results = get_image_inference(IMAGE_PATH)
    print("Resultados de inferencia en imagen:", image_results)

if __name__ == "__main__":
    # Ejecuta las pruebas de inferencia
    test_video_inference()
    test_image_inference()
