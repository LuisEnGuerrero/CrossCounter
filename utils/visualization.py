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
    level = "year"  # Predeterminado para la agrupación general

    if analysis_level == "Día":
        selected_day = st.sidebar.date_input("Selecciona el día").strftime("%Y-%m-%d")
        filters = {"year": int(selected_day[:4]), "month": int(selected_day[5:7]), "day": int(selected_day[8:10])}
        level = "day"
    elif analysis_level == "Mes":
        selected_month = st.sidebar.selectbox("Selecciona el mes", range(1, 13))
        selected_year = st.sidebar.number_input("Selecciona el año", min_value=2000, max_value=2100, step=1)
        filters = {"year": selected_year, "month": selected_month}
        level = "month"
    elif analysis_level == "Año":
        selected_year = st.sidebar.number_input("Selecciona el año", min_value=2000, max_value=2100, step=1)
        filters = {"year": selected_year}

    # Obtener estadísticas desde MongoDB
    statistics = get_inference_statistics(level, filters)

    if not statistics:
        st.write("No hay datos de estadísticas disponibles.")
        return

    # Procesar datos en DataFrame
    data = pd.DataFrame(statistics)

    # Transformar el _id en función del nivel de análisis
    if level == "day":
        data["_id"] = data["_id"].apply(
            lambda x: f"{x.get('year', 'N/A')}-{x.get('month', 'N/A'):02d}-{x.get('day', 'N/A'):02d} {x.get('hour', 'N/A')}h"
        )
    elif level == "month":
        data["_id"] = data["_id"].apply(
            lambda x: f"{x.get('year', 'N/A')}-{x.get('month', 'N/A'):02d}-{x.get('day', 'N/A'):02d}"
        )
    elif level == "year":
        data["_id"] = data["_id"].apply(
            lambda x: f"{x.get('year', 'N/A')}-{x.get('month', 'N/A'):02d}"
        )

    data = data.rename(columns={"total_motos": "Cantidad de Motocicletas", "_id": "Unidad de Tiempo"})
    data = data.set_index("Unidad de Tiempo")

    # Gráficos
    st.subheader(f"Estadísticas por {analysis_level}")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=data.index,
        y=data["Cantidad de Motocicletas"],
        name="Cantidad de Motocicletas",
        marker_color="blue"
    ))
    fig.update_layout(
        title="Conteo de Motocicletas Detectadas",
        xaxis_title="Unidad de Tiempo",
        yaxis_title="Cantidad de Motocicletas",
        template="plotly_white"
    )
    st.plotly_chart(fig)



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

