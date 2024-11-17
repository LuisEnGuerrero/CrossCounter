import os
import base64
import qrcode
from io import BytesIO

# Convertir imágenes a Base64
def get_base64_image(image_path):
    """
    Convierte una imagen a Base64.
    
    Args:
        image_path (str): Ruta de la imagen.
    
    Returns:
        str: Cadena Base64 de la imagen.
    """
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

# Generar imágenes Base64 desde la carpeta /media
logo_path = os.path.join(os.path.dirname(__file__), "../media/logox512.jpg")
logo_base64 = get_base64_image(logo_path)

Enrique_path = os.path.join(os.path.dirname(__file__), "../media/Enrique.jpg")
Enrique_base64 = get_base64_image(Enrique_path)

Alex_path = os.path.join(os.path.dirname(__file__), "../media/Alex.jpg")
Alex_base64 = get_base64_image(Alex_path)

Adriana_path = os.path.join(os.path.dirname(__file__), "../media/Adriana.jpg")
Adriana_base64 = get_base64_image(Adriana_path)

Jeisson_path = os.path.join(os.path.dirname(__file__), "../media/Jeisson.jpg")
Jeisson_base64 = get_base64_image(Jeisson_path)

def generate_qr_code(video_url):
    """
    Genera un código QR en Base64 para un enlace.

    Args:
        video_url (str): URL del video.

    Returns:
        str: Imagen del código QR en Base64.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(video_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# HTML de cada sección
def anchor_html():
    """
    Ancla para volver al inicio.
    """
    return """
    <div id="inicio"></div>
    """

def header_html():
    """
    Encabezado principal con logo y navegación.
    """
    return f"""
    <div class="header">
        <img src="data:image/jpeg;base64,{logo_base64}" alt="Logo">
        <h1>AI·MotorCycle CrossCounter TalentoTECH</h1>
        <div class="nav">
            <a href="#inicio">Inicio</a>
            <a href="#acerca-de">Acerca·de</a>
            <a href="#documentacion">Documentación</a>
        </div>
    </div>
    """

def logo_separator_html():
    """
    Separador con el logo en el centro.
    """
    return f"""
    <div style="text-align: center; margin: 20px 0;">
        <img src="data:image/jpeg;base64,{logo_base64}" alt="Logo" style="width: 150px;">
    </div>
    """

def qr_code_html(video_url):
    """
    Código QR para ver el video en YouTube.

    Args:
        video_url (str): URL del video de YouTube.
    """
    qr_base64 = generate_qr_code(video_url)
    return f"""
    <div style="text-align: center;">
        <p>Escanea el siguiente código QR para ver el video en YouTube:</p>
        <img src="data:image/png;base64,{qr_base64}" alt="QR Code">
    </div>
    """

def about_section_html():
    """
    Sección 'Acerca de' del proyecto.
    """
    return """
    <div class="acerca-de">
        <h2>Acerca de</h2>
        <p>
            Somos <strong>TechRoads Innovators</strong>, un equipo dedicado a desarrollar soluciones innovadoras para el monitoreo y análisis de tráfico.
            Nuestro proyecto <strong>AI·MotorCycle CrossCounter TalentoTECH</strong> utiliza inteligencia artificial para detectar y contar motocicletas en videos,
            proporcionando datos valiosos para mejorar la seguridad y eficiencia del tráfico.
        </p>
    </div>
    """

def team_section_html():
    """
    Sección del equipo con tarjetas de presentación.
    """
    return f"""
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
    <a href="#inicio" class="back-to-top">↑ ­VOLVER ARRIBA ↑</a>
    """

def documentation_html():
    """
    Sección de documentación de uso.
    """
    return """
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
    """
