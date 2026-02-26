from dotenv import load_dotenv
import os

load_dotenv()

OLLAMA_API_KEY=os.getenv("OLLAMA_API_KEY") or False
OLLAMA_BASE_URL=os.getenv("OLLAMA_BASE_URL") or False
OLLAMA_MODEL_NAME=os.getenv("OLLAMA_MODEL_NAME") or False
OPENMETEO_BASE_URL=os.getenv("OPENMETEO_BASE_URL") or False
WEATHER_BASE_URL=os.getenv("WEATHER_BASE_URL") or False
WEATHER_API_KEY=os.getenv("WEATHER_API_KEY") or False
GEOCODING_URL=os.getenv("GEOCODING_URL") or False

if not OLLAMA_API_KEY or not OLLAMA_BASE_URL or not OLLAMA_MODEL_NAME or not OPENMETEO_BASE_URL or not WEATHER_API_KEY or not WEATHER_BASE_URL or not GEOCODING_URL:
    raise ValueError(
        "Please set OLLAMA_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL_NAME, OPENMETEO_BASE_URL, WEATHER_API_KEY, WEATHER_BASE_URL, GEOCODING_URL via env var or code."
    )