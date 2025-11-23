"""Weather Tool - Fetch weather information using OpenWeatherMap API"""

from typing import Any, Dict

from pyowm import OWM
from pyowm.utils.config import get_default_config

from src.utils.logger import get_logger

logger = get_logger(__name__)


class WeatherTool:
    """Fetch weather information from OpenWeatherMap"""

    def __init__(
        self,
        api_key: str,
        units: str = "metric",
        language: str = "zh_cn",
    ):
        """
        Initialize Weather Tool

        Args:
            api_key: OpenWeatherMap API key
            units: Temperature units (metric/imperial/kelvin)
            language: Language code (zh_cn, en, etc.)
        """
        if not api_key:
            raise ValueError("OpenWeatherMap API key is required")

        self.api_key = api_key
        self.units = units
        self.language = language

        # Configure OWM
        config_dict = get_default_config()
        config_dict["language"] = language

        try:
            self.owm = OWM(api_key, config_dict)
            self.mgr = self.owm.weather_manager()
            logger.info(f"WeatherTool initialized (units: {units}, lang: {language})")
        except Exception as e:
            logger.error(f"Failed to initialize WeatherTool: {e}")
            raise

    async def get_current_weather(
        self, location: str
    ) -> Dict[str, Any]:
        """
        Get current weather for a location

        Args:
            location: City name or "City, Country Code"

        Returns:
            Dict with weather information
        """
        try:
            observation = self.mgr.weather_at_place(location)
            weather = observation.weather

            # Get temperature in specified units
            # Convert metric/imperial to celsius/fahrenheit for PyOWM
            temp_unit = 'celsius' if self.units == 'metric' else 'fahrenheit' if self.units == 'imperial' else 'kelvin'
            temp_dict = weather.temperature(temp_unit)

            result = {
                "location": location,
                "status": weather.detailed_status,
                "temperature": temp_dict["temp"],
                "feels_like": temp_dict.get("feels_like"),
                "temp_min": temp_dict.get("temp_min"),
                "temp_max": temp_dict.get("temp_max"),
                "humidity": weather.humidity,
                "pressure": weather.pressure.get("press"),
                "wind_speed": weather.wind().get("speed"),
                "wind_deg": weather.wind().get("deg"),
                "clouds": weather.clouds,
                "rain": weather.rain,
                "snow": weather.snow,
                "visibility": weather.visibility_distance,
                "sunrise": weather.sunrise_time(timeformat="iso"),
                "sunset": weather.sunset_time(timeformat="iso"),
                "units": self.units,
            }

            logger.info(f"Weather for {location}: {result['status']}, {result['temperature']}°")
            return result

        except Exception as e:
            logger.error(f"Error fetching weather for {location}: {e}")
            return {
                "location": location,
                "error": str(e),
                "status": "Error fetching weather data",
            }

    async def get_forecast(
        self,
        location: str,
        days: int = 5,
    ) -> Dict[str, Any]:
        """
        Get weather forecast for a location

        Args:
            location: City name or "City, Country Code"
            days: Number of days (1-5 for free tier)

        Returns:
            Dict with forecast information
        """
        try:
            # Get 3-hour forecast
            forecaster = self.mgr.forecast_at_place(location, "3h")
            forecast = forecaster.forecast

            # Extract daily forecasts
            daily_forecasts = []
            processed_dates = set()

            for weather in forecast.weathers[:days * 8]:  # 8 intervals per day
                date_str = weather.reference_time("iso").split("T")[0]

                if date_str not in processed_dates:
                    temp_unit = 'celsius' if self.units == 'metric' else 'fahrenheit' if self.units == 'imperial' else 'kelvin'
                    temp = weather.temperature(temp_unit)

                    daily_forecasts.append({
                        "date": date_str,
                        "status": weather.detailed_status,
                        "temp": temp["temp"],
                        "temp_min": temp.get("temp_min"),
                        "temp_max": temp.get("temp_max"),
                        "humidity": weather.humidity,
                        "wind_speed": weather.wind().get("speed"),
                        "clouds": weather.clouds,
                    })

                    processed_dates.add(date_str)

                if len(daily_forecasts) >= days:
                    break

            result = {
                "location": location,
                "forecast_days": len(daily_forecasts),
                "forecasts": daily_forecasts[:days],
                "units": self.units,
            }

            logger.info(f"Forecast for {location}: {len(daily_forecasts)} days")
            return result

        except Exception as e:
            logger.error(f"Error fetching forecast for {location}: {e}")
            return {
                "location": location,
                "error": str(e),
                "forecasts": [],
            }

    async def search_city(self, city_name: str, limit: int = 5) -> list:
        """
        Search for cities by name

        Args:
            city_name: City name to search
            limit: Maximum number of results

        Returns:
            List of matching cities
        """
        try:
            registry = self.owm.city_id_registry()
            cities = registry.locations_for(city_name, matching="like")

            results = []
            for city in cities[:limit]:
                results.append({
                    "name": city.name,
                    "country": city.country,
                    "lat": city.lat,
                    "lon": city.lon,
                    "id": city.id,
                })

            logger.info(f"Found {len(results)} cities matching '{city_name}'")
            return results

        except Exception as e:
            logger.error(f"Error searching for city {city_name}: {e}")
            return []

    def format_weather_summary(self, weather_data: Dict[str, Any]) -> str:
        """
        Format weather data into human-readable summary

        Args:
            weather_data: Weather data from get_current_weather

        Returns:
            Formatted summary string
        """
        if "error" in weather_data:
            return f"无法获取 {weather_data['location']} 的天气信息: {weather_data['error']}"

        temp_unit = "°C" if self.units == "metric" else "°F" if self.units == "imperial" else "K"

        summary = f"""📍 {weather_data['location']}

🌡️ 温度: {weather_data['temperature']}{temp_unit}
   体感: {weather_data.get('feels_like', 'N/A')}{temp_unit}
   最低: {weather_data.get('temp_min', 'N/A')}{temp_unit}
   最高: {weather_data.get('temp_max', 'N/A')}{temp_unit}

🌤️ 天气: {weather_data['status']}
💧 湿度: {weather_data['humidity']}%
🌬️ 风速: {weather_data['wind_speed']} m/s
☁️ 云量: {weather_data['clouds']}%"""

        if weather_data.get('rain'):
            summary += f"\n🌧️ 降雨: {weather_data['rain']}"

        if weather_data.get('snow'):
            summary += f"\n❄️ 降雪: {weather_data['snow']}"

        return summary
