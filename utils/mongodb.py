import streamlit as st
from pymongo import MongoClient
from datetime import datetime

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

def save_inference_result(results):
    """
    Guarda el resultado de inferencia en MongoDB con la fecha/hora actual.
    """
    if not isinstance(results, list):
        st.write("Error: El resultado de inferencia no es una lista.")
        return

    motorcycle_count = sum(1 for result in results if result.get("name") == "motorcycle")

    document = {
        "timestamp": datetime.now(),  # Fecha y hora de almacenamiento
        "motorcycle_count": motorcycle_count
    }

    # st.write("Guardando en MongoDB:", document)
    collection.insert_one(document)
    # st.write(f"Resultado de inferencia guardado en MongoDB con ID {document['_id']}")

def get_inference_statistics(period="day"):
    """
    Obtiene estadísticas de conteo de motocicletas, agregando por día, mes o año.
    """
    if period == "day":
        group_id = {"day": {"$dayOfMonth": "$timestamp"}, "month": {"$month": "$timestamp"}, "year": {"$year": "$timestamp"}}
    elif period == "month":
        group_id = {"month": {"$month": "$timestamp"}, "year": {"$year": "$timestamp"}}
    elif period == "year":
        group_id = {"year": {"$year": "$timestamp"}}
    else:
        raise ValueError("Periodo no válido. Debe ser 'day', 'month' o 'year'.")

    pipeline = [
        {
            "$group": {
                "_id": group_id,
                "total_motos": {"$sum": "$motorcycle_count"},
                "average_motos": {"$avg": "$motorcycle_count"}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    return list(collection.aggregate(pipeline))
