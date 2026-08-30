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
4 targets, no houses), and natal Sun/Moon/Ascendant sign are shown as
standing identity anchors alongside today's real transiting Sun sign
-- all reusing astrology.transits.build_transits()'s existing
machinery rather than new aspect-finding logic. Per the Query-
Answering/Daily-Reading Repair phase: those three identity anchors,
and any other natal placement a real hit touches that day, now carry
a real, source-cited sign-meaning interpretation (_resolve_sign_claim)
rather than a bare computed label -- 219 already-reviewed claims that
existed but were silently dropped by the daily-mode theme-tag filter.

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
from astrology.chara_dasha import build_chara_dasha
from astrology.daily import (
    compute_current_moon_phase,
    compute_current_sun_sign,
    compute_daily_day_pillar_relationship,
    compute_full_transit_matrix,
)
from astrology.daily_highlights import compute_eclipse_context, compute_todays_highlights
from astrology.daily_hits import compute_daily_hits
from astrology.dasha import build_vimshottari_dasha
from astrology.event_significance import natal_targets
from astrology.normaliser import longitude_to_zodiac
from astrology.sidereal import build_sidereal_chart, get_ayanamsa, sidereal_longitude
from astrology.time import local_to_utc
from astrology.yogini_dasha import build_yogini_dasha
from providers.astronomy import get_astronomy
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
from lenses.overclaim_guard import build_batch_overclaim_constraints, check_batch_overclaims


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


def _resolve_sign_claim(role: str, sign: str):
    """One targeted sign-meaning claim lookup (astrology_{body}_sign_
    {sign}.json / astrology_ascendant_sign_{sign}.json -- 219 already-
    reviewed files) -- deliberately bypassing _resolve_daily_claims'
    blanket sweep and its "daily_mode" theme-tag filter entirely.
    Those 219 files are NOT tagged daily_mode, and that's
    intentional: build_features() fires a sign:{body}:{sign} tag for
    EVERY natal placement on every single run (it's fed the full
    natal chart), so tagging them daily_mode would flood every
    reading with every natal placement's sign every day -- the exact
    "unfiltered spray" bug this session already fixed once, for
    houses. Callers of this function decide relevance themselves
    (see build_daily_reading) and call this once per role that
    actually matters that day; the full chart is still available as
    data (any role can be looked up), it's just never surfaced
    unconditionally.

    Returns the matched RelevantClaim, or None if no claim exists for
    this exact role (e.g. vertex has no authored sign-claim family;
    degrade honestly, don't guess -- though see _resolve_pure_sign_
    claim below for an honest last-resort fallback callers can use).

    Some bodies (e.g. Sun) also have a generic "what this planet
    represents" claim reused across all 12 signs (feature_ids lists
    every sign, not just this one -- same generic-fallback pattern
    already seen elsewhere in this codebase for aspect types). When
    multiple claims match, prefer the most specific one -- the fewest
    feature_ids -- so the sign-specific claim (feature_ids == exactly
    this one tag) wins over a same-tagged generic one."""

    tag = f"ascendant:{sign}" if role == "ascendant" else f"sign:{role}:{sign}"
    matches = resolve_claims({}, lens_id="astrology", features=[tag])
    if not matches:
        return None
    return min(matches, key=lambda item: len(item.claim.feature_ids))


def _resolve_pure_sign_claim(sign: str):
    """Combinatorial-Meaning Expansion Phase 3: what a sign means on
    its own (element/modality/rulership), independent of any body --
    an honest LAST-RESORT fallback for a role with no body-specific
    sign-claim family at all (_resolve_sign_claim returns None). Real
    beneficiary: lilith_true is a genuine PRIMARY_NATAL_ROLES member
    (astrology/event_significance.py) that can be a real hit target
    with zero prior sign-meaning content. NOT a substitute for
    role-specific content where it exists -- callers should always try
    _resolve_sign_claim first and only fall back here on a miss (see
    _use_sign_claim in build_daily_reading)."""

    tag = f"pure_sign:{sign}"
    matches = resolve_claims({}, lens_id="astrology", features=[tag])
    return matches[0] if matches else None


def _resolve_house_claim(transiting_body: str, house: int):
    """One targeted house-meaning claim lookup (astrology_house_{N}.
    json, already tagged daily_transit_house:{body}:{house} for all
    10 transiting bodies x 12 houses -- see the Aug-21 daily-transit-
    sweep widening). Same non-blanket-sweep discipline as
    _resolve_sign_claim: the resolve->tier->guard rebuild (PR #4)
    stopped feeding daily_transit_houses through the old
    concepts->features sweep -- that sweep was itself the unfiltered-
    spray mechanism behind the "citation list naming irrelevant
    houses" bug -- which orphaned this tag family without a
    replacement. This restores real per-hit house-meaning citations
    the same way natal/Vedic sign meaning was restored: called once
    per hit that already survived resolve->tier, never for every
    transiting body's every house placement."""

    tag = f"daily_transit_house:{transiting_body}:{house}"
    matches = resolve_claims({}, lens_id="astrology", features=[tag])
    return matches[0] if matches else None


def _resolve_natal_house_claim(role: str, house: int):
    """One targeted lookup for a NATAL point's own birth house -- e.g.
    natal Saturn radix in house 10, NOT the house a transiting body is
    currently passing through (that's _resolve_house_claim, above).
    This distinction is the actual gap this closes: a real audit found
    natal_chart["bodies"][role]["house"] has always been computed
    correctly (astrology/chart.py -> normalise_body ->
    longitude_in_house against the chart's own natal cusps), but
    nothing in this pipeline ever cited it -- every existing "house"
    reference here is transit-through-house. Reuses the plain
    house:{role}:{house} tag already on astrology_house_N.json (no new
    claim content needed), which only covers the 10 classical planets
    (_PLANETS_FOR_HOUSE_TAGS in knowledge/claims/seeds/astrology.py) --
    honest None degrade for nodes/Chiron/asteroids/angles, same as
    every other honest-degrade precedent in this file."""

    tag = f"house:{role}:{house}"
    matches = resolve_claims({}, lens_id="astrology", features=[tag])
    if not matches:
        return None
    return min(matches, key=lambda item: len(item.claim.feature_ids))


