"""
Antiscia and contra-antiscia: mirror points across two symmetry axes
of the zodiac, first elaborated in detail by Firmicus Maternus
(4th century CE, Matheseos Libri VIII).

Antiscion mirrors a longitude across the solstice axis (0 deg Cancer
/ 0 deg Capricorn) — signs equidistant from the solstices pair up
(Gemini/Leo, Taurus/Virgo, Aries/Libra, ...), read as a hidden
harmony or blending between the placement and its mirror.

Contra-antiscion mirrors across the equinox axis (0 deg Aries / 0 deg
Libra) — the exact opposite point of the antiscion — read as a
hidden tension needing integration.

Formulas verified via search and hand-checked against sign-pair
logic during curation: antiscion(L) = (180 - L) % 360 (Aries 0 -> 180
= Libra 0, Gemini 0 (60) -> 120 = Leo 0, Cancer 0 (90) -> 90 = itself,
correct self-mirror at the solstice point); contra-antiscion(L) =
(360 - L) % 360, the antiscion's exact opposite.

Pure arithmetic on longitudes an already-computed chart supplies — no
new ephemeris calls.
"""

from astrology.normaliser import longitude_in_house, longitude_to_zodiac


def antiscion_longitude(longitude: float) -> float:
    return (180.0 - longitude) % 360.0


def contra_antiscion_longitude(longitude: float) -> float:
    return (360.0 - longitude) % 360.0


def _point(longitude: float, cusps: dict) -> dict:
    zodiac = longitude_to_zodiac(longitude)
    return {
        "longitude": longitude,
        "sign": zodiac["sign"],
        "sign_index": zodiac["sign_index"],
        "degree": zodiac["degree"],
        "minute": zodiac["minute"],
        "second": zodiac["second"],
        "house": longitude_in_house(longitude, cusps),
    }


def build_antiscia(tropical_chart: dict, bodies_to_mirror: tuple = ("sun", "moon")) -> dict:
    """
    Antiscion and contra-antiscion points for a curated set of bodies
    (defaults to Sun and Moon, the most commonly read antiscia
    points) from an already-built tropical chart.
    """

    cusps = tropical_chart["houses"]["cusps"]
    bodies = tropical_chart["bodies"]

    result = {}

    for name in bodies_to_mirror:
        body = bodies.get(name)

        if body is None:
            continue

        longitude = body["longitude"]
        result[name] = {
            "antiscion": _point(antiscion_longitude(longitude), cusps),
            "contra_antiscion": _point(contra_antiscion_longitude(longitude), cusps),
        }

    return result


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc

    # Hand-check: Aries 0 -> antiscion Libra 0; Gemini 0 -> Leo 0.
    assert round(antiscion_longitude(0.0), 6) == 180.0
    assert round(antiscion_longitude(60.0), 6) == 120.0
    assert round(antiscion_longitude(90.0), 6) == 90.0  # solstice self-mirror
    print("Worked-example checks passed.")
    print()

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")
    antiscia = build_antiscia(tropical)

    for name, points in antiscia.items():
        anti = points["antiscion"]
        contra = points["contra_antiscion"]
        print(
            f"{name:8s} antiscion {anti['sign']:12s} {anti['degree']}°{anti['minute']}' "
            f"house {anti['house']} | contra-antiscion {contra['sign']:12s} "
            f"{contra['degree']}°{contra['minute']}' house {contra['house']}"
        )
