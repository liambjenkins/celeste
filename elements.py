def classify_observations(observations):
    return {
        "fire": {
            "solar_activity":
                observations.get(
                    "space_weather"
                ),
            "thermal":
                observations.get(
                    "atmosphere"
                )
        },
        "water": {
            "tides":
                observations.get(
                    "tides"
                ),
            "hydrology":
                observations.get(
                    "hydrology"
                ),
            "marine":
                observations.get(
                    "marine"
                )
        },
        "earth": {
            "geology":
                observations.get(
                    "earth",
                    {}
                ).get(
                    "geology"
                ),
            "earthquakes":
                observations.get(
                    "earth",
                    {}
                ).get(
                    "earthquakes"
                ),
            "elevation":
                observations.get(
                    "earth",
                    {}
                ).get(
                    "elevation"
                ),
            "land":
                observations.get(
                    "land"
                ),
            "biosphere":
                observations.get(
                    "biosphere"
                )
        },
        "air": {
            "atmosphere":
                observations.get(
                    "atmosphere"
                )
        },
        "space": {
            "astronomy":
                observations.get(
                    "astronomy"
                ),
            "space_weather":
                observations.get(
                    "space_weather"
                )
        }
    }