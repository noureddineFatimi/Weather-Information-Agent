from pydantic import BaseModel, Field

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

class HourlyWeatherUnit(BaseModel):
    time_unit: str
    temperature_unit: str
    relative_humidity_unit: str
    rain_unit: str
    visibility_unit: str
    wind_speed_unit: str
    wind_direction_unit: str
    precipitation_probability_unit: str
    showers_unit: str
    snowfall_unit: str
    cloud_cover_unit: str

class HourlyWeather(BaseModel):
    hourly_time: str
    order_hour: float
    temperature: float
    relative_humidity: float
    rain: float
    visibility: float
    wind_speed: float
    wind_direction: float
    precipitation_probability: float
    showers: float
    snowfall: float
    cloud_cover: float

class HourlyWeatherResponse(BaseModel):
    hourly_weather_unit :HourlyWeatherUnit
    hourly_weather: list[HourlyWeather]

class WeatherAlert(BaseModel):
    title: str
    event: str
    message_type: str
    urgency: str
    areas: str
    description: str
    severity: str
    instruction: str
    effective_time: str
    expiry_time: str