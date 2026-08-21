"""
Celeste daily mode: given a birth chart and today's date, assemble a
short, attributed daily reading.

CLI/library scope only, per the daily-mode brief v2 -- no UI, no
server, no persistence. Run as a script for plain-text + JSON output,
or import build_daily_reading() as a library call.

Reuses the existing natal pipeline (astrology.chart.build_chart,
chinese.pillars.build_four_pillars), the existing claim-matching
architecture (concepts.normaliser, lenses.features, knowledge.claims.
resolver -- exactly the same resolve_claims() natal claims already go
through), and astrology.daily's computations to resolve today's
claims. Per "Celeste — Daily-Mode Scope Expansion Brief": the daily
transit sweep now covers all 10 transiting bodies against the full
natal chart plus natal house placements (previously 5 bodies against
4 targets, no houses), and natal Moon/Rising sign are shown as
standing display context alongside today's Sun sign -- all reusing
astrology.transits.build_transits()'s existing machinery rather than
new aspect-finding logic.

Reading assembly is real LLM-based synthesis (lenses.narrative_backend,
reused unmodified from N4's natal narrative feature), per "Celeste —
Daily Mode Synthesis Addendum": two prior deterministic attempts (flat
concatenation, then ordering + connector phrases) were both rejected --
connective words are not connective logic. _synthesize_reading() finds
the day's actual throughline and folds/composes claims into 2-3
sentences of real prose. When no ANTHROPIC_API_KEY is available (the
synthesis backend's own MissingAPIKeyError), _assemble_reading_text()
is a clearly-labeled deterministic fallback -- ordering claims by
priority and joining with rotating connector phrases -- so the CLI
still produces a reading rather than failing outright.
"""

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone

from astrology.chart import build_chart
from astrology.daily import (
    compute_current_moon_phase,
    compute_current_sun_sign,
    compute_daily_day_pillar_relationship,
    compute_full_transit_matrix,
    compute_transit_aspects_to_key_points,
    compute_transit_house_placements,
)
from astrology.normaliser import longitude_to_zodiac
from astrology.time import local_to_utc
from chinese.pillars import build_four_pillars
from concepts.normaliser import normalise_observations
from knowledge.claims.resolver import resolve_claims
from lenses.daily_narrative_style import build_daily_synthesis_prompt
from lenses.features import build_features
from lenses.narrative_backend import (
    AnthropicNarrativeBackend,
    MissingAPIKeyError,
    NarrativeBackend,
    NarrativeBackendError,
)
from lenses.narrative_input import NarrativeClaim, format_source
from lenses.narrative_validation import check_coverage, fact_check


def _resolve_daily_claims(concepts, features):
    """Same resolve_claims() natal claims already go through,
    filtered down to the ones tagged for daily mode specifically."""

    daily_claims = []

    for lens_id in ("astrology", "chinese_zodiac"):
        relevant = resolve_claims(concepts, lens_id=lens_id, features=features.tags)

        for item in relevant:
            if "daily_mode" in item.claim.theme_tags:
                daily_claims.append(item)

    return daily_claims


# Action-prompt lines, keyed by life_domain -- deliberately a small,
# hand-written lookup rather than generated text, so every prompt is
# a real, reviewed sentence rather than assembled on the fly. Picked
# per the single highest-priority resolved claim's life_domain (see
# _CLAIM_PRIORITY below), not one per claim, since the daily
# reading's action prompt is meant to be singular and concrete.
_ACTION_PROMPTS = {
    "relationships": "Say the thing to the one person it's actually about, not to everyone else first.",
    "identity": "Do the one thing today that's unmistakably you, even if it's small.",
    "emotion": "Let whatever you're actually feeling be the thing you act from today, not the thing you manage around.",
    "persona": "Show up as exactly who you are today. Don't pre-soften it.",
    "communication": "Say the specific thing you've been rounding down to something vaguer.",
    "drive_and_ambition": "Push the one thing that's actually stalled, not the easy thing sitting next to it.",
    "cyclicality": "Match today's pace instead of forcing yesterday's.",
}

