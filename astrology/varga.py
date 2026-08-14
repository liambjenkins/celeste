"""
Generalized Vedic (Jyotish) divisional chart (Varga / Amsha) engine.

Implements the classical Parashari division rules from Brihat Parashara
Hora Shastra, Chapter 6 ("The Sixteen Divisions of a Rasi"), for the
Shodasavarga charts beyond D1 (Rasi, the birth chart itself) and D9
(Navamsa, already implemented separately in astrology/navamsa.py using
the same mechanism this module generalizes). Rules verified via web
search against a BPHS Ch.6 transcription (jyotishvidya.com/ch6.htm)
and cross-referenced against multiple independent technical sources
during curation, per this project's sourcing discipline.

Most divisional charts share the same underlying shape: divide each
30-degree sign into N equal divisions, then map each division to a
sign by counting forward from a per-chart "starting sign" that itself
depends on the natal sign's odd/even parity, modality (movable/fixed/
dual), or triplicity (element) -- exactly the mechanism Navamsa uses,
just with a different N and starting-sign rule. That shared shape is
expressed once, in _varga_sign_index(), and each chart supplies
(division count, starting-sign function, step).

Three charts don't fit that shape and are handled as special cases:
  - D2 (Hora): not a sign-counting rule at all -- a direct binary map
    (Sun's half of the sign -> Leo, Moon's half -> Cancer).
  - D30 (Trimshamsa): unequal-width divisions, each assigned to a
    fixed planetary lord's OWN sign (not counted from the natal sign
    at all), with the lord order reversed between odd and even signs.
  - D60 (Shashtyamsa): fits the shared shape mechanically (same sign,
    step 1, 60 divisions -- the %12 in _varga_sign_index() naturally
    reproduces the classical "divide by 2, mod 12" cycling), but
    sources disagree on whether an odd/even branch applies to the
    sign-counting itself or only to the (unimplemented here) deity-
    name ordering. Implemented using the reading directly supported
    by the primary-text transcription (no odd/even branch on sign-
    counting); flagged here as the least airtight of the 13 rules,
    per this project's "note as requires curation where genuinely
    contested" discipline rather than silently picking a side.

Operates on sidereal longitudes an already-built sidereal chart
(astrology.sidereal.build_sidereal_chart's output) supplies, same as
Navamsa.
"""

from astrology.sidereal import whole_sign_house

ZODIAC_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

_MOVABLE_SIGNS = {0, 3, 6, 9}
_FIXED_SIGNS = {1, 4, 7, 10}
_DUAL_SIGNS = {2, 5, 8, 11}
_FIRE_SIGNS = {0, 4, 8}
_EARTH_SIGNS = {1, 5, 9}
_AIR_SIGNS = {2, 6, 10}
_WATER_SIGNS = {3, 7, 11}


def _is_odd_sign(sign_index: int) -> bool:
    # Aries (index 0) is the zodiac's 1st sign, an odd-numbered sign.
    return sign_index % 2 == 0


def _same_sign(sign_index: int) -> int:
    return sign_index


def _odd_same_even_offset(offset: int):
    def _start(sign_index: int) -> int:
        if _is_odd_sign(sign_index):
            return sign_index
        return (sign_index + offset) % 12
    return _start


def _odd_even_start(odd_start: int, even_start: int):
    def _start(sign_index: int) -> int:
        return odd_start if _is_odd_sign(sign_index) else even_start
    return _start


def _modality_start(movable_start: int, fixed_start: int, dual_start: int):
    def _start(sign_index: int) -> int:
        if sign_index in _MOVABLE_SIGNS:
            return movable_start
        if sign_index in _FIXED_SIGNS:
            return fixed_start
        return dual_start
    return _start


def _triplicity_start(fire_start: int, earth_start: int, air_start: int, water_start: int):
    def _start(sign_index: int) -> int:
        if sign_index in _FIRE_SIGNS:
            return fire_start
        if sign_index in _EARTH_SIGNS:
            return earth_start
        if sign_index in _AIR_SIGNS:
            return air_start
        return water_start
    return _start


def _varga_sign_index(sign_index: int, division_index: int, start_fn, step: int = 1) -> int:
    return (start_fn(sign_index) + division_index * step) % 12


# ------------------------------------------------------------
# Per-chart configuration for the 11 charts that fit the shared
# "equal divisions, counted from a rule-derived starting sign" shape.
# D2 and D30 are handled as dedicated special cases below.
# ------------------------------------------------------------

