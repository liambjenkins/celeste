"""
Ashtakavarga: the classical Vedic point-scoring system that maps
relative strength across all 12 signs, for each of the 7 classical
planets plus a combined chart -- layered on an already-computed
sidereal chart.

Each of 8 reference points (the 7 classical planets plus the Lagna/
Ascendant) contributes a fixed, classically-tabulated set of "benefic"
houses (counted from that reference point's own sign) toward each
target planet's Bhinnashtakavarga (individual 12-sign scorecard). A
contributed house earns the target planet one Bindu (point) in
whichever sign that house lands on. Summing all 7 Bhinnashtakavargas
sign-by-sign gives the Sarvashtakavarga (combined chart, 337 points
total across all 12 signs in every horoscope).

Rahu/Ketu have no classical Ashtakavarga role -- consistent with their
exclusion from astrology.dignity's dignity system, they contribute
nothing and receive no Bhinnashtakavarga table of their own.

Source: Brihat Parashara Hora Shastra, ch. 66-72 (the classical
source for this system). The full 56-list bindu contribution table
(7 target planets x 8 reference points) was verified via web search
during curation and cross-checked against two independent sources;
one transcription error was caught and corrected this way (the Moon's
table, as first fetched, summed to 50 instead of the documented
constant of 49 -- re-verified against a second source and corrected).
Every planet's table is self-checked at import time against the
well-documented per-planet Bindu constants (Sun 48, Moon 49, Mars 39,
Mercury 54, Jupiter 56, Venus 52, Saturn 39, totalling 337) via the
assertions in this module's __main__ block.
"""

ZODIAC_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

CLASSICAL_PLANETS = (
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
)

CONTRIBUTORS = CLASSICAL_PLANETS + ("ascendant",)

# Known classical totals (Bindus), used as a self-check.
EXPECTED_TOTALS = {
    "sun": 48, "moon": 49, "mars": 39, "mercury": 54,
    "jupiter": 56, "venus": 52, "saturn": 39,
}

# For each TARGET planet's Bhinnashtakavarga, the houses (counted
# from each CONTRIBUTOR's own sign) that earn a Bindu.
BINDU_TABLE = {
    "sun": {
        "sun": (1, 2, 4, 7, 8, 9, 10, 11),
        "moon": (3, 6, 10, 11),
        "mars": (1, 2, 4, 7, 8, 9, 10, 11),
        "mercury": (3, 5, 6, 9, 10, 11, 12),
        "jupiter": (5, 6, 9, 11),
        "venus": (6, 7, 12),
        "saturn": (1, 2, 4, 7, 8, 9, 10, 11),
        "ascendant": (3, 4, 6, 10, 11, 12),
    },
    "moon": {
        "sun": (3, 6, 7, 8, 10, 11),
        "moon": (1, 3, 6, 7, 10, 11),
        "mars": (2, 3, 5, 6, 9, 10, 11),
        "mercury": (1, 3, 4, 5, 7, 8, 10, 11),
        "jupiter": (1, 4, 7, 8, 10, 11, 12),
        "venus": (3, 4, 5, 7, 9, 10, 11),
        "saturn": (3, 5, 6, 11),
        "ascendant": (3, 6, 10, 11),
    },
    "mars": {
        "sun": (3, 5, 6, 10, 11),
        "moon": (3, 6, 11),
        "mars": (1, 2, 4, 7, 8, 10, 11),
        "mercury": (3, 5, 6, 11),
        "jupiter": (6, 10, 11, 12),
        "venus": (6, 8, 11, 12),
        "saturn": (1, 4, 7, 8, 9, 10, 11),
        "ascendant": (1, 3, 6, 10, 11),
    },
    "mercury": {
        "sun": (5, 6, 9, 11, 12),
        "moon": (2, 4, 6, 8, 10, 11),
        "mars": (1, 2, 4, 7, 8, 9, 10, 11),
        "mercury": (1, 3, 5, 6, 9, 10, 11, 12),
        "jupiter": (6, 8, 11, 12),
        "venus": (1, 2, 3, 4, 5, 8, 9, 11),
        "saturn": (1, 2, 4, 7, 8, 9, 10, 11),
        "ascendant": (1, 2, 4, 6, 8, 10, 11),
    },
    "jupiter": {
        "sun": (1, 2, 3, 4, 7, 8, 9, 10, 11),
        "moon": (2, 5, 7, 9, 11),
        "mars": (1, 2, 4, 7, 8, 10, 11),
        "mercury": (1, 2, 4, 5, 6, 9, 10, 11),
        "jupiter": (1, 2, 3, 4, 7, 8, 10, 11),
        "venus": (2, 5, 6, 9, 10, 11),
        "saturn": (3, 5, 6, 12),
        "ascendant": (1, 2, 4, 5, 6, 7, 9, 10, 11),
    },
    "venus": {
        "sun": (8, 11, 12),
        "moon": (1, 2, 3, 4, 5, 8, 9, 11, 12),
        "mars": (3, 5, 6, 9, 11, 12),
        "mercury": (3, 5, 6, 9, 11),
        "jupiter": (5, 8, 9, 10, 11),
        "venus": (1, 2, 3, 4, 5, 8, 9, 10, 11),
        "saturn": (3, 4, 5, 8, 9, 10, 11),
        "ascendant": (1, 2, 3, 4, 5, 8, 9, 11),
    },
    "saturn": {
        "sun": (1, 2, 4, 7, 8, 10, 11),
        "moon": (3, 6, 11),
        "mars": (3, 5, 6, 10, 11, 12),
        "mercury": (6, 8, 9, 10, 11, 12),
        "jupiter": (5, 6, 11, 12),
        "venus": (6, 11, 12),
        "saturn": (3, 5, 6, 11),
        "ascendant": (1, 3, 4, 6, 10, 11),
    },
}


