import requests
from datetime import datetime


def get_atmosphere(
    latitude,
    longitude,
    requested_time
):

    url = "https://archive-api.open-meteo.com/v1/archive"


    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "pressure_msl",
            "precipitation",
            "cloud_cover"
        ],
        "start_date": requested_time.strftime("%Y-%m-%d"),
        "end_date": requested_time.strftime("%Y-%m-%d"),
        "timezone": "Australia/Melbourne"
    }


    response = requests.get(
        url,
        params=params
    )


    weather = response.json()


    times = weather["hourly"]["time"]


    closest_index = min(
        range(len(times)),
        key=lambda i: abs(
            datetime.fromisoformat(times[i]) - requested_time
        )
    )


    observed_time = datetime.fromisoformat(
        times[closest_index]
    )


    difference_minutes = abs(
        int(
            (observed_time - requested_time).total_seconds()
            / 60
        )
    )


    return {

        "source": "Open-Meteo Archive",

        "requested_time": requested_time.isoformat(),

        "observed_time": observed_time.isoformat(),

        "uncertainty_minutes": difference_minutes,

        "temperature_c": weather["hourly"]["temperature_2m"][closest_index],

        "humidity_percent": weather["hourly"]["relative_humidity_2m"][closest_index],

        "pressure_hpa": weather["hourly"]["pressure_msl"][closest_index],

        "precipitation_mm": weather["hourly"]["precipitation"][closest_index],

        "cloud_cover_percent": weather["hourly"]["cloud_cover"][closest_index]

    }