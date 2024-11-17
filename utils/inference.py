from PIL import Image, ImageDraw
from utils.yoloconnect import get_image_inference, get_video_inference

def process_image(image_file):
    """
    Procesa una imagen cargada para realizar inferencias con YOLO.
    Dibuja las detecciones directamente en la imagen.
    
    Args:
        image_file: Archivo de imagen cargado por el usuario.
    
    Returns:
        dict: Contiene la imagen con detecciones y el conteo total de motocicletas.
    """
    # Obtener resultados de inferencia
    detections = get_image_inference(image_file)
    
    # Abrir la imagen
    img = Image.open(image_file)
    draw = ImageDraw.Draw(img)

    motorcycle_count = 0
    for detection in detections:
        if detection['name'] == 'motorcycle':
            motorcycle_count += 1

            # Coordenadas del rectángulo
            x_min, y_min, x_max, y_max = detection['xmin'], detection['ymin'], detection['xmax'], detection['ymax']

            # Dibujar el rectángulo en la imagen
            draw.rectangle([(x_min, y_min), (x_max, y_max)], outline="red", width=2)
            draw.text((x_min, y_min), f"{detection['confidence']:.2f}", fill="red")

    return {
        "detections": detections,
        "image_with_detections": img,
        "motorcycle_count": motorcycle_count,
    }

def process_video(video_file):
    """
    Procesa un video cargado para realizar inferencias con YOLO.
    
    Args:
        video_file: Archivo de video cargado por el usuario.
    
    Returns:
        dict: Contiene la ruta al video procesado y el conteo total de motocicletas.
    """
    # Obtener resultados de inferencia para el video
    results = get_video_inference(video_file)

    return {
        "processed_video_path": results.get("signed_url"),
        "motorcycle_count": results.get("total_motos", 0),
    }