# Houses whose cusp is exactly one of the four angles in this engine's
# house systems (confirmed by direct query: cusp longitude == the
# angle's own longitude, to full float precision) -- Combinatorial-
# Meaning Expansion Phase 2 deliberately does NOT author sign-in-house
# content for these four, since it would duplicate the existing
# Ascendant/MC/IC/Descendant-by-sign claims for the same underlying
# chart fact.
_ANGULAR_HOUSES = frozenset({1, 4, 7, 10})


def _house_cusp_sign(natal_chart: dict, house: int) -> str:
    """The real sign on this natal chart's own house cusp -- a fixed,
    chart-specific fact (not a transiting one), read directly off
    natal_chart["houses"]["cusps"] (string-keyed, per astrology/
    normaliser.py's own convention)."""

    cusp_longitude = natal_chart["houses"]["cusps"][str(house)]
    return longitude_to_zodiac(cusp_longitude)["sign"]


def _resolve_house_cusp_sign_claim(house: int, sign: str):
    """One targeted lookup for what sign colors a given (non-angular)
    house's affairs in THIS chart -- e.g. Capricorn on the natal 8th
    house cusp. Distinct from _resolve_house_claim/
    _resolve_natal_house_claim (which planet, if any, occupies the
    house) -- a house can carry real, personalized cusp-sign content
    even with no planet in it at all. Only houses 2, 3, 5, 6, 8, 9, 11,
    12 have an authored claim family (see _ANGULAR_HOUSES); the four
    angular houses' cusp sign is already covered by the Ascendant/MC/
    IC/Descendant-by-sign claims -- honest None degrade here, callers
    should resolve those instead for house in _ANGULAR_HOUSES."""

    tag = f"house_cusp_sign:{house}:{sign}"
    matches = resolve_claims({}, lens_id="astrology", features=[tag])
    return matches[0] if matches else None


# The nine classical Navagraha that carry a real Vedic karaka
# (signification) -- Uranus/Neptune/Pluto are tracked structurally but
# have no traditional karakatva, so they never get a "planet meaning"
# fusion (honest degrade, not a gap -- see _resolve_vedic_planet_fusion).
_VEDIC_PLANET_MEANING_BODIES = frozenset({
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
    "north_node_true", "south_node_true",
})


def _resolve_vedic_claim(tag: str):
    """One targeted Vedic claim lookup (lens_id="vedic_astrology"),
    the same non-blanket-sweep discipline as _resolve_sign_claim and
    for the identical reason: none of the ~150 Vedic claim files are
    tagged "daily_mode" -- build_features() fires a vedic_sign:*/
    dasha_*:* tag for every natal placement and every Dasha level on
    every run, so a blanket sweep would flood daily mode with
    standing Vedic content unrelated to what's actually relevant that
    day. Unlike the Western sign lookup, no generic multi-tag claim
    exists in this family to disambiguate against -- confirmed each
    tag maps to exactly one claim file -- so this is a plain single-
    match lookup. Returns None if nothing matches."""

    matches = resolve_claims({}, lens_id="vedic_astrology", features=[tag])
    return matches[0] if matches else None


def _resolve_vedic_sign_fusion(role: str, sign: str):
    """The sign-meaning claim plus (when this role has a real
    karaka -- see _VEDIC_PLANET_MEANING_BODIES) the planet-meaning
    claim, returned as a list of 1 or 2 RelevantClaims -- presented
    together rather than fused into one "Venus is Leo"-style blended
    statement, which is less astrologically standard than giving the
    planet's own significations and the sign's own qualities as
    paired facts for synthesis to combine (confirmed with Liam)."""

    tag = "ascendant" if role == "ascendant" else role
    sign_claim = _resolve_vedic_claim(f"vedic_sign:{tag}:{sign}")
    claims = [sign_claim] if sign_claim is not None else []

    if role in _VEDIC_PLANET_MEANING_BODIES:
        planet_claim = _resolve_vedic_claim(f"vedic_planet:{role}")
        if planet_claim is not None:
            claims.append(planet_claim)

    return claims


def _resolve_vedic_house_claim(body: str, house: int):
    """Combinatorial-Meaning Expansion Phase 5: the Vedic counterpart
    to _resolve_natal_house_claim. Same most-specific-wins mechanism
    (fewest feature_ids) as the Western resolver -- the generic
    vedic_house:{body}:{house} tag is shared across all 22 _ALL_BODIES
    on the body-agnostic bhava claim (knowledge/claims/seeds/
    vedic_astrology.py's own established pattern), while the nine
    classical Navagraha now also have a single-tag, graha-specific
    claim that automatically outranks it. Honest None degrade never
    happens for a body actually in a chart (every _ALL_BODIES member
    has the generic fallback) -- this only returns None for a
    genuinely invalid tag."""

    tag = f"vedic_house:{body}:{house}"
    matches = resolve_claims({}, lens_id="vedic_astrology", features=[tag])
    if not matches:
        return None
    return min(matches, key=lambda item: len(item.claim.feature_ids))