# Shared priority ranking, hand-ordered by urgency/tension first (day-
# pillar clash outranks a combination; Mars/tension transits outrank
# Venus/Sun/Mercury ease transits) -- used both to pick the single
# action-prompt claim below AND, now, to order the supporting claims
# that get woven into the reading text (see _order_reading_claims).
# One canonical ranking rather than two, so "what matters most today"
# means the same thing in both places. Any daily claim_id not listed
# here (future additions) simply falls to the end in original order
# rather than being dropped -- this list is not required to stay
# exhaustive as new daily claims are added.
_CLAIM_PRIORITY = (
    "chinese_zodiac_daily_day_pillar_branch_clash",
    "chinese_zodiac_daily_day_pillar_stem_combination",
    "chinese_zodiac_daily_day_pillar_branch_combination",
    "chinese_zodiac_daily_day_pillar_branch_harm",
    "astrology_daily_transit_mars_square_moon",
    "astrology_daily_transit_mars_square_sun",
    "astrology_daily_transit_mars_opposition_ascendant",
    "astrology_daily_transit_mars_square_chart_ruler",
    "astrology_daily_transit_venus_trine_sun",
    "astrology_daily_transit_venus_trine_moon",
    "astrology_daily_transit_sun_trine_ascendant",
    "astrology_daily_transit_mercury_sextile_chart_ruler",
)


def _pick_action_prompt(daily_claims):
    """Returns (prompt_text, source_claim_id) -- the claim_id lets
    callers (e.g. the web scaffold) show real attribution for the
    action prompt instead of inferring it after the fact."""

    by_id = {item.claim.claim_id: item.claim for item in daily_claims}

    for claim_id in _CLAIM_PRIORITY:
        if claim_id in by_id:
            claim = by_id[claim_id]
            return (
                _ACTION_PROMPTS.get(
                    claim.life_domain,
                    "Meet today on its own terms, not yesterday's.",
                ),
                claim_id,
            )

    # Moon phase always resolves (it's a standalone daily fact), so
    # this is the real fallback when nothing else fired today.
    for item in daily_claims:
        if item.claim.claim_id.startswith("astrology_daily_moon_phase"):
            return (
                _ACTION_PROMPTS.get(
                    item.claim.life_domain, "Match today's pace instead of forcing yesterday's."
                ),
                item.claim.claim_id,
            )

    return "Meet today on its own terms, not yesterday's.", None


# Small, hand-checked pool of connective phrases (no em dash, no
# hedging, no astrology jargon, no reference to method/confidence --
# same bar as celeste-style-guide.md's language rules) used only by
# the DETERMINISTIC FALLBACK path below, when the real LLM synthesis
# backend (_synthesize_reading) is unavailable. Per "Celeste — Daily
# Mode Synthesis Addendum," ordering + connector phrases is NOT real
# synthesis -- connective words are not connective logic -- so this is
# clearly a degraded-mode fallback, not the primary path. Rotated so
# two connectors never repeat back to back within one reading.
_CONNECTORS = (
    "Alongside that",
    "Still",
    "At the same time",
    "On top of that",
)

# Fallback-only cap on supporting claims (moon phase always additional
# to this). See _order_reading_claims for why this exists post-widening.
_MAX_FALLBACK_SUPPORTING_CLAIMS = 3


