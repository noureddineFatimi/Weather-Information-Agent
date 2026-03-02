from config import OPENMETEO_BASE_URL, WEATHER_BASE_URL, WEATHER_API_KEY, GEOCODING_URL
import requests, json
from agents import function_tool
from typing import Literal
from pydantic import Field
import models

@function_tool
def get_current_weather(location:models.Location=Field(description="Geographic coordinates (latitude and longitude in decimal degrees)"), temperature_unit:Literal["celsius", "fahrenheit"]="celsius", wind_speed_unit:Literal["kmh", "ms", "mph", "kn"]="kmh")-> models.CurrentWeatherResponse:
    """"
    Retrieve current weather conditions for a given location.

    Returns temperature and wind speed, using the specified measurement units.
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
        return models.CurrentWeatherResponse(temperature=data["current"]["temperature_2m"], wind_speed=data["current"]["wind_speed_10m"], relative_humidity=data["current"]["relative_humidity_2m"], visibility=data["current"]["visibility"], temperature_unit=data["current_units"]["temperature_2m"], wind_speed_unit=data["current_units"]["wind_speed_10m"], relative_humidity_unit=data["current_units"]["relative_humidity_2m"], visibility_unit=data["current_units"]["visibility"])
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

@function_tool
def get_weather_forecast(location:models.Location=Field(description="Geographic coordinates (latitude and longitude in decimal degrees)"),temperature_unit:Literal["celsius", "fahrenheit"]="celsius", wind_speed_unit:Literal["kmh", "ms", "mph", "kn"]="kmh", forecast_days:int=Field(ge=2, le=16, default=2, description="Number of forecast days to retrieve, including today. Minimum is 2 (today and tomorrow), maximum is 16")) -> models.DailyWeatherResponse:
    """
    Retrieve forecast weather conditions for a given location and by days of forecast.

    Returns temperature and wind speed, using the specified measurement units.
    """
    daily_forecast_weathers: list[models.DailyWeather] = []
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
            daily_forecast_weather= models.DailyWeather(daily_time=data["daily"]["time"][i], order_day=i, temperature_max=data["daily"]["temperature_2m_max"][i], temperature_min=data["daily"]["temperature_2m_min"][i], precipitation_probability_max=data["daily"]["precipitation_probability_max"][i], wind_speed_max=data["daily"]["wind_speed_10m_max"][i], precipitation_hours=data["daily"]["precipitation_hours"][i], precipitation_sum=data["daily"]["precipitation_sum"][i], wind_gusts_max=data["daily"]["wind_gusts_10m_max"][i], wind_direction_dominant=data["daily"]["wind_direction_10m_dominant"][i])
            daily_forecast_weathers.append(daily_forecast_weather)
        daily_weather_unit = models.DailyWeatherUnit(time_unit=data["daily_units"]["time"], temperature_unit=data["daily_units"]["temperature_2m_max"], precipitation_probability_unit=data["daily_units"]["precipitation_probability_max"], wind_speed_unit=data["daily_units"]["wind_speed_10m_max"], precipitation_hours_unit=data["daily_units"]["precipitation_hours"], precipitation_sum_unit=data["daily_units"]["precipitation_sum"], wind_gusts_unit=data["daily_units"]["wind_gusts_10m_max"], wind_direction_unit=data["daily_units"]["wind_direction_10m_dominant"])
        return models.DailyWeatherResponse(daily_weather_unit=daily_weather_unit, daily_weather=daily_forecast_weathers)
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

@function_tool
def get_hourly_forecast(location:models.Location=Field(description="Geographic coordinates (latitude and longitude in decimal degrees)"), forecast_hours:int=Field(ge=12, le=48, description="Number of hours to forecast to retrieve, Minimum is 12, Maximum is 48"), temperature_unit:Literal["celsius", "fahrenheit"]="celsius", wind_speed_unit:Literal["kmh", "ms", "mph", "kn"]="kmh")-> models.HourlyWeatherResponse:
    """
    Retrieve forecast weather conditions for a given location and by hours of forecast.

    Returns temperature and wind speed, using the specified measurement units.
    """
    params={
        "latitude":location.latitude,
        "longitude":location.longitude,
        "temperature_unit":temperature_unit,
        "wind_speed_unit":wind_speed_unit,
        "forecast_hours":forecast_hours,
		"hourly": ["temperature_2m", "relative_humidity_2m", "rain", "visibility", "wind_speed_10m", "wind_direction_10m", "precipitation_probability", "showers", "snowfall", "cloud_cover"]
    }
    try:
        response=requests.get(OPENMETEO_BASE_URL + "/v1/forecast", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        hourly_forecast_weathers: list[models.HourlyWeather] = []
        number_of_forecast_hours_returned = len(data["hourly"]["time"])
        for i in range(number_of_forecast_hours_returned):
            hourly_forecast_weathers.append(models.HourlyWeather(
                hourly_time=data["hourly"]["time"][i],
                order_hour=i,
                temperature=data["hourly"]["temperature_2m"][i],
                relative_humidity=data["hourly"]["relative_humidity_2m"][i],
                rain=data["hourly"]["rain"][i],
                visibility=data["hourly"]["visibility"][i],
                wind_speed=data["hourly"]["wind_speed_10m"][i],
                wind_direction=data["hourly"]["wind_direction_10m"][i],
                precipitation_probability=data["hourly"]["precipitation_probability"][i],
                showers=data["hourly"]["showers"][i],
                snowfall=data["hourly"]["snowfall"][i],
                cloud_cover=data["hourly"]["cloud_cover"][i]
            ))
        hourly_weather_unit = models.HourlyWeatherUnit(time_unit=data["hourly_units"]["time"], temperature_unit=data["hourly_units"]["temperature_2m"], relative_humidity_unit=data["hourly_units"]["relative_humidity_2m"], rain_unit=data["hourly_units"]["rain"], visibility_unit=data["hourly_units"]["visibility"], wind_speed_unit=data["hourly_units"]["wind_speed_10m"], wind_direction_unit=data["hourly_units"]["wind_direction_10m"], precipitation_probability_unit=data["hourly_units"]["precipitation_probability"], showers_unit=data["hourly_units"]["showers"], snowfall_unit=data["hourly_units"]["snowfall"], cloud_cover_unit=data["hourly_units"]["cloud_cover"])
        return models.HourlyWeatherResponse(hourly_weather_unit=hourly_weather_unit, hourly_weather=hourly_forecast_weathers)
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

@function_tool
def get_weather_alerts(location:str=Field(description="City name or geographic coordinates (latitude and longitude in decimal degrees) to retrieve weather alerts for (e.g., 'Paris, France' or '48.8566, 2.3522')")) -> list[models.WeatherAlert]:
    """
    Retrieve weather alerts for a given location.

    Returns a list of weather alerts, including their title, severity, urgency, and description.
    """
    params={ 
        "key":WEATHER_API_KEY,
        "q":location
    }
    try:
        response=requests.get(WEATHER_BASE_URL + "/v1/alerts.json", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        weather_alerts: list[models.WeatherAlert] = []
        for alert in data["alerts"]["alert"]:
            weather_alerts.append(models.WeatherAlert(title=alert["headline"], message_type=alert["msgtype"], severity=alert["severity"], urgency=alert["urgency"], areas=alert["areas"], event=alert["event"], effective_time=alert["effective"], expiry_time=alert["expires"], description=alert["desc"], instruction=alert["instruction"]))
        return weather_alerts
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

@function_tool
def resolve_location(name:str=Field(description="City name to resolve into geographic coordinates (e.g., 'Paris, France')"))-> models.Location:
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
        return models.Location(latitude=data["results"][0]["latitude"], longitude=data["results"][0]["longitude"])
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