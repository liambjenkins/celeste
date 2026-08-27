"""
Vedic structural findings: the sidereal-chart counterpart to
astrology.structural_findings — chart-wide observations that
describe how several independently-computed placements relate as a
system, rather than attaching to one body alone.

Two detectors, verified via search during curation:

- Bhava concentration: the same "house stellium" logic as the
  Western detector, applied to the sidereal chart's bhavas.
- Vargottama: a planet occupying the same sign in both the D1
  (Rashi) and D9 (Navamsa) charts — classical Vedic technique,
  "best among the divisions," read as a significant strength-and-
  stability booster, EXCEPT when the shared D1 house is a Dusthana
  (6th/8th/12th) — sources are consistent that Vargottama there is
  read as difficult/unfavorable rather than strong, a real,
  documented exception captured explicitly here rather than
  flattened into a uniformly positive claim.
"""

from collections import defaultdict

# Mirrors astrology.structural_findings.CONCENTRATION_POINTS — the
# sidereal chart's equivalent set of significant points. Lagna is
# excluded for the same reason the Western Ascendant/MC are: it
# defines bhava 1's cusp by definition, which would make every chart
# trivially "concentrate" there.
CONCENTRATION_POINTS = (
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
    "uranus", "neptune", "pluto", "chiron",
    "north_node_true", "south_node_true", "lilith_true",
    "ceres", "pallas", "juno", "vesta",
)

BHAVA_CONCENTRATION_THRESHOLD = 3

DUSTHANA_HOUSES = (6, 8, 12)

# Vargottama is a classical technique for the 7 traditional grahas
# only (Rahu/Ketu are excluded from dignity elsewhere in this
# project for the same reason — no classical system for them, and
# later conventions disagree — kept consistent here).
_VARGOTTAMA_PLANETS = (
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
)


def find_bhava_concentrations(
    sidereal_bodies: dict, threshold: int = BHAVA_CONCENTRATION_THRESHOLD
) -> list[dict]:
    """Bhavas (houses) where 3+ significant points cluster together."""

    by_bhava = defaultdict(list)

    for name in CONCENTRATION_POINTS:
        body = sidereal_bodies.get(name)

        if body and body.get("house") is not None:
            by_bhava[body["house"]].append(name)

    return [
        {
            "finding": "bhava_concentration",
            "house": house,
            "points": sorted(members),
            "count": len(members),
        }
        for house, members in by_bhava.items()
        if len(members) >= threshold
    ]


def find_vargottama(sidereal_bodies: dict, navamsa_bodies: dict) -> list[dict]:
    """
    Planets sharing the same sign in D1 (sidereal Rashi) and D9
    (Navamsa). Flags separately when the D1 house is a Dusthana
    (6/8/12) — classically read as unfavorable there rather than
    strong, the opposite of Vargottama's usual meaning.
    """

    findings = []

    for name in _VARGOTTAMA_PLANETS:
        d1 = sidereal_bodies.get(name)
        d9 = navamsa_bodies.get(name)

        if not d1 or not d9:
            continue

        if d1.get("sign") and d1["sign"] == d9.get("sign"):
            findings.append({
                "finding": "vargottama",
                "planet": name,
                "sign": d1["sign"],
                "d1_house": d1.get("house"),
                "is_dusthana": d1.get("house") in DUSTHANA_HOUSES,
            })

    return findings


def find_vedic_structural_findings(sidereal_chart: dict, navamsa_chart: dict) -> dict:
    """
    Runs every Vedic structural detector and returns all findings
    together. sidereal_chart is astrology.sidereal.build_sidereal_chart's
    output; navamsa_chart is astrology.navamsa.build_navamsa_chart's.
    """

    return {
        "bhava_concentrations": find_bhava_concentrations(
            sidereal_chart.get("bodies", {})
        ),
        "vargottama": find_vargottama(
            sidereal_chart.get("bodies", {}), navamsa_chart.get("bodies", {})
        ),
    }


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.navamsa import build_navamsa_chart
    from astrology.sidereal import build_sidereal_chart
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")
    sidereal = build_sidereal_chart(tropical)
    navamsa = build_navamsa_chart(sidereal)

    findings = find_vedic_structural_findings(sidereal, navamsa)

    print("Bhava concentrations:")
    for f in findings["bhava_concentrations"]:
        print(f"  Bhava {f['house']}: {', '.join(f['points'])} ({f['count']})")

    print("\nVargottama:")
    if findings["vargottama"]:
        for f in findings["vargottama"]:
            note = "  ** Dusthana — unfavorable, not strong **" if f["is_dusthana"] else ""
            print(f"  {f['planet']} in {f['sign']} (D1 house {f['d1_house']}){note}")
    else:
        print("  None.")
