"""
Jaimini Chara Dasha: the signature sign-based (not planet-based) Vedic
timing system of the Jaimini school of astrology, layered on an
already-computed sidereal chart.

Genuinely more complex and more contested across sources than
Vimshottari or Yogini Dasha -- this implementation follows the reading
most consistently corroborated across independent sources checked
during curation, with the specific point of residual disagreement
documented below rather than hidden.

Two SEPARATE direction concepts are involved, easy to conflate (and
several secondary sources online do conflate them):
  1. SEQUENCE direction -- which sign follows which in the 12-sign
     Mahadasha sequence. Fixed once for the whole sequence, by the
     Ascendant (Lagna) sign's plain odd/even sign number: odd Lagna
     (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius) -> sequence
     runs forward through the zodiac from the Lagna sign; even Lagna
     -> backward.
  2. PER-SIGN YEAR-COUNT direction -- for each individual sign in that
     sequence, how many years IT rules is found by counting
     (inclusively) from that sign to the sign its own lord currently
     occupies, then subtracting 1 (0 becomes 12, when the lord sits in
     its own sign). This count's direction depends on that sign's own
     "footedness", a DIFFERENT odd/even-style grouping than plain sign
     parity: odd-footed (Aries, Taurus, Gemini, Libra, Scorpio,
     Sagittarius) counts forward; even-footed (Cancer, Leo, Virgo,
     Capricorn, Aquarius, Pisces) counts backward.

Dignity adjustment (a sign whose lord is exalted gains a year; whose
lord is debilitated loses a year, years floored at 1) is applied here
because it was the majority reading across sources checked during
curation -- but one otherwise-detailed source explicitly denied any
such adjustment exists. Flagged here as the one point of real residual
disagreement found, rather than silently picking a side. Reuses
astrology.dignity.classify_dignity (the F4 dignity foundation) for
this check.

Only the main (sign-Mahadasha) level is computed -- classical
technique also has Chara Antardasha sub-periods, left out of this pass
as further depth, same discipline this project applies to Yogini
Dasha's sub-periods. If as_of_utc_time falls beyond the single 12-sign
sequence computed from birth (which, unlike Vimshottari's fixed 120
years, can total anywhere from 12 to 144 years depending on the
chart), the last sign period in the sequence is returned rather than
cycling -- the same simplification astrology.dasha's Vimshottari
already uses for a moment beyond its own computed range.
"""

from datetime import datetime, timedelta

from astrology.dignity import TRADITIONAL_RULERS, classify_dignity

ZODIAC_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

_ODD_FOOTED = {0, 1, 2, 6, 7, 8}     # Aries, Taurus, Gemini, Libra, Scorpio, Sagittarius
_EVEN_FOOTED = {3, 4, 5, 9, 10, 11}  # Cancer, Leo, Virgo, Capricorn, Aquarius, Pisces

YEAR_DAYS = 365.25


def _is_odd_sign(sign_index: int) -> bool:
    return sign_index % 2 == 0  # Aries (index 0) is the 1st, an odd sign


def _count_inclusive(from_index: int, to_index: int, forward: bool) -> int:
    if forward:
        return ((to_index - from_index) % 12) + 1
    return ((from_index - to_index) % 12) + 1


def sign_years(sign_index: int, sidereal_chart: dict) -> int:
    """Years the sign at sign_index rules, per its own footedness and lord's dignity."""

    lord = TRADITIONAL_RULERS[ZODIAC_SIGNS[sign_index]]
    lord_body = sidereal_chart["bodies"][lord]
    lord_sign_index = lord_body["sign_index"]

    forward = sign_index in _ODD_FOOTED
    count = _count_inclusive(sign_index, lord_sign_index, forward)
    years = count - 1

    if years == 0:
        years = 12

    degree_in_sign = lord_body["longitude"] % 30.0
    dignity = classify_dignity(lord, ZODIAC_SIGNS[lord_sign_index], degree_in_sign)

    if dignity == "exalted":
        years += 1
    elif dignity == "debilitated":
        years -= 1

    return max(years, 1)


def _find_covering(periods: list[dict], moment: datetime) -> dict:
    for period in periods:
        if period["start"] <= moment < period["end"]:
            return period

    if moment < periods[0]["start"]:
        return periods[0]

    return periods[-1]


def _serialise(period: dict) -> dict:
    return {
        "sign": period["sign"],
        "start": period["start"].isoformat(),
        "end": period["end"].isoformat(),
        "years": period["years"],
    }


def build_chara_dasha(
    sidereal_chart: dict,
    birth_utc_time: datetime,
    as_of_utc_time: datetime,
) -> dict:
    """
    Compute the full 12-sign Chara Dasha sequence from birth, plus the
    sign-Mahadasha active at as_of_utc_time.
    """

    ascendant_sign_index = sidereal_chart["ascendant"]["sign_index"]
    forward = _is_odd_sign(ascendant_sign_index)

    sequence = []
    cursor = birth_utc_time
    sign_index = ascendant_sign_index

    for _ in range(12):
        years = sign_years(sign_index, sidereal_chart)
        start = cursor
        end = cursor + timedelta(days=years * YEAR_DAYS)
        sequence.append(
            {"sign": ZODIAC_SIGNS[sign_index], "start": start, "end": end, "years": years}
        )
        cursor = end
        sign_index = (sign_index + 1) % 12 if forward else (sign_index - 1) % 12

    current = _find_covering(sequence, as_of_utc_time)

    return {
        "as_of_utc_time": as_of_utc_time.isoformat(),
        "sequence_direction": "forward" if forward else "backward",
        "sign_sequence": [_serialise(p) for p in sequence],
        "current_sign_dasha": _serialise(current),
    }


if __name__ == "__main__":
    from datetime import timezone

    from astrology.chart import build_chart
    from astrology.sidereal import build_sidereal_chart
    from astrology.time import local_to_utc

    # Worked-example checks (from the module's own stated rule, since
    # no independently-sourced numeric worked example was found during
    # curation for this genuinely more contested technique):
    #   - Forward count, sign 0 (Aries) to sign 0 (lord in own sign)
    #     -> count 1 -> years 0 -> replaced by 12.
    assert _count_inclusive(0, 0, forward=True) == 1
    #   - Forward count, Aries(0) to Capricorn(9) -> 10 signs
    #     inclusive -> years 9.
    assert _count_inclusive(0, 9, forward=True) == 10
    #   - Backward count, Cancer(3, even-footed) to Aries(0) -> counts
    #     Cancer, Gemini, Taurus, Aries = 4 -> years 3.
    assert _count_inclusive(3, 0, forward=False) == 4

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
    dasha = build_chara_dasha(sidereal, birth_utc, as_of)

    print(f"Sequence direction: {dasha['sequence_direction']}")
    print()
    print("Sign sequence:")
    for period in dasha["sign_sequence"]:
        print(
            f"  {period['sign']:12s} {period['start'][:10]} -> "
            f"{period['end'][:10]} ({period['years']}y)"
        )

    print()
    print(f"As of {as_of.date()}: {dasha['current_sign_dasha']}")
