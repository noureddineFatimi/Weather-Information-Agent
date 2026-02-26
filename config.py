from dotenv import load_dotenv
import os

load_dotenv()

ollama_api_key=os.getenv("OLLAMA_API_KEY") or False
ollama_base_url=os.getenv("OLLAMA_BASE_URL") or False
ollama_model_name=os.getenv("OLLAMA_MODEL_NAME") or False
openmeteo_base_url=os.getenv("OPENMETEO_BASE_URL") or False

if not ollama_api_key or not ollama_base_url or not ollama_model_name or not openmeteo_base_url:
    raise ValueError(
        "Please set OLLAMA_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL_NAME, OPENMETEO_BASE_URL via env var or code."
    )