from config import OPENMETEO_BASE_URL, WEATHER_BASE_URL, WEATHER_API_KEY, GEOCODING_URL
import httpx, json
from agents import function_tool
from typing import Literal
from pydantic import Field
import models
import time

get_current_weather_cache = {}
cache_timeout_current_weather = 900

@function_tool(failure_error_function=None)
async def get_current_weather(location:models.Location=Field(description="Geographic coordinates (latitude and longitude in decimal degrees)"), temperature_unit:Literal["celsius", "fahrenheit"]="celsius", wind_speed_unit:Literal["kmh", "ms", "mph", "kn"]="kmh")-> models.CurrentWeatherResponse:
    """"
    Retrieve current weather conditions for a given location.

    Returns temperature and wind speed, using the specified measurement units.
    """
    start_time = time.perf_counter()
    cache_key = f"current_weather_{location.latitude}_{location.longitude}_{temperature_unit}_{wind_speed_unit}"

    if cache_key in get_current_weather_cache and time.time() - get_current_weather_cache[cache_key]['timestamp'] < cache_timeout_current_weather:
            print(f"-- Current weather retrieved from cache for location ({location.latitude}, {location.longitude}) with temperature unit {temperature_unit} and wind speed unit {wind_speed_unit} : {get_current_weather_cache[cache_key]['data']}")
            return get_current_weather_cache[cache_key]['data']

    params={
        "latitude":location.latitude,
        "longitude":location.longitude,
        "temperature_unit":temperature_unit,
        "wind_speed_unit":wind_speed_unit,
	    "current": ["temperature_2m", "wind_speed_10m", "relative_humidity_2m", "precipitation"]
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(OPENMETEO_BASE_URL + "/v1/forecast", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            get_current_weather_cache[cache_key] = {}
            get_current_weather_cache[cache_key]['timestamp'] = time.time()
            get_current_weather_cache[cache_key]['data'] = models.CurrentWeatherResponse(temperature=data["current"]["temperature_2m"], wind_speed=data["current"]["wind_speed_10m"], relative_humidity=data["current"]["relative_humidity_2m"], precipitation=data["current"]["precipitation"], temperature_unit=data["current_units"]["temperature_2m"], wind_speed_unit=data["current_units"]["wind_speed_10m"], relative_humidity_unit=data["current_units"]["relative_humidity_2m"], precipitation_unit=data["current_units"]["precipitation"])
            end_time = time.perf_counter()
            tool_time_seconds = round(end_time - start_time, 2)
            print(f"-- current weather tool response time: {tool_time_seconds} seconds")
            return get_current_weather_cache[cache_key]['data']
    except KeyError:
        raise RuntimeError("Weather API returned unexpected data format")
    except ValueError:
        raise RuntimeError("Weather API returned unexpected data format")
    except json.JSONDecodeError:
        raise RuntimeError("Weather API returned unexpected data format")
    except TypeError:
        raise RuntimeError("Weather API returned unexpected data format")
    except httpx.Timeout:
        raise RuntimeError("Weather service timeout")
    except httpx.HTTPError as e:
        raise RuntimeError(f"Weather API returned {e}")
    except Exception:
        raise RuntimeError("Weather service unavailable") 

get_weather_forecast_cache = {}
cache_timeout_weather_forecast = 3600

@function_tool
async def get_weather_forecast(location:models.Location=Field(description="Geographic coordinates (latitude and longitude in decimal degrees)"),temperature_unit:Literal["celsius", "fahrenheit"]="celsius", wind_speed_unit:Literal["kmh", "ms", "mph", "kn"]="kmh", forecast_days:int=Field(ge=1, le=16, description="Number of forecast days to retrieve, include today.")) -> models.DailyWeatherResponse:
    """
    Retrieve forecast weather conditions for a given location and by days of forecast.

    Returns temperature and wind speed, using the specified measurement units.
    """
    start_time = time.perf_counter()
    cache_key = f"weather_forecast_{location.latitude}_{location.longitude}_{temperature_unit}_{wind_speed_unit}_{forecast_days}"

    if cache_key in get_weather_forecast_cache and time.time() - get_weather_forecast_cache[cache_key]['timestamp'] < cache_timeout_weather_forecast:
        print(f"-- Forecast weather retrieved from cache for location ({location.latitude}, {location.longitude}) with temperature unit {temperature_unit} and wind speed unit {wind_speed_unit} : {get_weather_forecast_cache[cache_key]['data']}")
        return get_weather_forecast_cache[cache_key]['data']

    daily_forecast_weathers: list[models.DailyWeather] = []
    params={
        "latitude":location.latitude,
        "longitude":location.longitude,
        "temperature_unit":temperature_unit,
        "wind_speed_unit":wind_speed_unit,
        "forecast_days":forecast_days,
	    "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_probability_max", "wind_speed_10m_max", "precipitation_hours"]
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(OPENMETEO_BASE_URL + "/v1/forecast", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            number_of_forecast_days_returned = len(data["daily"]["time"])
            for i in range(number_of_forecast_days_returned):
                daily_forecast_weather= models.DailyWeather(daily_time=data["daily"]["time"][i], temperature_max=data["daily"]["temperature_2m_max"][i], temperature_min=data["daily"]["temperature_2m_min"][i], precipitation_probability_max=data["daily"]["precipitation_probability_max"][i], wind_speed_max=data["daily"]["wind_speed_10m_max"][i], precipitation_hours=data["daily"]["precipitation_hours"][i])
                daily_forecast_weathers.append(daily_forecast_weather)
            daily_weather_unit = models.DailyWeatherUnit(time_unit=data["daily_units"]["time"], temperature_unit=data["daily_units"]["temperature_2m_max"], precipitation_probability_unit=data["daily_units"]["precipitation_probability_max"], wind_speed_unit=data["daily_units"]["wind_speed_10m_max"], precipitation_hours_unit=data["daily_units"]["precipitation_hours"])
            get_weather_forecast_cache[cache_key] = {}
            get_weather_forecast_cache[cache_key]['timestamp'] = time.time()
            get_weather_forecast_cache[cache_key]['data'] = models.DailyWeatherResponse(daily_weather_unit=daily_weather_unit, daily_weather=daily_forecast_weathers)
            end_time = time.perf_counter()
            tool_time_seconds = round(end_time - start_time, 2)
            print(f"-- weather forecast tool response time: {tool_time_seconds} seconds")
            return get_weather_forecast_cache[cache_key]['data']
    except KeyError:
        raise RuntimeError("Weather API returned unexpected data format")
    except ValueError:
        raise RuntimeError("Weather API returned unexpected data format")
    except json.JSONDecodeError:
        raise RuntimeError("Weather API returned unexpected data format")
    except TypeError:
        raise RuntimeError("Weather API returned unexpected data format")
    except httpx.Timeout:
        raise RuntimeError("Weather service timeout")
    except httpx.HTTPError as e:
        raise RuntimeError(f"Weather API returned {e}")
    except Exception:
        raise RuntimeError("Weather service unavailable") 

@function_tool
async def get_hourly_forecast(location:models.Location=Field(description="Geographic coordinates (latitude and longitude in decimal degrees)"), forecast_hours:int=Field(ge=1, le=48, description="Number of how many hours separate the current hour from the requested hours, included the current hour, maximum is 48 hours"), temperature_unit:Literal["celsius", "fahrenheit"]="celsius", wind_speed_unit:Literal["kmh", "ms", "mph", "kn"]="kmh")-> models.HourlyWeatherResponse:
    """
    Retrieve forecast weather conditions for a given location and by hours of forecast.

    Returns temperature and wind speed, using the specified measurement units.
    """
    start_time = time.perf_counter()
    params={
        "latitude":location.latitude,
        "longitude":location.longitude,
        "temperature_unit":temperature_unit,
        "wind_speed_unit":wind_speed_unit,
        "forecast_hours":forecast_hours,
		"hourly": ["temperature_2m", "relative_humidity_2m", "rain", "visibility", "wind_speed_10m", "precipitation_probability"]
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(OPENMETEO_BASE_URL + "/v1/forecast", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            hourly_forecast_weathers: list[models.HourlyWeather] = []
            number_of_forecast_hours_returned = min(len(data["hourly"]["time"]), forecast_hours)
            for i in range(number_of_forecast_hours_returned):
                hourly_forecast_weathers.append(models.HourlyWeather(
                hourly_time=data["hourly"]["time"][i],
                temperature=data["hourly"]["temperature_2m"][i],
                relative_humidity=data["hourly"]["relative_humidity_2m"][i],
                rain=data["hourly"]["rain"][i],
                visibility=data["hourly"]["visibility"][i],
                wind_speed=data["hourly"]["wind_speed_10m"][i],
                precipitation_probability=data["hourly"]["precipitation_probability"][i]
            ))
            hourly_weather_unit = models.HourlyWeatherUnit(utc_offset_seconds=data["utc_offset_seconds"], timezone=data["timezone"], time_unit=data["hourly_units"]["time"], temperature_unit=data["hourly_units"]["temperature_2m"], relative_humidity_unit=data["hourly_units"]["relative_humidity_2m"], rain_unit=data["hourly_units"]["rain"], visibility_unit=data["hourly_units"]["visibility"], wind_speed_unit=data["hourly_units"]["wind_speed_10m"], precipitation_probability_unit=data["hourly_units"]["precipitation_probability"])
            end_time = time.perf_counter()
            tool_time_seconds = round(end_time - start_time, 2)
            print(f"-- weather forecast tool response time: {tool_time_seconds} seconds")
            return models.HourlyWeatherResponse(hourly_weather_unit=hourly_weather_unit, hourly_weather=hourly_forecast_weathers)
    except KeyError:
        raise RuntimeError("Weather API returned unexpected data format")
    except ValueError:
        raise RuntimeError("Weather API returned unexpected data format")
    except json.JSONDecodeError:
        raise RuntimeError("Weather API returned unexpected data format")
    except TypeError:
        raise RuntimeError("Weather API returned unexpected data format")
    except httpx.Timeout:
        raise RuntimeError("Weather service timeout")
    except httpx.HTTPError as e:
        raise RuntimeError(f"Weather API returned {e}")
    except Exception:
        raise RuntimeError("Weather service unavailable") 

get_weather_alerts_cache = {}
cache_timeout_weather_alerts = 1800

@function_tool
async def get_weather_alerts(location:models.Location=Field(description="Geographic coordinates (latitude and longitude in decimal degrees)"), severity: Literal["all", "minor", "moderate", "severe", "extreme"] = "all") -> list[models.WeatherAlert]:
    """
    Retrieve weather alerts for a given location.

    Returns a list of weather alerts, including their title, severity, urgency, and description.
    """
    start_time = time.perf_counter()
    cache_key = f"weather_alerts_{location.latitude}_{location.longitude}_{severity}"

    if cache_key in get_weather_alerts_cache:
        print(f"-- Weather alerts retrieved from cache for location ({location.latitude}, {location.longitude}) with severity {severity} : {get_weather_alerts_cache[cache_key]['data']}")
        return get_weather_alerts_cache[cache_key]

    params={ 
        "key":WEATHER_API_KEY,
        "q":f"{location.latitude},{location.longitude}"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(WEATHER_BASE_URL + "/v1/alerts.json", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            weather_alerts: list[models.WeatherAlert] = []
            for alert in data["alerts"]["alert"]:
                if severity == "all" or alert["severity"].lower() == severity:
                    weather_alerts.append(models.WeatherAlert(title=alert["headline"], message_type=alert["msgtype"], severity=alert["severity"], urgency=alert["urgency"], areas=alert["areas"], event=alert["event"], effective_time=alert["effective"], expiry_time=alert["expires"], description=alert["desc"], instruction=alert["instruction"]))
            if len(weather_alerts) == 0:
                get_weather_alerts_cache[cache_key] = {}
                get_weather_alerts_cache[cache_key]['timestamp'] = time.time()
                get_weather_alerts_cache[cache_key]['data'] = {"message": "No weather alerts for this location and severity level."}
                return get_weather_alerts_cache[cache_key]['data']
            get_weather_alerts_cache[cache_key] = {}
            get_weather_alerts_cache[cache_key]['timestamp'] = time.time()
            get_weather_alerts_cache[cache_key]['data'] = weather_alerts
            end_time = time.perf_counter()
            tool_time_seconds = round(end_time - start_time, 2)
            print(f"-- weather alerts tool response time: {tool_time_seconds} seconds")
            return get_weather_alerts_cache[cache_key]['data']
    except KeyError:
        raise RuntimeError("Weather API returned unexpected data format")
    except ValueError:
        raise RuntimeError("Weather API returned unexpected data format")
    except json.JSONDecodeError:
        raise RuntimeError("Weather API returned unexpected data format")
    except TypeError:
        raise RuntimeError("Weather API returned unexpected data format")
    except httpx.Timeout:
        raise RuntimeError("Weather service timeout")
    except httpx.HTTPError as e:
        raise RuntimeError(f"Weather API returned {e}")
    except Exception:
        raise RuntimeError("Weather service unavailable") 

resolve_location_cache = {}

@function_tool
async def resolve_location(name:str=Field(description="City name to resolve into geographic coordinates"))-> models.Location:
    """
    Convert a city name into geographic coordinates.

    Returns latitude and longitude in decimal degrees.
    """
    start_time = time.perf_counter()
    cache_key = f"location_{name}"
    
    if cache_key in resolve_location_cache:
        print(f"-- Location resolved from cache for {name} : {resolve_location_cache[cache_key]}")
        return resolve_location_cache[cache_key]

    params={
        "name":name,
        "count":1
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(GEOCODING_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            resolve_location_cache[cache_key] = models.Location(latitude=data["results"][0]["latitude"], longitude=data["results"][0]["longitude"])
            end_time = time.perf_counter()
            tool_time_seconds = round(end_time - start_time, 2)
            print(f"-- location resolution tool response time: {tool_time_seconds} seconds")
            return resolve_location_cache[cache_key]
    except KeyError:
        raise RuntimeError("Weather API returned unexpected data format")
    except ValueError:
        raise RuntimeError("Weather API returned unexpected data format")
    except json.JSONDecodeError:
        raise RuntimeError("Weather API returned unexpected data format")
    except TypeError:
        raise RuntimeError("Weather API returned unexpected data format")
    except httpx.Timeout:
        raise RuntimeError("Weather service timeout")
    except httpx.HTTPError as e:
        raise RuntimeError(f"Weather API returned {e}")
    except Exception:
        raise RuntimeError("Weather service unavailable")

suggest_weather_clothing_cache = {}

@function_tool
async def suggest_weather_clothing(weather: models.Weather=Field(description="The weather conditions"), activity_type: Literal["outdoor", "indoor"]=Field(description="The type of activity the user plans to do, either 'outdoor' or 'indoor'")):
    """
    Suggest appropriate clothing based on weather conditions and activity type.

    Returns a clothing recommendation string.
    """
    start_time = time.perf_counter()
    cache_key = f"clothing_{weather.temperature}_{weather.temperature_unit}_{weather.wind_speed}_{weather.wind_speed_unit}_{activity_type}"

    if cache_key in suggest_weather_clothing_cache:
        print(f"-- Clothing suggestion retrieved from cache for current weather with temperature {weather.temperature} {weather.temperature_unit} and wind speed {weather.wind_speed} {weather.wind_speed_unit} and activity type {activity_type} : {suggest_weather_clothing_cache[cache_key]}")
        return suggest_weather_clothing_cache[cache_key]

    recommendations = [] 
    if weather.temperature_unit != "celsius":
        temperature_celsius = (weather.temperature - 32) * 5/9
    else:
        temperature_celsius = weather.temperature
    if weather.wind_speed_unit != "kmh":
        if weather.wind_speed_unit == "ms":
            wind_speed_kmh = weather.wind_speed * 3.6
        elif weather.wind_speed_unit == "mph":
            wind_speed_kmh = weather.wind_speed * 1.60934
        elif weather.wind_speed_unit == "kn":
            wind_speed_kmh = weather.wind_speed * 1.852
    else:
        wind_speed_kmh = weather.wind_speed
    if activity_type == "outdoor":
        if temperature_celsius < 0:
            recommendations.append("It's very cold outside. Wear a heavy coat, gloves, and a hat.")
        elif temperature_celsius < 10 :
            recommendations.append("It's cold outside. Wear a coat and consider layering with a sweater.")
        elif temperature_celsius < 20 :
            recommendations.append("It's cool outside. A light jacket or sweater should be sufficient.")
        elif temperature_celsius < 30:
            recommendations.append("The weather is warm. Wear comfortable clothing like a t-shirt and shorts.")
        else:
            recommendations.append("It's hot outside. Wear lightweight and breathable clothing, and stay hydrated.")
        if wind_speed_kmh > 40:
            recommendations.append("It's also very windy. Consider wearing a windbreaker or a jacket that can protect you from the wind.")
    elif activity_type == "indoor":
        if temperature_celsius < 15:
            recommendations.append("It's cold indoors. Consider wearing a sweater or layering your clothing.")
        elif temperature_celsius > 25:
            recommendations.append("It's warm indoors. Wear comfortable and breathable clothing.")
        else:
            recommendations.append("The indoor temperature is comfortable. Dress as you normally would.")
    
    suggest_weather_clothing_cache[cache_key] = " ".join(recommendations)
    end_time = time.perf_counter()
    tool_time_seconds = round(end_time - start_time, 2)
    print(f"-- clothing suggestion tool response time: {tool_time_seconds} seconds")
    return suggest_weather_clothing_cache[cache_key]