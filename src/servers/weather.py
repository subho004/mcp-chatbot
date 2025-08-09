from mcp.server.fastmcp import FastMCP

import os
import requests
from dotenv import load_dotenv
load_dotenv()

mcp = FastMCP("Weather")

@mcp.tool()
async def get_weather(location: str) -> str:
    """Get current weather for a location using WeatherAPI.com."""
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return "Error: WEATHER_API_KEY is not set. Set it in your environment or .env file."
    url = "http://api.weatherapi.com/v1/current.json"
    params = {"key": api_key, "q": location, "aqi": "no"}
    try:
        resp = requests.get(url, params=params, timeout=8)
        data = resp.json()
        if resp.status_code != 200 or "error" in data:
            return f"Error: {data.get('error', {}).get('message', 'Unable to fetch weather')}"
        loc = data.get("location", {})
        curr = data.get("current", {})
        name = f"{loc.get('name')}, {loc.get('region')}, {loc.get('country')}"
        condition = curr.get("condition", {}).get("text", "Unknown")
        temp_c = curr.get("temp_c")
        feelslike_c = curr.get("feelslike_c")
        humidity = curr.get("humidity")
        wind_kph = curr.get("wind_kph")
        wind_dir = curr.get("wind_dir")
        return (
            f"Weather in {name}:\n"
            f"Condition: {condition}\n"
            f"Temperature: {temp_c}°C (feels like {feelslike_c}°C)\n"
            f"Humidity: {humidity}%\n"
            f"Wind: {wind_kph} km/h {wind_dir}"
        )
    except Exception as e:
        return f"Error fetching weather: {e}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")