from config import OPENMETEO_BASE_URL, WEATHER_BASE_URL, WEATHER_API_KEY, GEOCODING_URL
import requests, json
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

class DailyWeatherUnit(BaseModel):
    time_unit: str
    temperature_unit: str
    precipitation_probability_unit: str
    wind_speed_unit: str
    precipitation_hours_unit: str
    precipitation_sum_unit: str
    wind_gusts_unit: str
    wind_direction_unit: str

class DailyWeather(BaseModel):
    daily_time: str
    order_day: float
    temperature_max: float
    temperature_min: float
    precipitation_probability_max: float
    wind_speed_max: float
    precipitation_hours: float
    precipitation_sum: float
    wind_gusts_max: float
    wind_direction_dominant: float

class DailyWeatherResponse(BaseModel):
    daily_weather_unit :DailyWeatherUnit
    daily_weather: list[DailyWeather]

@function_tool
def get_current_weather(location:Location=Field(description="Geographic coordinates (latitude and longitude in decimal degrees)"), temperature_unit:Literal["celsius", "fahrenheit"]="celsius", wind_speed_unit:Literal["kmh", "ms", "mph", "kn"]="kmh")-> CurrentWeatherResponse:
    """"
    Retrieve current weather conditions for a given location.

    Returns temperature, wind speed, humidity, and visibility
    using the specified measurement units.
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
    except KeyError:
        raise RuntimeError("Weather API returned unexpected data format")
    except ValueError:
        raise RuntimeError("Weather API returned unexpected data format")
    except json.JSONDecodeError:
        raise RuntimeError("Weather API returned unexpected data format")
    except TypeError:
        raise RuntimeError("Weather API returned unexpected data format")
    except requests.Timeout:
        raise RuntimeError("Weather service timeout")
    except requests.HTTPError as e:
        raise RuntimeError(f"Weather API returned {e.response.status_code}")
    except requests.RequestException:
        raise RuntimeError("Weather service unavailable") 

@function_tool(failure_error_function=None)
def get_weather_forecast(location:Location=Field(description="Geographic coordinates (latitude and longitude in decimal degrees)"),temperature_unit:Literal["celsius", "fahrenheit"]="celsius", wind_speed_unit:Literal["kmh", "ms", "mph", "kn"]="kmh", forecast_days:int=Field(ge=2, le=16, default=2, description="Number of forecast days to retrieve, including today. Minimum is 2 (today and tomorrow), maximum is 16")) -> DailyWeatherResponse:
    """
    Retrieve forecast weather conditions for a given location and by days of forecast.

    Returns temperature, wind speed, humidity, and visibility
    using the specified measurement units.
    """
    daily_forecast_weathers: list[DailyWeather] = []
    params={
        "latitude":location.latitude,
        "longitude":location.longitude,
        "temperature_unit":temperature_unit,
        "wind_speed_unit":wind_speed_unit,
        "forecast_days":forecast_days,
	    "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_probability_max", "wind_speed_10m_max", "precipitation_hours", "precipitation_sum", "wind_gusts_10m_max", "wind_direction_10m_dominant"],
    }
    try:
        response=requests.get(OPENMETEO_BASE_URL + "/v1/forecast", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        number_of_forecast_days_returned = len(data["daily"]["time"])
        for i in range(number_of_forecast_days_returned):
            daily_forecast_weather= DailyWeather(daily_time=data["daily"]["time"][i], order_day=i, temperature_max=data["daily"]["temperature_2m_max"][i], temperature_min=data["daily"]["temperature_2m_min"][i], precipitation_probability_max=data["daily"]["precipitation_probability_max"][i], wind_speed_max=data["daily"]["wind_speed_10m_max"][i], precipitation_hours=data["daily"]["precipitation_hours"][i], precipitation_sum=data["daily"]["precipitation_sum"][i], wind_gusts_max=data["daily"]["wind_gusts_10m_max"][i], wind_direction_dominant=data["daily"]["wind_direction_10m_dominant"][i])
            daily_forecast_weathers.append(daily_forecast_weather)
        daily_weather_unit = DailyWeatherUnit(time_unit=data["daily_units"]["time"], temperature_unit=data["daily_units"]["temperature_2m_max"], precipitation_probability_unit=data["daily_units"]["precipitation_probability_max"], wind_speed_unit=data["daily_units"]["wind_speed_10m_max"], precipitation_hours_unit=data["daily_units"]["precipitation_hours"], precipitation_sum_unit=data["daily_units"]["precipitation_sum"], wind_gusts_unit=data["daily_units"]["wind_gusts_10m_max"], wind_direction_unit=data["daily_units"]["temperature_2m_max"])
        return DailyWeatherResponse(daily_weather_unit=daily_weather_unit, daily_weather=daily_forecast_weathers)
    except KeyError:
        raise RuntimeError("Weather API returned unexpected data format")
    except ValueError:
        raise RuntimeError("Weather API returned unexpected data format")
    except json.JSONDecodeError:
        raise RuntimeError("Weather API returned unexpected data format")
    except TypeError:
        raise RuntimeError("Weather API returned unexpected data format")
    except requests.Timeout:
        raise RuntimeError("Weather service timeout")
    except requests.HTTPError as e:
        raise RuntimeError(f"Weather API returned {e.response.status_code}")
    except requests.RequestException:
        raise RuntimeError("Weather service unavailable") 

def get_hourly_forecast(location:Location=Field(description="Geographic coordinates (latitude and longitude in decimal degrees)"), forecast_hours=12, temperature_unit:Literal["celsius", "fahrenheit"]="celsius", wind_speed_unit:Literal["kmh", "ms", "mph", "kn"]="kmh"):
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

@function_tool
def resolve_location(name:str=Field(description="City name to resolve into geographic coordinates (e.g., 'Paris, France')"))-> Location:
    """
    Convert a city name into geographic coordinates.

    Returns latitude and longitude in decimal degrees.
    """
    params={
        "name":name,
        "count":1
    }
    try:
        response=requests.get(GEOCODING_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return Location(latitude=data["results"][0]["latitude"], longitude=data["results"][0]["longitude"])
    except KeyError:
        raise RuntimeError("Weather API returned unexpected data format")
    except ValueError:
        raise RuntimeError("Weather API returned unexpected data format")
    except json.JSONDecodeError:
        raise RuntimeError("Weather API returned unexpected data format")
    except TypeError:
        raise RuntimeError("Weather API returned unexpected data format")
    except requests.Timeout:
        raise RuntimeError("Weather service timeout")
    except requests.HTTPError as e:
        raise RuntimeError(f"Weather API returned {e.response.status_code}")
    except requests.RequestException:
        raise RuntimeError("Weather service unavailable")