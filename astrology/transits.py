"""
Transits: current planetary positions evaluated at a specific moment
("--as-of") and compared against a natal chart.

Reuses the same aspect-finding arithmetic as natal aspects
(astrology/aspects.py's find_aspect) but pairs a transiting body's
longitude against each NATAL body's longitude, rather than natal
bodies against each other — with tighter, transit-specific orbs
(traditional convention: a transiting aspect is only read as active
close to exact, unlike a natal aspect which stays meaningful across a
wider orb for the whole of a life).

A transiting body is also placed within the natal house wheel (the
classic "transiting Saturn is moving through your 10th house"
reading) — the natal cusps stay fixed; only the transiting body's
longitude changes.

Pure arithmetic plus one fresh ephemeris call (providers/astronomy.py)
for the as-of moment. No interpretation.
"""

from datetime import datetime

from astrology.aspects import aspect_strength, find_aspect
from astrology.normaliser import longitude_in_house, longitude_to_zodiac
from providers.astronomy import get_astronomy

TRANSIT_ORBS = {
    "conjunction": 2.0,
    "sextile": 2.0,
    "square": 2.0,
    "trine": 2.0,
    "quincunx": 1.0,
    "opposition": 2.0,
    # semisextile matches quincunx (1.0) -- its traditional aspect-
    # family counterpart (both "no major relationship" aspects, 30/150
    # degrees). semisquare/sesquiquadrate match MINOR_ORBS (2.0).
    "semisextile": 1.0,
    "semisquare": 2.0,
    "sesquiquadrate": 2.0,
}

# Fast personal-planet transits (Mercury/Venus/Mars) are traditionally
# read alongside the slower social/outer planets; the Sun and Moon
# are included too (solar-return-style Sun contacts, lunar transits).
TRANSIT_BODIES = (
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
    "uranus", "neptune", "pluto",
)

NATAL_TARGETS = TRANSIT_BODIES


def build_transits(
    natal_chart: dict,
    as_of_utc_time: datetime,
    orbs: dict = None,
) -> dict:
    """
    Compute transiting positions at as_of_utc_time and their aspects
    to natal_chart's bodies, plus each transiting body's placement in
    the natal house wheel.
    """

    if orbs is None:
        orbs = TRANSIT_ORBS

    astronomy = get_astronomy(as_of_utc_time)
    natal_cusps = natal_chart["houses"]["cusps"]
    natal_bodies = natal_chart["bodies"]

    transiting_bodies = {}
    aspects = []

    for name in TRANSIT_BODIES:
        data = astronomy["bodies"].get(name)

        if data is None:
            continue

        longitude = data["longitude"]
        zodiac = longitude_to_zodiac(longitude)

        transiting_bodies[name] = {
            "longitude": longitude,
            "sign": zodiac["sign"],
            "sign_index": zodiac["sign_index"],
            "degree": zodiac["degree"],
            "minute": zodiac["minute"],
            "second": zodiac["second"],
            "retrograde": data["longitude_speed"] < 0,
            "natal_house": longitude_in_house(longitude, natal_cusps),
        }

        for natal_name in NATAL_TARGETS:
            natal_body = natal_bodies.get(natal_name)

            if natal_body is None:
                continue

            result = find_aspect(longitude, natal_body["longitude"], orbs)

            if result is None:
                continue

            aspects.append(
                {
                    "transiting_body": name,
                    "natal_body": natal_name,
                    "aspect": result["aspect"],
                    "angle": result["angle"],
                    "orb": result["orb"],
                    "orb_strength": aspect_strength(
                        result["orb"], orbs[result["aspect"]]
                    ),
                }
            )

    return {
        "as_of_utc_time": astronomy["utc_time"],
        "julian_day": astronomy["julian_day"],
        "bodies": transiting_bodies,
        "aspects": aspects,
    }


if __name__ == "__main__":
    from datetime import timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    natal = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")

    as_of = datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)
    transits = build_transits(natal, as_of)

    print(f"As of: {transits['as_of_utc_time']}")
    for name, body in transits["bodies"].items():
        retro = " (R)" if body["retrograde"] else ""
        print(
            f"  {name:10s} {body['sign']:12s} {body['degree']:2d}°{body['minute']:02d}'{retro} "
            f"| natal house {body['natal_house']}"
        )

    print()
    print(f"{len(transits['aspects'])} transit aspects:")
    for item in sorted(transits["aspects"], key=lambda a: a["orb"]):
        print(
            f"  transiting {item['transiting_body']:8s} {item['aspect']:12s} "
            f"natal {item['natal_body']:8s} orb={item['orb']:.2f}° ({item['orb_strength']})"
        )