def _order_reading_claims(daily_claims):
    """
    Split the resolved daily claims into (moon_phase_item, ordered
    supporting_items), where supporting_items is ranked by
    _CLAIM_PRIORITY (ties/unlisted claims keep their original relative
    order) with transit-aspect orb as a documented secondary key --
    tighter orb means the aspect is more exactly in effect today, a
    real astrological quantity rather than an arbitrary tiebreaker.
    Uncapped: every resolved claim is represented in the fallback
    reading (see _assemble_reading_text) so `reading` and the
    attributed `claims` list can never go out of sync.

    Returns (None, []) in the degenerate case where moon phase somehow
    didn't resolve (shouldn't happen -- it's a standalone daily fact --
    but this function doesn't assume it as a precondition).
    """

    moon_phase_item = None
    supporting = []

    for item in daily_claims:
        if item.claim.claim_id.startswith("astrology_daily_moon_phase"):
            moon_phase_item = item
        else:
            supporting.append(item)

    def _orb(item):
        # matched_values["daily_transit_aspects"] holds one entry per
        # observation, and that concept always has exactly one
        # observation whose value is the full list of today's aspect
        # dicts -- so matched_values["daily_transit_aspects"][0] is
        # that list. Find the specific aspect this claim's feature
        # tag names (e.g. "daily_transit_aspect:mars:square:sun") and
        # return its real orb, rather than guessing at a shape.
        aspect_lists = item.matched_values.get("daily_transit_aspects")
        if not aspect_lists:
            return 999.0

        all_aspects = aspect_lists[0]

        for feature_id in item.matched_features:
            parts = feature_id.split(":")
            if len(parts) != 4 or parts[0] != "daily_transit_aspect":
                continue
            _, body, aspect_type, target_role = parts

            for aspect in all_aspects:
                if (
                    aspect.get("transiting_body") == body
                    and aspect.get("aspect") == aspect_type
                    and aspect.get("target_role") == target_role
                ):
                    return aspect["orb"]

        return 999.0

    def _priority_rank(item):
        claim_id = item.claim.claim_id
        if claim_id in _CLAIM_PRIORITY:
            return (0, _CLAIM_PRIORITY.index(claim_id))
        return (1, 0)

    ranked = sorted(
        enumerate(supporting),
        key=lambda pair: (_priority_rank(pair[1]), _orb(pair[1]), pair[0]),
    )
    # Capped here, not left uncapped as before the Daily-Mode Scope
    # Expansion widening: with the sweep now covering all 10 planets
    # against the full natal chart plus houses, a busy day can resolve
    # 15+ claims (mostly via the generic aspect/house fallback claims,
    # which are real but low-specificity -- "a trine lets the two
    # placements involved flow together" x6, "the Nth house governs
    # X" x12). Uncapped, the FALLBACK text becomes an unreadable list
    # of jargon-heavy generic statements -- real synthesis doesn't
    # have this problem (it folds/prioritizes via actual judgment
    # regardless of volume), so this cap applies only to the
    # deterministic degraded-mode path, never to what synthesis sees
    # or to the attributed `claims`/`reading_source_claim_ids` output,
    # which both stay fully uncapped. _CLAIM_PRIORITY-listed (curated,
    # specific) claims already rank above unlisted (generic fallback)
    # ones, so the cap keeps the most specific content, not just
    # whatever resolved first.
    ordered_supporting = [item for _, item in ranked][:_MAX_FALLBACK_SUPPORTING_CLAIMS]

    return moon_phase_item, ordered_supporting


def _assemble_reading_text(daily_claims):
    """
    DETERMINISTIC FALLBACK ONLY -- used when _synthesize_reading()
    can't run (no ANTHROPIC_API_KEY). This is ordering + connector
    phrases, not real synthesis; it does not find a throughline or
    fold claims together the way the real synthesis path does. Moon
    phase (always present) anchors the reading, followed by up to
    _MAX_FALLBACK_SUPPORTING_CLAIMS other resolved claims ranked by
    priority, joined with rotating connector phrases instead of raw
    concatenation. A single resolved claim is returned as-is -- no
    connector needed for a one-claim day.
    """

    moon_phase_item, ordered_supporting = _order_reading_claims(daily_claims)

    pieces = []
    if moon_phase_item is not None:
        pieces.append(moon_phase_item.claim.statement)
    pieces.extend(item.claim.statement for item in ordered_supporting)

    if not pieces:
        return ""
    if len(pieces) == 1:
        return pieces[0]

    reading = pieces[0]
    for index, piece in enumerate(pieces[1:]):
        connector = _CONNECTORS[index % len(_CONNECTORS)]
        reading += f" {connector}, {piece[0].lower()}{piece[1:]}"

    return reading


# daily_claims only ever comes from these two lenses (see
# _resolve_daily_claims above) -- a small local mapping rather than
# importing narrative_input's private, natal-scoped _LENS_LABELS.
_DAILY_LENS_LABELS = {
    "astrology": "Western",
    "chinese_zodiac": "Chinese",
}


def _to_narrative_claims(daily_claims) -> list[NarrativeClaim]:
    """Converts resolved daily RelevantClaims into the same
    NarrativeClaim shape N4's natal synthesis already uses, reusing
    format_source() rather than re-deriving citation formatting."""

    narrative_claims = []

    for item in daily_claims:
        claim = item.claim
        source = format_source(claim.source_ids[0]) if claim.source_ids else "Uncited"

        narrative_claims.append(NarrativeClaim(
            lens_id=claim.lens_id,
            tradition=_DAILY_LENS_LABELS.get(claim.lens_id, claim.lens_id),
            claim_id=claim.claim_id,
            statement=claim.statement,
            source=source,
            life_domain=claim.life_domain,
        ))

    return narrative_claims


