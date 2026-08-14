from datetime import datetime

from astrology.antiscia import build_antiscia
from astrology.arabic_parts import build_arabic_parts
from astrology.aspect_patterns import find_aspect_patterns
from astrology.declination import find_declination_aspects, get_declinations
from astrology.harmonics import build_harmonic_charts
from astrology.houses import calculate_houses
from astrology.rulership import build_rulership
from astrology.aspects import calculate_aspects
from astrology.elemental_balance import chart_elemental_balance
from astrology.normaliser import normalise_body
from astrology.stars import find_star_conjunctions, get_star_positions
from providers.astronomy import BODIES, get_astronomy


def build_chart(
    utc_time: datetime,
    latitude: float,
    longitude: float,
    house_system: str = "placidus",
    include_minor_aspects: bool = False,
    include_declinations: bool = False,
    include_antiscia: bool = False,
    include_harmonics: bool = False,
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

    aspects = calculate_aspects(bodies, include_minor=include_minor_aspects)
    elemental_balance = chart_elemental_balance(bodies)

    star_positions = get_star_positions(astronomy["julian_day"])

    stars = {}

    for name, data in star_positions.items():
        normalised_star = normalise_body(name, data, houses["cusps"])
        normalised_star["magnitude"] = data.get("magnitude")
        stars[name] = normalised_star

    # Conjunctions are found against the raw (pre-normalisation)
    # positions, which is where magnitude lives.
    star_conjunctions = find_star_conjunctions(bodies, star_positions)

    arabic_parts = build_arabic_parts({"houses": houses, "bodies": bodies})

    vertex_longitude = houses["angles"]["vertex"]
    vertex = normalise_body("vertex", {"longitude": vertex_longitude}, houses["cusps"])
    anti_vertex = normalise_body(
        "anti_vertex", {"longitude": (vertex_longitude + 180.0) % 360.0}, houses["cusps"]
    )

    declination_aspects = []

    if include_declinations:
        declinations = get_declinations(astronomy["julian_day"], BODIES)
        declination_aspects = find_declination_aspects(declinations)

    antiscia = {}

    if include_antiscia:
        antiscia = build_antiscia({"houses": houses, "bodies": bodies})

    rulership = build_rulership({"houses": houses, "bodies": bodies})

    aspect_patterns = find_aspect_patterns({"aspects": aspects, "bodies": bodies})

    harmonic_charts = {}

    if include_harmonics:
        harmonic_charts = build_harmonic_charts({"houses": houses, "bodies": bodies})

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
        "elemental_balance": elemental_balance,
        "stars": stars,
        "star_conjunctions": star_conjunctions,
        "arabic_parts": arabic_parts,
        "vertex": vertex,
        "anti_vertex": anti_vertex,
        "declination_aspects": declination_aspects,
        "antiscia": antiscia,
        "rulership": rulership,
        "aspect_patterns": aspect_patterns,
        "harmonic_charts": harmonic_charts,
    }
