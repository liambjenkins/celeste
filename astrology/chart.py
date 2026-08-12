from datetime import datetime

from astrology.houses import calculate_houses
from astrology.aspects import calculate_aspects
from astrology.normaliser import normalise_body
from providers.astronomy import get_astronomy


def build_chart(
    utc_time: datetime,
    latitude: float,
    longitude: float,
    house_system: str = "placidus",
):
    astronomy = get_astronomy(utc_time)

    houses = calculate_houses(
        astronomy["julian_day"],
        latitude,
        longitude,
        house_system,
    )

    bodies = {}

    for name, data in astronomy["bodies"].items():

        # Derived nodes don't contain a speed or full
        # astronomical record, but they still have a longitude.
        bodies[name] = normalise_body(
            name,
            data,
            houses["cusps"],
        )

    aspects = calculate_aspects(bodies)

    return {
        "utc_time": astronomy["utc_time"],
        "julian_day": astronomy["julian_day"],
        "location": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "house_system": house_system,
        "houses": houses,
        "bodies": bodies,
        "aspects": aspects,
    }