def _render_daily_narrative_input(
    narrative_claims: list[NarrativeClaim],
    daily_transit_aspects: list[dict] | None = None,
    daily_transit_houses: list[dict] | None = None,
) -> str:
    """Plain-text CLAIM_ID/STATEMENT/SOURCE block for today's claims,
    same shape as N4's render_narrative_input(), plus a trailing raw-
    data section (same precedent as N4's Cross-Tradition Synthesis /
    Elemental Alignment sections: already-computed fact, reference
    only, not itself a claim).

    Needed post-widening: the generic aspect-type claims (e.g.
    "a square pulls the two placements involved...") and generic
    house claims ("the 3rd house governs...") don't name WHICH bodies
    or WHICH transiting body -- that specificity only exists in a
    resolved claim's matched_features when a curated fragment exists
    for that exact combo (the 8 daily_transit_* claims). For the many
    aspect/house instances the widened sweep resolves that DON'T have
    a curated fragment, the only way synthesis can be specific rather
    than vague is to see the real underlying data -- which already
    exists (astrology.daily's own computed output), just wasn't being
    passed through before."""

    lines = []

    for claim in narrative_claims:
        lines.append(f"- CLAIM_ID: {claim.claim_id}")
        lines.append(f"  TRADITION: {claim.tradition}")
        lines.append(f"  LIFE_DOMAIN: {claim.life_domain or 'general'}")
        lines.append(f"  STATEMENT: {claim.statement}")
        lines.append(f"  SOURCE: {claim.source}")

    if daily_transit_aspects or daily_transit_houses:
        lines.append("")
        lines.append("# Today's exact transit data (reference only, not itself a claim)")
        lines.append("")
        lines.append(
            "Use this only to know which specific placement a generic "
            "claim above is actually about, when the claim's own "
            "STATEMENT doesn't say (e.g. \"a square pulls the two "
            "placements involved...\" or \"the 3rd house governs...\"). "
            "If a claim above already names the specific pairing (like "
            "astrology_daily_transit_mars_square_moon), you already "
            "have what you need from the claim itself. Planet/aspect/"
            "house names stay backend per the grounding rules either way "
            "-- this is disambiguation for your own reasoning, not "
            "content to quote."
        )

        for aspect in daily_transit_aspects or []:
            lines.append(
                f"  aspect: {aspect['transiting_body']} {aspect['aspect']} "
                f"{aspect['target_role']} (orb {aspect['orb']:.2f}°)"
            )

        for house in daily_transit_houses or []:
            lines.append(
                f"  house: {house['transiting_body']} in natal house {house['natal_house']}"
            )

    return "\n".join(lines)


def _synthesize_reading(
    daily_claims,
    backend: NarrativeBackend,
    daily_transit_aspects: list[dict] | None = None,
    daily_transit_houses: list[dict] | None = None,
):
    """
    Real synthesis path: builds today's claims into the daily
    synthesis prompt (lenses.daily_narrative_style) and calls the
    backend. Returns (reading_text, validation_dict) on success, or
    (None, None) if the backend can't run (no API key, or a backend-
    level failure) -- the caller falls back to the deterministic path
    in that case. validation_dict carries check_coverage() (kept
    informational for daily mode -- a claim the model correctly folded
    into implicit context, per the synthesis addendum, will legitimately
    score low on keyword overlap without that being a real bug) and
    fact_check()'s findings (a real check -- catches invented
    specificity the source claims don't support).

    daily_transit_aspects/daily_transit_houses (the raw computed data,
    not claims) are passed through to _render_daily_narrative_input so
    synthesis has real grounding for the generic-only aspect/house
    claims the widened sweep resolves -- see that function's docstring.
    """

    narrative_claims = _to_narrative_claims(daily_claims)
    prompt = build_daily_synthesis_prompt(
        _render_daily_narrative_input(
            narrative_claims, daily_transit_aspects, daily_transit_houses
        )
    )

    try:
        reading_text = backend.synthesize(prompt)
    except (MissingAPIKeyError, NarrativeBackendError):
        return None, None

    coverage = check_coverage(narrative_claims, reading_text)
    fact_check_findings = fact_check(backend, narrative_claims, reading_text)

    validation = {
        "coverage_ratio": coverage.coverage_ratio,
        "coverage_missing_claim_ids": [c.claim_id for c in coverage.missing],
        "coverage_note": (
            "Informational only for daily mode: a claim folded into "
            "implicit context (per the synthesis addendum) can score "
            "low here without being a real omission."
        ),
        "fact_check_findings": fact_check_findings,
    }

    return reading_text, validation


