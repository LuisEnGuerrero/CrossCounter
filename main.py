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
import base64

# Configuración inicial de la página de Streamlit
st.set_page_config(page_title="AI·MotorCycle CrossCounter TalentoTECH", layout="wide")

st.markdown('<div id="top"></div>', unsafe_allow_html=True) # Anchor para volver arriba

# Función para convertir imagen a base64
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Ruta de la imagen del logo
logo_path = os.path.join(os.path.dirname(__file__), "media", "logox512.jpg")
logo_base64 = get_base64_image(logo_path)
#TTech_path = os.path.join(os.path.dirname(__file__), "media", "TTechWhide.jpg")
#TTech_base64 = get_base64_image(TTech_path)
Enrique_path = os.path.join(os.path.dirname(__file__), "media", "Enrique.jpg")
Enrique_base64 = get_base64_image(Enrique_path)
Alex_path = os.path.join(os.path.dirname(__file__), "media", "Alex.jpg")
Alex_base64 = get_base64_image(Alex_path)
Adriana_path = os.path.join(os.path.dirname(__file__), "media", "Adriana.jpg")
Adriana_base64 = get_base64_image(Adriana_path)
Jeisson_path = os.path.join(os.path.dirname(__file__), "media", "Jeisson.jpg")
Jeisson_base64 = get_base64_image(Jeisson_path)


# Crear un contenedor para el header
header_container = st.container()