def _sidereal_sign_now(body: str, as_of_utc_time: datetime) -> str:
    """Today's real transiting position in sidereal (Lahiri) terms --
    the one piece that didn't exist anywhere in the engine before this
    phase (astrology/sidereal.py only ever derives from a NATAL
    tropical chart -- every call site in the repo confirmed natal-
    only). Composes three already-existing primitives (get_astronomy,
    get_ayanamsa, sidereal_longitude) rather than adding new engine
    machinery."""

    astronomy = get_astronomy(as_of_utc_time)
    ayanamsa = get_ayanamsa(astronomy["julian_day"])
    sidereal_lon = sidereal_longitude(astronomy["bodies"][body]["longitude"], ayanamsa)
    return longitude_to_zodiac(sidereal_lon)["sign"]


def _identity_field(label: str, claim, plain_note: str) -> dict:
    """The result-dict shape for a standing natal identity anchor.
    `note` is always present (a short, honest description -- the
    prior behavior, kept as a fallback); when a sign claim resolved
    (the normal case -- all 219 sign claims cover every western body
    plus the Ascendant), `claim_text`/`claim_id`/`source_ids` are
    added so the identity anchor carries a real, cited interpretation
    instead of a bare label."""

    field = {"label": label, "note": plain_note}
    if claim is not None:
        field["claim_text"] = claim.claim.statement
        field["claim_id"] = claim.claim.claim_id
        field["source_ids"] = list(claim.claim.source_ids)
    return field


def _vedic_identity_field(label: str, nakshatra: str | None, pada: int | None, claims: list, plain_note: str) -> dict:
    """The result-dict shape for a Vedic (sidereal) identity anchor --
    same `note`-always-present, `claim_text` when real content
    resolved pattern as `_identity_field`, extended for `claims` being
    a LIST of 1-2 items (sign-meaning plus, where a real karaka
    exists, planet-meaning -- see _resolve_vedic_sign_fusion) rather
    than a single claim."""

    field = {"label": label, "note": plain_note}
    if nakshatra is not None:
        field["nakshatra"] = nakshatra
        field["nakshatra_pada"] = pada
    if claims:
        field["claim_text"] = " ".join(c.claim.statement for c in claims)
        field["claim_ids"] = [c.claim.claim_id for c in claims]
        field["source_ids"] = sorted({sid for c in claims for sid in c.claim.source_ids})
    return field


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


def _pick_action_prompt(daily_claims, hits: list[dict] | None = None):
    """Returns (prompt_text, source_claim_id) -- the claim_id lets
    callers (e.g. the web scaffold) show real attribution for the
    action prompt instead of inferring it after the fact.

    Moon phase is no longer unconditional (it's now a tiered hit like
    everything else -- see astrology/daily_hits.py -- absent on
    ordinary, non-New/Full days), so the fallback chain now has one
    more tier below it: any surviving hit at all, before finally
    reaching the true catch-all for a genuinely quiet day."""

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

    for item in daily_claims:
        if item.claim.claim_id.startswith("astrology_daily_moon_phase"):
            return (
                _ACTION_PROMPTS.get(
                    item.claim.life_domain, "Match today's pace instead of forcing yesterday's."
                ),
                item.claim.claim_id,
            )

    if hits:
        return _ACTION_PROMPTS["cyclicality"], hits[0]["hit_id"]

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

# Shown when astrology.daily_hits.compute_daily_hits() returns nothing
# (no standout/background-tier activity today) -- a diagnostic/API
# field (result["astrology_highlights_note"]), never injected verbatim
# into the reading prose itself (the style guide's plain-voice rules
# forbid jargon like "background noise" appearing in user-facing text).
_ASTROLOGY_QUIET_NOTE = "Nothing in today's sky rises above routine background noise -- no standout events today."

# The one hand-written, style-guide-compliant fallback for a fully
# quiet day: no surviving hits AND no day-pillar relationship claim,
# so daily_claims is empty too. Without this, _assemble_reading_text([])
# would silently return "" -- a latent bug this rework makes
# materially more likely, since moon phase is no longer unconditional.
_QUIET_DAY_READING = "Nothing's pulling hard today. Whatever you do with it is genuinely up to you."


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
    phase, when it resolved (it's now a tiered hit like everything
    else -- present only on a New/Full Moon day, see astrology/
    daily_hits.py), anchors the reading; otherwise the highest-
    priority claim does. Up to _MAX_FALLBACK_SUPPORTING_CLAIMS other
    resolved claims follow, ranked by priority, joined with rotating
    connector phrases instead of raw concatenation. A single resolved
    claim is returned as-is -- no connector needed for a one-claim
    day. daily_claims here only ever contains curated fragments (the
    computed-fact hit records built for hits without one are
    deliberately excluded -- see build_daily_reading -- since this
    path never calls an LLM and should only ever emit pre-written,
    already-reviewed sentences, never assemble hit-derived prose
    freely). Returns "" when daily_claims is empty; build_daily_reading
    replaces that with _QUIET_DAY_READING.
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


