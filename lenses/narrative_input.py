"""
Narrative-synthesis input: gathers every claim actually resolved for
a real chart across all lenses, plus the cross-system convergence
narrative and elemental alignment, into one clean, structured text
block — the exact material a grounded-generation synthesis step is
allowed to draw on and nothing else.

This module does no synthesis itself. It only formats already-
resolved, already-approved claims (knowledge.claims.model.ApprovedClaim,
via lenses.pipeline.run_lenses) for a downstream prompt — the same
discipline as every other part of this pipeline: claims are pre-
written and pre-sourced, never generated here.
"""

import re
from dataclasses import dataclass

_SOURCE_YEAR_RE = re.compile(r"^(c\d{1,4}(st|nd|rd|th)?|\d{4})$")

_LENS_LABELS = {
    "astrology": "Western",
    "vedic_astrology": "Vedic",
    "chinese_zodiac": "Chinese",
}


def format_source(slug: str) -> str:
    """Turns a source_id slug (e.g. 'brennan_hellenistic_astrology_2017')
    into a readable citation ('Brennan Hellenistic Astrology (2017)')."""

    parts = slug.split("_")
    year = None

    if parts and _SOURCE_YEAR_RE.match(parts[-1]):
        year = parts[-1]
        parts = parts[:-1]

    words = [p.upper() if p.upper() in ("BPHS",) else p.capitalize() for p in parts]
    name = " ".join(words)

    return f"{name} ({year})" if year else name


@dataclass(frozen=True)
class NarrativeClaim:
    lens_id: str
    tradition: str
    claim_id: str
    statement: str
    source: str
    life_domain: str | None


def gather_narrative_claims(interpretations: dict) -> list[NarrativeClaim]:
    """
    interpretations: the dict returned by lenses.pipeline.run_lenses's
    second value, {lens_id: LensInterpretation}. Only the three
    tradition lenses with real claim content are included — cosmology/
    philosophy lenses with zero approved claims are naturally absent
    since they simply won't resolve anything.
    """

    claims = []

    for lens_id, label in _LENS_LABELS.items():
        interpretation = interpretations.get(lens_id)

        if not interpretation:
            continue

        for item in interpretation.relevant_claims:
            claim = item.claim
            source = format_source(claim.source_ids[0]) if claim.source_ids else "Uncited"

            claims.append(NarrativeClaim(
                lens_id=lens_id,
                tradition=label,
                claim_id=claim.claim_id,
                statement=claim.statement,
                source=source,
                life_domain=claim.life_domain,
            ))

    return claims


def render_narrative_input(
    interpretations: dict,
    cross_system_narrative: str = "",
    elemental_alignment: dict = None,
) -> str:
    """
    Formats gathered claims (grouped by tradition, then by
    life_domain) plus the cross-system narrative and elemental
    alignment summary into one plain-text block — the exact input a
    synthesis prompt is grounded against.
    """

    claims = gather_narrative_claims(interpretations)
    lines = []

    for lens_id, label in _LENS_LABELS.items():
        lens_claims = [c for c in claims if c.lens_id == lens_id]

        if not lens_claims:
            continue

        lines.append(f"## {label}")
        lines.append("")

        by_domain: dict[str, list] = {}

        for claim in lens_claims:
            by_domain.setdefault(claim.life_domain or "general", []).append(claim)

        for domain, domain_claims in by_domain.items():
            lines.append(f"### {domain.replace('_', ' ').title()}")

            for claim in domain_claims:
                lines.append(f"- CLAIM_ID: {claim.claim_id}")
                lines.append(f"  STATEMENT: {claim.statement}")
                lines.append(f"  SOURCE: {claim.source}")

            lines.append("")

    if cross_system_narrative:
        lines.append("## Cross-Tradition Synthesis")
        lines.append("")
        lines.append(cross_system_narrative)
        lines.append("")

    if elemental_alignment:
        lines.append("## Elemental Alignment")
        lines.append("")
        lines.append(f"Western dominant: {', '.join(elemental_alignment.get('western_dominant', []))}")
        lines.append(f"Vedic dominant: {', '.join(elemental_alignment.get('vedic_dominant', []))}")
        lines.append(f"Chinese dominant: {', '.join(elemental_alignment.get('chinese_dominant', []))}")

        if elemental_alignment.get("three_way_agreement"):
            lines.append(f"Three-way agreement: {', '.join(elemental_alignment['three_way_agreement'])}")

        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.sidereal import build_sidereal_chart
    from astrology.time import local_to_utc
    from chinese.pillars import build_four_pillars
    from chinese.ten_gods import build_ten_gods
    from chinese.elemental_balance import build_elemental_balance
    from concepts.normaliser import normalise_observations
    from lenses.pipeline import run_lenses
    from lenses.cross_system import build_cross_system_convergence
    from lenses.elemental_alignment import build_elemental_alignment

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")
    sidereal = build_sidereal_chart(tropical)
    four_pillars = build_four_pillars(tropical, local_time)
    ten_gods = build_ten_gods(
        four_pillars, four_pillars.day_master_element, four_pillars.day_master_polarity
    )
    chinese_balance = build_elemental_balance(four_pillars)

    observations = {
        "astrology": tropical,
        "vedic_astrology": sidereal,
        "chinese_pillars": four_pillars.to_dict(),
        "chinese_ten_gods": ten_gods,
    }

    normalised = normalise_observations(observations)
    features, interpretations = run_lenses(normalised)
    cross_system = build_cross_system_convergence(interpretations)
    alignment = build_elemental_alignment(tropical, sidereal, chinese_balance)

    text = render_narrative_input(interpretations, cross_system.narrative, alignment)

    print(text[:3000])
    print(f"\n... [{len(text)} characters total]")
