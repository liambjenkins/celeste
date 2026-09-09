"""
Lot of Fortune and Lot of Spirit -- sect-based Hermetic Lots.

Formula matches astrology/arabic_parts.py exactly (same classical
sect-aware convention: Fortune reverses by sect, Spirit is Fortune's
exact mirror at the same sect) but reimplemented here rather than
imported, to (a) use this package's own whole-sign house placement
and (b) use hellenistic.sect's horizon-precise day/night determination
rather than arabic_parts.py's simpler sun_house>=7 shortcut.

    Day:   Fortune = Asc + Moon - Sun    Spirit = Asc + Sun - Moon
    Night: Fortune = Asc + Sun - Moon    Spirit = Asc + Moon - Sun
"""

from hellenistic.constants import ZODIAC_SIGNS
from hellenistic.positions import whole_sign_house


def _lot_longitude(chart_sect: str, ascendant: float, term_a: float, term_b: float) -> float:
    if chart_sect == "day":
        return (ascendant + term_a - term_b) % 360.0
    return (ascendant + term_b - term_a) % 360.0


def _point(longitude: float, asc_sign_index: int) -> dict:
    sign_index = int(longitude // 30)
    return {
        "longitude": longitude,
        "sign": ZODIAC_SIGNS[sign_index],
        "sign_index": sign_index,
        "house": whole_sign_house(sign_index, asc_sign_index),
    }


def build_lots(ascendant_longitude: float, sun_longitude: float, moon_longitude: float, chart_sect: str, asc_sign_index: int) -> dict:
    fortune_longitude = _lot_longitude(chart_sect, ascendant_longitude, moon_longitude, sun_longitude)
    spirit_longitude = _lot_longitude(chart_sect, ascendant_longitude, sun_longitude, moon_longitude)

    return {
        "fortune": _point(fortune_longitude, asc_sign_index),
        "spirit": _point(spirit_longitude, asc_sign_index),
    }
