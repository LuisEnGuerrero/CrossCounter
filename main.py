import streamlit as st
import os
import tempfile
import cv2
from PIL import Image, ImageDraw
from utils.yoloconnect import get_video_inference, get_image_inference
from utils.mongodb import save_inference_result, get_inference_statistics
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración inicial de la página de Streamlit
st.set_page_config(page_title="AI·MotorCycle CrossCounter TalentoTECH", layout="wide")

# Crear un contenedor para el header
header_container = st.container()

with header_container:

    # HTML y CSS para el header
    st.markdown(
        """
        <style>
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 20px;
            background-color: #f8f9fa;
            border-bottom: 2px solid #dee2e6;
        }
        .header img {
            width: 100px;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
            color: #343a40;
        }
        .nav {
            display: flex;
            gap: 20px;
        }
        .nav a {
            text-decoration: none;
            color: #007bff;
            font-size: 18px;
        }
        </style>
        <div class="header">
            <img src="media/logox512.jpg" alt="Logo">
            <h1>AI·MotorCycle CrossCounter TalentoTECH</h1>
            <div class="nav">
                <a href="#inicio">Inicio</a>
                <a href="#acerca-de">Acerca de</a>
                <a href="#documentacion">Documentación</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    
# Crear un contenedor para el contenido principal con márgenes
content_container = st.container()

with content_container:
    # Seleccionar modo de inferencia: Imagen o Video
    inference_mode = st.sidebar.selectbox("Selecciona el modo de inferencia", ("Imagen", "Video"))

    # Sección para inferencia de imágenes
    if inference_mode == "Imagen":
        st.subheader("Cargar una imagen")
        
        # Subir imagen
        uploaded_image = st.file_uploader("Elige una imagen", type=["jpg", "jpeg", "png"])

        if uploaded_image is not None:
            # Mostrar imagen original
            image = Image.open(uploaded_image)
            st.image(image, caption="Imagen Original", use_container_width=True)

            # Guardar la imagen temporalmente
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_image_file:
                image.save(temp_image_file.name)
                temp_image_path = temp_image_file.name
                st.write(f"Imagen guardada temporalmente en: {temp_image_path}")

            # Realizar inferencia
            if st.button("Realizar inferencia"):
                with st.spinner("Realizando inferencia en la imagen..."):
                    results = get_image_inference(temp_image_path)
                    st.success("Inferencia completada.")

                    # Guardar los resultados en MongoDB
                    save_inference_result(results)

                # Visualizar resultados de inferencia
                st.subheader("Resultados de Inferencia")
                st.json(results)

                # Dibujar detecciones en la imagen
                image_with_boxes = image.copy()
                draw = ImageDraw.Draw(image_with_boxes)
                motorcycle_count = 0
                
                for prediction in results:
                    print("Predicción:", prediction)  # Depuración: Imprimir cada predicción
                    if prediction['name'] == 'motorcycle':
                        x, y, w, h = prediction['xmin'], prediction['ymin'], prediction['xmax'] - prediction['xmin'], prediction['ymax'] - prediction['ymin']
                        confidence = prediction['confidence']
                        motorcycle_count += 1
                        
                        # Dibuja el rectángulo en torno a la detección
                        top_left = (x, y)
                        bottom_right = (x + w, y + h)
                        draw.rectangle([top_left, bottom_right], outline="red", width=2)
                        draw.text(top_left, f"{confidence:.2f}", fill="red")
                
                st.write(f"Total de motocicletas detectadas: {motorcycle_count}")
                st.image(image_with_boxes, caption="Imagen con detecciones", use_container_width=True)

                # Eliminar el archivo temporal
                os.remove(temp_image_path)

    # Sección para inferencia de video
    elif inference_mode == "Video":
        st.subheader("Cargar un video")
        
        # Subir video
        uploaded_video = st.file_uploader("Elige un video", type=["mp4", "avi", "mov"])

        if uploaded_video is not None:
            # Guardar el video temporalmente
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video_file:
                temp_video_file.write(uploaded_video.read())
                temp_video_path = temp_video_file.name
                st.write(f"Video guardado temporalmente en: {temp_video_path}")

            # Realizar inferencia en el video
            if st.button("Realizar inferencia en video"):
                with st.spinner("Realizando inferencia en el video..."):
                    cap = cv2.VideoCapture(temp_video_path)
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    
                    # Crear un archivo temporal para el video de salida
                    temp_video_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    out = cv2.VideoWriter(temp_video_output.name, fourcc, 30, (width, height))  # Cambiar a 30 fps para hacer el video 6 veces más rápido

                    frame_count = 0
                    total_motorcycle_count = 0

                    # Crear un contenedor para las imágenes
                    image_container = st.empty()

                    while cap.isOpened():
                        ret, frame = cap.read()
                        if not ret:
                            break

                        # Procesar solo un frame de cada nueve
                        if frame_count % 9 == 0:
                            # Realizar inferencia en el frame
                            results = get_image_inference(frame)
                            motorcycle_count = 0
                            for prediction in results:
                                if prediction['name'] == 'motorcycle':
                                    x, y, w, h = prediction['xmin'], prediction['ymin'], prediction['xmax'] - prediction['xmin'], prediction['ymax'] - prediction['ymin']
                                    confidence = prediction['confidence']
                                    motorcycle_count += 1
                                    
                                    # Dibuja el rectángulo en torno a la detección
                                    top_left = (x, y)
                                    bottom_right = (x + w, y + h)
                                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                                    cv2.putText(frame, f"{confidence:.2f}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                            # Actualizar el contador total de motos encontradas
                            total_motorcycle_count += motorcycle_count

                            # Guardar los resultados en MongoDB
                            save_inference_result(results)

                        # Añadir el nombre de la aplicación y el contador de motos encontradas en todos los frames
                        app_name = "AI MotorCycle CrossCounter TalentoTECH"
                        motos_text = f"Motos encontradas: {total_motorcycle_count}"
                        cv2.putText(frame, app_name, (10, height - 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                        cv2.putText(frame, motos_text, (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

                        # Mostrar el frame procesado
                        image_container.image(frame, channels="BGR", caption=f"Frame {frame_count}")

                        # Escribir el frame procesado en el video de salida
                        out.write(frame)
                        frame_count += 1

                    cap.release()
                    out.release()

                    st.success("Inferencia en video completada.")

                    # Proporcionar un botón de descarga para el video procesado
                    with open(temp_video_output.name, "rb") as file:
                        btn = st.download_button(
                            label="Descargar video procesado",
                            data=file,
                            file_name="video_procesado.mp4",
                            mime="video/mp4"
                        )

                    # Eliminar los archivos temporales después de la descarga
                    if btn:
                        os.remove(temp_video_path)
                        os.remove(temp_video_output.name)

    # Gráfico de estadísticas
    st.header("Estadísticas de Conteo de Motocicletas")

    # Seleccionar el periodo para las estadísticas
    period = st.sidebar.selectbox("Selecciona el periodo para las estadísticas", ("Día", "Mes", "Año"))

    # Obtener estadísticas según el periodo seleccionado
    if period == "Día":
        statistics = get_inference_statistics("day")
    elif period == "Mes":
        statistics = get_inference_statistics("month")
    elif period == "Año":
        statistics = get_inference_statistics("year")

    if statistics:
        # Convertir estadísticas a DataFrame para su uso en gráficos
        data = pd.DataFrame(statistics)
        if period == "Día":
            data["_id"] = data["_id"].apply(lambda x: f"{x['day']} - {x['hour']}h" if 'hour' in x else f"{x['day']}")
        elif period == "Mes":
            data["_id"] = data["_id"].apply(lambda x: f"{x['month']} - {x['year']}")
        elif period == "Año":
            data["_id"] = data["_id"].apply(lambda x: f"{x['year']}")
        data = data.rename(columns={"total_motos": "Cantidad de Motocicletas", "_id": "Fecha y Hora"})
        data = data.set_index("Fecha y Hora")

        # Crear el gráfico combinado de líneas y barras
        fig = go.Figure()

        # Añadir barras
        fig.add_trace(go.Bar(x=data.index, y=data["Cantidad de Motocicletas"], name="Cantidad de Motocicletas", marker_color='blue'))

        # Añadir línea
        fig.add_trace(go.Scatter(x=data.index, y=data["Cantidad de Motocicletas"], name="Línea de Motocicletas", mode='lines+markers', line=dict(color='red')))

        # Actualizar el layout del gráfico
        fig.update_layout(
            title="Conteo de Motocicletas por Fecha y Hora",
            xaxis_title="Fecha y Hora",
            yaxis_title="Cantidad de Motocicletas",
            barmode='group'
        )

        st.plotly_chart(fig)
        st.write(data)
    else:
        st.write("No hay datos de estadísticas disponibles.")


    # Secciones de "Acerca de" y "Documentación"
    st.markdown(
        """
        <div id="acerca-de">
            <h2>Acerca de</h2>
            <p>Somos TechRoads Innovators, un equipo dedicado a desarrollar soluciones innovadoras para el monitoreo y análisis de tráfico. Nuestro proyecto AI·MotorCycle CrossCounter TalentoTECH utiliza inteligencia artificial para detectar y contar motocicletas en videos, proporcionando datos valiosos para mejorar la seguridad y eficiencia del tráfico.</p>
        </div>
        <div id="documentacion">
            <h2>Documentación</h2>
            <h3>Guía de Uso</h3>
            <ol>
                <li><strong>Cargar una Imagen o Video</strong>: Selecciona el modo de inferencia (Imagen o Video) y carga el archivo correspondiente.</li>
                <li><strong>Realizar Inferencia</strong>: Haz clic en el botón "Realizar inferencia" para procesar la imagen o video.</li>
                <li><strong>Ver Resultados</strong>: Los resultados de la inferencia se mostrarán en la pantalla, incluyendo el conteo de motocicletas detectadas.</li>
                <li><strong>Descargar Video Procesado</strong>: Si has cargado un video, podrás descargar el video procesado con las detecciones resaltadas.</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True
    )