def _render_hit_block(hit: dict) -> str:
    """One backend-only grounding line for a single resolve->tier'd
    hit -- house/orb/contact/retrograde facts, never the interpretive
    prose itself. Planet/aspect/house names stay backend per the
    grounding rules; this is disambiguation for the model's own
    reasoning, not content to quote verbatim.

    `hit.get("natal_sign_note")` (set by build_daily_reading, only
    for hits genuinely touching a natal point today -- see its own
    docstring) is appended as one more grounding line when present:
    the natal sign-meaning of whatever point the hit is about,
    letting synthesis fuse "your naturally private Scorpio Venus"
    with "eases today via transiting Jupiter" into one sentence,
    rather than leaving sign meaning as an unpaired, context-free
    fact. `hit.get("natal_house_note")` is the same idea for the
    house a transit_aspect hit's TRANSITING body currently occupies
    (see _resolve_house_claim) -- NOT a natal placement.
    `hit.get("target_natal_house_note")` is the natal point's OWN
    birth house instead (see _resolve_natal_house_claim) -- a real
    audit found reading copy had confused these two, stating a natal
    planet's house with a number sourced from nowhere in the engine;
    the two grounding lines below are deliberately labeled
    unambiguously so synthesis can't make the same mix-up.
    `hit.get("house_cusp_sign_note")` is a further, separate atomic
    fact about that same natal house: what sign colors its affairs in
    this chart (see _resolve_house_cusp_sign_claim) -- distinct from
    which planet occupies it, real even with no planet there at all.
    `hit.get("vedic_sign_note")` is the same idea for the Vedic/
    sidereal lens -- today's real transiting sidereal sign for this
    hit's own transiting body, when it's genuinely relevant."""

    r = hit["resolution"]
    d = hit["display"]

    if hit["kind"] == "eclipse":
        line = (
            f"  [{hit['tier']}] eclipse: {d['eclipse_type']} eclipse at {d['sign']} "
            f"{d['degree']} degrees, exact around {d['utc_time']}. Contact: {r['contact']} "
            f"(house {r['natal_house']}, nearest point {r['nearest_natal_point']}, "
            f"{r['orb_to_nearest']:.1f} degrees away)."
        )
        if hit["nodal"] is not None:
            line += f"\n    Nodal-axis amplification: {hit['nodal']['amplification_note']}"
    elif hit["kind"] == "transit_aspect":
        retro = " (retrograde)" if d["retrograde"] else ""
        line = (
            f"  [{hit['tier']}] transit: {d['transiting_body']} {d['aspect']} natal "
            f"{d['target_role']}{retro}, orb {r['orb_to_nearest']:.2f} degrees, contact: "
            f"{r['contact']}. Transiting {d['transiting_body']} is currently PASSING THROUGH "
            f"natal house {r['natal_house']} (not {d['transiting_body']}'s own birth house)."
        )
    else:  # moon_phase
        phase_label = hit["hit_id"].split(":", 1)[1].replace("_", " ")
        line = (
            f"  [{hit['tier']}] moon phase: {phase_label}. Nearest natal point: "
            f"{r['nearest_natal_point']} ({r['orb_to_nearest']:.2f} degrees, contact: {r['contact']})."
        )

    natal_sign_note = hit.get("natal_sign_note")
    if natal_sign_note:
        line += f"\n    Natal {r['nearest_natal_point']}'s sign meaning: {natal_sign_note}"

    natal_house_note = hit.get("natal_house_note")
    if natal_house_note:
        line += f"\n    Transiting body's current (transit-through) house meaning: {natal_house_note}"

    target_natal_house_note = hit.get("target_natal_house_note")
    if target_natal_house_note:
        line += f"\n    Natal {r['nearest_natal_point']}'s OWN birth house: {target_natal_house_note}"

    house_cusp_sign_note = hit.get("house_cusp_sign_note")
    if house_cusp_sign_note:
        line += f"\n    Sign on that house's cusp: {house_cusp_sign_note}"

    vedic_sign_note = hit.get("vedic_sign_note")
    if vedic_sign_note:
        line += f"\n    Vedic (sidereal): {vedic_sign_note}"

    return line


def _render_daily_narrative_input(
    narrative_claims: list[NarrativeClaim],
    hits: list[dict] | None = None,
) -> str:
    """Plain-text CLAIM_ID/STATEMENT/SOURCE block for today's claims,
    same shape as N4's render_narrative_input(), plus a per-hit
    grounding section and an OVERCLAIM CONSTRAINTS section built from
    `hits` -- astrology.daily_hits.compute_daily_hits' output, already
    resolved and tiered.

    Replaces the old free-text eclipse-context block and the raw,
    UNFILTERED transit-data dump: both were the actual mechanism
    behind a real live bug (an eclipse called "exact" when it was
    5.69 degrees from natal MC, and a citation list naming irrelevant
    houses) -- see lenses/overclaim_guard.py and astrology/
    daily_hits.py's docstrings for the full story. `hits` is already
    filtered to standout+background tier, so every hit named here is
    something genuinely worth the reading's attention, not a spray of
    every placement in the chart."""

    lines = []

    for claim in narrative_claims:
        lines.append(f"- CLAIM_ID: {claim.claim_id}")
        lines.append(f"  TRADITION: {claim.tradition}")
        lines.append(f"  LIFE_DOMAIN: {claim.life_domain or 'general'}")
        lines.append(f"  STATEMENT: {claim.statement}")
        lines.append(f"  SOURCE: {claim.source}")

    hits = hits or []

    if hits:
        lines.append("")
        lines.append("# Today's active astrological hits (real, resolved, tiered -- ground your writing in these)")
        lines.append("")
        for hit in hits:
            lines.append(_render_hit_block(hit))

        constraints = build_batch_overclaim_constraints(hits)
        if constraints:
            lines.append("")
            lines.append("# OVERCLAIM CONSTRAINTS (follow exactly, per hit -- see grounding rule 6)")
            lines.append("")
            lines.append(constraints)
    else:
        lines.append("")
        lines.append("# Today's active astrological hits")
        lines.append("")
        lines.append(
            "  Nothing astrologically significant is active today -- no standout or "
            "background-tier hits. Say so plainly if nothing else below fills the reading; "
            "see grounding rule 7."
        )

    return "\n".join(lines)


