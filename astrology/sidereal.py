"""
Sidereal (Vedic/Jyotish) chart derivation.

Derives a sidereal chart from an already-computed tropical chart
(astrology.chart.build_chart's output) rather than recomputing
planetary positions independently. Ayanamsa is a constant coordinate-
frame offset for a given moment — it applies uniformly to every body
and chart angle — so subtracting it from tropical longitudes already
computed is equivalent to (and cheaper than) a second Swiss Ephemeris
pass with SEFLG_SIDEREAL, and was validated this way in the V0
prototype against real Lahiri ayanamsa reference values.

Houses use the whole-sign method (the traditional Jyotish convention,
not Placidus) — the sign containing the Ascendant is the 1st house,
and house number simply counts forward sign by sign.
"""

import swisseph as swe

from astrology.normaliser import longitude_to_zodiac

NAKSHATRAS = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
    "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
)

NAKSHATRA_SPAN = 360 / 27  # 13 deg 20'

AYANAMSA_MODES = {
    "lahiri": swe.SIDM_LAHIRI,
}


def get_ayanamsa(julian_day: float, mode: str = "lahiri") -> float:
    swe.set_sid_mode(AYANAMSA_MODES[mode])
    return swe.get_ayanamsa_ut(julian_day)


def sidereal_longitude(tropical_longitude: float, ayanamsa: float) -> float:
    return (tropical_longitude - ayanamsa) % 360.0


def nakshatra_for(longitude: float):
    index = int(longitude // NAKSHATRA_SPAN)
    within = longitude % NAKSHATRA_SPAN
    pada = int(within // (NAKSHATRA_SPAN / 4)) + 1
    return NAKSHATRAS[index], pada


def whole_sign_house(sign_index: int, ascendant_sign_index: int) -> int:
    return ((sign_index - ascendant_sign_index) % 12) + 1


def _sidereal_point(tropical_longitude, ayanamsa, ascendant_sign_index, retrograde=False):
    longitude = sidereal_longitude(tropical_longitude, ayanamsa)
    zodiac = longitude_to_zodiac(longitude)
    nakshatra, pada = nakshatra_for(longitude)

    return {
        "longitude": longitude,
        "sign": zodiac["sign"],
        "sign_index": zodiac["sign_index"],
        "degree": zodiac["degree"],
        "minute": zodiac["minute"],
        "second": zodiac["second"],
        "nakshatra": nakshatra,
        "nakshatra_pada": pada,
        "house": whole_sign_house(zodiac["sign_index"], ascendant_sign_index),
        "retrograde": retrograde,
    }


def build_sidereal_chart(tropical_chart: dict, ayanamsa_mode: str = "lahiri") -> dict:
    """
    Derive a sidereal chart from build_chart()'s tropical output.
    """

    julian_day = tropical_chart["julian_day"]
    ayanamsa = get_ayanamsa(julian_day, ayanamsa_mode)

    asc_tropical = tropical_chart["houses"]["angles"]["ascendant"]
    asc_sidereal_longitude = sidereal_longitude(asc_tropical, ayanamsa)
    ascendant_sign_index = int(asc_sidereal_longitude // 30)

    bodies = {
        name: _sidereal_point(
            data["longitude"],
            ayanamsa,
            ascendant_sign_index,
            retrograde=data.get("retrograde", False),
        )
        for name, data in tropical_chart["bodies"].items()
    }

    ascendant = _sidereal_point(asc_tropical, ayanamsa, ascendant_sign_index)
    ascendant["house"] = 1  # the Ascendant is the 1st house cusp, by definition

    return {
        "julian_day": julian_day,
        "ayanamsa": ayanamsa,
        "ayanamsa_mode": ayanamsa_mode,
        "bodies": bodies,
        "ascendant": ascendant,
    }


if __name__ == "__main__":
    from datetime import datetime, timezone
    from astrology.chart import build_chart
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = aware_utc.replace(tzinfo=timezone.utc) if aware_utc.tzinfo is None else aware_utc

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")
    sidereal = build_sidereal_chart(tropical)

    print(f"Ayanamsa ({sidereal['ayanamsa_mode']}): {sidereal['ayanamsa']:.4f}")
    for body in ("sun", "moon"):
        p = sidereal["bodies"][body]
        print(f"{body:8s} {p['sign']} {p['degree']}°{p['minute']}' | {p['nakshatra']} pada {p['nakshatra_pada']} | house {p['house']}")
    a = sidereal["ascendant"]
    print(f"{'asc':8s} {a['sign']} {a['degree']}°{a['minute']}' | {a['nakshatra']} pada {a['nakshatra_pada']} | house {a['house']}")
