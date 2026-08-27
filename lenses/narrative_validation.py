"""
Narrative-synthesis validation: the two-part check proven during the
hand-run prototype (see project history) — a synthesis step told
"don't add anything" still drifts sometimes, so the grounding rules
in lenses.narrative_style are necessary but not sufficient. This
module makes the check real and repeatable rather than a one-off
manual pass.

- check_coverage(): deterministic, no API call. Confirms every claim
  given to the synthesis step left some trace in its output, so
  nothing was silently dropped.
- fact_check(): a second backend call with a distinct verification
  prompt, comparing the narrative back against the same claims it was
  supposed to be grounded in, flagging assertions that aren't
  supported by any of them. This is the check that actually caught
  real drift in the prototype (invented descriptive flourish,
  interpretation added to claims that had none, an invented causal
  link between two separately-listed claims) — coverage alone would
  have missed all three, since nothing was dropped in that run, only
  added.
"""

import re
from dataclasses import dataclass

from lenses.narrative_backend import NarrativeBackend
from lenses.narrative_input import NarrativeClaim

_STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "from", "into",
    "your", "you", "its", "his", "her", "their", "than", "then",
    "also", "core", "chart", "fixed", "star", "declination",
}


def _keywords(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z]{4,}", text.lower())
    return {t for t in tokens if t not in _STOPWORDS}


@dataclass(frozen=True)
class CoverageResult:
    total_claims: int
    covered_claims: int
    missing: list[NarrativeClaim]

    @property
    def coverage_ratio(self) -> float:
        return self.covered_claims / self.total_claims if self.total_claims else 1.0


def check_coverage(claims: list[NarrativeClaim], narrative_text: str, min_keyword_overlap: float = 0.35) -> CoverageResult:
    """
    For each claim, checks whether a meaningful fraction of its
    distinctive keywords appear somewhere in the narrative output.
    This is a coarse, mechanical check — it catches claims that were
    silently dropped entirely, not subtler paraphrase drift (that's
    fact_check's job).
    """

    narrative_lower = narrative_text.lower()
    missing = []

    for claim in claims:
        keywords = _keywords(claim.statement)

        if not keywords:
            continue

        hits = sum(1 for kw in keywords if kw in narrative_lower)
        ratio = hits / len(keywords)

        if ratio < min_keyword_overlap:
            missing.append(claim)

    return CoverageResult(
        total_claims=len(claims),
        covered_claims=len(claims) - len(missing),
        missing=missing,
    )


FACT_CHECK_PROMPT_TEMPLATE = """You are a fact-checker. Below are (1) a list of \
source claims and (2) a narrative that was supposed to be generated ONLY from \
those claims, with instructions not to add any fact, placement, aspect, or \
interpretation not present in the source claims.

Read both and report ONLY genuine discrepancies: any specific assertion in the \
narrative (a placement, number, technique, or interpretation) that is NOT \
supported by anything in the source claims. Ordinary rephrasing, added \
transitions, or reordering is fine and expected -- not a discrepancy. Only \
flag actual new facts or invented connections between claims that weren't \
stated as connected in the source.

For each discrepancy, quote the exact phrase from the narrative and explain \
what it asserts that isn't in the source claims.

If you find zero discrepancies, say so plainly in one sentence -- do not \
manufacture minor stylistic nitpicks to seem thorough.

=== SOURCE CLAIMS ===
{claims_block}

=== NARRATIVE TO FACT-CHECK ===
{narrative_text}
"""


def fact_check(backend: NarrativeBackend, claims: list[NarrativeClaim], narrative_text: str) -> str:
    """
    Issues a second backend call with a distinct verification prompt.
    Returns the backend's raw fact-check findings as text -- this is
    surfaced to the caller (main.py's --narrate output), never
    silently discarded, since a validation step that isn't shown to
    anyone isn't actually a safeguard.
    """

    claims_block = "\n".join(
        f"- {claim.claim_id}: {claim.statement}" for claim in claims
    )

    prompt = FACT_CHECK_PROMPT_TEMPLATE.format(
        claims_block=claims_block,
        narrative_text=narrative_text,
    )

    return backend.synthesize(prompt)
