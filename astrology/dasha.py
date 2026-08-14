"""
Vimshottari Dasha: the classical Vedic planetary-period timing
system, layered on an already-computed sidereal chart (like Navamsa
and the curated yogas) — not new astronomy.

A fixed 120-year cycle is divided among the nine grahas in a fixed
sequence and fixed proportion:
    Ketu 7, Venus 20, Sun 6, Moon 10, Mars 7, Rahu 18, Jupiter 16,
    Saturn 19, Mercury 17 (= 120 years total).

Entered at birth according to which nakshatra (lunar mansion) the
Moon occupies: the nakshatra's ruling planet — the same Vimshottari
lord cycle already documented in
knowledge/claims/seeds/vedic_astrology.py (Ashwini=Ketu, Bharani=
Venus, ... repeating every 9 nakshatras) — is the starting Mahadasha
lord, and the BALANCE of that first Mahadasha (how much of its full
period remains) is proportional to how far the Moon has already
progressed through that nakshatra at birth. Every Mahadasha lord's
own period is further subdivided among all nine planets in the same
fixed order for its Antardashas (sub-periods), each lasting
(mahadasha_years * antardasha_lord_years / 120).

Year length: 365.25 days (the modern standard convention — verified
via search; the older 360-day 'savana' convention drifts by roughly
100 days over a 19-year Saturn Mahadasha and is not what contemporary
reference calculators use).
"""

from datetime import datetime, timedelta

from astrology.sidereal import NAKSHATRA_SPAN, NAKSHATRAS

VIMSHOTTARI_ORDER = (
    "ketu", "venus", "sun", "moon", "mars",
    "rahu", "jupiter", "saturn", "mercury",
)

VIMSHOTTARI_YEARS = {
    "ketu": 7, "venus": 20, "sun": 6, "moon": 10, "mars": 7,
    "rahu": 18, "jupiter": 16, "saturn": 19, "mercury": 17,
}

TOTAL_YEARS = sum(VIMSHOTTARI_YEARS.values())  # 120

YEAR_DAYS = 365.25


def nakshatra_lord(nakshatra_index: int) -> str:
    """The Vimshottari dasha lord that rules a given nakshatra (0-26)."""
    return VIMSHOTTARI_ORDER[nakshatra_index % 9]


def _next_lord(lord: str) -> str:
    index = VIMSHOTTARI_ORDER.index(lord)
    return VIMSHOTTARI_ORDER[(index + 1) % 9]


def _sub_periods(parent_lord: str, parent_start: datetime, parent_years: float) -> list[dict]:
    """
    Subdivide a period among all nine planets in Vimshottari order,
    starting with the parent's own lord — used for both Antardashas
    (within a Mahadasha) and, when called again, could extend to
    Pratyantardashas, though only one level deep is computed here.
    """

    periods = []
    lord = parent_lord
    cursor = parent_start

    for _ in range(9):
        years = parent_years * VIMSHOTTARI_YEARS[lord] / TOTAL_YEARS
        start = cursor
        end = cursor + timedelta(days=years * YEAR_DAYS)
        periods.append({"lord": lord, "start": start, "end": end, "years": years})
        cursor = end
        lord = _next_lord(lord)

    return periods


def _find_covering(periods: list[dict], moment: datetime) -> dict:
    for period in periods:
        if period["start"] <= moment < period["end"]:
            return period

    if moment < periods[0]["start"]:
        return periods[0]

    return periods[-1]


def _serialise(period: dict) -> dict:
    return {
        "lord": period["lord"],
        "start": period["start"].isoformat(),
        "end": period["end"].isoformat(),
    }


def build_vimshottari_dasha(
    sidereal_chart: dict,
    birth_utc_time: datetime,
    as_of_utc_time: datetime,
) -> dict:
    """
    Compute the full birth-to-120-year Mahadasha sequence from an
    already-built sidereal chart, plus the Mahadasha and Antardasha
    active at as_of_utc_time.
    """

    moon = sidereal_chart["bodies"]["moon"]
    moon_longitude = moon["longitude"]

    nakshatra_index = int(moon_longitude // NAKSHATRA_SPAN)
    fraction_elapsed = (moon_longitude % NAKSHATRA_SPAN) / NAKSHATRA_SPAN

    starting_lord = nakshatra_lord(nakshatra_index)
    starting_balance_years = VIMSHOTTARI_YEARS[starting_lord] * (1 - fraction_elapsed)

    mahadashas = []
    lord = starting_lord
    cursor = birth_utc_time
    years = starting_balance_years

    for _ in range(9):
        start = cursor
        end = cursor + timedelta(days=years * YEAR_DAYS)
        mahadashas.append({"lord": lord, "start": start, "end": end, "years": years})
        cursor = end
        lord = _next_lord(lord)
        years = VIMSHOTTARI_YEARS[lord]

    current_mahadasha = _find_covering(mahadashas, as_of_utc_time)
    antardashas = _sub_periods(
        current_mahadasha["lord"],
        current_mahadasha["start"],
        current_mahadasha["years"],
    )
    current_antardasha = _find_covering(antardashas, as_of_utc_time)

    return {
        "as_of_utc_time": as_of_utc_time.isoformat(),
        "birth_nakshatra": NAKSHATRAS[nakshatra_index],
        "starting_mahadasha_lord": starting_lord,
        "starting_balance_years": starting_balance_years,
        "mahadasha_sequence": [_serialise(m) for m in mahadashas],
        "current_mahadasha": _serialise(current_mahadasha),
        "current_antardasha": _serialise(current_antardasha),
    }


if __name__ == "__main__":
    from datetime import timezone

    from astrology.chart import build_chart
    from astrology.sidereal import build_sidereal_chart
    from astrology.time import local_to_utc

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
    dasha = build_vimshottari_dasha(sidereal, birth_utc, as_of)

    print(f"Birth nakshatra: {dasha['birth_nakshatra']}")
    print(
        f"Starting Mahadasha lord: {dasha['starting_mahadasha_lord']} "
        f"(balance {dasha['starting_balance_years']:.2f} years)"
    )
    print()
    print("Mahadasha sequence:")
    for maha in dasha["mahadasha_sequence"]:
        print(f"  {maha['lord']:8s} {maha['start'][:10]} -> {maha['end'][:10]}")

    print()
    print(f"As of {as_of.date()}:")
    print(f"  Mahadasha:  {dasha['current_mahadasha']}")
    print(f"  Antardasha: {dasha['current_antardasha']}")
