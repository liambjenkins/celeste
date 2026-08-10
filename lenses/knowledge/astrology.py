"""
Celeste V1 — Astrology knowledge base.

This module stores curated traditional astrological associations.

Important:
- These are representations of an astrological tradition.
- They are not scientific claims.
- Claims must remain attributable to their tradition.
- Final editorial language does not belong here.
"""

from ..model import (
    InterpretiveRule,
    LensKnowledge,
    SourceClaim,
)


CLAIMS = (
    SourceClaim(
        claim_id="astrology_moon_cycle",
        statement=(
            "In traditional astrology, the Moon's phase and position "
            "are treated as symbolically significant indicators of "
            "cycles, change, timing, and fluctuating conditions."
        ),
        source=(
            "Traditional Western astrological literature concerning "
            "the Moon and lunar cycles."
        ),
        source_type="traditional_astrology",
        concepts=("moon",),
        notes=(
            "Represents a broad traditional association; the exact "
            "meaning depends on astrological school and technique."
        ),
    ),

    SourceClaim(
        claim_id="astrology_sun_cycle",
        statement=(
            "In traditional astrology, the Sun is associated with "
            "vitality, identity, illumination, and the ordering of "
            "the individual within a larger cosmic pattern."
        ),
        source=(
            "Traditional Western astrological literature concerning "
            "the Sun."
        ),
        source_type="traditional_astrology",
        concepts=("sun",),
        notes=(
            "Broad symbolic association rather than a scientific claim."
        ),
    ),

    SourceClaim(
        claim_id="astrology_planetary_relationships",
        statement=(
            "Traditional astrology interprets relationships between "
            "planets and their positions as symbolically meaningful "
            "patterns."
        ),
        source=(
            "Traditional Western astrological literature concerning "
            "planetary configurations and aspects."
        ),
        source_type="traditional_astrology",
        concepts=("planetary_positions",),
        notes=(
            "Specific interpretations depend on the planets, signs, "
            "houses, aspects, and astrological tradition involved."
        ),
    ),

    SourceClaim(
        claim_id="astrology_seasonal_cycle",
        statement=(
            "Astrological traditions commonly connect the annual solar "
            "cycle and seasonal turning points with symbolic themes "
            "of growth, culmination, decline, renewal, and transition."
        ),
        source=(
            "Traditional astrological treatment of the annual solar "
            "and seasonal cycle."
        ),
        source_type="traditional_astrology",
        concepts=("season", "sun"),
        notes=(
            "Seasonal symbolism varies across traditions and cultures."
        ),
    ),
)


RULES = (
    InterpretiveRule(
        rule_id="astrology_rule_moon",
        concept_ids=("moon",),
        claim_ids=("astrology_moon_cycle",),
        notes="Activate when lunar information is available.",
    ),

    InterpretiveRule(
        rule_id="astrology_rule_sun",
        concept_ids=("sun",),
        claim_ids=("astrology_sun_cycle",),
        notes="Activate when solar information is available.",
    ),

    InterpretiveRule(
        rule_id="astrology_rule_planets",
        concept_ids=("planetary_positions",),
        claim_ids=("astrology_planetary_relationships",),
        notes="Activate when planetary position data is available.",
    ),

    InterpretiveRule(
        rule_id="astrology_rule_season",
        concept_ids=("season", "sun"),
        claim_ids=("astrology_seasonal_cycle",),
        notes="Activate when seasonal or solar-cycle information is available.",
    ),
)


KNOWLEDGE = LensKnowledge(
    lens_id="astrology",
    claims=CLAIMS,
    rules=RULES,
)
