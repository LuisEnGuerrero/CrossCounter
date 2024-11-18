import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.mongodb import get_inference_statistics  # Importar desde mongodb.py
from PIL import Image, ImageDraw

def show_statistics():
    """
    Obtiene estadísticas desde MongoDB y muestra un gráfico en Streamlit.
    """
    # Selección del nivel de análisis
    analysis_level = st.sidebar.selectbox("Selecciona el nivel de análisis", ["Día", "Mes", "Año"])
    filters = {}

    if analysis_level == "Día":
        selected_day = st.sidebar.date_input("Selecciona el día").strftime("%Y-%m-%d")
        filters = {"year": int(selected_day[:4]), "month": int(selected_day[5:7]), "day": int(selected_day[8:10])}
        level = "day"
    elif analysis_level == "Mes":
        selected_month = st.sidebar.selectbox("Selecciona el mes", range(1, 13))
        selected_year = st.sidebar.number_input("Selecciona el año", min_value=2000, max_value=2100, step=1)
        filters = {"year": selected_year, "month": selected_month}
        level = "month"
    else:
        selected_year = st.sidebar.number_input("Selecciona el año", min_value=2000, max_value=2100, step=1)
        filters = {"year": selected_year}
        level = "year"

    # Obtener estadísticas desde MongoDB
    statistics = get_inference_statistics(level, filters)

    if not statistics:
        st.write("No hay datos de estadísticas disponibles.")
        return

    # Procesar datos en DataFrame
    data = pd.DataFrame(statistics)
    data["_id"] = data["_id"].apply(lambda x: f"{x.get('day', x.get('hour', x.get('month')))}")
    data = data.rename(columns={"total_motos": "Cantidad de Motocicletas", "_id": "Unidad de Tiempo"})
    data = data.set_index("Unidad de Tiempo")

    # Gráficos
    st.subheader(f"Estadísticas por {analysis_level}")
    st.bar_chart(data)

    # Resumen adicional
    st.subheader(f"Resumen para el nivel: {analysis_level}")
    st.write(f"**Total de motocicletas detectadas:** {data['Cantidad de Motocicletas'].sum()}")
    st.write(f"**Promedio de detecciones:** {data['Cantidad de Motocicletas'].mean():.0f}")
    st.write(f"**Máximo de detecciones:** {data['Cantidad de Motocicletas'].max()} en {data['Cantidad de Motocicletas'].idxmax()}")
    


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
