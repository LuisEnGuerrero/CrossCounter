from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde .env
load_dotenv()

def get_database():
    """Conecta a MongoDB y devuelve una referencia a la base de datos."""
    try:
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client.get_database()  # Obtener la base de datos por defecto en la URI
        print("Conexión a MongoDB Atlas exitosa")
        return db
    except Exception as e:
        print("Error al conectar a MongoDB Atlas:", e)
        return None

if __name__ == "__main__":
    # Prueba la conexión a la base de datos
    db = get_database()
    if db:
        print("Base de datos:", db.name)
