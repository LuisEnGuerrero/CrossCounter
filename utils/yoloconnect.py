import streamlit as st
from PIL import Image
import torch
from ultralytics import YOLO
import cv2
import tempfile
import os

#from roboflow import Roboflow, CLIPModel, GazeModel

# Obtener las variables de entorno desde los secretos de Streamlit Cloud
# API_KEY = st.secrets["ROBOFLOW"]["ROBOFLOW_API_KEY"]
# MODEL_ID = st.secrets["ROBOFLOW"]["ROBOFLOW_MODEL_ID"]
# API_URL = st.secrets["ROBOFLOW"]["ROBOFLOW_API_URL"]

# Agregar mensajes de depuración
# st.write(f"API_KEY: {API_KEY}")
# st.write(f"MODEL_ID: {MODEL_ID}")
# st.write(f"API_URL: {API_URL}")

# Cargar el modelo YOLOv8 pre-entrenado
model_path = "models/best.pt"
model = YOLO(model_path)

# if not API_KEY or not MODEL_ID or not API_URL:
#     raise st.error("API_KEY, MODEL_ID o API_URL no están configurados en los secretos de Streamlit")

# Inicializar la instancia de Roboflow
#rf = Roboflow(api_key=API_KEY)

def get_video_inference(video_path: str, fps: int = 5):
    """
    Realiza inferencia en video usando la API de Roboflow.
    """
    # if method == "object-detection":
    #     project = rf.workspace().project("etiquetado-de-motos")
    #     model = project.version("1").model
    # elif method == "clip":
    #     model = CLIPModel()
    # elif method == "gaze-detection":
    #     model = GazeModel()
    # else:
    #     raise ValueError("Método de inferencia no soportado.")

    #job_id, signed_url, expire_time = model.predict_video(
    #    video_path,
    #    fps=fps,
    #    prediction_type="batch-video",
    #)
    
    # results = model.poll_until_video_results(job_id)
    # return results

        # Abrir el video
    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    # Crear un archivo temporal para el video de salida
    temp_video_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    out = cv2.VideoWriter(temp_video_output.name, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Realizar inferencia en el frame
        results = model(frame)
        for *box, conf, cls in results.xyxy[0]:
            label = f'{model.names[int(cls)]} {conf:.2f}'
            cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 255, 0), 2)
            cv2.putText(frame, label, (int(box[0]), int(box[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Escribir el frame procesado en el video de salida
        out.write(frame)

    cap.release()
    out.release()

    # Devolver la ruta del video procesado
    return {"video_path": temp_video_output.name}

def get_image_inference(image_path: str):
    """
    Realiza inferencia en una imagen usando la API de Roboflow para imágenes individuales.
    """
    img = Image.open(image_path)
    results = model(img)

    #from inference_sdk import InferenceHTTPClient
    
    # client = InferenceHTTPClient(api_url=API_URL, api_key=API_KEY)
    # result = client.infer(image_path, model_id=MODEL_ID)
    
    return results.pandas().xyxy[0].to_dict(orient="records")
