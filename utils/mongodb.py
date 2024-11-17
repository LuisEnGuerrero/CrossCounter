from pymongo import MongoClient
from datetime import datetime
import streamlit as st

# Obtener la URI de MongoDB desde los secretos de Streamlit Cloud
MONGO_URI = st.secrets["MONGO"]["MONGO_URI"]

# Crear una instancia del cliente de MongoDB
try:
    client = MongoClient(MONGO_URI)
    db = client["motorcycle_detection"]  # Nombre de la base de datos
    collection = db["detections"]        # Nombre de la colección
    # st.write("Conexión a MongoDB establecida correctamente.")
except Exception as e:
    st.error(f"Error al conectar con MongoDB: {e}")

def save_inference_result_image(data):
    """
    Guarda los resultados de inferencia de imagen en MongoDB.

    Args:
        data (dict): Contiene los datos de la inferencia, incluyendo:
            - type: Tipo de inferencia ('image')
            - inference_id: Identificador de la inferencia
            - motorcycle_count: Cantidad de motocicletas detectadas
    """
    # Insertar los datos
    collection.insert_one(data)
    st.success(f"Resultado de inferencia guardado en MongoDB con ID {data.get('inference_id')}")

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
