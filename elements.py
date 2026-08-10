def classify_observations(concepts):
    """
    Classify canonical concepts into elemental domains.

    This operates on the output of normalise_observations(),
    not on the raw provider data.
    """

    def get(name):
        return concepts.get(name)

    return {
        "fire": {
            "solar_activity": get("solar_activity"),
            "thermal": get("temperature"),
        },

        "water": {
            "tides": get("tide"),
            "hydrology": get("precipitation"),
            "marine": get("marine_conditions"),
        },

        "earth": {
            "geology": get("geology"),
            "earthquakes": get("earthquake"),
            "elevation": get("elevation"),
            "land": get("soil_moisture"),
            "biosphere": get("vegetation"),
            "soil_temperature": get("soil_temperature"),
        },

        "air": {
            "atmosphere": {
                "moisture": get("atmospheric_moisture"),
                "pressure": get("pressure"),
                "cloud": get("cloud"),
                "temperature": get("temperature"),
            },
        },

        "space": {
            "astronomy": get("astronomy"),
            "space_weather": get("solar_activity"),
        },
    }