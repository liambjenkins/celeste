import os
import requests

from datetime import datetime, timedelta
from dotenv import load_dotenv


load_dotenv()


def get_tides(
    latitude,
    longitude,
    requested_time
):

    api_key = os.getenv(
        "WORLDTIDES_API_KEY"
    )


    url = "https://www.worldtides.info/api/v3"


    start_date = (
        requested_time - timedelta(days=1)
    )

    end_date = (
        requested_time + timedelta(days=1)
    )


    params = {

        "extremes": "",

        "lat": latitude,

        "lon": longitude,

        "start": int(start_date.timestamp()),

        "end": int(end_date.timestamp()),

        "key": api_key

    }


    response = requests.get(
        url,
        params=params
    )


    tides = response.json()


    if "error" in tides:

        return {

            "source": "WorldTides",

            "available": False,

            "reason": tides["error"]

        }


    extremes = tides.get(
        "extremes",
        []
    )


    historical_extremes = []


    for tide in extremes:

        tide_time = datetime.fromtimestamp(
            tide["dt"]
        )


        if abs(
            tide_time - requested_time
        ) <= timedelta(days=1):

            historical_extremes.append(
                tide
            )


    if not historical_extremes:

        return {

            "source": "WorldTides",

            "available": False,

            "requested_time": requested_time.isoformat(),

            "reason": "No historical tide data available for requested period"

        }


    nearest = min(
        historical_extremes,

        key=lambda tide: abs(
            datetime.fromtimestamp(
                tide["dt"]
            ) - requested_time
        )
    )


    observed_time = datetime.fromtimestamp(
        nearest["dt"]
    )


    uncertainty_minutes = abs(
        int(
            (
                observed_time - requested_time
            ).total_seconds()
            / 60
        )
    )


    return {

        "source": "WorldTides",

        "available": True,

        "requested_time": requested_time.isoformat(),

        "observed_time": observed_time.isoformat(),

        "uncertainty_minutes": uncertainty_minutes,


        "location": {

            "latitude": latitude,

            "longitude": longitude

        },


        "observation": {

            "type": nearest["type"],

            "height_m": nearest["height"]

        }

    }