from pymongo import MongoClient
from datetime import datetime
import streamlit as st

# Conexión a MongoDB usando st.secrets
client = MongoClient(st.secrets["MONGO_URI"])
db = client["motorcycle_detection"]  # Base de datos
collection = db["detections"]        # Colección para los resultados de inferencia

def save_inference_result_image(inference_id, motorcycle_count):
    """
    Guarda los resultados de una inferencia en una imagen en MongoDB.
    
    Args:
        inference_id (str): Identificador único de la inferencia.
        motorcycle_count (int): Número total de motocicletas detectadas.
    """
    document = {
        "timestamp": datetime.now(),
        "type": "image",
        "inference_id": inference_id,
        "motorcycle_count": motorcycle_count,
    }
    collection.insert_one(document)
    print(f"Resultado de inferencia (imagen) guardado en MongoDB con ID {document['_id']}")

def save_inference_result_video(inference_id, motorcycle_count_per_frame):
    """
    Guarda los resultados de una inferencia en un video en MongoDB.

    Args:
        inference_id (str): Identificador único de la inferencia.
        motorcycle_count_per_frame (list[dict]): Lista de conteos por frame. Cada elemento debe incluir:
            - "timestamp" (datetime): Fecha y hora del frame procesado.
            - "motorcycle_count" (int): Número total de motocicletas detectadas en ese frame.
    """
    for frame_result in motorcycle_count_per_frame:
        document = {
            "timestamp": frame_result["timestamp"],
            "type": "video",
            "inference_id": inference_id,
            "motorcycle_count": frame_result["motorcycle_count"],
        }
        collection.insert_one(document)
    print(f"Resultados de inferencia (video) guardados en MongoDB para inference_id {inference_id}")

def get_inference_statistics():
    """
    Obtiene estadísticas de detección agrupadas por día y hora.

    Returns:
        list: Lista de documentos con la cantidad de motocicletas detectadas.
    """
    pipeline = [
        {
            "$group": {
                "_id": {
                    "day": {"$dayOfMonth": "$timestamp"},
                    "hour": {"$hour": "$timestamp"},
                },
                "total_motos": {"$sum": "$motorcycle_count"},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    return list(collection.aggregate(pipeline))
