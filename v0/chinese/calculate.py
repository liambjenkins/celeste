"""
V0 Chinese calculation layer — BaZi Four Pillars.

Pure structured facts: Year/Month/Day/Hour pillars (each a Heavenly
Stem + Earthly Branch), and the Day Master. No prose.

Chinese astrology has no native Sun/Moon/Ascendant — it's built from
Four Pillars, not planets-in-signs, so this module doesn't try to
force one. See v0/convergence.py for how Chinese enters the
cross-tradition comparison (only via Day Master, on the identity
theme) without inventing equivalents BaZi tradition doesn't make.

New code — no lunisolar/sexagenary logic existed anywhere in this
repo before this module. Two facts anchor everything else and were
independently verified before writing this (not just recalled):
    - Lichun (Start of Spring, solar longitude 315 deg) is the
      Year Pillar boundary, NOT Lunar New Year. Already validated in
      the earlier Sun-only prototype: root-finding on the existing
      Sun ephemeris call landed Lichun 1996 at Feb 4, 13:13 UTC.
    - 1 January 2000 is a documented Wu-Wu (Yang Earth Horse) day,
      used here as the Day Pillar's reference epoch.

Known simplification, stated plainly rather than silently assumed:
the Day Pillar boundary is taken as local civil midnight. Classical
practice sometimes uses a "Zi hour" boundary (23:00-01:00 spans two
days) instead -- immaterial for this birth time (3:10am, nowhere near
midnight) but worth flagging as a real edge case for other dates.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta

import swisseph as swe

from v0.western.calculate import calculate as calculate_western

STEMS = (
    ("Jia", "Wood", "Yang"), ("Yi", "Wood", "Yin"),
    ("Bing", "Fire", "Yang"), ("Ding", "Fire", "Yin"),
    ("Wu", "Earth", "Yang"), ("Ji", "Earth", "Yin"),
    ("Geng", "Metal", "Yang"), ("Xin", "Metal", "Yin"),
    ("Ren", "Water", "Yang"), ("Gui", "Water", "Yin"),
)

BRANCHES = (
    ("Zi", "Rat"), ("Chou", "Ox"), ("Yin", "Tiger"), ("Mao", "Rabbit"),
    ("Chen", "Dragon"), ("Si", "Snake"), ("Wu", "Horse"), ("Wei", "Goat"),
    ("Shen", "Monkey"), ("You", "Rooster"), ("Xu", "Dog"), ("Hai", "Pig"),
)

# 1 Jan 2000 = day index 54 in the 60-day cycle (independently
# verified: stem index 54%10=4=Wu, branch index 54%12=6=Wu -> Wu-Wu).
_DAY_PILLAR_EPOCH = date(2000, 1, 1)
_DAY_PILLAR_EPOCH_INDEX = 54


@dataclass(frozen=True)
class Pillar:
    stem: str
    stem_element: str
    stem_polarity: str
    branch: str
    branch_animal: str

    @property
    def name(self) -> str:
        return f"{self.stem}-{self.branch}"


@dataclass(frozen=True)
class FourPillars:
    year: Pillar
    month: Pillar
    day: Pillar
    hour: Pillar

    @property
    def day_master(self) -> str:
        return self.day.stem

    @property
    def day_master_element(self) -> str:
        return self.day.stem_element

    @property
    def day_master_polarity(self) -> str:
        return self.day.stem_polarity


_STEM_INDEX = {name: index for index, (name, _, _) in enumerate(STEMS)}


def _pillar(stem_index: int, branch_index: int) -> Pillar:
    stem_index %= 10
    branch_index %= 12
    stem_name, stem_element, stem_polarity = STEMS[stem_index]
    branch_name, branch_animal = BRANCHES[branch_index]
    return Pillar(
        stem=stem_name,
        stem_element=stem_element,
        stem_polarity=stem_polarity,
        branch=branch_name,
        branch_animal=branch_animal,
    )


def _find_solar_longitude_crossing(target_longitude, jd_low, jd_high):
    """
    Bisection root-find for the moment the Sun's tropical longitude
    crosses target_longitude, given a search window already known
    to bracket the crossing (longitude assumed monotonically
    increasing across the window, no 360->0 wraparound within it).
    """

    def sun_longitude(jd):
        return swe.calc_ut(jd, swe.SUN)[0][0]

    lo, hi = jd_low, jd_high
    for _ in range(60):
        mid = (lo + hi) / 2
        if sun_longitude(mid) < target_longitude:
            lo = mid
        else:
            hi = mid
    return hi


def _lichun_julian_day(gregorian_year: int) -> float:
    jd_low = swe.julday(gregorian_year, 2, 1, 0.0)
    jd_high = swe.julday(gregorian_year, 2, 8, 0.0)
    return _find_solar_longitude_crossing(315.0, jd_low, jd_high)


def _year_pillar(utc_time: datetime) -> tuple[Pillar, int]:
    """
    Returns the Year Pillar and the BaZi year number used (which can
    differ from the Gregorian year for Jan/early-Feb births, before
    that year's Lichun).
    """

    jd_birth = swe.julday(
        utc_time.year, utc_time.month, utc_time.day,
        utc_time.hour + utc_time.minute / 60,
    )
    lichun_this_year = _lichun_julian_day(utc_time.year)

    bazi_year = (
        utc_time.year if jd_birth >= lichun_this_year
        else utc_time.year - 1
    )

    stem_index = (bazi_year - 4) % 10
    branch_index = (bazi_year - 4) % 12
    return _pillar(stem_index, branch_index), bazi_year


def _month_pillar(solar_longitude: float, year_stem_index: int) -> Pillar:
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

    return _pillar(stem_index, branch_index)


def _day_pillar(local_civil_date: date) -> Pillar:
    days_elapsed = (local_civil_date - _DAY_PILLAR_EPOCH).days
    day_index = (_DAY_PILLAR_EPOCH_INDEX + days_elapsed) % 60
    return _pillar(day_index, day_index)


def _hour_pillar(local_hour: int, local_minute: int, day_stem_index: int) -> Pillar:
    """
    Each Earthly Branch governs a 2-hour window, Zi = 23:00-00:59.
    Hour stem derives from the Day Stem via the classical
    "Five Rats" rule.
    """

    minutes_since_11pm = ((local_hour * 60 + local_minute) - 23 * 60) % (24 * 60)
    branch_index = minutes_since_11pm // 120

    zi_hour_stem_index = (2 * (day_stem_index % 5)) % 10
    stem_index = (zi_hour_stem_index + branch_index) % 10

    return _pillar(stem_index, branch_index)


def calculate(
    local_time: datetime,
    timezone_name: str,
    latitude: float,
    longitude: float,
) -> FourPillars:
    western = calculate_western(local_time, timezone_name, latitude, longitude)

    year_pillar, _bazi_year = _year_pillar(western.utc_time)
    month_pillar = _month_pillar(western.sun.longitude, _STEM_INDEX[year_pillar.stem])

    day_pillar = _day_pillar(local_time.date())
    hour_pillar = _hour_pillar(
        local_time.hour, local_time.minute, _STEM_INDEX[day_pillar.stem]
    )

    return FourPillars(
        year=year_pillar,
        month=month_pillar,
        day=day_pillar,
        hour=hour_pillar,
    )


if __name__ == "__main__":
    result = calculate(
        datetime(1996, 7, 22, 3, 10),
        "Australia/Melbourne",
        -37.7392,
        144.7967,
    )
    print(f"Year:  {result.year.name} ({result.year.stem_polarity} {result.year.stem_element} {result.year.branch_animal})")
    print(f"Month: {result.month.name} ({result.month.stem_polarity} {result.month.stem_element} {result.month.branch_animal})")
    print(f"Day:   {result.day.name} ({result.day.stem_polarity} {result.day.stem_element} {result.day.branch_animal})")
    print(f"Hour:  {result.hour.name} ({result.hour.stem_polarity} {result.hour.stem_element} {result.hour.branch_animal})")
    print()
    print(f"Day Master: {result.day_master} ({result.day_master_polarity} {result.day_master_element})")
