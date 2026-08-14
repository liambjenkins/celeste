"""
Tertiary progressions: a faster symbolic timing technique than
secondary progressions, giving month-by-month resolution rather than
year-by-year. Introduced by Garth Allen; verified via search during
curation, including the distinction from the less common "Tertiary
II" variant (which isn't implemented here).

One civil day after birth equates to one SIDEREAL month (~27.32166
days, the time the Moon takes to orbit the Earth relative to the
stars) of life — the "T I" convention, the one usually meant by
"tertiary progressions" without further qualification. This is
distinct from secondary progressions' day-for-a-year and from the
less common "T II" variant (one synodic month = one year), which
isn't implemented here.

Same aspect-finding mechanism as secondary progressions
(astrology/progressions.py) and transits, with the same very tight
1-degree orbs (tertiary aspects move faster than secondary ones but
are still a slow, symbolic technique compared to transits).
"""

from datetime import datetime, timezone

import swisseph as swe

from astrology.aspects import aspect_strength, find_aspect
from astrology.normaliser import longitude_in_house, longitude_to_zodiac
from providers.astronomy import get_astronomy

SIDEREAL_MONTH_DAYS = 27.32166

TERTIARY_ORBS = {
    "conjunction": 1.0,
    "sextile": 1.0,
    "square": 1.0,
    "trine": 1.0,
    "quincunx": 1.0,
    "opposition": 1.0,
}

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


def build_tertiary_progressions(
    natal_chart: dict,
    birth_utc_time: datetime,
    as_of_utc_time: datetime,
    orbs: dict = None,
) -> dict:
    """
    Compute the tertiary-progressed chart for as_of_utc_time (one day
    per sidereal month after birth_utc_time) and its aspects to
    natal_chart's bodies.
    """

    if orbs is None:
        orbs = TERTIARY_ORBS

    elapsed_days = (as_of_utc_time - birth_utc_time).total_seconds() / 86400.0
    elapsed_months = elapsed_days / SIDEREAL_MONTH_DAYS

    progressed_julian_day = natal_chart["julian_day"] + elapsed_months
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
        "elapsed_months": elapsed_months,
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
    tertiary = build_tertiary_progressions(natal, utc_aware, as_of)

    print(f"Elapsed sidereal months: {tertiary['elapsed_months']:.2f}")
    print(f"Progressed moment: {tertiary['progressed_utc_time']}")
    for name, body in tertiary["bodies"].items():
        retro = " (R)" if body["retrograde"] else ""
        print(
            f"  {name:10s} {body['sign']:12s} {body['degree']:2d}°{body['minute']:02d}'{retro} "
            f"| natal house {body['natal_house']}"
        )

    print()
    print(f"{len(tertiary['aspects'])} tertiary aspects:")
    for item in sorted(tertiary["aspects"], key=lambda a: a["orb"]):
        print(
            f"  tertiary {item['progressed_body']:8s} {item['aspect']:12s} "
            f"natal {item['natal_body']:8s} orb={item['orb']:.2f}° ({item['orb_strength']})"
        )
