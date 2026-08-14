"""
Yogini Dasha: a compact 36-year Vedic timing cycle, distinct from
Vimshottari Dasha, layered on an already-computed sidereal chart.

Eight Yoginis rule fixed durations in a fixed sequence (Mangala 1yr,
Pingala 2yr, Dhanya 3yr, Bhramari 4yr, Bhadrika 5yr, Ulka 6yr, Siddha
7yr, Sankata 8yr = 36 years total). Entered at birth via the Moon's
nakshatra: the starting Yogini is (nakshatra_number + 3) mod 8, with
nakshatra numbered 1-27 (Ashwini=1) and a remainder of 0 read as 8
(Sankata). The BALANCE of that first Yogini period (how much of its
full duration remains) is proportional to how far the Moon has
already progressed through its nakshatra at birth -- the identical
balance mechanism astrology.dasha already uses for Vimshottari.

Ketu plays no role in this system (unlike Vimshottari, which is
Ketu-first). Only the main 8-period level is computed here -- classical
technique also has Yogini Antardasha sub-periods, left out of this
pass as further depth.

Source: standard classical Yogini Dasha convention, verified via web
search during curation, cross-referenced across multiple independent
technical sources for the starting-Yogini formula, the lord/duration
table, and the balance calculation.
"""

from datetime import datetime, timedelta

from astrology.sidereal import NAKSHATRA_SPAN, NAKSHATRAS

YOGINI_ORDER = (
    "Mangala", "Pingala", "Dhanya", "Bhramari",
    "Bhadrika", "Ulka", "Siddha", "Sankata",
)

YOGINI_YEARS = {
    "Mangala": 1, "Pingala": 2, "Dhanya": 3, "Bhramari": 4,
    "Bhadrika": 5, "Ulka": 6, "Siddha": 7, "Sankata": 8,
}

YOGINI_LORDS = {
    "Mangala": "moon", "Pingala": "sun", "Dhanya": "jupiter",
    "Bhramari": "mars", "Bhadrika": "mercury", "Ulka": "saturn",
    "Siddha": "venus", "Sankata": "rahu",
}

TOTAL_YEARS = sum(YOGINI_YEARS.values())  # 36

YEAR_DAYS = 365.25


def starting_yogini(nakshatra_index: int) -> str:
    """nakshatra_index is 0-26 (Ashwini=0); classical numbering is 1-27."""

    nakshatra_number = nakshatra_index + 1
    remainder = (nakshatra_number + 3) % 8
    position = 8 if remainder == 0 else remainder
    return YOGINI_ORDER[position - 1]


def _next_yogini(yogini: str) -> str:
    index = YOGINI_ORDER.index(yogini)
    return YOGINI_ORDER[(index + 1) % 8]


def _find_covering(periods: list[dict], moment: datetime) -> dict:
    for period in periods:
        if period["start"] <= moment < period["end"]:
            return period

    if moment < periods[0]["start"]:
        return periods[0]

    return periods[-1]


def _serialise(period: dict) -> dict:
    return {
        "yogini": period["yogini"],
        "lord": YOGINI_LORDS[period["yogini"]],
        "start": period["start"].isoformat(),
        "end": period["end"].isoformat(),
    }


def build_yogini_dasha(
    sidereal_chart: dict,
    birth_utc_time: datetime,
    as_of_utc_time: datetime,
) -> dict:
    """
    Compute the full birth-to-36-year Yogini sequence from an
    already-built sidereal chart, plus the Yogini active at
    as_of_utc_time.
    """

    moon = sidereal_chart["bodies"]["moon"]
    moon_longitude = moon["longitude"]

    nakshatra_index = int(moon_longitude // NAKSHATRA_SPAN)
    fraction_elapsed = (moon_longitude % NAKSHATRA_SPAN) / NAKSHATRA_SPAN

    starting = starting_yogini(nakshatra_index)
    starting_balance_years = YOGINI_YEARS[starting] * (1 - fraction_elapsed)

    periods = []
    yogini = starting
    cursor = birth_utc_time
    years = starting_balance_years

    for _ in range(8):
        start = cursor
        end = cursor + timedelta(days=years * YEAR_DAYS)
        periods.append({"yogini": yogini, "start": start, "end": end, "years": years})
        cursor = end
        yogini = _next_yogini(yogini)
        years = YOGINI_YEARS[yogini]

    current = _find_covering(periods, as_of_utc_time)

    return {
        "as_of_utc_time": as_of_utc_time.isoformat(),
        "birth_nakshatra": NAKSHATRAS[nakshatra_index],
        "starting_yogini": starting,
        "starting_balance_years": starting_balance_years,
        "yogini_sequence": [_serialise(p) for p in periods],
        "current_yogini_dasha": _serialise(current),
    }


if __name__ == "__main__":
    from datetime import timezone

    from astrology.chart import build_chart
    from astrology.sidereal import build_sidereal_chart
    from astrology.time import local_to_utc

    # Worked-example checks: nakshatra 1 (Ashwini) -> (1+3)%8=4 ->
    # Bhramari. Nakshatra 5 (Mrigashira) -> (5+3)%8=0 -> Sankata (the
    # remainder-0 case). Nakshatra 27 (Revati) -> (27+3)%8=6 -> Ulka.
    assert starting_yogini(0) == "Bhramari"
    assert starting_yogini(4) == "Sankata"
    assert starting_yogini(26) == "Ulka"
    assert TOTAL_YEARS == 36

    print("Worked-example checks passed.")
    print()

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    birth_utc = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    tropical = build_chart(birth_utc, -37.7392, 144.7967, house_system="placidus")
    sidereal = build_sidereal_chart(tropical)

    as_of = datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)
    dasha = build_yogini_dasha(sidereal, birth_utc, as_of)

    print(f"Birth nakshatra: {dasha['birth_nakshatra']}")
    print(
        f"Starting Yogini: {dasha['starting_yogini']} "
        f"(balance {dasha['starting_balance_years']:.2f} years)"
    )
    print()
    print("Yogini sequence:")
    for period in dasha["yogini_sequence"]:
        print(f"  {period['yogini']:8s} {period['start'][:10]} -> {period['end'][:10]}")

    print()
    print(f"As of {as_of.date()}: {dasha['current_yogini_dasha']}")
