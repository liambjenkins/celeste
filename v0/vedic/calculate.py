"""
V0 Vedic calculation layer.

Pure structured facts — sidereal sign, nakshatra, whole-sign house —
for Sun, Moon, and Ascendant. No prose. New code (sidereal mode isn't
used anywhere else in the codebase yet), but small: reuses the same
ephemeris already vendored, and reuses the already-computed tropical
chart from v0/western/calculate.py rather than re-deriving positions
from scratch — ayanamsa is a constant offset for a given moment, so
sidereal longitude = tropical longitude - ayanamsa applies uniformly
to every point, houses included.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import swisseph as swe

from v0.western.calculate import WesternBigThree, calculate as calculate_western

VEDIC_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

NAKSHATRAS = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
    "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
)

NAKSHATRA_SPAN = 360 / 27  # 13deg 20'


@dataclass(frozen=True)
class VedicPlacement:
    body: str
    sidereal_longitude: float
    sign: str
    degree: int
    minute: int
    nakshatra: str
    pada: int
    house: int  # whole-sign, 1-12


@dataclass(frozen=True)
class VedicBigThree:
    utc_time: datetime
    ayanamsa: float
    sun: VedicPlacement
    moon: VedicPlacement
    ascendant: VedicPlacement


def _sidereal_from_tropical(tropical_longitude: float, ayanamsa: float) -> float:
    return (tropical_longitude - ayanamsa) % 360.0


def _to_placement(body: str, sidereal_longitude: float, ascendant_sign_index: int) -> VedicPlacement:
    sign_index = int(sidereal_longitude // 30)
    within_sign = sidereal_longitude % 30
    degree = int(within_sign)
    minute = int((within_sign - degree) * 60)

    nak_index = int(sidereal_longitude // NAKSHATRA_SPAN)
    within_nak = sidereal_longitude % NAKSHATRA_SPAN
    pada = int(within_nak // (NAKSHATRA_SPAN / 4)) + 1

    # Whole-sign houses: the sign containing the Ascendant is house 1,
    # and house number simply counts forward sign by sign.
    house = ((sign_index - ascendant_sign_index) % 12) + 1

    return VedicPlacement(
        body=body,
        sidereal_longitude=sidereal_longitude,
        sign=VEDIC_SIGNS[sign_index],
        degree=degree,
        minute=minute,
        nakshatra=NAKSHATRAS[nak_index],
        pada=pada,
        house=house,
    )


def calculate(
    local_time: datetime,
    timezone_name: str,
    latitude: float,
    longitude: float,
) -> VedicBigThree:
    western: WesternBigThree = calculate_western(
        local_time, timezone_name, latitude, longitude
    )

    julian_day = swe.julday(
        western.utc_time.year,
        western.utc_time.month,
        western.utc_time.day,
        western.utc_time.hour + western.utc_time.minute / 60,
    )

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsa = swe.get_ayanamsa_ut(julian_day)

    sun_sidereal = _sidereal_from_tropical(western.sun.longitude, ayanamsa)
    moon_sidereal = _sidereal_from_tropical(western.moon.longitude, ayanamsa)
    asc_sidereal = _sidereal_from_tropical(western.ascendant.longitude, ayanamsa)

    ascendant_sign_index = int(asc_sidereal // 30)

    return VedicBigThree(
        utc_time=western.utc_time,
        ayanamsa=ayanamsa,
        sun=_to_placement("sun", sun_sidereal, ascendant_sign_index),
        moon=_to_placement("moon", moon_sidereal, ascendant_sign_index),
        ascendant=_to_placement("ascendant", asc_sidereal, ascendant_sign_index),
    )


if __name__ == "__main__":
    result = calculate(
        datetime(1996, 7, 22, 3, 10),
        "Australia/Melbourne",
        -37.7392,
        144.7967,
    )
    print(f"Ayanamsa (Lahiri): {result.ayanamsa:.4f}°")
    for placement in (result.sun, result.moon, result.ascendant):
        print(
            f"{placement.body:10s} {placement.sign} "
            f"{placement.degree}°{placement.minute}' "
            f"| {placement.nakshatra} pada {placement.pada} "
            f"| house {placement.house}"
        )
