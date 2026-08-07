import requests
from datetime import datetime


def get_hydrology(
    latitude,
    longitude,
    requested_time
):

    url = "https://archive-api.open-meteo.com/v1/archive"


    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": [
            "precipitation",
            "et0_fao_evapotranspiration",
            "soil_moisture_0_to_7cm"
        ],
        "start_date": requested_time.strftime("%Y-%m-%d"),
        "end_date": requested_time.strftime("%Y-%m-%d"),
        "timezone": "Australia/Melbourne"
    }


    response = requests.get(
        url,
        params=params
    )


    hydrology = response.json()


    times = hydrology["hourly"]["time"]


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

        value = hydrology["hourly"][variable][closest_index]

        return {
            "value": value,
            "available": value is not None
        }


    return {

        "source": "Open-Meteo Archive",

        "requested_time": requested_time.isoformat(),

        "observed_time": observed_time.isoformat(),

        "uncertainty_minutes": uncertainty_minutes,


        "observations": {

            "precipitation_mm": extract(
                "precipitation"
            ),

            "evapotranspiration_mm": extract(
                "et0_fao_evapotranspiration"
            ),

            "soil_moisture_0_7cm_m3m3": extract(
                "soil_moisture_0_to_7cm"
            )

        }

    }