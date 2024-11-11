from pymongo import MongoClient
from datetime import datetime
#import os
import streamlit as st
# from dotenv import load_dotenv

# Cargar variables de entorno
# load_dotenv()

# Conexión a MongoDB
#client = MongoClient(os.getenv("MONGO_URI"))

# Obtener la URI de MongoDB desde los secretos de Streamlit Cloud
MONGO_URI = st.secrets["MONGO"]["MONGO_URI"]

# Crear una instancia del cliente de MongoDB
client = MongoClient(MONGO_URI)


db = client["motorcycle_detection"]  # Nombre de la base de datos
collection = db["detections"]        # Nombre de la colección

def save_inference_result(result):
    """
    Guarda el resultado de inferencia en MongoDB con la fecha/hora actual.
    """
    document = {
        "inference_id": result.get("inference_id"),
        "time": result.get("time"),
        "detection_id": result["predictions"][0].get("detection_id") if result["predictions"] else None,
        "timestamp": datetime.now(),  # Fecha y hora de almacenamiento en MongoDB
        "motorcycle_count": len([pred for pred in result["predictions"] if pred["class"] == "motorcycle"]),
    }
    collection.insert_one(document)
    print(f"Resultado de inferencia guardado en MongoDB con ID {document['inference_id']}")
    return document

def get_inference_statistics():
    """
    Obtiene estadísticas de conteo de motocicletas, agregando por fecha y hora.
    """
    pipeline = [
        {
            "$group": {
                "_id": {"day": {"$dayOfMonth": "$timestamp"}, "hour": {"$hour": "$timestamp"}},
                "total_motos": {"$sum": "$motorcycle_count"},
            }
        },
        {"$sort": {"_id": 1}}
    ]
    return list(collection.aggregate(pipeline))
