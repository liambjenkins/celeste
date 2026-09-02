"""
Celeste Vedic astrology knowledge seed — Phase N2 additions: Vedic
structural findings (astrology.vedic_structural_findings) — the
sidereal counterpart to astrology_structural_findings.py. Same
compositional building-block pattern and sourcing discipline.

Run as a script to write ApprovedClaim JSON into
knowledge/claims/approved/.
"""

import json
from dataclasses import asdict
from pathlib import Path

from knowledge.claims.model import ApprovedClaim

APPROVED_DIR = Path(__file__).resolve().parent.parent / "approved"

# Same disclosure the Western astrology seeds give every claim by
# default -- citation-audit gap found and fixed: this file's own
# _add() defaulted notes to "" instead, so a claim here with no
# explicit override (e.g. vargottama_favorable) shipped with no
# editorial_note at all despite carrying a real named source_id.
GENERAL_NOTE = (
    "Reflects a widely-repeated interpretation found throughout "
    "standard Vedic/Jyotish astrology literature, exemplified by (not "
    "claimed as a verbatim quotation of) the cited source."
)

claims: list[ApprovedClaim] = []


def _add(
    claim_id,
    statement,
    concept_ids=(),
    feature_ids=(),
    theme_tags=(),
    life_domain=None,
    source_id="",
    notes=GENERAL_NOTE,
):
    claims.append(
        ApprovedClaim(
            claim_id=f"vedic_astrology_{claim_id}",
            lens_id="vedic_astrology",
            statement=statement,
            concept_ids=tuple(concept_ids),
            feature_ids=tuple(feature_ids),
            source_ids=(source_id,),
            theme_tags=tuple(theme_tags),
            life_domain=life_domain,
            editorial_note=notes,
        )
    )


# Bhava concentration ("house stellium") — same technique as the
# Western house-concentration claim, applied to the sidereal chart's
# bhavas. Verified via search during the Western N1 pass; the
# underlying logic (3+ significant points sharing a house regardless
# of sign) transfers directly to bhavas.
_add(
    "bhava_concentration_core",
    (
        "Three or more significant points sharing one bhava mark an "
        "unusual concentration of life-area emphasis — distinct from "
        "planets simply sharing a rashi (sign), since points can "
        "share a bhava while spanning two different signs near a "
        "bhava-cusp boundary. Whatever that bhava governs stops being "
        "one thread among several and becomes a genuinely central, "
        "load-bearing area of life."
    ),
    concept_ids=["vedic_structural_findings"],
    feature_ids=[f"bhava_concentration:{house}" for house in range(1, 13)],
    theme_tags=["structural_finding", "bhava_concentration"],
    source_id="structural_findings_modern_convention",
    notes=(
        "Same threshold and point set as the Western house-"
        "concentration claim (see astrology/vedic_structural_"
        "findings.py) — Lagna excluded since it defines bhava 1's "
        "cusp by definition."
    ),
)

# Vargottama — verified via search: a planet in the same sign in D1
# and D9 is "best among the divisions," read as exceptionally stable
# and strong. Sources are consistent that the SAME condition in a
# Dusthana house (6th/8th/12th) is read as unfavorable instead — a
# real, documented exception, captured as its own separate claim
# rather than folded into (and contradicting) the favorable one.
_add(
    "vargottama_favorable",
    (
        "Vargottama — a planet occupying the same sign in both the D1 "
        "(Rasi) birth chart and the D9 (Navamsa) chart — is 'best "
        "among the divisions': the planet's outer expression (D1) and "
        "inner, soul-level nature (D9) are aligned, giving it unusual "
        "stability and doubled strength. Results connected to this "
        "planet tend to be consistent and reliable rather than "
        "fluctuating, including during its own Dasha periods."
    ),
    concept_ids=["vedic_structural_findings"],
    feature_ids=["vargottama:favorable"],
    theme_tags=["structural_finding", "vargottama"],
    life_domain="underlying_strength",
    source_id="vargottama_classical_convention",
)

_add(
    "vargottama_dusthana",
    (
        "This chart has a Vargottama planet (same sign in D1 and D9) "
        "sitting in a Dusthana house — the 6th, 8th, or 12th. Sources "
        "are consistent that Vargottama's usual meaning inverts here: "
        "rather than added strength and stability, the same doubled "
        "consistency instead intensifies that house's characteristic "
        "difficulties (conflict, crisis, or loss respectively), making "
        "them a persistent rather than occasional theme."
    ),
    concept_ids=["vedic_structural_findings"],
    feature_ids=["vargottama:dusthana"],
    theme_tags=["structural_finding", "vargottama"],
    life_domain="underlying_strength",
    source_id="vargottama_classical_convention",
    notes=(
        "The specific favorable-vs-Dusthana split was cross-checked "
        "across multiple independent modern compilations during "
        "curation, not read from a single source alone."
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

    written = write_claims()
    print(f"\nWrote {len(written)} claim files to {APPROVED_DIR}")
