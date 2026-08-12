import swisseph as swe


HOUSE_SYSTEMS = {
    "placidus": b"P",
    "whole_sign": b"W",
    "equal": b"E",
    "koch": b"K",
    "porphyrius": b"O",
    "regiomontanus": b"R",
    "campanus": b"C",
}


def calculate_houses(
    julian_day: float,
    latitude: float,
    longitude: float,
    system: str = "placidus",
):
    """
    Calculate house cusps and chart angles.

    Placidus is the default, but the house system is configurable.
    """

    if system not in HOUSE_SYSTEMS:
        raise ValueError(
            f"Unknown house system: {system}. "
            f"Available: {', '.join(HOUSE_SYSTEMS)}"
        )

    cusps, ascmc = swe.houses_ex(
        julian_day,
        latitude,
        longitude,
        HOUSE_SYSTEMS[system],
    )

    return {
        "system": system,
        "cusps": {
            str(index + 1): cusp
            for index, cusp in enumerate(cusps)
        },
        "angles": {
            "ascendant": ascmc[0],
            "mc": ascmc[1],
            "armc": ascmc[2],
            "vertex": ascmc[3],
            "equatorial_ascendant": ascmc[4],
            "co_ascendant": ascmc[5],
            "polar_ascendant": ascmc[6],
            "additional_angle": ascmc[7],
        },
    }
