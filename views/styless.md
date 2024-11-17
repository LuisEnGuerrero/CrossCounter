<style>
/* Estilos Globales */
body {{
    font-family: Arial, sans-serif;
    background-color: #041033; /* Fondo oscuro general */
    color: #f7f9fa; /* Texto claro */
    margin: 0;
    padding: 0;
}}

/* Header */
.header {{
    text-align: center;
    padding: 20px;
    background-color: #007bff; /* Fondo azul */
    color: #ffffff; /* Texto blanco */
}}

.header img {{
    width: 120px;
    margin-bottom: 10px;
}}

.header h1 {{
    font-size: 2.5em;
    margin: 10px 0;
}}

.header .nav {{
    margin-top: 10px;
}}

.header .nav a {{
    margin: 0 15px;
    text-decoration: none;
    color: #ffffff; /* Texto blanco */
    font-weight: bold;
}}

.header .nav a:hover {{
    text-decoration: underline;
}}

/* Separador del Logo */
.logo-separator {{
    text-align: center;
    margin: 20px 0;
}}

.logo-separator img {{
    width: 150px;
}}

/* Acerca de */
.acerca-de {{
    background-color: #ffffff; /* Fondo blanco */
    color: #041033; /* Texto oscuro */
    border-radius: 10px;
    margin: 20px auto;
    padding: 20px;
    width: 80%;
    box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
}}

.acerca-de h2 {{
    text-align: center;
    color: #007bff; /* Azul */
}}

.acerca-de p {{
    font-size: 1.1em;
    line-height: 1.6;
    text-align: justify;
}}

/* Equipo */
.team-container {{
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    margin: 20px auto;
    gap: 20px;
    padding: 20px;
}}

.team-card {{
    background-color: #ffffff; /* Fondo blanco */
    color: #041033; /* Texto oscuro */
    border: 1px solid #ddd;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    width: 250px;
    text-align: center;
    padding: 20px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}

.team-card:hover {{
    transform: scale(1.05);
    box-shadow: 0 6px 8px rgba(0, 0, 0, 0.2);
}}

.team-card img {{
    width: 100px;
    height: 100px;
    border-radius: 50%;
    margin-bottom: 15px;
}}

.team-card h3 {{
    font-size: 1.2em;
    margin-bottom: 10px;
}}

.team-card p {{
    font-size: 0.9em;
    color: #555;
}}

/* Botón de Volver */
.back-to-top {{
    display: block;
    text-align: center;
    margin: 20px auto;
    padding: 10px 15px;
    background-color: #007bff;
    color: #ffffff;
    font-weight: bold;
    text-decoration: none;
    border-radius: 5px;
    width: fit-content;
}}

.back-to-top:hover {{
    background-color: #0056b3;
}}

/* Documentación */
#documentacion {{
    background-color: #f7f9fa; /* Fondo claro */
    color: #041033; /* Texto oscuro */
    padding: 20px;
    border-radius: 10px;
    width: 80%;
    margin: 20px auto;
    box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
}}

#documentacion h2 {{
    color: #007bff; /* Azul */
    text-align: center;
}}

#documentacion ol {{
    font-size: 1em;
    margin: 20px;
    line-height: 1.6;
}}

#documentacion li {{
    margin-bottom: 10px;
}}

/* Código QR */
.qr-section {{
    text-align: center;
    margin: 20px auto;
}}

.qr-section p {{
    margin-bottom: 10px;
    font-size: 1.1em;
}}

.qr-section img {{
    width: 200px;
}}

/* Footer */
footer {{
    text-align: center;
    padding: 10px;
    background-color: #041033;
    color: #f7f9fa;
    font-size: 12px;
    position: fixed;
    bottom: 0;
    width: 100%;
}}

/* Scrollbar Personalizado */
::-webkit-scrollbar {{
    width: 10px;
}}

::-webkit-scrollbar-track {{
    background: #041033; /* Fondo oscuro */
}}

::-webkit-scrollbar-thumb {{
    background: #888;
}}

::-webkit-scrollbar-thumb:hover {{
    background: #555;
}}
</style>
