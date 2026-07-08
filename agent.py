from google.adk.agents.llm_agent import Agent

import os
import requests
from dotenv import load_dotenv
from google.adk.agents import Agent
from callbacks import log_before_model, validate_input, log_after_model

load_dotenv()


def get_current_location() -> dict:
    """
    Detects the user's current location using IP-based geolocation
    via the Google Geolocation API.

    Returns:
        dict: A dictionary with 'status', 'lat', and 'lon' keys.
    """
    google_key = os.getenv("GOOGLE_GEO_API_KEY")
    geo_url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={google_key}"

    try:
        response = requests.post(geo_url, json={})
        response.raise_for_status()
        data = response.json()
        return {
            "status": "success",
            "lat": data["location"]["lat"],
            "lon": data["location"]["lng"],
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def get_weather(lat: float, lon: float) -> dict:
    """
    Fetches current weather conditions from the National Weather Service
    for a given latitude and longitude.

    Args:
        lat: Latitude of the location.
        lon: Longitude of the location.

    Returns:
        dict: A dictionary with 'status' and weather details (name,
        temperature, unit, forecast) or an error message.
    """
    headers = {"User-Agent": "weather-app (your_email@example.com)"}

    try:
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        points_resp = requests.get(points_url, headers=headers)
        points_resp.raise_for_status()
        forecast_url = points_resp.json()["properties"]["forecast"]

        forecast_resp = requests.get(forecast_url, headers=headers)
        forecast_resp.raise_for_status()
        current = forecast_resp.json()["properties"]["periods"][0]

        return {
            "status": "success",
            "name": current["name"],
            "temperature": current["temperature"],
            "unit": current["temperatureUnit"],
            "forecast": current["shortForecast"],
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def get_coordinates_for_city(city: str) -> dict:
    """
    Looks up the latitude and longitude for a given city name using
    the Google Geocoding API.

    Args:
        city: Name of the city, e.g. "Kansas City" or "Denver, CO".

    Returns:
        dict: A dictionary with 'status', 'lat', 'lon', and 'resolved_name'
        (the formatted address Google matched), or an error message if
        the city wasn't found.
    """
    google_key = os.getenv("GOOGLE_GEO_API_KEY")

    try:
        geo_url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": city, "key": google_key}
        response = requests.get(geo_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK" or not data.get("results"):
            return {
                "status": "error",
                "error_message": f"No location found for '{city}' (Google status: {data.get('status')})",
            }

        result = data["results"][0]
        location = result["geometry"]["location"]
        return {
            "status": "success",
            "lat": location["lat"],
            "lon": location["lng"],
            "resolved_name": result["formatted_address"],
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


root_agent = Agent(
    name="weather_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You help users find the current weather for a city they specify. "
        "If the user gives a city name, call get_coordinates_for_city to find "
        "its latitude/longitude, then call get_weather with those coordinates. "
        "If the user doesn't specify a city and asks for weather at their current "
        "location, call get_current_location instead. "
        "Present the result in a friendly, natural sentence, including the "
        "resolved city name if you looked it up."
    ),
    tools=[get_current_location, get_coordinates_for_city, get_weather],
    before_model_callback=[log_before_model, validate_input],
    after_model_callback=log_after_model,
)
