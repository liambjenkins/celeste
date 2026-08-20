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
through), and astrology.daily's three new computations. The only new
assembly step is: resolve, then filter down to claims tagged
"daily_mode", then weave those into one short reading plus a
structured, attributed JSON list -- per the daily-mode brief's
section 5 shape.
"""

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone

from astrology.chart import build_chart
from astrology.daily import (
    compute_current_moon_phase,
    compute_daily_day_pillar_relationship,
    compute_transit_aspects_to_key_points,
)
from astrology.time import local_to_utc
from chinese.pillars import build_four_pillars
from concepts.normaliser import normalise_observations
from knowledge.claims.resolver import resolve_claims
from lenses.features import build_features


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
    by_id = {item.claim.claim_id: item.claim for item in daily_claims}

    for claim_id in _CLAIM_PRIORITY:
        if claim_id in by_id:
            claim = by_id[claim_id]
            return _ACTION_PROMPTS.get(
                claim.life_domain,
                "Meet today on its own terms, not yesterday's.",
            )

    # Moon phase always resolves (it's a standalone daily fact), so
    # this is the real fallback when nothing else fired today.
    for item in daily_claims:
        if item.claim.claim_id.startswith("astrology_daily_moon_phase"):
            return _ACTION_PROMPTS.get(
                item.claim.life_domain, "Match today's pace instead of forcing yesterday's."
            )

    return "Meet today on its own terms, not yesterday's."


# How many non-moon-phase claims get woven into the flowing reading
# text. Moon phase always anchors the reading (it's the one claim
# guaranteed to resolve every day, and it's broad daily context rather
# than personal-chart-specific, so it leads before narrowing to the
# day-pillar/transit content). This cap keeps a busy day's reading
# "sparse and meaningful, not exhaustive" per the daily-mode brief --
# it does NOT affect the attributed `claims` JSON list, which stays
# built from every resolved claim, uncapped, since full attribution is
# a separate, non-negotiable requirement.
_MAX_READING_SUPPORTING_CLAIMS = 2

# Small, hand-checked pool of connective phrases (no em dash, no
# hedging, no astrology jargon, no reference to method/confidence --
# same bar as celeste-style-guide.md's language rules and its
# full-narrative-assembly addendum) used to join ordered claims into
# one flowing reading instead of bare concatenation. Rotated rather
# than fixed so two connectors never repeat back to back within one
# reading, per the addendum's "vary the moves" rule -- real even at
# the 2-3-claim scale a daily reading actually reaches.
_CONNECTORS = (
    "Alongside that",
    "Still",
    "At the same time",
    "On top of that",
)


def _order_reading_claims(daily_claims):
    """
    Split the resolved daily claims into (moon_phase_item, ordered
    supporting_items), where supporting_items is ranked by
    _CLAIM_PRIORITY (ties/unlisted claims keep their original relative
    order) with transit-aspect orb as a documented secondary key --
    tighter orb means the aspect is more exactly in effect today, a
    real astrological quantity rather than an arbitrary tiebreaker --
    then capped to _MAX_READING_SUPPORTING_CLAIMS.

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
    ordered_supporting = [item for _, item in ranked][:_MAX_READING_SUPPORTING_CLAIMS]

    return moon_phase_item, ordered_supporting


def _assemble_reading_text(daily_claims):
    """
    Real reading assembly: moon phase (always present) anchors the
    reading, followed by up to _MAX_READING_SUPPORTING_CLAIMS ranked
    supporting claims, joined with rotating connector phrases instead
    of raw concatenation. A single resolved claim is returned as-is --
    no connector needed or wanted for the common one-claim day.
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


def build_daily_reading(natal_chart: dict, four_pillars, as_of_utc_time: datetime) -> dict:
    """
    The library entry point: given an already-built natal chart
    (astrology.chart.build_chart output), the natal four pillars
    (chinese.pillars.build_four_pillars output), and the moment to
    evaluate "today" at, return the attributed claim list, the
    assembled short reading, and the action prompt.
    """

    observations = {
        "astrology": natal_chart,
        "daily_moon_phase": compute_current_moon_phase(as_of_utc_time),
        "daily_transit_aspects": compute_transit_aspects_to_key_points(
            natal_chart, as_of_utc_time
        ),
        "daily_day_pillar_relationship": compute_daily_day_pillar_relationship(
            four_pillars.day, as_of_utc_time.date()
        ),
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

    reading_text = _assemble_reading_text(daily_claims)
    action_prompt = _pick_action_prompt(daily_claims)

    return {
        "as_of_utc_time": as_of_utc_time.isoformat(),
        "claims": attributed,
        "reading": reading_text,
        "action_prompt": action_prompt,
    }


def _parse_args():
    parser = argparse.ArgumentParser(description="Celeste daily reading")
    parser.add_argument("--birth-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--birth-time", required=True, help="HH:MM, 24h, local")
    parser.add_argument("--timezone", required=True, help="IANA tz, e.g. Australia/Melbourne")
    parser.add_argument("--latitude", type=float, required=True)
    parser.add_argument("--longitude", type=float, required=True)
    parser.add_argument("--as-of", default=None, help="YYYY-MM-DDTHH:MM (UTC); default now")
    parser.add_argument("--json", action="store_true", help="print full attributed JSON")
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

    result = build_daily_reading(natal_chart, four_pillars, as_of)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["reading"])
        print()
        print(f"Today: {result['action_prompt']}")
        print()
        print(f"({len(result['claims'])} claims, sources below)")
        for claim in result["claims"]:
            sources = ", ".join(s["value"] for s in claim["sources"])
            print(f"  - {claim['claim_text']}")
            print(f"    [{sources}]")


if __name__ == "__main__":
    main()
