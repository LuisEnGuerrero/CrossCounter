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

    if analysis_level == "Día":
        selected_day = st.sidebar.date_input("Selecciona el día")
        filters = {"year": selected_day.year, "month": selected_day.month, "day": selected_day.day}
        level = "day"
    elif analysis_level == "Mes":
        selected_month = st.sidebar.selectbox("Selecciona el mes", range(1, 13))
        selected_year = st.sidebar.number_input("Selecciona el año", min_value=2000, max_value=2100, step=1)
        filters = {"year": int(selected_year), "month": int(selected_month)}
        level = "month"
    else:  # Año
        selected_year = st.sidebar.number_input("Selecciona el año", min_value=2000, max_value=2100, step=1)
        filters = {"year": int(selected_year)}
        level = "year"

    # Log filtros generados
    # st.write("Filtros generados:", filters)

    # Obtener estadísticas desde MongoDB
    statistics = get_inference_statistics(level, filters)

    # Verificar si el DataFrame está vacío
    if statistics.empty:
        st.write("No hay datos de estadísticas disponibles.")
        return

    # Procesar datos en DataFrame
    st.subheader(f"Estadísticas por {analysis_level}")
    
    # Mostrar gráfico de barras
    st.bar_chart(statistics)

    # Resumen adicional
    st.subheader(f"Resumen para el nivel: {analysis_level}")
    st.write(f"**Total de motocicletas detectadas:** {statistics['Cantidad de Motocicletas'].sum()}")
    st.write(f"**Promedio de detecciones:** {statistics['Cantidad de Motocicletas'].mean():.0f}")
    st.write(f"**Máximo de detecciones:** {statistics['Cantidad de Motocicletas'].max()} en {statistics['Cantidad de Motocicletas'].idxmax()}")

    