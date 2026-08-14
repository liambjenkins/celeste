"""
Celeste timing-technique knowledge seed: transits and secondary
progressions.

Scoped deliberately to what can be honestly sourced. Robert Hand's
"Planets in Transit" (1976) is the standard reference for full
transit-by-transit delineations (720 of them — every transiting
planet's aspect to every natal planet/angle, and every planet
transiting every house) but this project doesn't have that text in
hand to curate accurately from, and generating 720 specific
delineations from training-data recall alone would risk inventing
content not actually in the source — exactly what this project's
sourcing discipline exists to prevent.

What IS safely, generally true and well documented is:
  - what a transit is and how it's read (general technique)
  - what a secondary progression is and how it's read (general
    technique)
  - the progressed Moon's role as the technique's classical focus

Source for all of the above: Bernadette Brady, Predictive Astrology:
The Eagle and the Lark (1992) — a standard modern reference covering
both techniques with explicit technique-level guidance (verified via
web search during curation, not recalled from training).

The specific meaning of EACH aspect type (square, trine, ...) already
exists as a real, generic, source-backed claim (astrology.py's
_ASPECTS, Lilly 1647) and has been extended in this session to also
match transit_aspect:/progression_aspect: feature tags — so a
transiting square or a progressed trine already resolves to real
content without duplicating it here.

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


_add(
    "transit_technique_core",
    "A transit is the present position of a planet compared against "
    "the birth chart — where that planet is moving right now, read "
    "against where it was fixed at birth. The slower a transiting "
    "planet moves, the longer and broader the period it marks; the "
    "faster it moves, the shorter and more specific the window.",
    concept_ids=["current_transits"],
    feature_ids=["timing:transits"],
    theme_tags=["timing_and_technique"],
    life_domain="cyclicality",
    source_id="brady_predictive_astrology_1992",
)

_add(
    "progression_technique_core",
    "A secondary progression symbolically advances the birth chart "
    "by one day for each year of life, on the principle that the "
    "planetary motion of the days just after birth encodes the "
    "unfolding of the life that follows. It reads as a slow internal "
    "development, distinct from a transit's external, present-tense "
    "trigger.",
    concept_ids=["secondary_progressions"],
    feature_ids=["timing:secondary_progressions"],
    theme_tags=["timing_and_technique"],
    life_domain="cyclicality",
    source_id="brady_predictive_astrology_1992",
)

_ZODIAC_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

_add(
    "progressed_moon_core",
    "The progressed Moon is the classical focus of secondary "
    "progression: moving roughly one degree a day, it changes sign "
    "about every two and a half years, marking the current emotional "
    "and developmental chapter more precisely than any other "
    "progressed body.",
    concept_ids=["secondary_progressions"],
    feature_ids=[f"progressed_sign:moon:{sign}" for sign in _ZODIAC_SIGNS],
    theme_tags=["timing_and_technique", "emotional_depth"],
    life_domain="emotion",
    source_id="brady_predictive_astrology_1992",
)

# ------------------------------------------------------------
# Tertiary progressions
# Source: Garth Allen (originator of the technique) as documented in
# Astrodienst's Astrowiki (astro.com/astrowiki/en/Tertiary_Progression)
# and cross-referenced against Solunars/Aldebaran Sidereal Academy
# discussion of the same technique (verified via search during
# curation). Matched via tertiary_moon_sign: tags — the tertiary-
# progressed Moon, like the secondary-progressed Moon above, is the
# technique's most commonly read point.
# ------------------------------------------------------------

_add(
    "tertiary_technique_core",
    "A tertiary progression symbolically advances the birth chart by "
    "one day for each sidereal month (about 27.3 days) of life — "
    "roughly twelve times faster than a secondary progression's one "
    "day per year. It reads as a fast, month-by-month unfolding, "
    "prized for timing the specific month of a shift that a "
    "secondary progression only marks in broad, year-scale strokes.",
    concept_ids=["tertiary_progressions"],
    feature_ids=[
        f"tertiary_moon_sign:{sign}" for sign in _ZODIAC_SIGNS
    ],
    theme_tags=["timing_and_technique", "emotional_depth"],
    life_domain="cyclicality",
    source_id="allen_tertiary_progressions_astrowiki",
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
        source = claim.source_ids[0] if claim.source_ids else "none"
        by_source[source] = by_source.get(source, 0) + 1

    for source, count in sorted(by_source.items()):
        print(f"  {count:3} claims — {source}")
