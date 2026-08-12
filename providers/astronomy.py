from datetime import datetime, timezone
from pathlib import Path

import swisseph as swe


EPHEMERIS_PATH = Path(__file__).resolve().parent.parent / "ephe"
swe.set_ephe_path(str(EPHEMERIS_PATH))


BODIES = {
    "sun": swe.SUN,
    "moon": swe.MOON,
    "mercury": swe.MERCURY,
    "venus": swe.VENUS,
    "mars": swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn": swe.SATURN,
    "uranus": swe.URANUS,
    "neptune": swe.NEPTUNE,
    "pluto": swe.PLUTO,
    "north_node_true": swe.TRUE_NODE,
    "north_node_mean": swe.MEAN_NODE,
    "lilith_mean": swe.MEAN_APOG,
    "lilith_true": swe.OSCU_APOG,
    "chiron": swe.CHIRON,
    "ceres": swe.CERES,
    "pallas": swe.PALLAS,
    "juno": swe.JUNO,
    "vesta": swe.VESTA,
}


def datetime_to_julian_day(utc_time: datetime) -> float:
    """Convert an aware UTC datetime to a Swiss Ephemeris Julian Day."""
    if utc_time.tzinfo is None:
        raise ValueError("utc_time must be timezone-aware")

    utc_time = utc_time.astimezone(timezone.utc)

    hour = (
        utc_time.hour
        + utc_time.minute / 60
        + utc_time.second / 3600
        + utc_time.microsecond / 3_600_000_000
    )

    return swe.julday(
        utc_time.year,
        utc_time.month,
        utc_time.day,
        hour,
    )


def get_astronomy(utc_time: datetime):
    """Calculate raw astronomical positions for the chart moment."""

    julian_day = datetime_to_julian_day(utc_time)

    observations = {}

    for name, body in BODIES.items():

        data = swe.calc_ut(
            julian_day,
            body,
        )[0]

        observations[name] = {
            "longitude": data[0],
            "latitude": data[1],
            "distance_au": data[2],
            "longitude_speed": data[3],
            "latitude_speed": data[4],
            "distance_speed": data[5],
        }

    # South Node is always exactly opposite North Node.
    north_node = observations["north_node_true"]["longitude"]

    observations["south_node_true"] = {
        "longitude": (north_node + 180.0) % 360.0,
        "derived_from": "north_node_true",
    }

    north_node_mean = observations["north_node_mean"]["longitude"]

    observations["south_node_mean"] = {
        "longitude": (north_node_mean + 180.0) % 360.0,
        "derived_from": "north_node_mean",
    }

    return {
        "julian_day": julian_day,
        "utc_time": utc_time.astimezone(timezone.utc).isoformat(),
        "bodies": observations,
    }
