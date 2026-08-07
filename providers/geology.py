import requests


def get_geology(
    latitude,
    longitude
):

    url = (
        "https://services.ga.gov.au/"
        "gis/rest/services/"
        "Australian_Geological_Provinces/"
        "MapServer/identify"
    )


    params = {

        "geometry": f"{longitude},{latitude}",

        "geometryType": "esriGeometryPoint",

        "sr": 4326,

        "layers": "all",

        "tolerance": 10,

        "mapExtent": f"{longitude-0.1},{latitude-0.1},{longitude+0.1},{latitude+0.1}",

        "imageDisplay": "400,400,96",

        "returnGeometry": "false",

        "f": "json"

    }


    response = requests.get(
        url,
        params=params
    )


    data = response.json()


    results = data.get(
        "results",
        []
    )


    if results:

        return {

            "source": "Geoscience Australia",

            "available": True,

            "location": {
                "latitude": latitude,
                "longitude": longitude
            },

            "province": results[0]["attributes"]

        }


    return {

        "source": "Geoscience Australia",

        "available": False,

        "location": {
            "latitude": latitude,
            "longitude": longitude
        },

        "reason": "No mapped geological province available"

    }