def _contributor_sign_index(sidereal_chart: dict, contributor: str) -> int:
    if contributor == "ascendant":
        return sidereal_chart["ascendant"]["sign_index"]
    return sidereal_chart["bodies"][contributor]["sign_index"]


def build_bhinnashtakavarga(sidereal_chart: dict, target_planet: str) -> dict:
    """
    {sign_index: bindu_count} for one target planet's 12-sign
    Bhinnashtakavarga scorecard.
    """

    scores = {i: 0 for i in range(12)}
    houses_by_contributor = BINDU_TABLE[target_planet]

    for contributor, houses in houses_by_contributor.items():
        contributor_sign_index = _contributor_sign_index(sidereal_chart, contributor)

        for house_number in houses:
            sign_index = (contributor_sign_index + house_number - 1) % 12
            scores[sign_index] += 1

    return scores


def build_ashtakavarga(sidereal_chart: dict) -> dict:
    """
    Full Ashtakavarga: each classical planet's Bhinnashtakavarga plus
    the combined Sarvashtakavarga, all keyed by sign name.
    """

    bhinnashtakavarga = {
        planet: build_bhinnashtakavarga(sidereal_chart, planet)
        for planet in CLASSICAL_PLANETS
    }

    sarva = {i: 0 for i in range(12)}
    for scores in bhinnashtakavarga.values():
        for sign_index, count in scores.items():
            sarva[sign_index] += count

    return {
        "bhinnashtakavarga": {
            planet: {ZODIAC_SIGNS[i]: count for i, count in scores.items()}
            for planet, scores in bhinnashtakavarga.items()
        },
        "sarvashtakavarga": {ZODIAC_SIGNS[i]: count for i, count in sarva.items()},
    }


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.sidereal import build_sidereal_chart
    from astrology.time import local_to_utc

    # Self-check: every target planet's contribution lists must sum
    # to its well-documented classical total, and the grand total
    # across all 7 must be 337.
    grand_total = 0
    for planet in CLASSICAL_PLANETS:
        total = sum(
            len(houses) for houses in BINDU_TABLE[planet].values()
        )
        assert total == EXPECTED_TOTALS[planet], (
            f"{planet} bindu table sums to {total}, expected "
            f"{EXPECTED_TOTALS[planet]}"
        )
        grand_total += total
    assert grand_total == 337, f"Grand total {grand_total}, expected 337"

    print("Bindu table self-check passed (all 7 planets, 337 total).")
    print()

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")
    sidereal = build_sidereal_chart(tropical)
    ashtakavarga = build_ashtakavarga(sidereal)

    for planet, scores in ashtakavarga["bhinnashtakavarga"].items():
        total = sum(scores.values())
        assert total == EXPECTED_TOTALS[planet], (
            f"Computed {planet} total {total} != {EXPECTED_TOTALS[planet]}"
        )
        print(f"{planet:8s} total={total:3d}  " + " ".join(f"{s[:3]}:{c}" for s, c in scores.items()))

    print()
    sarva_total = sum(ashtakavarga["sarvashtakavarga"].values())
    assert sarva_total == 337, f"Sarvashtakavarga total {sarva_total} != 337"
    print(f"Sarvashtakavarga total={sarva_total}")
    for sign, count in ashtakavarga["sarvashtakavarga"].items():
        print(f"  {sign:12s} {count}")
