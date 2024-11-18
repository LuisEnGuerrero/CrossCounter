import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.mongodb import get_inference_statistics, inspect_mongodb_data  # Importar desde mongodb.py
from PIL import Image, ImageDraw


def show_statistics():
    """
    Obtiene estadísticas desde MongoDB y muestra gráficos y tablas en Streamlit.
    """
    # Selección del nivel de análisis
    analysis_level = st.sidebar.selectbox("Selecciona el nivel de análisis", ["Día", "Mes", "Año"])
    filters = {}

    # Configuración de filtros según nivel
    if analysis_level == "Día":
        selected_day = st.sidebar.date_input("Selecciona el día").strftime("%Y-%m-%d")
        filters = {"year": int(selected_day[:4]), "month": int(selected_day[5:7]), "day": int(selected_day[8:10])}
        level = "day"
    elif analysis_level == "Mes":
        selected_month = st.sidebar.selectbox("Selecciona el mes", range(1, 13))
        selected_year = st.sidebar.number_input("Selecciona el año", min_value=2000, max_value=2100, step=1)
        filters = {"year": selected_year, "month": selected_month}
        level = "month"
    else:  # Año
        selected_year = st.sidebar.number_input("Selecciona el año", min_value=2000, max_value=2100, step=1)
        filters = {"year": selected_year}
        level = "year"

    # Obtener datos del pipeline
    pipeline_results = get_inference_statistics(level, filters)

    if pipeline_results is None or len(pipeline_results) == 0:
        st.write("No hay datos de estadísticas disponibles.")
        return

    # Convertir resultados a DataFrame
    try:
        data = pd.DataFrame(pipeline_results)

        # Transformar _id a columnas independientes si está presente
        if "_id" in data.columns:
            data = pd.concat([data.drop(columns="_id"), data["_id"].apply(pd.Series)], axis=1)

        # Renombrar columnas
        data = data.rename(columns={
            "year": "Año",
            "month": "Mes",
            "day": "Día",
            "hour": "Hora",
            "total_motos": "Cantidad de Motocicletas"
        })

        # Verificar si el DataFrame está vacío
        if data.empty:
            st.write("No hay datos para mostrar después de procesar el pipeline.")
            return

        # Mostrar el DataFrame en Streamlit para depuración
        st.write("DataFrame Generado:", data)

        # Mostrar gráficos
        if level == "day":
            st.subheader("Estadísticas por Hora")
            st.bar_chart(data.set_index("Hora")["Cantidad de Motocicletas"])

        elif level == "month":
            st.subheader("Estadísticas por Día")
            st.bar_chart(data.set_index("Día")["Cantidad de Motocicletas"])

        elif level == "year":
            st.subheader("Estadísticas por Mes")
            st.bar_chart(data.set_index("Mes")["Cantidad de Motocicletas"])

    except Exception as e:
        st.error(f"Error procesando los datos: {e}")
        return


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

