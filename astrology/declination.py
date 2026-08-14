"""
Parallels and contraparallels: declination-based aspects, a
genuinely different mechanism from the longitude-based aspects in
astrology/aspects.py.

Declination is a body's angular distance north or south of the
celestial equator — a different coordinate axis from ecliptic
longitude entirely. A parallel (two bodies at the same declination,
same hemisphere) is traditionally read like a strong conjunction; a
contraparallel (same declination, opposite hemispheres) is
traditionally read like a weaker opposition. Orbs are conventionally
tight (~1 degree) since declination only spans about 47 degrees
total (rather than longitude's full 360), so even a small orb is
proportionally significant — verified via search during curation.
"""

import swisseph as swe

DECLINATION_ORB = 1.0


def get_declination(julian_day: float, body_code: int) -> float:
    """The body's declination (degrees, + north / - south) at a given moment."""

    result = swe.calc_ut(julian_day, body_code, swe.FLG_EQUATORIAL)[0]
    return result[1]  # (RA, Dec, distance, ...)


def get_declinations(julian_day: float, body_codes: dict) -> dict:
    """body_codes: {name: swisseph body constant} -> {name: declination}."""

    return {
        name: get_declination(julian_day, code)
        for name, code in body_codes.items()
    }


def find_declination_aspects(declinations: dict, orb: float = DECLINATION_ORB) -> list[dict]:
    """
    Pairwise parallel/contraparallel detection over a
    {name: declination} dict. Each pair evaluated once.
    """

    names = list(declinations.keys())
    aspects = []

    for index, name_a in enumerate(names):
        for name_b in names[index + 1:]:
            dec_a = declinations[name_a]
            dec_b = declinations[name_b]

            parallel_diff = abs(dec_a - dec_b)
            contraparallel_diff = abs(dec_a + dec_b)

            if parallel_diff <= orb:
                aspects.append(
                    {
                        "body_a": name_a,
                        "body_b": name_b,
                        "aspect": "parallel",
                        "orb": parallel_diff,
                    }
                )
            elif contraparallel_diff <= orb:
                aspects.append(
                    {
                        "body_a": name_a,
                        "body_b": name_b,
                        "aspect": "contraparallel",
                        "orb": contraparallel_diff,
                    }
                )

    return aspects


if __name__ == "__main__":
    from providers.astronomy import BODIES, datetime_to_julian_day
    from datetime import datetime, timezone
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    julian_day = datetime_to_julian_day(utc_aware)
    core_bodies = {
        name: code for name, code in BODIES.items()
        if name in ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn")
    }
    declinations = get_declinations(julian_day, core_bodies)

    for name, dec in declinations.items():
        print(f"{name:8s} declination {dec:+7.3f}")

    print()
    for item in find_declination_aspects(declinations):
        print(f"{item['body_a']:8s} {item['aspect']:14s} {item['body_b']:8s} orb={item['orb']:.3f}")
