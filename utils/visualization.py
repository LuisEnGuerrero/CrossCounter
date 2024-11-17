import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.mongodb import get_inference_statistics  # Importar desde mongodb.py
from PIL import Image, ImageDraw

def show_statistics():
    """
    Obtiene estadísticas desde MongoDB y muestra un gráfico en Streamlit.
    """
    # Obtener estadísticas desde MongoDB
    statistics = get_inference_statistics()

    if not statistics:
        st.write("No hay datos de estadísticas disponibles.")
        return

    # Convertir estadísticas a DataFrame para su uso en gráficos
    data = pd.DataFrame(statistics)
    data["_id"] = data["_id"].apply(lambda x: f"{x['day']} - {x['hour']}h")
    data = data.rename(columns={"total_motos": "Cantidad de Motocicletas", "_id": "Fecha y Hora"})
    data = data.set_index("Fecha y Hora")

    # Crear un gráfico de barras con Plotly
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=data.index,
        y=data["Cantidad de Motocicletas"],
        name="Cantidad de Motocicletas",
        marker_color="blue"
    ))
    fig.update_layout(
        title="Conteo de Motocicletas Detectadas",
        xaxis_title="Fecha y Hora",
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
