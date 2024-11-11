import os
from roboflow import Roboflow, CLIPModel, GazeModel
from dotenv import load_dotenv

# Cargar variables de entorno desde la raíz
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Obtener las variables de entorno
API_KEY = os.getenv("ROBOFLOW_API_KEY")
MODEL_ID = os.getenv("ROBOFLOW_MODEL_ID")
API_URL = os.getenv("ROBOFLOW_API_URL")

# if not API_KEY or not MODEL_ID or not API_URL:
#    raise EnvironmentError("API_KEY, MODEL_ID o API_URL no están configurados en el archivo .env")

# Inicializar la instancia de Roboflow
rf = Roboflow(api_key=API_KEY)

def get_video_inference(video_path: str, fps: int = 5, method: str = "object-detection"):
    """
    Realiza inferencia en video usando la API de Roboflow.
    """
    if method == "object-detection":
        project = rf.workspace().project("etiquetado-de-motos")
        model = project.version("1").model
    elif method == "clip":
        model = CLIPModel()
    elif method == "gaze-detection":
        model = GazeModel()
    else:
        raise ValueError("Método de inferencia no soportado.")

    job_id, signed_url, expire_time = model.predict_video(
        video_path,
        fps=fps,
        prediction_type="batch-video",
    )
    
    results = model.poll_until_video_results(job_id)
    return results

def get_image_inference(image_path: str):
    """
    Realiza inferencia en una imagen usando la API de Roboflow para imágenes individuales.
    """
    from inference_sdk import InferenceHTTPClient
    
    api_url = os.getenv("ROBOFLOW_API_URL")
    client = InferenceHTTPClient(api_url=api_url, api_key=API_KEY)
    result = client.infer(image_path, model_id=MODEL_ID)
    
    return result
