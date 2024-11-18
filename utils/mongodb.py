import streamlit as st
from uuid import uuid4
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

# Función para guardar los resultados de una inferencia de imagen en MongoDB
def save_inference_result_image(data):
    """
    Guarda los resultados de inferencia de una imagen en MongoDB.

    Args:
        data (dict): Contiene los datos de la inferencia.
            - type: Tipo de inferencia ('image')
            - inference_id: Identificador único
            - detection_id: ID único de la detección
            - motorcycle_count: Conteo de motocicletas detectadas
            - timestamp: Fecha y hora de la inferencia
    """
    # Añadir validación de campos necesarios
    required_fields = ["type", "inference_id", "detection_id", "motorcycle_count", "timestamp"]
    for field in required_fields:
        if field not in data:
            st.error(f"Falta el campo obligatorio: {field}")
            return

    # Insertar en MongoDB
    collection.insert_one(data)
    st.success(f"Resultado de inferencia guardado en MongoDB con ID {data.get('inference_id')}")

# Función para guardar los resultados de una inferencia de un video en MongoDB
def save_inference_result_video(inference_id, motorcycle_count_per_frame):
    """
    Guarda los resultados de inferencia de un video en MongoDB.

    Args:
        inference_id (str): Identificador único de la inferencia.
        motorcycle_count_per_frame (list[dict]): Lista de conteos por frame. Cada elemento debe incluir:
            - "timestamp" (datetime): Fecha y hora del frame procesado.
            - "motorcycle_count" (int): Conteo de motocicletas detectadas en ese frame.
    """
    for frame_result in motorcycle_count_per_frame:
        document = {
            "type": "video",
            "inference_id": inference_id,
            "detection_id": str(uuid4()),  # Generar un ID único para la detección
            "timestamp": frame_result["timestamp"],
            "motorcycle_count": frame_result["motorcycle_count"],
        }
        collection.insert_one(document)
    st.success(f"Resultados de inferencia guardados en MongoDB para inference_id {inference_id}")


# Función para obtener las estadísticas de detección
def get_inference_statistics(level, filters=None):
    """
    Obtiene estadísticas de detección agrupadas dinámicamente según el nivel seleccionado.

    Args:
        level (str): Nivel de análisis ('day', 'month', 'year').
        filters (dict): Filtros adicionales según el nivel.

    Returns:
        list: Lista de documentos con estadísticas agrupadas.
    """
    # Configurar la agrupación
    group_stage = {
        "day": {
            "$group": {
                "_id": {
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                    "day": {"$dayOfMonth": "$timestamp"},
                    "hour": {"$hour": "$timestamp"},
                },
                "total_motos": {"$sum": "$motorcycle_count"},
            }
        },
        "month": {
            "$group": {
                "_id": {
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                    "day": {"$dayOfMonth": "$timestamp"},
                },
                "total_motos": {"$sum": "$motorcycle_count"},
            }
        },
        "year": {
            "$group": {
                "_id": {
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                },
                "total_motos": {"$sum": "$motorcycle_count"},
            }
        },
    }

    # Construir la pipeline
    pipeline = []
    if filters:
        pipeline.append({"$match": filters})
    pipeline.append(group_stage[level])
    pipeline.append({"$sort": {"_id": 1}})

    # Log para depuración
    st.write("Pipeline construida:", pipeline)

    # Ejecutar la agregación
    try:
        return list(collection.aggregate(pipeline))
    except Exception as e:
        st.error(f"Error en la consulta de estadísticas: {e}")
        return []
        

def inspect_mongodb_data(limit=10):
    """
    Recupera y muestra los datos almacenados en MongoDB para inspección.

    Args:
        limit (int): Número máximo de documentos a recuperar.

    Returns:
        list: Lista de documentos recuperados.
    """
    try:
        # Recuperar los documentos
        documents = list(collection.find().limit(limit))
        
        # Opcional: convertir ObjectId a cadena para evitar problemas de serialización
        for doc in documents:
            doc["_id"] = str(doc["_id"])
        
        return documents
    except Exception as e:
        st.error(f"Error al inspeccionar los datos de MongoDB: {e}")
        return []
    
