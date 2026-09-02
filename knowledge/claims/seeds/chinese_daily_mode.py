"""
Celeste daily-mode knowledge seed (Chinese/BaZi): today's day pillar
against the natal day pillar -- stem combination, branch clash,
branch combination, branch harm.

Reuses the exact classical mechanism already source-backed elsewhere
in this codebase for natal pillar-to-pillar comparisons
(chinese/interactions.py's STEM_COMBINATIONS/BRANCH_CLASHES/
BRANCH_COMBINATIONS/BRANCH_HARMS tables, and the existing natal
Day/Hour branch-clash claim) -- applied here to a new pairing
(today's circulating day pillar vs. the fixed natal day pillar)
rather than two pillars within one natal chart. The underlying
technique (a circulating pillar interacting with a natal pillar via
the same clash/combination rules) is the same one already used for
Da Yun and Liu Nian elsewhere in this project; this is that same
mechanism at the day-pillar timescale, not a new invented one.

The Day Branch's specific significance as the "Spouse Palace" (self
via the Day Stem, closest partnership via the Day Branch) is already
an existing, source-backed claim in this codebase
(astrology_extended.py/chinese seeds, San Ming Tong Hui-derived) --
reused here rather than re-derived, which is why these claims read as
touching "your closest relationship specifically" for the branch-
level findings, not just "today."

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
# _add() defaulted notes to "" instead, so every claim here shipped
# with no editorial_note at all despite carrying a real named
# source_id.
GENERAL_NOTE = (
    "Reflects a widely-repeated interpretation found throughout "
    "standard Bazi/Chinese astrology literature, exemplified by (not "
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


_add(
    "daily_day_pillar_branch_clash",
    "Today doesn't sit quietly next to who you are. Whatever comes "
    "up is likely to land on your closest relationship "
    "specifically, not just you.",
    concept_ids=["daily_day_pillar_relationship"],
    feature_ids=["daily_day_pillar:branch_clash"],
    theme_tags=["daily_mode"],
    life_domain="relationships",
    source_id="bazi_pillar_interaction_modern_convention",
)

_add(
    "daily_day_pillar_branch_combination",
    "Today actually cooperates with who you are, especially in your "
    "closest relationship. Whatever needs harmony there gets it "
    "more easily than usual.",
    concept_ids=["daily_day_pillar_relationship"],
    feature_ids=["daily_day_pillar:branch_combination"],
    theme_tags=["daily_mode"],
    life_domain="relationships",
    source_id="bazi_pillar_interaction_modern_convention",
)

_add(
    "daily_day_pillar_branch_harm",
    "Nothing about today looks like conflict on the surface. But "
    "something's quietly working against your closest relationship "
    "anyway, in a way that's easy to miss until it's already cost "
    "you something.",
    concept_ids=["daily_day_pillar_relationship"],
    feature_ids=["daily_day_pillar:branch_harm"],
    theme_tags=["daily_mode"],
    life_domain="relationships",
    source_id="bazi_pillar_interaction_modern_convention",
)

_add(
    "daily_day_pillar_stem_combination",
    "Today isn't just getting along with you, it's actually aligned "
    "with you, right down to the core of who you are. Rare days "
    "like this are worth actually using, not coasting through.",
    concept_ids=["daily_day_pillar_relationship"],
    feature_ids=["daily_day_pillar:stem_combination"],
    theme_tags=["daily_mode"],
    life_domain="identity",
    source_id="bazi_pillar_interaction_modern_convention",
)


if __name__ == "__main__":
    for claim in claims:
        path = APPROVED_DIR / f"{claim.claim_id}.json"
        data = asdict(claim)
        data["status"] = "approved"

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    print(f"Wrote {len(claims)} claims to {APPROVED_DIR}")
