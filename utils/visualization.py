import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.mongodb import get_inference_statistics, inspect_mongodb_data  # Importar desde mongodb.py
from PIL import Image, ImageDraw


def show_statistics():
    """
    Obtiene estadísticas desde MongoDB y muestra gráficos en Streamlit.
    """
    # Selección del nivel de análisis
    analysis_level = st.sidebar.selectbox("Selecciona el nivel de análisis", ["Día", "Mes", "Año"])
    filters = {}

    if analysis_level == "Día":
        selected_day = st.sidebar.date_input("Selecciona el día")
        filters = {
            "year": selected_day.year,
            "month": selected_day.month,
            "day": selected_day.day
        }
        level = "day"
    elif analysis_level == "Mes":
        selected_month = st.sidebar.selectbox("Selecciona el mes", range(1, 13))
        selected_year = st.sidebar.number_input("Selecciona el año", min_value=2000, max_value=2100, step=1)
        filters = {"year": int(selected_year), "month": int(selected_month)}
        level = "month"
    elif analysis_level == "Año":
        selected_year = st.sidebar.number_input("Selecciona el año", min_value=2000, max_value=2100, step=1)
        filters = {"year": int(selected_year)}
        level = "year"

    # Log filtros para depuración
    st.write("Filtros generados:", filters)

    # Obtener estadísticas desde MongoDB
    statistics = get_inference_statistics(level, filters)

    # Log pipeline y datos obtenidos
    st.write("Pipeline construida:", statistics)

    if not statistics:
        st.write("No hay datos de estadísticas disponibles.")
        return

    # Procesar datos en DataFrame
    data = pd.DataFrame(statistics)
    if level == "day":
        data["_id"] = data["_id"].apply(
            lambda x: f"{x.get('year', 'N/A')}-{x.get('month', 'N/A')}-{x.get('day', 'N/A')} {x.get('hour', 'N/A')}:00"
        )
    elif level == "month":
        data["_id"] = data["_id"].apply(
            lambda x: f"{x.get('year', 'N/A')}-{x.get('month', 'N/A')}-{x.get('day', 'N/A')}"
        )
    elif level == "year":
        data["_id"] = data["_id"].apply(
            lambda x: f"{x.get('year', 'N/A')}-{x.get('month', 'N/A')}"
        )

    data = data.rename(columns={"total_motos": "Cantidad de Motocicletas", "_id": "Unidad de Tiempo"})
    data = data.set_index("Unidad de Tiempo")

    # Mostrar gráficos
    st.bar_chart(data)

    st.write(f"Total de motocicletas detectadas: {data['Cantidad de Motocicletas'].sum()}")



def draw_detections(image, detections):
    """
    Dibuja las detecciones en una imagen.
    
    Args:
        image (PIL.Image.Image): Imagen en la que se dibujarán las detecciones.
        detections (list): Lista de detecciones con campos como "name", "confidence", "xmin", "ymin", "xmax", "ymax".
    
    Returns:
        PIL.Image.Image: Imagen con las detecciones dibujadas.
    """
    draw = ImageDraw.Draw(image)

    for detection in detections:
        if isinstance(detection, dict):  # Validar que cada elemento sea un diccionario
            name = detection.get("name", "unknown")
            confidence = detection.get("confidence", 0.0)
            xmin, ymin, xmax, ymax = detection.get("xmin"), detection.get("ymin"), detection.get("xmax"), detection.get("ymax")
            
            # Dibujar el rectángulo
            if xmin is not None and ymin is not None and xmax is not None and ymax is not None:
                draw.rectangle([xmin, ymin, xmax, ymax], outline="red", width=3)
                # Añadir etiqueta
                label = f"{name} ({confidence:.2f})"
                draw.text((xmin, ymin - 10), label, fill="red")
    
    return image


def show_inspected_data():
    """
    Inspecciona y muestra los datos almacenados en MongoDB en Streamlit.
    """
    st.header("Inspección de Datos en MongoDB")
    documents = inspect_mongodb_data(limit=20)  # Ajusta el límite según sea necesario
    
    if not documents:
        st.write("No se encontraron datos en la base de datos.")
    else:
        st.write("Documentos recuperados de MongoDB:")
        for doc in documents:
            st.json(doc)  # Muestra cada documento en formato JSON

