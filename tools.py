from config import OPENMETEO_BASE_URL, WEATHER_BASE_URL, WEATHER_API_KEY, GEOCODING_URL
import requests
from pydantic import BaseModel, Field
from typing import Literal
from agents import function_tool

class Location(BaseModel):
    latitude: float=Field(ge=-90, le=90, description="Latitude in degrees")
    longitude: float=Field(ge=-180, le=180, description="Longitude in degrees")

class CurrentWeatherResponse(BaseModel):
    temperature: float
    wind_speed: float
    relative_humidity: float
    visibility: float
    temperature_unit: str
    wind_speed_unit: str
    relative_humidity_unit:str
    visibility_unit:str

@function_tool
def get_current_weather(location:Location=Field(description="The Location object created by the longitude and latitude input"), temperature_unit:Literal["celsius", "fahrenheit"]="celsius", wind_speed_unit:Literal["kmh", "ms", "mph ", "kn"]="kmh")-> CurrentWeatherResponse:
    """"
    Get weather informations from coordinates by the requested units.
    """
    params={
        "latitude":location.latitude,
        "longitude":location.longitude,
        "temperature_unit":temperature_unit,
        "wind_speed_unit":wind_speed_unit,
	    "current": ["temperature_2m", "wind_speed_10m", "relative_humidity_2m", "visibility"]
    }
    try:
        response=requests.get(OPENMETEO_BASE_URL + "/v1/forecast", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return CurrentWeatherResponse(temperature=data["current"]["temperature_2m"], wind_speed=data["current"]["wind_speed_10m"], relative_humidity=data["current"]["relative_humidity_2m"], visibility=data["current"]["visibility"], temperature_unit=data["current_units"]["temperature_2m"], wind_speed_unit=data["current_units"]["wind_speed_10m"], relative_humidity_unit=data["current_units"]["relative_humidity_2m"], visibility_unit=data["current_units"]["visibility"])
    except requests.RequestException as e:
        raise RuntimeError(f"Weather API error: {str(e)}")

def get_weather_forecast(latitude, longitude, temperature_unit="celsius", wind_speed_unit="kmh", forecast_days=1):
    params={
        "latitude":latitude,
        "longitude":longitude,
        "temperature_unit":temperature_unit,
        "wind_speed_unit":wind_speed_unit,
        "forecast_days":forecast_days,
	"daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_probability_max", "wind_speed_10m_max", "precipitation_hours", "precipitation_sum", "wind_gusts_10m_max", "wind_direction_10m_dominant"],
    }
    response=requests.get(OPENMETEO_BASE_URL + "/v1/forecast", params=params)
    return response.json()

def get_hourly_forecast(latitude, longitude, forecast_hours=12, temperature_unit="celsius", wind_speed_unit="kmh"):
    params={
        "latitude":latitude,
        "longitude":longitude,
        "temperature_unit":temperature_unit,
        "wind_speed_unit":wind_speed_unit,
        "forecast_hours":forecast_hours,
		"hourly": ["temperature_2m", "relative_humidity_2m", "rain", "visibility", "wind_speed_10m", "wind_direction_10m", "temperature_80m", "precipitation_probability", "showers", "snowfall", "cloud_cover", "soil_temperature_0cm", "soil_moisture_0_to_1cm"]
    }
    response=requests.get(OPENMETEO_BASE_URL + "/v1/forecast", params=params)
    return response.json()

def get_weather_alerts(q):
    params={
        "key":WEATHER_API_KEY,
        "q":q
    }
    response=requests.get(WEATHER_BASE_URL + "/v1/alerts.json", params=params)
    return response.json()

def resolve_location(name):
    params={
        "name":name,
        "count":1
    }
    response=requests.get(GEOCODING_URL, params=params)
    return response.json()    

if __name__ == "__main__":
    resolve_location("Bryansk")