def _synthesize_reading(daily_claims, backend: NarrativeBackend, hits: list[dict]):
    """
    Real synthesis path: builds today's claims into the daily
    synthesis prompt (lenses.daily_narrative_style) and calls the
    backend. Returns (reading_text, validation_dict) on success, or
    (None, None) if the backend can't run (no API key, or a backend-
    level failure) -- the caller falls back to the deterministic path
    in that case. validation_dict carries check_coverage() (kept
    informational for daily mode -- a claim the model correctly folded
    into implicit context, per the synthesis addendum, will legitimately
    score low on keyword overlap without that being a real bug),
    fact_check()'s findings (a real check -- catches invented
    specificity the source claims don't support), and (new)
    overclaim_findings from check_batch_overclaims -- the actual fix
    for a real live bug where an eclipse was called "exact" 5.69
    degrees off natal MC with nothing checking the generated text
    against what was actually computed.

    `hits` (astrology.daily_hits.compute_daily_hits output, already
    resolved and tiered) is passed through to _render_daily_narrative_input
    for the per-hit grounding block and the OVERCLAIM CONSTRAINTS
    section -- see that function's docstring.
    """

    narrative_claims = _to_narrative_claims(daily_claims)
    prompt = build_daily_synthesis_prompt(
        _render_daily_narrative_input(narrative_claims, hits)
    )

    try:
        reading_text = backend.synthesize(prompt)
    except (MissingAPIKeyError, NarrativeBackendError):
        return None, None

    coverage = check_coverage(narrative_claims, reading_text)
    fact_check_findings = fact_check(backend, narrative_claims, reading_text)
    overclaim_findings = check_batch_overclaims(reading_text, hits)

    validation = {
        "coverage_ratio": coverage.coverage_ratio,
        "coverage_missing_claim_ids": [c.claim_id for c in coverage.missing],
        "coverage_note": (
            "Informational only for daily mode: a claim folded into "
            "implicit context (per the synthesis addendum) can score "
            "low here without being a real omission."
        ),
        "fact_check_findings": fact_check_findings,
        "overclaim_findings": overclaim_findings,
    }

    return reading_text, validation