def build_daily_reading(
    natal_chart: dict,
    four_pillars,
    as_of_utc_time: datetime,
    use_synthesis: bool = True,
    backend: NarrativeBackend | None = None,
    include_debug_matrix: bool = False,
) -> dict:
    """
    The library entry point: given an already-built natal chart
    (astrology.chart.build_chart output), the natal four pillars
    (chinese.pillars.build_four_pillars output), and the moment to
    evaluate "today" at, return the attributed claim list, the
    assembled short reading, and the action prompt.

    Reading assembly tries real LLM synthesis first (unless
    use_synthesis=False, e.g. for offline/test use), falling back to
    the deterministic ordering+connector path when the synthesis
    backend can't run. `synthesis_method` in the result always says
    which path actually produced the reading; `synthesis_validation`
    is present only when real synthesis ran.
    """

    moon_phase_data = compute_current_moon_phase(as_of_utc_time)
    day_pillar_relationship = compute_daily_day_pillar_relationship(
        four_pillars.day, as_of_utc_time.date()
    )
    transit_aspects = compute_transit_aspects_to_key_points(natal_chart, as_of_utc_time)
    transit_houses = compute_transit_house_placements(natal_chart, as_of_utc_time)

    observations = {
        "astrology": natal_chart,
        "daily_moon_phase": moon_phase_data,
        "daily_transit_aspects": transit_aspects,
        "daily_transit_houses": transit_houses,
        "daily_day_pillar_relationship": day_pillar_relationship,
    }

    concepts = normalise_observations(observations)
    features = build_features(concepts)
    daily_claims = _resolve_daily_claims(concepts, features)

    attributed = []

    for item in daily_claims:
        claim = item.claim
        attributed.append({
            "claim_text": claim.statement,
            "sources": [
                {"type": "feature", "value": feature_id}
                for feature_id in item.matched_features
            ],
            "claim_id": claim.claim_id,
            "source_ids": list(claim.source_ids),
            "life_domain": claim.life_domain,
        })

    reading_text = None
    synthesis_validation = None
    synthesis_method = "deterministic_fallback"

    if use_synthesis and daily_claims:
        reading_text, synthesis_validation = _synthesize_reading(
            daily_claims,
            backend or AnthropicNarrativeBackend(),
            daily_transit_aspects=transit_aspects,
            daily_transit_houses=transit_houses,
        )
        if reading_text is not None:
            synthesis_method = "llm"

    if reading_text is None:
        reading_text = _assemble_reading_text(daily_claims)

    action_prompt, action_prompt_source_claim_id = _pick_action_prompt(daily_claims)

    moon_phase_claim_id = next(
        (
            item.claim.claim_id
            for item in daily_claims
            if item.claim.claim_id.startswith("astrology_daily_moon_phase")
        ),
        None,
    )
    sun_sign_data = compute_current_sun_sign(as_of_utc_time)
    today_pillar = day_pillar_relationship["today_pillar"]

    # Natal identity anchors, same "raw computed fact, no interpretive
    # claim" treatment as sun_sign above -- standing context per the
    # Daily-Mode Scope Expansion brief, not something that changes day
    # to day (unlike sun_sign, which is today's real transiting Sun).
    natal_moon_sign = longitude_to_zodiac(natal_chart["bodies"]["moon"]["longitude"])["sign"]
    rising_sign = longitude_to_zodiac(natal_chart["houses"]["angles"]["ascendant"])["sign"]

    result = {
        "as_of_utc_time": as_of_utc_time.isoformat(),
        "claims": attributed,
        "reading": reading_text,
        "reading_source_claim_ids": [item.claim.claim_id for item in daily_claims],
        "action_prompt": action_prompt,
        "action_prompt_source_claim_id": action_prompt_source_claim_id,
        "synthesis_method": synthesis_method,
        "moon_phase": {
            "label": moon_phase_data["phase_name"].replace("_", " ").title(),
            "source_claim_id": moon_phase_claim_id,
        },
        "sun_sign": {
            "label": sun_sign_data["sign"],
            "note": (
                "Computed from today's real Sun position (tropical), "
                "not an interpretive claim."
            ),
        },
        "chinese_day_pillar": {
            "label": today_pillar["name"],
            "note": (
                "Computed calendrical pillar, not itself an interpretive "
                "claim -- any clash/combination/harm relative to the "
                "natal day pillar is already reflected in the reading "
                "above when it applies."
            ),
        },
        "natal_moon_sign": {
            "label": natal_moon_sign,
            "note": "Your natal Moon sign -- standing identity context, not today's sky.",
        },
        "rising_sign": {
            "label": rising_sign,
            "note": "Your natal Ascendant (Rising) sign -- standing identity context, not today's sky.",
        },
    }

    if synthesis_validation is not None:
        result["synthesis_validation"] = synthesis_validation

    if include_debug_matrix:
        result["debug_matrix"] = compute_full_transit_matrix(natal_chart, as_of_utc_time)

    return result


