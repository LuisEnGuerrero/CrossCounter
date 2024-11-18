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

# Función para guardar los resultados de una inferencia de imagen en MongoDB
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

# Función para guardar los resultados de una inferencia de un video en MongoDB
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

# Función para obtener las estadísticas de detección
def get_inference_statistics(level="day", value=None):
    """
    Obtiene estadísticas de detección agrupadas dinámicamente según el nivel seleccionado.

    Args:
        level (str): Nivel de análisis ('day', 'month', 'year').
        value (dict): Filtro adicional según el nivel ({'year': 2024, 'month': 11, 'day': 15}).

    Returns:
        list: Lista de documentos con estadísticas agrupadas.
    """
    match_stage = {}
    if value:
        if "year" in value:
            match_stage["$expr"] = {"$eq": [{"$year": "$timestamp"}, value["year"]]}
        if "month" in value:
            match_stage["$expr"] = {"$and": [{"$eq": [{"$year": "$timestamp"}, value["year"]]},
                                             {"$eq": [{"$month": "$timestamp"}, value["month"]]}]}
        if "day" in value:
            match_stage["$expr"] = {"$and": [{"$eq": [{"$year": "$timestamp"}, value["year"]]},
                                             {"$eq": [{"$month": "$timestamp"}, value["month"]]},
                                             {"$eq": [{"$dayOfMonth": "$timestamp"}, value["day"]]}]}

    group_stage = {
        "$group": {
            "_id": {},
            "total_motos": {"$sum": "$motorcycle_count"},
        }
    }

    if level == "day":
        group_stage["_id"] = {
            "hour": {"$hour": "$timestamp"},
        }
    elif level == "month":
        group_stage["_id"] = {
            "day": {"$dayOfMonth": "$timestamp"},
        }
    elif level == "year":
        group_stage["_id"] = {
            "month": {"$month": "$timestamp"},
        }

    pipeline = []
    if match_stage:
        pipeline.append({"$match": match_stage})
    pipeline.append(group_stage)
    pipeline.append({"$sort": {"_id": 1}})
    return list(collection.aggregate(pipeline))

