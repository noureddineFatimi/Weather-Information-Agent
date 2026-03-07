from dotenv import load_dotenv
import os

load_dotenv()

OLLAMA_API_KEY=os.getenv("OLLAMA_API_KEY") or False
OLLAMA_BASE_URL=os.getenv("OLLAMA_BASE_URL") or False
OLLAMA_MODEL_NAME=os.getenv("OLLAMA_MODEL_NAME") or False

GEMINI_API_KEY=os.getenv("GEMINI_API_KEY") or False
GEMINI_MODEL_NAME=os.getenv("GEMINI_MODEL_NAME") or False
GEMINI_BASE_URL=os.getenv("GEMINI_BASE_URL") or False

OPENMETEO_BASE_URL=os.getenv("OPENMETEO_BASE_URL") or False

WEATHER_BASE_URL=os.getenv("WEATHER_BASE_URL") or False
WEATHER_API_KEY=os.getenv("WEATHER_API_KEY") or False

GEOCODING_URL=os.getenv("GEOCODING_URL") or False

if not OLLAMA_API_KEY and not GEMINI_API_KEY or not OLLAMA_BASE_URL and not GEMINI_BASE_URL or not OLLAMA_MODEL_NAME and not GEMINI_MODEL_NAME:
    raise ValueError(
        "Please set either OLLAMA_API_KEY or GEMINI_API_KEY or OLLAMA_BASE_URL or GEMINI_BASE_URL or OLLAMA_MODEL_NAME or GEMINI_MODEL_NAME via environment variables or .env file."
    )

if not OPENMETEO_BASE_URL or not WEATHER_API_KEY or not WEATHER_BASE_URL or not GEOCODING_URL:
    raise ValueError(
        "Please set OPENMETEO_BASE_URL, WEATHER_API_KEY, WEATHER_BASE_URL, GEOCODING_URL via env var or code."
    )