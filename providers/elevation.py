import requests


def get_elevation(
    latitude,
    longitude
):

    url = "https://api.open-elevation.com/api/v1/lookup"


    params = {

        "locations": f"{latitude},{longitude}"

    }


    response = requests.get(
        url,
        params=params
    )


    data = response.json()


    if "results" not in data:

        return {

            "source": "Open-Elevation",

            "available": False,

            "reason": "No elevation data"

        }


    elevation = data["results"][0]["elevation"]


    return {

        "source": "Open-Elevation",

        "available": True,

        "location": {

            "latitude": latitude,

            "longitude": longitude

        },

        "elevation_m": elevation

    }