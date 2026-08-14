"""
Navamsa (D9): the ninth-harmonic divisional chart in Vedic (Jyotish)
astrology — traditionally read as a subtler confirmation of the birth
(D1/Rasi) chart, consulted above all for marriage and for the inner
strength of a placement (a planet strong by sign but weak by navamsa,
or the reverse, is a real and commonly-drawn distinction, not a
simplification).

Each 30-degree sidereal sign is divided into nine navamsas of exactly
3d20' each. Which SIGN a given navamsa maps to depends on the natal
sign's modality — verified via web search against a worked example
during curation (Sun at sidereal 1d Gemini falls in the Libra
navamsa):
    - movable (Aries, Cancer, Libra, Capricorn): navamsas count
      starting from the SAME sign
    - fixed (Taurus, Leo, Scorpio, Aquarius): navamsas count starting
      from the 9th sign from it
    - dual/mutable (Gemini, Virgo, Sagittarius, Pisces): navamsas
      count starting from the 5th sign from it

This is arithmetically equivalent to the shortcut formula
(sign_index * 9 + navamsa_index_in_sign) % 12 used by many modern
calculators, but the modality-based form is implemented directly here
since it's the actual documented classical rule, not just a
computational trick.

Operates on sidereal longitudes an already-built sidereal chart
(astrology.sidereal.build_sidereal_chart's output) supplies — the
Navamsa is itself a purely sidereal Vedic technique with no tropical
equivalent, so it takes that chart as input rather than recomputing
positions.
"""

from astrology.sidereal import whole_sign_house

ZODIAC_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

NAVAMSA_SPAN = 30.0 / 9.0  # 3 degrees 20 minutes

_MOVABLE_SIGNS = {0, 3, 6, 9}      # Aries, Cancer, Libra, Capricorn
_FIXED_SIGNS = {1, 4, 7, 10}       # Taurus, Leo, Scorpio, Aquarius
_DUAL_SIGNS = {2, 5, 8, 11}        # Gemini, Virgo, Sagittarius, Pisces


def navamsa_sign_index(sidereal_longitude: float) -> int:
    """Return the 0-11 zodiac sign index of a longitude's Navamsa."""

    sign_index = int(sidereal_longitude // 30) % 12
    degree_in_sign = sidereal_longitude % 30
    navamsa_index_in_sign = int(degree_in_sign // NAVAMSA_SPAN)

    if sign_index in _MOVABLE_SIGNS:
        start_index = sign_index
    elif sign_index in _FIXED_SIGNS:
        start_index = (sign_index + 8) % 12
    else:
        start_index = (sign_index + 4) % 12

    return (start_index + navamsa_index_in_sign) % 12


def _navamsa_point(longitude: float, navamsa_ascendant_sign_index: int) -> dict:
    index = navamsa_sign_index(longitude)

    return {
        "sign": ZODIAC_SIGNS[index],
        "sign_index": index,
        "house": whole_sign_house(index, navamsa_ascendant_sign_index),
    }


def build_navamsa_chart(sidereal_chart: dict) -> dict:
    """
    Derive the D9 Navamsa chart from an already-built sidereal (D1)
    chart. The Navamsa has its own whole-sign house wheel, counted
    from its own (D9) Ascendant, distinct from the D1 house wheel.
    """

    ascendant_longitude = sidereal_chart["ascendant"]["longitude"]
    navamsa_ascendant_sign_index = navamsa_sign_index(ascendant_longitude)

    bodies = {
        name: _navamsa_point(point["longitude"], navamsa_ascendant_sign_index)
        for name, point in sidereal_chart["bodies"].items()
    }

    ascendant = _navamsa_point(ascendant_longitude, navamsa_ascendant_sign_index)
    ascendant["house"] = 1  # the D9 Ascendant is the 1st D9 house, by definition

    return {
        "bodies": bodies,
        "ascendant": ascendant,
    }


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.sidereal import build_sidereal_chart
    from astrology.time import local_to_utc

    # Verification case from web search: sidereal Sun at 1d Gemini
    # (sign_index 2) should fall in the Libra (sign_index 6) navamsa.
    assert navamsa_sign_index(61.0) == 6, "Gemini 1d should navamsa to Libra"
    print("Worked-example check passed: Gemini 1d -> Libra navamsa.")
    print()

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")
    sidereal = build_sidereal_chart(tropical)
    navamsa = build_navamsa_chart(sidereal)

    for name in ("sun", "moon"):
        d1 = sidereal["bodies"][name]
        d9 = navamsa["bodies"][name]
        print(
            f"{name:8s} D1 {d1['sign']:12s} {d1['degree']:2d}°{d1['minute']:02d}' "
            f"-> D9 {d9['sign']:12s} house {d9['house']}"
        )

    d1_asc = sidereal["ascendant"]
    d9_asc = navamsa["ascendant"]
    print(
        f"{'asc':8s} D1 {d1_asc['sign']:12s} {d1_asc['degree']:2d}°{d1_asc['minute']:02d}' "
        f"-> D9 {d9_asc['sign']:12s} house {d9_asc['house']}"
    )
