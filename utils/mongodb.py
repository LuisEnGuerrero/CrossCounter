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
    st.write("Conexión a MongoDB establecida correctamente.")
except Exception as e:
    st.error(f"Error al conectar con MongoDB: {e}")

def save_inference_result(results):
    """
    Guarda el resultado de inferencia en MongoDB con la fecha/hora actual.
    """
    if not isinstance(results, list):
        print("Error: El resultado de inferencia no es una lista.")
        return

    for result in results:
        # Validar que el resultado sea un diccionario
        if isinstance(result, dict):
            document = {
                "inference_id": result.get("inference_id"),
                "time": result.get("time"),
                "detection_id": result.get("predictions", [{}])[0].get("detection_id") if result.get("predictions") else None,
                "timestamp": datetime.now(),  # Fecha y hora de almacenamiento
            }
            print("Guardando en MongoDB:", document)

            collection.insert_one(document)
            st.write(f"Resultado de inferencia guardado en MongoDB con ID {document['inference_id']}")
            return document
        else:
            print("Error: Elemento de la lista no es un diccionario válido.")

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
