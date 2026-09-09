"""Which of the 5 non-luminary classical planets station (turn direct
or retrograde) within a given calendar day, by comparing speed sign
at the start and end of that UTC day."""

from datetime import datetime, timedelta, timezone

import swisseph as swe

from providers.astronomy import BODIES, datetime_to_julian_day

STATION_PLANETS = ("mercury", "venus", "mars", "jupiter", "saturn")


def _speed_at(utc_time: datetime, planet: str) -> float:
    jd = datetime_to_julian_day(utc_time)
    return swe.calc_ut(jd, BODIES[planet])[0][3]


def build_stations(as_of_utc_time: datetime) -> list:
    day_start = as_of_utc_time.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1) - timedelta(seconds=1)

    stations = []

    for planet in STATION_PLANETS:
        speed_start = _speed_at(day_start, planet)
        speed_end = _speed_at(day_end, planet)

        if (speed_start < 0) != (speed_end < 0):
            stations.append(
                {
                    "planet": planet,
                    "station_type": "stationary_direct" if speed_end > 0 else "stationary_retrograde",
                }
            )

    return stations
