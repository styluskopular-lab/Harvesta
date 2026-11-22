from fastapi import APIRouter, Query
import httpx

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("/forecast")
def weather_forecast(
    latitude: float = Query(0.3476, description="Uganda latitude"),
    longitude: float = Query(32.5825, description="Uganda longitude"),
):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "Africa/Kampala",
        "forecast_days": 7,
    }
    try:
        response = httpx.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "location": {"latitude": latitude, "longitude": longitude},
            "timezone": data.get("timezone"),
            "current": data.get("current"),
            "daily": data.get("daily"),
        }
    except httpx.HTTPError:
        return {
            "location": {"latitude": latitude, "longitude": longitude},
            "timezone": "Africa/Kampala",
            "current": {
                "temperature_2m": None,
                "relative_humidity_2m": None,
                "precipitation": None,
                "weather_code": None,
            },
            "daily": None,
            "warning": "Live forecast is temporarily unavailable.",
        }
