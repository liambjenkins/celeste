"""
V0 Western calculation layer.

Pure structured facts — sign, degree, house — for Sun, Moon, and
Ascendant. No prose, no interpretation. Reuses the existing,
already-built astrology/chart.py engine directly; there is no new
calculation logic here, only a thin extraction down to the three
placements V0 cares about.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from astrology.chart import build_chart
from astrology.normaliser import longitude_to_zodiac
from astrology.time import local_to_utc


@dataclass(frozen=True)
class Placement:
    body: str
    longitude: float
    sign: str
    degree: int
    minute: int
    house: Optional[int]


@dataclass(frozen=True)
class WesternBigThree:
    utc_time: datetime
    sun: Placement
    moon: Placement
    ascendant: Placement


def calculate(
    local_time: datetime,
    timezone_name: str,
    latitude: float,
    longitude: float,
) -> WesternBigThree:
    """
    Calculate tropical Sun, Moon, and Ascendant for one birth
    moment. Structured data only.
    """

    aware_utc = local_to_utc(local_time, timezone_name)
    utc_naive = aware_utc.replace(tzinfo=None)
    utc_aware = utc_naive.replace(tzinfo=timezone.utc)

    chart = build_chart(utc_aware, latitude, longitude, house_system="placidus")

    sun_data = chart["bodies"]["sun"]
    moon_data = chart["bodies"]["moon"]
    asc_longitude = chart["houses"]["angles"]["ascendant"]
    asc_zodiac = longitude_to_zodiac(asc_longitude)

    return WesternBigThree(
        utc_time=utc_naive,
        sun=Placement(
            body="sun",
            longitude=sun_data["longitude"],
            sign=sun_data["sign"],
            degree=sun_data["degree"],
            minute=sun_data["minute"],
            house=sun_data["house"],
        ),
        moon=Placement(
            body="moon",
            longitude=moon_data["longitude"],
            sign=moon_data["sign"],
            degree=moon_data["degree"],
            minute=moon_data["minute"],
            house=moon_data["house"],
        ),
        ascendant=Placement(
            body="ascendant",
            longitude=asc_longitude,
            sign=asc_zodiac["sign"],
            degree=asc_zodiac["degree"],
            minute=asc_zodiac["minute"],
            house=1,  # the Ascendant is the 1st house cusp, by definition
        ),
    )


if __name__ == "__main__":
    result = calculate(
        datetime(1996, 7, 22, 3, 10),
        "Australia/Melbourne",
        -37.7392,
        144.7967,
    )
    print(result)