def _parse_args():
    parser = argparse.ArgumentParser(description="Celeste daily reading")
    parser.add_argument("--birth-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--birth-time", required=True, help="HH:MM, 24h, local")
    parser.add_argument("--timezone", required=True, help="IANA tz, e.g. Australia/Melbourne")
    parser.add_argument("--latitude", type=float, required=True)
    parser.add_argument("--longitude", type=float, required=True)
    parser.add_argument("--as-of", default=None, help="YYYY-MM-DDTHH:MM (UTC); default now")
    parser.add_argument("--json", action="store_true", help="print full attributed JSON")
    parser.add_argument(
        "--no-synthesis",
        action="store_true",
        help=(
            "Skip the real LLM synthesis call and use the deterministic "
            "ordering+connector fallback directly (offline/testing use). "
            "Synthesis also falls back to this automatically if "
            "ANTHROPIC_API_KEY isn't set."
        ),
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help=(
            "Also compute and show the full transit matrix -- every "
            "transiting-body x natal-target x aspect-type combination "
            "evaluated today, including near-misses that didn't clear "
            "orb, not just what resolved into a claim. Diagnostic only; "
            "never feeds into the reading itself."
        ),
    )
    return parser.parse_args()


def main():
    args = _parse_args()

    birth_date = datetime.strptime(args.birth_date, "%Y-%m-%d").date()
    birth_hour, birth_minute = (int(x) for x in args.birth_time.split(":"))
    local_time = datetime(
        birth_date.year, birth_date.month, birth_date.day, birth_hour, birth_minute
    )
    aware_utc = local_to_utc(local_time, args.timezone)
    utc_time = (
        aware_utc.replace(tzinfo=timezone.utc) if aware_utc.tzinfo is None else aware_utc
    )

    if args.as_of:
        as_of = datetime.strptime(args.as_of, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
    else:
        as_of = datetime.now(timezone.utc)

    natal_chart = build_chart(
        utc_time, args.latitude, args.longitude, house_system="placidus"
    )
    four_pillars = build_four_pillars(natal_chart, local_time)

    result = build_daily_reading(
        natal_chart,
        four_pillars,
        as_of,
        use_synthesis=not args.no_synthesis,
        include_debug_matrix=args.debug,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["reading"])
        print()
        print(f"Today: {result['action_prompt']}")
        print(f"[{result['synthesis_method']}]")

        validation = result.get("synthesis_validation")
        if validation:
            print(f"Coverage: {validation['coverage_ratio']:.0%} ({validation['coverage_note']})")
            print(f"Fact-check: {validation['fact_check_findings']}")

        print()
        print(f"Moon: {result['natal_moon_sign']['label']}  |  Rising: {result['rising_sign']['label']}  |  Sun today: {result['sun_sign']['label']}")

        print()
        print(f"({len(result['claims'])} claims, sources below)")
        for claim in result["claims"]:
            sources = ", ".join(s["value"] for s in claim["sources"])
            print(f"  - {claim['claim_text']}")
            print(f"    [{sources}]")

        if args.debug:
            matrix = result["debug_matrix"]
            cleared = [r for r in matrix if r["cleared"]]
            print()
            print(f"[debug] {len(matrix)} transiting-body x target x aspect-type "
                  f"combinations evaluated today, {len(cleared)} cleared orb.")
            near_misses = sorted(
                (r for r in matrix if not r["cleared"]),
                key=lambda r: r["orb"] - r["max_orb"],
            )[:10]
            print("[debug] closest 10 near-misses (didn't clear orb):")
            for r in near_misses:
                print(
                    f"  {r['transiting_body']:10s} {r['aspect']:14s} -> "
                    f"{r['target_role']:12s} orb={r['orb']:.2f} (max {r['max_orb']})"
                )


if __name__ == "__main__":
    main()
