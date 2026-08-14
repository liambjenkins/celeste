"""
BaZi Four Pillars derivation.

Takes an already-computed tropical chart (astrology.chart.build_chart)
plus the birth's local civil time, and derives the Year/Month/Day/Hour
pillars. Year and Month boundaries are solar-term-based (timezone-
independent astronomical instants, so they read off the tropical
chart's UTC data); Day and Hour boundaries are local-civil-time-based
(so they need the original local time, not just its UTC conversion).

Known simplification, stated plainly rather than silently assumed:
the Day Pillar boundary is taken as local civil midnight. Classical
practice sometimes uses a "Zi hour" boundary (23:00-01:00 spans two
days) instead — a real edge case for births near midnight, not
resolved here.
"""

from dataclasses import dataclass
from datetime import date, datetime

from chinese.sexagenary import STEM_INDEX, Pillar, pillar_from_indices
from chinese.solar_terms import lichun_julian_day

import swisseph as swe

# 1 Jan 2000 = day index 54 in the 60-day cycle (independently
# verified: stem index 54%10=4=Wu, branch index 54%12=6=Wu -> Wu-Wu,
# and cross-checked against a third-party Chinese calendar converter
# for a real test date this session).
_DAY_PILLAR_EPOCH = date(2000, 1, 1)
_DAY_PILLAR_EPOCH_INDEX = 54


@dataclass(frozen=True)
class FourPillars:
    year: Pillar
    month: Pillar
    day: Pillar
    hour: Pillar
    bazi_year: int

    @property
    def day_master(self) -> str:
        return self.day.stem

    @property
    def day_master_element(self) -> str:
        return self.day.stem_element

    @property
    def day_master_polarity(self) -> str:
        return self.day.stem_polarity

    def to_dict(self) -> dict:
        return {
            "year": self.year.to_dict(),
            "month": self.month.to_dict(),
            "day": self.day.to_dict(),
            "hour": self.hour.to_dict(),
            "bazi_year": self.bazi_year,
            "day_master": self.day_master,
            "day_master_element": self.day_master_element,
            "day_master_polarity": self.day_master_polarity,
        }


def year_pillar(julian_day: float) -> tuple[Pillar, int]:
    """
    Returns the Year Pillar and the BaZi year number used (which can
    differ from the Gregorian year for Jan/early-Feb births, before
    that year's Lichun).
    """

    gregorian_year = swe.revjul(julian_day)[0]
    lichun_this_year = lichun_julian_day(gregorian_year)

    bazi_year = (
        gregorian_year if julian_day >= lichun_this_year
        else gregorian_year - 1
    )

    stem_index = (bazi_year - 4) % 10
    branch_index = (bazi_year - 4) % 12
    return pillar_from_indices(stem_index, branch_index), bazi_year


def month_pillar(solar_longitude: float, year_stem_index: int) -> Pillar:
    """
    BaZi month is a fixed 30-degree solar-longitude bucket starting
    at Lichun (315 deg = month 1 = Yin/Tiger branch); the month
    branch cycle is the same every year. Month stem derives from the
    Year Stem via the classical "Five Tigers" rule.
    """

    month_number = int((solar_longitude - 315) // 30) % 12 + 1
    branch_index = (2 + (month_number - 1)) % 12  # Yin(2) is month 1

    month1_stem_index = (2 * (year_stem_index % 5) + 2) % 10
    stem_index = (month1_stem_index + (month_number - 1)) % 10

    return pillar_from_indices(stem_index, branch_index)


def day_pillar(local_civil_date: date) -> Pillar:
    days_elapsed = (local_civil_date - _DAY_PILLAR_EPOCH).days
    day_index = (_DAY_PILLAR_EPOCH_INDEX + days_elapsed) % 60
    return pillar_from_indices(day_index, day_index)


def hour_pillar(local_hour: int, local_minute: int, day_stem_index: int) -> Pillar:
    """
    Each Earthly Branch governs a 2-hour window, Zi = 23:00-00:59.
    Hour stem derives from the Day Stem via the classical
    "Five Rats" rule.
    """

    minutes_since_11pm = ((local_hour * 60 + local_minute) - 23 * 60) % (24 * 60)
    branch_index = minutes_since_11pm // 120

    zi_hour_stem_index = (2 * (day_stem_index % 5)) % 10
    stem_index = (zi_hour_stem_index + branch_index) % 10

    return pillar_from_indices(stem_index, branch_index)


def build_four_pillars(tropical_chart: dict, local_time: datetime) -> FourPillars:
    """
    Derive the Four Pillars from an already-computed tropical chart
    plus the birth's local civil time (needed for Day/Hour, which are
    local-clock-based rather than UTC-instant-based like Year/Month).
    """

    sun_longitude = tropical_chart["bodies"]["sun"]["longitude"]

    year, bazi_year = year_pillar(tropical_chart["julian_day"])
    month = month_pillar(sun_longitude, STEM_INDEX[year.stem])
    day = day_pillar(local_time.date())
    hour = hour_pillar(local_time.hour, local_time.minute, STEM_INDEX[day.stem])

    return FourPillars(year=year, month=month, day=day, hour=hour, bazi_year=bazi_year)


if __name__ == "__main__":
    from astrology.chart import build_chart
    from astrology.time import local_to_utc
    from datetime import timezone

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = aware_utc.replace(tzinfo=timezone.utc) if aware_utc.tzinfo is None else aware_utc

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")
    pillars = build_four_pillars(tropical, local_time)

    for label, pillar in (("Year", pillars.year), ("Month", pillars.month), ("Day", pillars.day), ("Hour", pillars.hour)):
        print(f"{label}: {pillar.name} ({pillar.stem_polarity} {pillar.stem_element} {pillar.branch_animal})")
    print()
    print(f"Day Master: {pillars.day_master} ({pillars.day_master_polarity} {pillars.day_master_element})")
