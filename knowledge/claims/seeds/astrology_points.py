"""
Celeste Western astrology knowledge seed — Phase F1 additions: Vertex,
minor aspects, aspect patterns, chart rulers, additional Hermetic
Lots, antiscia. Same compositional building-block pattern and
sourcing discipline as astrology.py/astrology_extended.py.

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


# ------------------------------------------------------------
# Vertex
# Source: Sasha Fenton & Jan Budkowski, Understanding the
# Astrological Vertex (2006) — a dedicated reference on this exact
# point, cross-referenced against the general "auxiliary Descendant /
# fated encounter" framing repeated across modern sources (verified
# via search during curation).
#
# Scoped to core meaning + house placement only. No per-sign claims:
# unlike Sun/Moon/Ascendant, there is no confirmed dedicated
# sign-by-sign Vertex reference — writing 12 sign claims without one
# would risk fabricating content this project's sourcing discipline
# exists to prevent.
# ------------------------------------------------------------

_add(
    "vertex_core",
    "The Vertex is a mathematically calculated point (where the "
    "ecliptic crosses the prime vertical), traditionally read as an "
    "'auxiliary Descendant' marking fated or karmic encounters — "
    "significant people or events that feel drawn into a life rather "
    "than chosen.",
    concept_ids=["vertex"],
    theme_tags=["fated_encounter"],
    life_domain="relationships",
    source_id="fenton_budkowski_vertex_2006",
)

_VERTEX_HOUSES = {
    5: "romance, creative self-expression, and pleasure",
    6: "daily work, service, and health",
    7: "partnership and one-to-one relationship",
    8: "shared resources, intimacy, and transformation",
}

for _house, _domain_text in _VERTEX_HOUSES.items():
    _add(
        f"vertex_house_{_house}",
        f"With the Vertex in the {_house}th house, fated encounters "
        f"most often arrive through {_domain_text}.",
        concept_ids=["vertex"],
        feature_ids=[f"vertex_house:{_house}"],
        theme_tags=["fated_encounter"],
        life_domain="relationships",
        source_id="fenton_budkowski_vertex_2006",
        notes=(
            "The Vertex most commonly falls in the 5th-8th houses "
            "for most latitudes; houses outside this range are real "
            "but rarer and not separately claimed here."
        ),
    )


# ------------------------------------------------------------
# Minor aspects — matched via the general minor_aspect: presence tag
# (any occurrence in the chart, opt-in via include_minor_aspects),
# same pattern as astrology.py's major-aspect claims.
# Source: standard modern astrological convention on minor aspects,
# cross-referenced across multiple sources during curation (verified
# via search, not recalled from training alone).
# ------------------------------------------------------------

_MINOR_ASPECTS = {
    "semisquare": (
        "a semisquare (45°) carries a challenging, stimulating "
        "friction between the two placements involved — like a "
        "square but more internal and less immediately obvious"
    ),
    "sesquiquadrate": (
        "a sesquiquadrate (135°) carries a nervous, irritable "
        "tension between the two placements involved, more prone "
        "to surface unpredictably than the steadier friction of a "
        "square"
    ),
    "septile": (
        "a septile (~51.43°) carries a subtle, somewhat mystical "
        "link between the two placements involved, often associated "
        "with an intuitive or spiritual sensitivity that resists "
        "direct explanation"
    ),
    "novile": (
        "a novile (40°) carries a quiet sense of initiation between "
        "the two placements involved — a new, unfolding relationship "
        "to that combination of energies, rather than a fully "
        "resolved one"
    ),
}

for _minor, _meaning in _MINOR_ASPECTS.items():
    _add(
        f"minor_aspect_{_minor}",
        f"A {_minor.capitalize()}: {_meaning}.",
        feature_ids=[f"minor_aspect:{_minor}"],
        theme_tags=["relationship_between_placements", "minor_aspect"],
        source_id="minor_aspects_modern_convention",
    )


# ------------------------------------------------------------
# Declination aspects (parallel / contraparallel)
# Source: standard modern astrological convention on declinations,
# cross-referenced across multiple sources during curation (verified
# via search).
# ------------------------------------------------------------

_add(
    "declination_parallel",
    "A parallel (two bodies sharing the same declination, same "
    "hemisphere) is traditionally read like a strong conjunction — "
    "a reinforcing link on a different axis (distance from the "
    "celestial equator) from the zodiac.",
    concept_ids=["declination_aspects"],
    feature_ids=["declination_aspect:parallel"],
    theme_tags=["relationship_between_placements", "declination_aspect"],
    source_id="declinations_modern_convention",
)

_add(
    "declination_contraparallel",
    "A contraparallel (two bodies sharing the same declination but "
    "in opposite hemispheres) is traditionally read like a weaker "
    "opposition — a subtler tension on the declination axis rather "
    "than the zodiac.",
    concept_ids=["declination_aspects"],
    feature_ids=["declination_aspect:contraparallel"],
    theme_tags=["relationship_between_placements", "declination_aspect"],
    source_id="declinations_modern_convention",
)


# ------------------------------------------------------------
# Antiscia / contra-antiscia
# Source: Firmicus Maternus, Matheseos Libri VIII (4th century CE) —
# the earliest detailed source, cross-referenced against consistent
# modern usage (verified via search). Scoped to core meaning only,
# for the same reason as the Vertex above: no confirmed dedicated
# sign-by-sign antiscia reference to draw from honestly.
# ------------------------------------------------------------

_add(
    "antiscion_core",
    "The antiscion is a 'hidden axis' mirror point across the "
    "solstice line (0 Cancer/0 Capricorn) — traditionally read as a "
    "quiet, blended echo of the mirrored body's themes, expressed "
    "less directly and less consciously than the body's own placement.",
    concept_ids=["antiscia"],
    theme_tags=["hidden_axis"],
    source_id="firmicus_maternus_matheseos_c4th",
)

_add(
    "contra_antiscion_core",
    "The contra-antiscion — the antiscion's exact opposite point, "
    "mirrored across the equinox axis (0 Aries/0 Libra) — is "
    "traditionally read as a hidden tension needing integration, "
    "rather than the antiscion's hidden harmony.",
    concept_ids=["antiscia"],
    theme_tags=["hidden_axis"],
    source_id="firmicus_maternus_matheseos_c4th",
)


# ------------------------------------------------------------
# Additional Hermetic (Panaretos) Lots — Eros, Necessity, Courage,
# Victory, Nemesis. Core meaning only (no per-sign delineations —
# unlike Fortune, these five don't have a dedicated sign-by-sign
# reference this project could verify).
# Source: the Hermetic/Panaretos lot tradition attributed to Hermes
# Trismegistus, as preserved and cross-referenced in modern
# Hellenistic astrology scholarship (verified via search during
# curation).
# ------------------------------------------------------------

_HERMETIC_LOTS = {
    "eros": (
        "The Lot of Eros (built from Venus and the Lot of Spirit) "
        "marks desire, attraction, and what draws the soul toward "
        "union — friendship and love in their most personally "
        "compelling form.",
        "values_and_desire",
    ),
    "necessity": (
        "The Lot of Necessity (built from Mercury and the Lot of "
        "Fortune) marks obligation and constraint — the areas of "
        "life where circumstance imposes its demands and "
        "adaptability is required.",
        "discipline",
    ),
    "courage": (
        "The Lot of Courage (built from Mars and the Lot of Fortune) "
        "marks boldness, physical energy, and assertive action — "
        "where the capacity for bravery and risk-taking shows itself.",
        "drive_and_ambition",
    ),
    "victory": (
        "The Lot of Victory (built from Jupiter and the Lot of "
        "Spirit) marks success and achievement — where recognition "
        "and the expansion of influence are most readily won.",
        "expansion_and_meaning",
    ),
    "nemesis": (
        "The Lot of Nemesis (built from Saturn and the Lot of "
        "Fortune) marks fate and consequence — where limitation, "
        "responsibility, and the weight of time shape experience "
        "most heavily.",
        "discipline",
    ),
}

for _lot, (_meaning, _domain) in _HERMETIC_LOTS.items():
    _add(
        f"part_of_{_lot}_core",
        _meaning,
        concept_ids=[f"part_of_{_lot}"],
        feature_ids=[f"sign:{_lot}:{sign}" for sign in (
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        )],
        theme_tags=["hermetic_lot"],
        life_domain=_domain,
        source_id="hermetic_panaretos_lots",
    )


# ------------------------------------------------------------
# Chart ruler by house + final dispositor
# Source: William Lilly, Christian Astrology (1647) — already the
# cited source for traditional rulership/dispositor technique
# elsewhere in this codebase.
# ------------------------------------------------------------

_add(
    "chart_ruler_core",
    "The chart ruler — the traditional ruler of the Ascendant sign — "
    "is a personal significator whose own sign, house, and "
    "condition describe how a person actually moves through the "
    "world, distinct from the Ascendant's outward first impression.",
    concept_ids=["rulership"],
    theme_tags=["chart_ruler"],
    life_domain="identity",
    source_id="lilly_christian_astrology_1647",
)

_RULER_HOUSES = {
    1: "the self directly — an unusually strong, self-directed expression of persona",
    2: "personal resources and self-worth",
    3: "communication and everyday learning",
    4: "home, family, and emotional foundation",
    5: "creative self-expression and pleasure",
    6: "daily work and service",
    7: "partnership and open relationship",
    8: "shared resources and transformation",
    9: "belief, higher learning, and travel",
    10: "public role and reputation",
    11: "community and group belonging",
    12: "solitude and the unconscious",
}

for _house, _domain_text in _RULER_HOUSES.items():
    _add(
        f"chart_ruler_house_{_house}",
        f"With the chart ruler in the {_house}th house, the outward "
        f"persona moves through the world by way of {_domain_text}.",
        concept_ids=["rulership"],
        feature_ids=[f"chart_ruler_house:{_house}"],
        theme_tags=["chart_ruler"],
        life_domain="identity",
        source_id="lilly_christian_astrology_1647",
    )

_add(
    "final_dispositor_core",
    "A final dispositor — a single planet, in its own sign, that "
    "every other planet's rulership chain eventually leads back to — "
    "acts as a real organizing anchor for the whole chart. Most "
    "charts don't have one; when present, it's a significant "
    "structural finding, not just another placement.",
    concept_ids=["rulership"],
    feature_ids=[
        f"final_dispositor:{p}" for p in
        ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn")
    ],
    theme_tags=["chart_ruler", "final_dispositor"],
    life_domain="identity",
    source_id="lilly_christian_astrology_1647",
)


# ------------------------------------------------------------
# Aspect patterns (Grand Trine, T-Square, Grand Cross, Yod, Kite,
# Mystic Rectangle, Stellium) and chart shape (Marc Edmund Jones).
# Source: standard modern astrological convention on aspect
# patterns, cross-referenced across multiple sources during
# curation (verified via search, not recalled from training alone).
# ------------------------------------------------------------

_ASPECT_PATTERNS = {
    "grand_trine": (
        "a closed triangle of three mutual trines, flowing with "
        "natural ease and talent between the three placements "
        "involved — sometimes so easy the gift goes undeveloped "
        "without deliberate effort"
    ),
    "t_square": (
        "an opposition with a third placement squaring both ends, "
        "creating a dynamic, action-forcing tension — the apex "
        "placement is where the pressure of the whole configuration "
        "tends to focus and demand resolution"
    ),
    "grand_cross": (
        "two oppositions mutually squared into a closed four-point "
        "configuration — sustained, structural tension pulling in "
        "four directions at once, demanding ongoing balance rather "
        "than a single resolution"
    ),
    "yod": (
        "two placements in sextile, both in quincunx to a third "
        "'apex' placement — sometimes called the 'Finger of Fate', "
        "pointing toward a specialized, adjustment-demanding purpose "
        "focused through the apex"
    ),
    "kite": (
        "a Grand Trine with a fourth placement opposing one corner "
        "and sextile the other two — the opposing placement gives "
        "the trine's easy flow a specific outlet and direction, "
        "turning talent into achievement"
    ),
    "mystic_rectangle": (
        "two oppositions linked by trines and sextiles into a closed "
        "rectangle — tension held in a stable, workable frame, "
        "combining the Grand Cross's structural tension with the "
        "Grand Trine's ease"
    ),
    "stellium": (
        "three or more placements concentrated in the same sign — "
        "an intense, single-minded focus on that sign's themes, "
        "often the chart's single most emphasized area"
    ),
}

for _pattern, _meaning in _ASPECT_PATTERNS.items():
    _add(
        f"aspect_pattern_{_pattern}",
        f"A {_pattern.replace('_', ' ').title()}: {_meaning}.",
        concept_ids=["aspect_patterns"],
        feature_ids=[f"aspect_pattern:{_pattern}"],
        theme_tags=["aspect_pattern"],
        source_id="aspect_patterns_modern_convention",
    )

_CHART_SHAPES = {
    "bundle": "energy concentrated tightly (within about a third of the wheel), a focused, specialized life with a narrow but deep range of concern",
    "bowl": "all placements within one half of the chart, a self-contained life oriented toward a defined project or purpose, spilling out from a sealed boundary",
    "locomotive": "placements spanning about two-thirds of the wheel with one wide empty gap, suggesting a strong, self-driven sense of purpose and direction",
    "splash": "placements distributed fairly evenly around the whole wheel, suggesting a multifaceted personality with wide-ranging interests rather than one central focus",
}

for _shape, _meaning in _CHART_SHAPES.items():
    _add(
        f"chart_shape_{_shape}",
        f"A {_shape.capitalize()}-shaped chart tends toward {_meaning}.",
        concept_ids=["chart_shape"],
        feature_ids=[f"chart_shape:{_shape}"],
        theme_tags=["chart_shape"],
        source_id="jones_chart_shapes_modern_convention",
        notes=(
            "Marc Edmund Jones' original chart-shape classification; "
            "this implementation's boundary rule is a documented "
            "computational approximation (see astrology/"
            "aspect_patterns.py), not an exact reproduction of "
            "Jones' method — a genuinely fuzzy judgment-call area "
            "even among professional astrologers."
        ),
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