with header_container:
# HTML y CSS para el header
    st.markdown(
        f"""
            <style>
            /* Estilos Globales */
            body {{
                font-family: Arial, sans-serif;
                background-color: #041033; /* Fondo oscuro general */
                color: #f7f9fa; /* Texto claro */
                margin: 0;
                padding: 0;
            }}

            h2, h3, p {{
                margin: 0;
                padding: 0;
            }}

            /* Header */
            .header {{
                position: sticky;
                top: 0;
                z-index: 1000;
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 15px 20px 20px;
                background-color: #041033;
                border-bottom: 2px solid #f7f9fa;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            }}

            .header img {{
                width: 100px;
                height: auto;
                padding-right: 15px;
            }}

            .header h1 {{
                margin: 0;
                font-size: 24px;
                color: #f7f9fa;
            }}

            .css-1d391kg {{
                background-color: #041033;
                }} /* Cambiar el color de fondo de la barra lateral */

            .nav {{
                display: flex;
                gap: 20px;
            }}

            .nav a {{
                text-decoration: none;
                color: #f7f9fa;
                font-size: 18px;
                padding: 10px;
                border-radius: 4px;
                transition: background-color 0.3s, color 0.3s;
            }}

            .nav a:hover {{
                background-color: #f7f9fa;
                color: #041033;
            }}

            /* Secciones */
            section {{
                padding: 50px 20px;
                margin: 20px auto;
                max-width: 1200px;
                border-radius: 10px;
                background-color: #041033;
                color: #f7f9fa;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            }}

            section h2 {{
                text-align: center;
                font-size: 28px;
                color: #f7f9fa;
                margin-bottom: 20px;
            }}

            section p {{
                font-size: 18px;
                line-height: 1.6;
                color: #f7f9fa;
                text-align: justify;
            }}

            .acerca-de {{
                padding: 50px 20px;
                margin: 20px auto;
                max-width: 1200px;
                border-radius: 10px;
                background-color: #041033;
                color: #f7f9fa;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            }}


            /* Tarjetas de Equipo */
            .team-container {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); /* Adaptable a pantallas pequeñas */
                gap: 20px;
                margin-top: 30px;
            }}

            .team-card {{
                text-align: center;
                padding: 20px;
                border-radius: 10px;
                background-color: #1b2735;
                color: #f7f9fa;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                transition: transform 0.3s, box-shadow 0.3s;
            }}

            .team-card:hover {{
                transform: scale(1.05);
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.4);
            }}

            .team-card img {{
                width: 120px;
                height: 120px;
                border-radius: 50%;
                object-fit: cover;
                margin-bottom: 15px;
                background-color: #ddd; /* Fondo para cuando no cargue la imagen */
            }}

            .team-card h3 {{
                font-size: 20px;
                color: #f7f9fa;
                margin: 0 0 10px;
            }}

            .team-card p {{
                font-size: 16px;
                color: #a8c0ff;
                margin: 0;
            }}

            /* Documentación */
            #documentacion ol {{
                padding-left: 40px;
                font-size: 18px;
                color: #f7f9fa;
                line-height: 1.8;
            }}

            #documentacion li {{
                margin-bottom: 10px;
            }}

            #documentacion li strong {{
                color: #a8c0ff;
            }}

            .back-to-top {{
                position: fixed;
                bottom: 20px;
                left: 50%; /* Centra horizontalmente */
                transform: translateX(-50%); /* Ajusta la posición para centrar */
                right: 20px;
                background-color: none;
                color: #f7f9fa;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
                transition: background-color 0.3s ease;
                text-decoration: none;
                text-align: center;
                z-index: 1000;
            }}

            .back-to-top:hover {{
                background-color: #f7f9fa;
                color: #041033;
            }}


            /* Responsividad */
            @media (max-width: 768px) {{
                .header {{
                    flex-direction: column;
                    align-items: flex-start;
                }}

                .nav {{
                    flex-direction: column;
                    gap: 10px;
                    width: 100%;
                }}

                .nav a {{
                    width: 100%;
                }}

                .team-container {{
                    grid-template-columns: repeat(1, 1fr);
                }}
            }}
            </style>


            <div class="header">
                <img src="data:image/jpeg;base64,{logo_base64}" alt="Logo">
                <h1>AI·MotorCycle CrossCounter TalentoTECH</h1>
                <div class="nav">
                    <a href="#inicio">Inicio</a>
                    <a href="#acerca-de">Acerca·de</a>
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

    # Mostrar la imagen del logo en la barra lateral
    st.sidebar.image(logo_path, use_column_width=True)


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

    # Mostrar la imagen TalentoTECH en la barra lateral
    st.sidebar.image({{'media\TTechWhide.jpg'}}, use_column_width=True)

    # Seccion de "Acerca de"
    st.markdown(
        """
            <div class="acerca-de">
                    <h2>Acerca de</h2>
                    <p>
                        Somos <strong>TechRoads Innovators</strong>, un equipo dedicado a desarrollar soluciones innovadoras para el monitoreo y análisis de tráfico. 
                        Nuestro proyecto <strong>AI·MotorCycle CrossCounter TalentoTECH</strong> utiliza inteligencia artificial para detectar y contar motocicletas en videos, 
                        proporcionando datos valiosos para mejorar la seguridad y eficiencia del tráfico.
                    </p>
            </div>
        """,
        unsafe_allow_html=True
    )

    # Seccion de "tarjetas"
    st.markdown(
        f"""
            <div class="team-container">
                <div class="team-card">
                    <img src="data:image/jpeg;base64,{Enrique_base64}" alt="Luis Enrique Guerrero">
                    <h3>Luis Enrique Guerrero</h3>
                    <p>Ingeniero de Infraestructura y Desarrollo Fullstack</p>
                </div>
                <div class="team-card">
                    <img src="data:image/jpeg;base64,{Alex_base64}" alt="Alex García">
                    <h3>Alex García</h3>
                    <p>Líder de Proyecto y Especialista en Machine Learning</p>
                </div>
                <div class="team-card">
                    <img src="data:image/jpeg;base64,{Adriana_base64}" alt="Adriana Garay">
                    <h3>Adriana Garay</h3>
                    <p>Coordinadora de Presentaciones y Gestión de Datos</p>
                </div>
                <div class="team-card">
                    <img src="data:image/jpeg;base64,{Jeisson_base64}" alt="Jeisson Poveda">
                    <h3>Jeisson Poveda</h3>
                    <p>Gestor de Recursos y Analista de Datos</p>
                </div>
            </div>
            <a href="#top" class="back-to-top">↑ /­VOLVER\ ↑</a>
        """,
        unsafe_allow_html=True
    )

    # Seccion de "Documentación"
    st.markdown(
        """
            <div id="documentacion">
                <section>
                    <h2>Documentación</h2>
                    <h3>Guía de Uso</h3>
                    <ol>
                        <li>
                            <strong>Cargar una Imagen o Video</strong>: Selecciona el modo de inferencia (Imagen o Video) y carga el archivo correspondiente.
                        </li>
                        <li>
                            <strong>Realizar Inferencia</strong>: Haz clic en el botón "Realizar inferencia" para procesar la imagen o video.
                        </li>
                        <li>
                            <strong>Ver Resultados</strong>: Los resultados de la inferencia se mostrarán en la pantalla, incluyendo el conteo de motocicletas detectadas.
                        </li>
                        <li>
                            <strong>Descargar Video Procesado</strong>: Si has cargado un video, podrás descargar el video procesado con las detecciones resaltadas.
                        </li>
                    </ol>
                </section>
            </div>
        """,
        unsafe_allow_html=True
    )

    # Leer el contenido del archivo README.md y mostrarlo en la sección de Documentación
    with open("README.md", "r") as readme_file:
        readme_content = readme_file.read()

    # Seccion de "readme"

    st.markdown("### Información Técnica")
    st.markdown("*Consulta el archivo 'README.md' para más detalles:*")
    st.markdown(readme_content)  # Renderiza Markdown directamente
    # st.markdown(f"""<a href="#top" class="back-to-top">Volver arriba</a>""", unsafe_allow_html=True)
