"""
Liu Nian (流年, "Flowing Year"): the annual pillar overlaid on the
Four Pillars as of a given moment — the same sexagenary Year Pillar
mechanism chinese.pillars.year_pillar() already uses for the birth
chart's own Year Pillar, applied to the "as of" date instead. Read
alongside Da Yun (the 10-year Luck Pillar) as the finer, year-by-year
layer of BaZi timing technique -- opt-in via the same --as-of-date/
--as-of-time CLI flags Da Yun and Western transits/progressions
already use.

Source: standard classical BaZi convention (the annual pillar is the
same Lichun-bounded sexagenary year construction used for the natal
Year Pillar itself), consistent with this project's existing
chinese.pillars.year_pillar() implementation.
"""

from chinese.pillars import year_pillar
from providers.astronomy import get_astronomy


def build_liu_nian(as_of_utc_time) -> dict:
    astronomy = get_astronomy(as_of_utc_time)
    pillar, liu_nian_year = year_pillar(astronomy["julian_day"])

    return {
        "as_of_utc_time": as_of_utc_time.isoformat(),
        "liu_nian_year": liu_nian_year,
        "pillar": pillar.to_dict(),
    }


if __name__ == "__main__":
    from datetime import datetime, timezone

    as_of = datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)
    liu_nian = build_liu_nian(as_of)

    print(f"As of {as_of.date()}: Liu Nian year {liu_nian['liu_nian_year']}")
    print(f"Pillar: {liu_nian['pillar']['name']}")
