"""
Celeste Western astrology knowledge seed — Phase N1 additions:
structural findings (astrology.structural_findings). Same
compositional building-block pattern and sourcing discipline as
astrology_points.py/astrology.py.

Each claim here is generic across its whole finding TYPE (matching
however many houses/patterns/relationships actually fire for a given
chart), not written per specific chart — the same pattern already
used for final_dispositor_core, chart_shape, and the aspect-pattern
core-meaning claims.

Run as a script to write ApprovedClaim JSON into
knowledge/claims/approved/.
"""

import json
from dataclasses import asdict
from pathlib import Path

from knowledge.claims.model import ApprovedClaim

APPROVED_DIR = Path(__file__).resolve().parent.parent / "approved"

claims: list[ApprovedClaim] = []


def _add(
    claim_id,
    statement,
    concept_ids=(),
    feature_ids=(),
    theme_tags=(),
    life_domain=None,
    source_id="",
    notes="",
):
    claims.append(
        ApprovedClaim(
            claim_id=f"astrology_{claim_id}",
            lens_id="astrology",
            statement=statement,
            concept_ids=tuple(concept_ids),
            feature_ids=tuple(feature_ids),
            source_ids=(source_id,),
            theme_tags=tuple(theme_tags),
            life_domain=life_domain,
            editorial_note=notes,
        )
    )


# House concentration ("house stellium") — 3+ significant points
# sharing one house, regardless of sign. A real, standard technique
# distinct from a same-sign stellium (already covered by
# aspect_pattern:stellium): verified via search — a "house stellium"
# is established modern terminology, read as an intense concentration
# of life-area emphasis wherever it falls.
_add(
    "house_concentration_core",
    (
        "Three or more significant points sharing one house — a "
        "'house stellium' — mark an unusual concentration of life-area "
        "emphasis. Distinct from a same-sign stellium: points can "
        "share a house while spanning two different signs near a "
        "house-cusp boundary, so this catches a real clustering of "
        "focus a sign-only reading would miss. Whatever that house "
        "governs stops being one thread among several in the chart "
        "and becomes a genuinely central, load-bearing area of life."
    ),
    concept_ids=["structural_findings"],
    feature_ids=[f"house_concentration:{house}" for house in range(1, 13)],
    theme_tags=["structural_finding", "house_concentration"],
    source_id="structural_findings_modern_convention",
    notes=(
        "Threshold (3+ points) and the point set counted (10 "
        "planets, true nodes, Chiron, Lilith, the 4 main asteroids, "
        "Part of Fortune/Spirit) are this implementation's own "
        "reasoned choice — see astrology/structural_findings.py — "
        "not a claim to reproduce one single named authority's exact "
        "list. Angles (Ascendant/MC) are deliberately excluded: in a "
        "quadrant house system they sit on their own house cusp by "
        "definition, which would make every chart show a trivial "
        "'concentration' in houses 1 and 10 every time."
    ),
)

# T-square empty-leg match — the point opposite the apex ("the empty
# leg") coinciding, by sign, with another placement. Verified via
# search: the empty leg is standard T-square theory (the sign/house
# the pattern doesn't automatically develop, and where deliberate
# integration work pays off) — this claim covers the further, chart-
# specific case where something else already sits there.
_add(
    "pattern_empty_leg_core",
    (
        "A T-Square's 'empty leg' — the point directly opposite the "
        "apex, which the pattern's built-in tension doesn't "
        "automatically develop — happens to share a sign with another "
        "placement elsewhere in the chart. That's not automatic (most "
        "T-squares have no such match): when it happens, the "
        "deliberate integration work the T-square calls for is "
        "pointed at a specific, otherwise-unrelated part of the "
        "chart, rather than staying an abstract missing quality with "
        "nowhere concrete to land."
    ),
    concept_ids=["structural_findings", "aspect_patterns"],
    feature_ids=["pattern_empty_leg_match:t_square"],
    theme_tags=["structural_finding", "aspect_pattern"],
    source_id="structural_findings_modern_convention",
    notes=(
        "Same-SIGN coincidence, not a tight-orb conjunction at the "
        "exact empty-leg degree — a body sitting exactly at that "
        "degree would already register as a Grand Cross via the "
        "existing aspect-pattern detection, which this is "
        "deliberately distinct from and complementary to."
    ),
)

# Declination relationships — a parallel/contraparallel classified
# against the existing longitude aspect list. "Reinforces" needs no
# new claim (the underlying aspect's own claim already covers the
# theme; the declination just adds confidence). "New information" is
# the genuinely new case: a real, close relationship the longitude
# aspects alone don't show at all.
_add(
    "declination_new_information_core",
    (
        "A parallel or contraparallel — declination-based aspects, a "
        "second axis of measurement entirely independent from "
        "zodiacal longitude — links two placements with no matching "
        "longitude aspect between them at all. That makes it "
        "genuinely new information rather than a second confirmation "
        "of something already visible: a real, close relationship "
        "between these two placements that an aspect grid alone would "
        "miss completely."
    ),
    concept_ids=["structural_findings", "declination_aspects"],
    feature_ids=["declination_relationship:new_information"],
    theme_tags=["structural_finding", "declination_aspect"],
    life_domain=None,
    source_id="structural_findings_modern_convention",
)

_add(
    "declination_reinforces_core",
    (
        "A parallel or contraparallel independently confirms an "
        "aspect already visible by zodiacal longitude between the "
        "same two placements — two different measurements, ecliptic "
        "longitude and declination, agreeing. That agreement is worth "
        "noting on its own: it makes the underlying aspect's theme "
        "more structurally reliable, not just a single coincidental "
        "alignment."
    ),
    concept_ids=["structural_findings", "declination_aspects"],
    feature_ids=["declination_relationship:reinforces"],
    theme_tags=["structural_finding", "declination_aspect"],
    life_domain=None,
    source_id="structural_findings_modern_convention",
)


def write_claims():
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)

    written = []

    for claim in claims:
        path = APPROVED_DIR / f"{claim.claim_id}.json"

        data = asdict(claim)
        data["status"] = "approved"

        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        written.append(path)

    return written


if __name__ == "__main__":
    print(f"Prepared {len(claims)} claims.")

    by_source = {}
    for claim in claims:
        for source_id in claim.source_ids:
            by_source[source_id] = by_source.get(source_id, 0) + 1

    for source_id, count in sorted(by_source.items()):
        print(f"  {source_id}: {count}")

    written = write_claims()
    print(f"\nWrote {len(written)} claim files to {APPROVED_DIR}")
