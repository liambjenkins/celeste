"""
Celeste Chinese astrology knowledge seed — Phase N3 additions:
Chinese (BaZi) structural findings (chinese.structural_findings) —
the Four-Pillars counterpart to astrology_structural_findings.py and
vedic_astrology_structural_findings.py. Same compositional
building-block pattern and sourcing discipline.

Run as a script to write ApprovedClaim JSON into
knowledge/claims/approved/.
"""

import json
from dataclasses import asdict
from pathlib import Path

from knowledge.claims.model import ApprovedClaim

APPROVED_DIR = Path(__file__).resolve().parent.parent / "approved"

claims: list[ApprovedClaim] = []

# All 10 possible Ten God classifications (chinese/ten_gods.py's
# _SAME_POLARITY and _DIFFERENT_POLARITY tables) — the repeated-Ten-
# God claim is generic across whichever ones actually repeat in a
# given chart, matching how every other "generic across every tag
# value" claim in this project (final_dispositor_core, house/bhava
# concentration) is written once rather than per instance.
_TEN_GODS = (
    "Friend", "Rob Wealth", "Eating God", "Hurting Officer",
    "Indirect Wealth", "Direct Wealth", "Seven Killings",
    "Direct Officer", "Indirect Resource", "Direct Resource",
)


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
            claim_id=f"chinese_zodiac_{claim_id}",
            lens_id="chinese_zodiac",
            statement=statement,
            concept_ids=tuple(concept_ids),
            feature_ids=tuple(feature_ids),
            source_ids=(source_id,),
            theme_tags=tuple(theme_tags),
            life_domain=life_domain,
            editorial_note=notes,
        )
    )


# Repeated Ten God — verified via search: repetition of a Ten God
# across a chart's stems is a recognized BaZi analytical
# consideration, read as emphasis rather than an automatic verdict
# (its ultimate meaning still depends on chart balance and exactly
# which pillars/positions it repeats in).
_add(
    "repeated_ten_god_core",
    (
        "The same Ten God classification repeats across two or more "
        "of this chart's stems — visible or hidden. Repetition creates "
        "real emphasis: that Ten God's theme (wealth, authority, "
        "output, resource, or companionship, depending on which one) "
        "isn't a passing note but a recurring pressure or resource "
        "this chart returns to more than once. How that emphasis "
        "actually plays out still depends on the chart's overall "
        "balance and exactly which pillars carry it, not on the "
        "repetition alone."
    ),
    concept_ids=["chinese_structural_findings"],
    feature_ids=[f"repeated_ten_god:{name.lower().replace(' ', '_')}" for name in _TEN_GODS],
    theme_tags=["structural_finding", "ten_god"],
    source_id="bazi_ten_gods_modern_convention",
)

# Guan Sha Hun Za (官殺混雜) — verified via search: a specifically
# named classical pattern, Direct Officer and Seven Killings both
# present without one clearly dominating. Framed here around its
# core, gender-neutral meaning (tension between two different modes
# of authority/pressure) rather than the more culturally specific
# marriage-vs-career gendered framing some modern sources add on top
# of it, since this project's Chinese pipeline treats gender as
# optional (only used elsewhere for the Yuan Chen Shen Sha).
_add(
    "guan_sha_hun_za",
    (
        "Both Direct Officer and Seven Killings appear in this chart "
        "without one clearly dominating — the classically named Guan "
        "Sha Hun Za (官殺混雜, 'Officer and Killings mixed') pattern. "
        "Direct Officer represents structured, rule-bound authority "
        "and expectation; Seven Killings represents a more relentless, "
        "unrestrained form of pressure and drive. Carrying both at "
        "once, without a clear tiebreaker elsewhere in the chart, "
        "reads as a genuine and ongoing tension between those two "
        "modes rather than a settled preference for one."
    ),
    concept_ids=["chinese_structural_findings", "chinese_ten_gods"],
    feature_ids=["guan_sha_hun_za:present"],
    theme_tags=["structural_finding", "ten_god"],
    life_domain="drive_and_ambition",
    source_id="guan_sha_hun_za_classical_convention",
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