_CHARTS = {
    # D3 Drekkana: 1st=same sign, 2nd=5th sign from it (+4), 3rd=9th
    # sign from it (+8) -- the classical Parashari 1-5-9 trine rule.
    3: {"divisions": 3, "start_fn": _same_sign, "step": 4},
    # D4 Chaturthamsa: 1st=same, 2nd=4th(+3), 3rd=7th(+6), 4th=10th(+9)
    # sign from it -- counted through the four kendras (angles).
    4: {"divisions": 4, "start_fn": _same_sign, "step": 3},
    # D7 Saptamsa: odd sign starts from itself, even sign starts from
    # its 7th sign (+6).
    7: {"divisions": 7, "start_fn": _odd_same_even_offset(6), "step": 1},
    # D10 Dasamsa: odd sign starts from itself, even sign starts from
    # its 9th sign (+8).
    10: {"divisions": 10, "start_fn": _odd_same_even_offset(8), "step": 1},
    # D12 Dwadasamsa: always starts from the occupied sign itself, no
    # odd/even or modality distinction.
    12: {"divisions": 12, "start_fn": _same_sign, "step": 1},
    # D16 Shodasamsa: movable->Aries, fixed->Leo, dual->Sagittarius.
    16: {"divisions": 16, "start_fn": _modality_start(0, 4, 8), "step": 1},
    # D20 Vimshamsa: movable->Aries, fixed->Sagittarius, dual->Leo --
    # note this is a DIFFERENT fixed/dual assignment than D16.
    20: {"divisions": 20, "start_fn": _modality_start(0, 8, 4), "step": 1},
    # D24 Chaturvimshamsa (Siddhamsa): odd sign starts from Leo, even
    # sign starts from Cancer.
    24: {"divisions": 24, "start_fn": _odd_even_start(4, 3), "step": 1},
    # D27 Saptavimshamsa (Nakshatramsa/Bhamsa): triplicity-based,
    # anchored to the four movable signs -- fire->Aries, earth->
    # Cancer, air->Libra, water->Capricorn.
    27: {"divisions": 27, "start_fn": _triplicity_start(0, 3, 6, 9), "step": 1},
    # D40 Khavedamsa: odd sign starts from Aries, even sign starts
    # from Libra.
    40: {"divisions": 40, "start_fn": _odd_even_start(0, 6), "step": 1},
    # D45 Akshavedamsa: same modality triad as D16 -- movable->Aries,
    # fixed->Leo, dual->Sagittarius.
    45: {"divisions": 45, "start_fn": _modality_start(0, 4, 8), "step": 1},
    # D60 Shashtyamsa: always starts from the occupied sign itself.
    # See module docstring -- the odd/even question genuinely
    # contested in sources is about deity-name ordering, not this
    # sign-counting rule, per the primary-text reading used here.
    60: {"divisions": 60, "start_fn": _same_sign, "step": 1},
}


def _hora_sign_index(sign_index: int, degree_in_sign: float) -> int:
    """
    D2 Hora: not a sign-counting rule. Odd sign, first half (0-15d) =
    Sun's hora; second half = Moon's. Even sign: reversed. Every
    Sun's-hora division maps to Leo (the Sun's own sign); every
    Moon's-hora division maps to Cancer (the Moon's own sign) -- so
    the whole D2 chart only ever occupies these two signs.
    """

    first_half = degree_in_sign < 15.0

    if _is_odd_sign(sign_index):
        is_sun_hora = first_half
    else:
        is_sun_hora = not first_half

    return 4 if is_sun_hora else 3  # Leo=4 (Sun), Cancer=3 (Moon)


# D30 Trimshamsa: unequal-width divisions, each ruled by a fixed
# planetary lord (mapped to that lord's own sign), NOT counted from
# the natal sign. Order is Mars-Saturn-Jupiter-Mercury-Venus for odd
# signs (5,5,8,7,5 degrees), reversed to Venus-Mercury-Jupiter-Saturn-
# Mars for even signs (5,7,8,5,5 degrees). Sun and Moon hold no
# trimshamsa lordship.
_TRIMSHAMSA_ODD = (
    (5.0, 0),    # Mars -> Aries
    (10.0, 10),  # Saturn -> Aquarius
    (18.0, 8),   # Jupiter -> Sagittarius
    (25.0, 2),   # Mercury -> Gemini
    (30.0, 6),   # Venus -> Libra
)
_TRIMSHAMSA_EVEN = (
    (5.0, 1),    # Venus -> Taurus
    (12.0, 5),   # Mercury -> Virgo
    (20.0, 11),  # Jupiter -> Pisces
    (25.0, 9),   # Saturn -> Capricorn
    (30.0, 7),   # Mars -> Scorpio
)


