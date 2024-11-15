# AI·MotorCycle CrossCounter TalentoTECH

AI·MotorCycle CrossCounter TalentoTECH es una aplicación desarrollada por TechRoads Innovators para el monitoreo y análisis de tráfico utilizando inteligencia artificial. Esta aplicación detecta y cuenta motocicletas en videos, proporcionando datos valiosos para mejorar la seguridad y eficiencia del tráfico.

## Características

- **Detección de Motocicletas**: Utiliza un modelo YOLOv8 entrenado localmente para detectar motocicletas en imágenes y videos.
- **Conteo de Motocicletas**: Realiza el conteo de motocicletas detectadas y guarda los resultados en una base de datos MongoDB.
- **Visualización de Resultados**: Muestra los resultados de la inferencia en la interfaz de usuario, incluyendo el conteo de motocicletas y las detecciones resaltadas.
- **Descarga de Video Procesado**: Permite descargar el video procesado con las detecciones resaltadas.
- **Estadísticas de Conteo**: Genera gráficos combinados de líneas y barras para visualizar las estadísticas de conteo de motocicletas por día, mes y año.

## Requisitos

- Python 3.8 o superior
- Streamlit
- OpenCV
- PIL (Pillow)
- Pandas
- Plotly
- MongoDB
- YOLOv8 (Ultralytics)

## Instalación

1. Clona el repositorio:

    ```sh
    git clone https://github.com/LuisEnGuerrero/CrossCounter.git
    cd CrossCounter
    ```

2. Crea un entorno virtual e instala las dependencias:

    ```sh
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3. Configura las variables de entorno para MongoDB en `secrets.toml`:

    ```toml
    [MONGO]
    MONGO_URI = "tu_uri_de_mongodb"
    ```

## Uso

1. Ejecuta la aplicación:

    ```sh
    streamlit run main.py
    ```

2. Abre tu navegador web y ve a `http://localhost:8501`.

3. Carga una imagen o video para realizar la inferencia.

4. Visualiza los resultados de la inferencia y descarga el video procesado si es necesario.

## Estructura del Proyecto

- `main.py`: Archivo principal de la aplicación Streamlit.
- `utils/yoloconnect.py`: Funciones para la inferencia de imágenes y videos utilizando YOLOv8.
- `utils/mongodb.py`: Funciones para guardar y obtener resultados de inferencia en MongoDB.
- `media/`: Carpeta que contiene los archivos multimedia, incluyendo el logo de la aplicación.

## Equipo

- **Luis Enrique Guerrero**: Ingeniero de Infraestructura y Desarrollo Fullstack
- **Alex García**: Líder de Proyecto y Especialista en Machine Learning
- **Adriana Garay**: Coordinadora de Presentaciones y Gestión de Datos
- **Jeisson Poveda**: Gestor de Recursos y Analista de Datos

## Contribuciones

Las contribuciones son bienvenidas. Si deseas contribuir, por favor abre un issue o envía un pull request.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para obtener más detalles.
