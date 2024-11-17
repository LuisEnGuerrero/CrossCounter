import streamlit as st
from ultralytics import YOLO
import cv2
from PIL import Image
import tempfile

# Cargar el modelo YOLOv8
model_path = "models/best.pt"
try:
    model = YOLO(model_path, verbose=False)
    # st.write("Modelo cargado correctamente!")
except Exception as e:
    st.error(f"Error al cargar el modelo: {e}")
    st.stop()

def get_image_inference(image_path):
    """
    Realiza inferencia en una imagen utilizando el modelo YOLO entrenado localmente.
    
    Args:
        image_path (str): Ruta al archivo de imagen.
    
    Returns:
        list: Lista de detecciones con coordenadas y confianza.
    """
    # Realizar la inferencia
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
    
    return detections

def get_video_inference(video_path):
    """
    Realiza inferencia en un video utilizando el modelo YOLO entrenado localmente.
    
    Args:
        video_path (str): Ruta al archivo de video.
    
    Returns:
        dict: Incluye la ruta al video procesado y conteo total de detecciones.
    """
    # Crear un archivo temporal para el video procesado
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    output_path = temp_output.name

    # Leer el video
    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    total_motorcycle_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convertir frame a formato PIL para la inferencia
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # Realizar inferencia en el frame
        results = model(img)

        for result in results:
            frame_motorcycle_count = 0
            for box in result.boxes:
                cls = result.names[int(box.cls[0])]
                if cls == "motorcycle":
                    conf = box.conf[0]
                    x_min, y_min, x_max, y_max = map(int, box.xyxy[0].tolist())
                    # Dibujar detección en el frame
                    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                    cv2.putText(frame, f"{cls} {conf:.2f}", (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    frame_motorcycle_count += 1

            # Acumular el conteo total de motocicletas
            total_motorcycle_count += frame_motorcycle_count

        # Escribir el frame procesado en el video de salida
        out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    cap.release()
    out.release()

    return {
        "processed_video_path": output_path,
        "total_motos": total_motorcycle_count,
    }