def _trimshamsa_sign_index(sign_index: int, degree_in_sign: float) -> int:
    table = _TRIMSHAMSA_ODD if _is_odd_sign(sign_index) else _TRIMSHAMSA_EVEN

    for upper_bound, target_sign in table:
        if degree_in_sign < upper_bound:
            return target_sign

    return table[-1][1]  # degree_in_sign == 30.0 edge case


SHODASAVARGA_CHARTS = (2, 3, 4, 7, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60)


def varga_sign_index(sidereal_longitude: float, n: int) -> int:
    """Return the 0-11 zodiac sign index of a longitude's Dn division."""

    sign_index = int(sidereal_longitude // 30) % 12
    degree_in_sign = sidereal_longitude % 30

    if n == 2:
        return _hora_sign_index(sign_index, degree_in_sign)

    if n == 30:
        return _trimshamsa_sign_index(sign_index, degree_in_sign)

    config = _CHARTS[n]
    division_width = 30.0 / config["divisions"]
    division_index = min(
        int(degree_in_sign // division_width), config["divisions"] - 1
    )

    return _varga_sign_index(
        sign_index, division_index, config["start_fn"], config["step"]
    )


def _varga_point(longitude: float, n: int, varga_ascendant_sign_index: int) -> dict:
    index = varga_sign_index(longitude, n)

    return {
        "sign": ZODIAC_SIGNS[index],
        "sign_index": index,
        "house": whole_sign_house(index, varga_ascendant_sign_index),
    }


def build_varga_chart(sidereal_chart: dict, n: int) -> dict:
    """
    Derive the Dn divisional chart from an already-built sidereal (D1)
    chart. Each Dn has its own whole-sign house wheel, counted from
    its own Dn Ascendant, distinct from the D1 house wheel -- same
    convention as astrology.navamsa.build_navamsa_chart.
    """

    ascendant_longitude = sidereal_chart["ascendant"]["longitude"]
    varga_ascendant_sign_index = varga_sign_index(ascendant_longitude, n)

    bodies = {
        name: _varga_point(point["longitude"], n, varga_ascendant_sign_index)
        for name, point in sidereal_chart["bodies"].items()
    }

    ascendant = _varga_point(ascendant_longitude, n, varga_ascendant_sign_index)
    ascendant["house"] = 1  # the Dn Ascendant is the 1st Dn house, by definition

    return {"bodies": bodies, "ascendant": ascendant}


def build_all_vargas(sidereal_chart: dict, charts=SHODASAVARGA_CHARTS) -> dict:
    return {n: build_varga_chart(sidereal_chart, n) for n in charts}


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.sidereal import build_sidereal_chart
    from astrology.time import local_to_utc

    # Worked examples from the research pass, verified arithmetically:
    #   D7: odd sign Aries 1st saptamsa -> Aries; even sign Taurus
    #       1st saptamsa -> Scorpio.
    assert varga_sign_index(0.5, 7) == 0, "Aries early degree -> Aries D7"
    assert varga_sign_index(30.5, 7) == 7, "Taurus early degree -> Scorpio D7"

    #   D10: 15d Aries (odd) -> 6th dasamsa -> Virgo (index 5).
    #        15d Taurus (even) -> 6th dasamsa -> Gemini (index 2).
    assert varga_sign_index(15.0, 10) == 5, "15d Aries -> Virgo D10"
    assert varga_sign_index(45.0, 10) == 2, "15d Taurus -> Gemini D10"

    #   D27: 22d07' Aquarius (air sign, start Libra) -> 20th
    #        nakshatramsa -> Taurus (index 1).
    assert varga_sign_index(300.0 + 22.0 + 7 / 60, 27) == 1, (
        "22d07' Aquarius -> Taurus D27"
    )

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
    sidereal = build_sidereal_chart(tropical)
    vargas = build_all_vargas(sidereal)

    for n in SHODASAVARGA_CHARTS:
        chart = vargas[n]
        sun = chart["bodies"]["sun"]
        asc = chart["ascendant"]
        print(
            f"D{n:<3} Asc {asc['sign']:12s}  Sun {sun['sign']:12s} house {sun['house']}"
        )
