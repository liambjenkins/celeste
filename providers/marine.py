import requests
from datetime import datetime


def get_marine(
    latitude,
    longitude,
    requested_time
):

    url = "https://marine-api.open-meteo.com/v1/marine"


    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": [
            "wave_height",
            "wave_direction",
            "wave_period",
            "sea_surface_temperature",
            "ocean_current_velocity",
            "ocean_current_direction"
        ],
        "start_date": requested_time.strftime("%Y-%m-%d"),
        "end_date": requested_time.strftime("%Y-%m-%d"),
        "timezone": "UTC"
    }


    response = requests.get(
        url,
        params=params
    )


    marine = response.json()


    times = marine["hourly"]["time"]


    closest_index = min(
        range(len(times)),
        key=lambda i: abs(
            datetime.fromisoformat(times[i]) - requested_time
        )
    )


    observed_time = datetime.fromisoformat(
        times[closest_index]
    )


    uncertainty_minutes = abs(
        int(
            (observed_time - requested_time).total_seconds()
            / 60
        )
    )


    def extract(variable):

        value = marine["hourly"][variable][closest_index]

        return {
            "value": value,
            "available": value is not None
        }


    return {

        "source": "Open-Meteo Marine",

        "location": {
            "latitude": marine.get("latitude"),
            "longitude": marine.get("longitude")
        },

        "requested_time": requested_time.isoformat(),

        "observed_time": observed_time.isoformat(),

        "uncertainty_minutes": uncertainty_minutes,


        "observations": {

            "wave_height_m": extract(
                "wave_height"
            ),

            "wave_direction_deg": extract(
                "wave_direction"
            ),

            "wave_period_seconds": extract(
                "wave_period"
            ),

            "sea_surface_temperature_c": extract(
                "sea_surface_temperature"
            ),

            "ocean_current_velocity_kmh": extract(
                "ocean_current_velocity"
            ),

            "ocean_current_direction_deg": extract(
                "ocean_current_direction"
            )

        }

    }