def _computed_hit_claim(hit: dict) -> dict:
    """A citable record for a surviving hit with no matching curated
    fragment -- a plain, backend-generated factual summary built from
    the hit's own resolved display data, not hand-written prose. This
    is the concrete fix for a real live bug: the old citation list
    was built from an unscoped feature-tag sweep (every house any
    transiting body happened to occupy) with no connection to what
    the reading actually discussed. Every surviving hit is citable
    now, tied to its own hit_id, whether or not a hand-written
    fragment exists for it -- the same "computed fact, no
    interpretive claim" treatment `sun_sign` (today's real transiting
    Sun, a live astronomical fact rather than an interpretive
    statement) already gets in the result dict below (source_ids=[]
    rather than inventing a book citation for a raw computed number)."""

    r = hit["resolution"]
    d = hit["display"]

    if hit["kind"] == "eclipse":
        text = (
            f"A {d['eclipse_type']} eclipse at {d['sign']} {d['degree']} degrees -- "
            f"{r['contact']} on your {r['nearest_natal_point']} (house {r['natal_house']})."
        )
    elif hit["kind"] == "transit_aspect":
        text = (
            f"Transiting {d['transiting_body']} {d['aspect']} your natal {d['target_role']} "
            f"(orb {r['orb_to_nearest']:.1f} degrees, house {r['natal_house']})."
        )
    else:  # moon_phase
        phase_label = hit["hit_id"].split(":", 1)[1].replace("_", " ")
        text = f"Today is a {phase_label} -- {r['contact']} with your {r['nearest_natal_point']}."

    return {
        "claim_text": text,
        "sources": [{"type": "computed_event", "value": hit["hit_id"]}],
        "claim_id": hit["hit_id"],
        "source_ids": [],
        "life_domain": None,
    }


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
    hits = compute_daily_hits(natal_chart, as_of_utc_time)
    highlights = compute_todays_highlights(natal_chart, as_of_utc_time)

    # daily_transit_aspects/daily_moon_phase, fed to the existing
    # concepts->features->resolve_claims machinery below, are now
    # scoped to SURVIVING hits only -- previously this fed the full,
    # unfiltered sweep (every transiting body's every aspect and
    # house placement, regardless of significance), which is the
    # actual mechanism behind a real live bug: a citation list naming
    # houses with no connection to what the reading discussed. See
    # astrology/daily_hits.py's docstring for the full story.
    aspect_hits = [h for h in hits if h["kind"] == "transit_aspect"]
    moon_hit = next((h for h in hits if h["kind"] == "moon_phase"), None)

    observations = {
        "astrology": natal_chart,
        "daily_transit_aspects": [
            {
                "transiting_body": h["display"]["transiting_body"],
                "target_role": h["display"]["target_role"],
                "aspect": h["display"]["aspect"],
                "orb": h["resolution"]["orb_to_nearest"],
            }
            for h in aspect_hits
        ],
        "daily_day_pillar_relationship": day_pillar_relationship,
    }
    if moon_hit is not None:
        # Only fed as a claims-resolution observation when today's
        # phase actually survived as a hit (New/Full Moon) -- moon
        # phase is one more tiered hit now, not an unconditional
        # claim. moon_phase_data (above) still always exists for the
        # separate result["moon_phase"] display block regardless.
        observations["daily_moon_phase"] = moon_phase_data

    concepts = normalise_observations(observations)
    features = build_features(concepts)
    daily_claims = _resolve_daily_claims(concepts, features)

    # Natal sign-meaning content: 219 already-reviewed claims exist
    # for exactly this (astrology_{body}_sign_{sign}.json) but were
    # never surfaced in daily mode -- see _resolve_sign_claim's
    # docstring for why that's a targeted lookup here, not a
    # daily_mode theme tag. Full chart considered (role_longitudes
    # covers every natal point), but only surfaced when relevant:
    # the Big-3 identity anchors always (standing identity context,
    # same as before -- now with a real citation instead of a bare
    # label), and whichever natal points today's real hits actually
    # touch, never unconditionally.
    role_longitudes = natal_targets(natal_chart)
    sign_claims_used: dict[str, object] = {}

    def _use_sign_claim(role, sign):
        if role is None or sign is None:
            return None
        item = _resolve_sign_claim(role, sign)
        if item is None:
            # Combinatorial-Meaning Expansion Phase 3: honest last-
            # resort fallback so a role with no body-specific sign-
            # claim family (e.g. lilith_true) still gets real sign
            # meaning instead of total silence -- never a substitute
            # for role-specific content, only tried on a genuine miss.
            item = _resolve_pure_sign_claim(sign)
        if item is None:
            return None
        if item.claim.claim_id not in sign_claims_used:
            sign_claims_used[item.claim.claim_id] = item
            daily_claims.append(item)
        return item

    natal_sun_sign = longitude_to_zodiac(natal_chart["bodies"]["sun"]["longitude"])["sign"]
    natal_moon_sign = longitude_to_zodiac(natal_chart["bodies"]["moon"]["longitude"])["sign"]
    rising_sign = longitude_to_zodiac(natal_chart["houses"]["angles"]["ascendant"])["sign"]

    sun_sign_claim = _use_sign_claim("sun", natal_sun_sign)
    moon_sign_claim = _use_sign_claim("moon", natal_moon_sign)
    ascendant_sign_claim = _use_sign_claim("ascendant", rising_sign)

    # Natal house content: a natal point's OWN birth house (e.g. natal
    # Saturn radix in house 10), never to be confused with the house a
    # TRANSITING body is currently passing through (_use_house_claim,
    # below -- a real audit found reading copy had blurred exactly
    # this distinction, stating a natal planet's house with a number
    # that traced to nothing Celeste actually computed). Ascendant
    # excluded -- it's a house cusp itself, not "in" a house.
    # Shared dedupe cache: _resolve_house_claim (transit-through) and
    # _resolve_natal_house_claim (natal-own) both draw from the SAME
    # astrology_house_N claim family (just different tags on the same
    # claim file), so a transiting body currently sitting in the same
    # house number as a natal point's own house must not append that
    # claim to daily_claims twice.
    house_meaning_claims_used: dict[str, object] = {}

    def _use_natal_house_claim(role, house):
        if role is None or house is None:
            return None
        item = _resolve_natal_house_claim(role, house)
        if item is None:
            return None
        if item.claim.claim_id not in house_meaning_claims_used:
            house_meaning_claims_used[item.claim.claim_id] = item
            daily_claims.append(item)
        return item

    sun_house_claim = _use_natal_house_claim("sun", natal_chart["bodies"]["sun"]["house"])
    moon_house_claim = _use_natal_house_claim("moon", natal_chart["bodies"]["moon"]["house"])

    # Sign-on-house-cusp (Combinatorial-Meaning Expansion, Phase 2): a
    # SEPARATE atomic fact from "which planet occupies the house" above
    # -- what sign colors the house's affairs in this chart, real even
    # with no planet there. Own dedupe cache (different claim
    # namespace: astrology_sign_{sign}_house_{N}, not astrology_house_N
    # or astrology_{planet}_house_N). Only resolved for the 8 non-
    # angular houses (_ANGULAR_HOUSES honest-skips, since that content
    # already exists as the Ascendant/MC/IC/Descendant-by-sign claims).
    house_cusp_sign_claims_used: dict[str, object] = {}

    def _use_house_cusp_sign_claim(house):
        if house is None or house in _ANGULAR_HOUSES:
            return None
        sign = _house_cusp_sign(natal_chart, house)
        item = _resolve_house_cusp_sign_claim(house, sign)
        if item is None:
            return None
        if item.claim.claim_id not in house_cusp_sign_claims_used:
            house_cusp_sign_claims_used[item.claim.claim_id] = item
            daily_claims.append(item)
        return item

    for hit in hits:
        if hit["kind"] not in ("transit_aspect", "eclipse", "moon_phase"):
            continue
        role = hit["resolution"]["nearest_natal_point"]
        if role is None:
            continue
        real_role = natal_chart["rulership"]["chart_ruler"] if role == "chart_ruler" else role
        longitude = role_longitudes.get(real_role)
        sign = longitude_to_zodiac(longitude)["sign"] if longitude is not None else None
        claim = _use_sign_claim(real_role, sign)
        if claim is not None:
            hit["natal_sign_note"] = claim.claim.statement

        natal_house = natal_chart["bodies"].get(real_role, {}).get("house")
        natal_house_claim = _use_natal_house_claim(real_role, natal_house)
        if natal_house_claim is not None:
            hit["target_natal_house_note"] = (
                f"natal {real_role} radix is in house {natal_house} -- {natal_house_claim.claim.statement}"
            )

        cusp_sign_claim = _use_house_cusp_sign_claim(natal_house)
        if cusp_sign_claim is not None:
            hit["house_cusp_sign_note"] = cusp_sign_claim.claim.statement

    # House-meaning content: same targeted-lookup restoration as the
    # sign-meaning content above, for the daily_transit_house:{body}:
    # {house} tag family PR #4's rebuild orphaned (see
    # _resolve_house_claim's docstring). Only for transit_aspect hits
    # -- eclipse/moon-phase hits aren't "a transiting body currently
    # in a house" facts the same way, and never an unconditional
    # sweep over all 10 transiting bodies' house placements.
    def _use_house_claim(transiting_body, house):
        if house is None:
            return None
        item = _resolve_house_claim(transiting_body, house)
        if item is None:
            return None
        if item.claim.claim_id not in house_meaning_claims_used:
            house_meaning_claims_used[item.claim.claim_id] = item
            daily_claims.append(item)
        return item

    for hit in hits:
        if hit["kind"] != "transit_aspect":
            continue
        claim = _use_house_claim(hit["display"]["transiting_body"], hit["resolution"]["natal_house"])
        if claim is not None:
            hit["natal_house_note"] = claim.claim.statement

    # Vedic (sidereal): full chart considered in the data layer (the
    # sidereal chart and current Dasha standing are always computed),
    # but surfaced with the same relevance discipline as the Western
    # content above -- Dasha standing and natal sidereal Big-3 always
    # (standing context, like the tropical identity anchors), today's
    # transiting sidereal sign only for whichever body a real hit
    # already touches, never an unconditional sweep. See
    # _resolve_vedic_claim's docstring for why this bypasses the
    # daily_mode filter the same way the Western sign lookup does.
    vedic_claims_used: dict[str, object] = {}

    def _use_vedic_claims(items):
        result = []
        for item in items:
            if item.claim.claim_id not in vedic_claims_used:
                vedic_claims_used[item.claim.claim_id] = item
                daily_claims.append(item)
            result.append(item)
        return result

    birth_utc_time = datetime.fromisoformat(natal_chart["utc_time"])
    sidereal_natal = build_sidereal_chart(natal_chart)

    vimshottari = build_vimshottari_dasha(sidereal_natal, birth_utc_time, as_of_utc_time)
    yogini = build_yogini_dasha(sidereal_natal, birth_utc_time, as_of_utc_time)
    chara = build_chara_dasha(sidereal_natal, birth_utc_time, as_of_utc_time)

    dasha_lords = {
        vimshottari["current_mahadasha"]["lord"],
        vimshottari["current_antardasha"]["lord"],
        vimshottari["current_pratyantardasha"]["lord"],
        vimshottari["current_sookshma_dasha"]["lord"],
    }
    dasha_lord_claims = {}
    for lord in dasha_lords:
        item = _resolve_vedic_claim(f"dasha_mahadasha:{lord}")
        if item is not None:
            dasha_lord_claims[lord] = item
    _use_vedic_claims(dasha_lord_claims.values())

    chara_sign_claim = _resolve_vedic_claim(f"chara_dasha_sign:{chara['current_sign_dasha']['sign']}")
    if chara_sign_claim is not None:
        _use_vedic_claims([chara_sign_claim])

    # Natal sidereal Big-3 -- same identity-anchor treatment as the
    # tropical Sun/Moon/Ascendant, sign-meaning + planet-meaning
    # presented together rather than one blended "Venus is Leo"-style
    # statement (confirmed with Liam -- see _resolve_vedic_sign_fusion).
    vedic_sun_sign = sidereal_natal["bodies"]["sun"]["sign"]
    vedic_moon_sign = sidereal_natal["bodies"]["moon"]["sign"]
    vedic_ascendant_sign = sidereal_natal["ascendant"]["sign"]

    vedic_sun_claims = _use_vedic_claims(_resolve_vedic_sign_fusion("sun", vedic_sun_sign))
    vedic_moon_claims = _use_vedic_claims(_resolve_vedic_sign_fusion("moon", vedic_moon_sign))
    vedic_ascendant_claims = _use_vedic_claims(_resolve_vedic_sign_fusion("ascendant", vedic_ascendant_sign))

    # Natal sidereal bhava (house) -- Combinatorial-Meaning Expansion
    # Phase 5. Confirmed by direct search: nothing in this pipeline
    # cited ANY bhava content before this, at all -- the body-agnostic
    # bhava claims existed but were never wired in. Ascendant excluded,
    # same reasoning as the tropical Big-3: it's a house cusp itself,
    # not "in" a house.
    vedic_sun_house = sidereal_natal["bodies"]["sun"]["house"]
    vedic_moon_house = sidereal_natal["bodies"]["moon"]["house"]
    vedic_sun_house_claim = _resolve_vedic_house_claim("sun", vedic_sun_house)
    vedic_moon_house_claim = _resolve_vedic_house_claim("moon", vedic_moon_house)
    if vedic_sun_house_claim is not None:
        _use_vedic_claims([vedic_sun_house_claim])
    if vedic_moon_house_claim is not None:
        _use_vedic_claims([vedic_moon_house_claim])

    # Today's transiting sidereal sign -- only for a body already part
    # of a real hit today (never an unconditional sweep over all 10
    # transiting bodies, same discipline as the natal-sign grounding
    # above).
    for hit in hits:
        if hit["kind"] != "transit_aspect":
            continue
        body = hit["display"]["transiting_body"]
        sidereal_sign = _sidereal_sign_now(body, as_of_utc_time)
        fused = _use_vedic_claims(_resolve_vedic_sign_fusion(body, sidereal_sign))
        if fused:
            hit["vedic_sign_note"] = (
                f"transiting {body} is in sidereal {sidereal_sign} -- "
                + " ".join(c.claim.statement for c in fused)
            )

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

    # Every surviving hit is citable -- if its own specific feature
    # tag already matched a curated claim above, that claim IS its
    # citation (real prose, real source_ids); otherwise it gets a
    # computed-fact record here, tied to its own hit_id. Either way,
    # every hit named in the reading traces to something real, never
    # to an unrelated feature-tag match.
    matched_tags = {fid for item in daily_claims for fid in item.matched_features}
    uncited_hits = [h for h in hits if h["feature_tag"] not in matched_tags]
    for hit in uncited_hits:
        attributed.append(_computed_hit_claim(hit))

    reading_text = None
    synthesis_validation = None
    synthesis_method = "deterministic_fallback"

    if use_synthesis and (daily_claims or hits):
        reading_text, synthesis_validation = _synthesize_reading(
            daily_claims,
            backend or AnthropicNarrativeBackend(),
            hits,
        )
        if reading_text is not None:
            synthesis_method = "llm"

    if reading_text is None:
        reading_text = _assemble_reading_text(daily_claims)

    if not reading_text:
        # Genuinely nothing today -- no surviving hits, no day-pillar
        # relationship claim either. _assemble_reading_text([]) would
        # otherwise silently return "".
        reading_text = _QUIET_DAY_READING

    action_prompt, action_prompt_source_claim_id = _pick_action_prompt(daily_claims, hits)

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

    result = {
        "as_of_utc_time": as_of_utc_time.isoformat(),
        "claims": attributed,
        "reading": reading_text,
        "reading_source_claim_ids": (
            [item.claim.claim_id for item in daily_claims] + [h["hit_id"] for h in uncited_hits]
        ),
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
        "natal_sun_sign": _identity_field(
            natal_sun_sign, sun_sign_claim,
            "Your natal Sun sign -- standing identity context, not today's sky.",
        ),
        "natal_moon_sign": _identity_field(
            natal_moon_sign, moon_sign_claim,
            "Your natal Moon sign -- standing identity context, not today's sky.",
        ),
        "rising_sign": _identity_field(
            rising_sign, ascendant_sign_claim,
            "Your natal Ascendant (Rising) sign -- standing identity context, not today's sky.",
        ),
        "natal_sun_house": _identity_field(
            f"House {natal_chart['bodies']['sun']['house']}", sun_house_claim,
            "Your natal Sun's own birth house -- standing identity context, "
            "distinct from any house a transiting body is currently passing through.",
        ),
        "natal_moon_house": _identity_field(
            f"House {natal_chart['bodies']['moon']['house']}", moon_house_claim,
            "Your natal Moon's own birth house -- standing identity context, "
            "distinct from any house a transiting body is currently passing through.",
        ),
        "highlights": highlights,
        "astrology_highlights_note": None if hits else _ASTROLOGY_QUIET_NOTE,
        "vedic_dasha": {
            "mahadasha": vimshottari["current_mahadasha"],
            "antardasha": vimshottari["current_antardasha"],
            "pratyantardasha": vimshottari["current_pratyantardasha"],
            "sookshma": vimshottari["current_sookshma_dasha"],
            "yogini": yogini["current_yogini_dasha"],
            "chara_sign": chara["current_sign_dasha"],
            "lord_claims": [
                {
                    "lord": lord,
                    "claim_text": item.claim.statement,
                    "claim_id": item.claim.claim_id,
                    "source_ids": list(item.claim.source_ids),
                }
                for lord, item in dasha_lord_claims.items()
            ],
            "chara_sign_claim": (
                {
                    "claim_text": chara_sign_claim.claim.statement,
                    "claim_id": chara_sign_claim.claim.claim_id,
                    "source_ids": list(chara_sign_claim.claim.source_ids),
                }
                if chara_sign_claim is not None else None
            ),
            "note": (
                "Vedic (Vimshottari/Yogini/Chara) timing standing as of today -- "
                "doesn't change day to day (each level spans months to years), "
                "shown as standing context alongside today's reading."
            ),
        },
        "vedic_sun_sign": _vedic_identity_field(
            vedic_sun_sign,
            sidereal_natal["bodies"]["sun"]["nakshatra"], sidereal_natal["bodies"]["sun"]["nakshatra_pada"],
            vedic_sun_claims,
            "Your natal sidereal Sun sign (Lahiri ayanamsa) -- standing identity context, not today's sky.",
        ),
        "vedic_moon_sign": _vedic_identity_field(
            vedic_moon_sign,
            sidereal_natal["bodies"]["moon"]["nakshatra"], sidereal_natal["bodies"]["moon"]["nakshatra_pada"],
            vedic_moon_claims,
            "Your natal sidereal Moon sign (Lahiri ayanamsa) -- standing identity context, not today's sky.",
        ),
        "vedic_ascendant_sign": _vedic_identity_field(
            vedic_ascendant_sign, None, None,
            vedic_ascendant_claims,
            "Your natal sidereal Ascendant sign (Lahiri ayanamsa) -- standing identity context, not today's sky.",
        ),
        "vedic_sun_house": _vedic_identity_field(
            f"Bhava {vedic_sun_house}", None, None,
            [vedic_sun_house_claim] if vedic_sun_house_claim is not None else [],
            "Your natal sidereal Sun's own bhava (house) -- standing identity context, not today's sky.",
        ),
        "vedic_moon_house": _vedic_identity_field(
            f"Bhava {vedic_moon_house}", None, None,
            [vedic_moon_house_claim] if vedic_moon_house_claim is not None else [],
            "Your natal sidereal Moon's own bhava (house) -- standing identity context, not today's sky.",
        ),
    }

    eclipse_context = compute_eclipse_context(natal_chart, as_of_utc_time)
    if eclipse_context is not None:
        result["eclipse_context"] = eclipse_context

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
            if validation.get("overclaim_findings"):
                print(f"Overclaim guard: {validation['overclaim_findings']}")

        print()
        print(f"Moon: {result['natal_moon_sign']['label']}  |  Rising: {result['rising_sign']['label']}  |  Sun today: {result['sun_sign']['label']}")
        print(
            f"Vedic (sidereal): Sun {result['vedic_sun_sign']['label']}  |  "
            f"Moon {result['vedic_moon_sign']['label']}  |  Asc {result['vedic_ascendant_sign']['label']}  |  "
            f"Dasha {result['vedic_dasha']['mahadasha']['lord']}/{result['vedic_dasha']['antardasha']['lord']}"
        )

        eclipse_context = result.get("eclipse_context")
        if eclipse_context:
            resolution = eclipse_context["resolution"]
            print()
            print(
                f"Eclipse: {eclipse_context['type']} {eclipse_context['kind']} in "
                f"{eclipse_context['sign']} ({resolution['contact']}, house {resolution['natal_house']})"
            )

        highlighted_planets = result["highlights"]["highlighted_planets"]
        standouts = [p for p in highlighted_planets if p["tier"] == "standout"]
        if standouts:
            print()
            print("Standout today: " + ", ".join(p["body"] for p in standouts))

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
