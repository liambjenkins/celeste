"""
Secondary progressions: the classical "a day for a year" symbolic
timing technique — the chart recomputed at (natal Julian day +
elapsed years since birth) is read as the "progressed chart" for that
age. One day of actual planetary motion after birth is taken to
symbolize one year of life.

Source: Bernadette Brady, Predictive Astrology: The Eagle and the
Lark (1992) — a standard modern reference on predictive technique,
covering transits and progressions together with explicit orb and
interpretation guidance (verified via web search during curation).

Progressed positions are compared to the natal chart with the same
aspect-finding arithmetic as transits (astrology/aspects.py's
find_aspect), using very tight progression-specific orbs: progressed
aspects move at most about one degree a year (for the fastest-moving
progressed body, the Moon), so even a one-degree orb represents a
real multi-year window, not a fleeting moment. Progressed outer
planets (Uranus onward) move negligibly over a human lifespan and are
conventionally excluded — only personal/social planets are
progressed here.

The progressed Moon, moving roughly one degree a day (=one zodiac
sign every ~2.5 years), is the technique's classical focus and the
only progressed body commonly read by sign on its own.
"""

from datetime import datetime, timezone

import swisseph as swe

from astrology.aspects import aspect_strength, find_aspect
from astrology.normaliser import longitude_in_house, longitude_to_zodiac
from providers.astronomy import get_astronomy

PROGRESSION_ORBS = {
    "conjunction": 1.0,
    "sextile": 1.0,
    "square": 1.0,
    "trine": 1.0,
    "quincunx": 1.0,
    "opposition": 1.0,
}

# Traditional scope: only personal/social planets are progressed.
PROGRESSED_BODIES = ("sun", "moon", "mercury", "venus", "mars")

NATAL_TARGETS = (
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
    "uranus", "neptune", "pluto",
)


def _julian_day_to_utc(julian_day: float) -> datetime:
    year, month, day, hour = swe.revjul(julian_day)
    whole_hour = int(hour)
    minute_float = (hour - whole_hour) * 60
    minute = int(minute_float)
    second = round((minute_float - minute) * 60)

    if second == 60:
        second = 0
        minute += 1
    if minute == 60:
        minute = 0
        whole_hour += 1

    return datetime(
        year, month, day, whole_hour, minute, second, tzinfo=timezone.utc
    )


def build_secondary_progressions(
    natal_chart: dict,
    birth_utc_time: datetime,
    as_of_utc_time: datetime,
    orbs: dict = None,
) -> dict:
    """
    Compute the progressed chart for as_of_utc_time (a "day for a
    year" after birth_utc_time) and its aspects to natal_chart's
    bodies, plus each progressed body's placement in the natal house
    wheel.
    """

    if orbs is None:
        orbs = PROGRESSION_ORBS

    elapsed_years = (
        (as_of_utc_time - birth_utc_time).total_seconds() / 86400.0
    ) / 365.25

    progressed_julian_day = natal_chart["julian_day"] + elapsed_years
    progressed_utc_time = _julian_day_to_utc(progressed_julian_day)

    astronomy = get_astronomy(progressed_utc_time)
    natal_cusps = natal_chart["houses"]["cusps"]
    natal_bodies = natal_chart["bodies"]

    progressed_bodies = {}
    aspects = []

    for name in PROGRESSED_BODIES:
        data = astronomy["bodies"].get(name)

        if data is None:
            continue

        longitude = data["longitude"]
        zodiac = longitude_to_zodiac(longitude)

        progressed_bodies[name] = {
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
                    "progressed_body": name,
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
        "elapsed_years": elapsed_years,
        "progressed_julian_day": progressed_julian_day,
        "progressed_utc_time": progressed_utc_time.isoformat(),
        "bodies": progressed_bodies,
        "aspects": aspects,
    }


if __name__ == "__main__":
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
    progressions = build_secondary_progressions(natal, utc_aware, as_of)

    print(f"Elapsed years: {progressions['elapsed_years']:.2f}")
    print(f"Progressed moment: {progressions['progressed_utc_time']}")
    for name, body in progressions["bodies"].items():
        retro = " (R)" if body["retrograde"] else ""
        print(
            f"  {name:10s} {body['sign']:12s} {body['degree']:2d}°{body['minute']:02d}'{retro} "
            f"| natal house {body['natal_house']}"
        )

    print()
    print(f"{len(progressions['aspects'])} progressed aspects:")
    for item in sorted(progressions["aspects"], key=lambda a: a["orb"]):
        print(
            f"  progressed {item['progressed_body']:8s} {item['aspect']:12s} "
            f"natal {item['natal_body']:8s} orb={item['orb']:.2f}° ({item['orb_strength']})"
        )
