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

The same deterministic fallback is also the enforcement mechanism for
lenses.overclaim_guard's checks (Query-Answering/Daily-Reading Repair
phase, extended by Synthesis Repair Brief Part 2.4): a real, audited
gap found the guard's findings were computed but never actually
gated anything -- a flagged LLM reading still shipped unchanged, since
neither web.py nor daily.py's own CLI path ever checked them before
showing the reading. _synthesize_reading() now rejects its own output
(returns reading_text=None, forcing this same fallback) whenever a
real overclaim finding fires, same treatment as a missing API key or
a backend error -- synthesis_method reports "guard_rejected"
specifically so this is distinguishable from "the backend was
unavailable" in the result.
"""

import argparse
import json
import sys
import time as _time
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
from astrology.daily_hits import attach_continuity_note, compute_arc_status, compute_daily_hits
from astrology.dasha import build_vimshottari_dasha
from astrology.event_significance import ASPECT_WEIGHTS, natal_targets
from astrology.key_events import EXACT_HIT_BODIES
from astrology.transits import TRANSIT_ORBS
from astrology.normaliser import longitude_to_zodiac
from astrology.sidereal import build_sidereal_chart, get_ayanamsa, sidereal_longitude
from astrology.time import local_to_utc
from astrology.yogini_dasha import build_yogini_dasha
from providers.astronomy import get_astronomy
from chinese.pillars import build_four_pillars
from chinese.ten_gods import build_ten_gods
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
from lenses.overclaim_guard import (
    build_batch_overclaim_constraints,
    check_batch_overclaims,
    check_house_number_overclaims,
    check_life_domain_overclaims,
    check_moon_phase_overclaims,
    check_occasion_overclaims,
)


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


def _resolve_aspect_claim(hit: dict):
    """One targeted lookup for what a transit_aspect hit's own aspect
    TYPE means -- e.g. "a trine lets the two placements involved flow
    together smoothly...". A real audit found this content already
    existed and was already being cited once per day per aspect type
    via the old blanket sweep, but never paired to the specific hit
    that earned it: every hit's own feature_tag is a hyper-specific
    per-pair string (daily_transit_aspect:{body}:{aspect}:{role}) that
    essentially no claim's feature_ids ever match, except 8 hand-
    written special-pair claims (e.g. Mars square Sun) -- so every
    OTHER hit fell through to _computed_hit_claim's bare, meaningless
    fact, even though real meaning for its aspect type existed
    elsewhere in the very same citation list. Checks both the hit's
    own hyper-specific tag (catches the 8 special pairs) and the
    generic transit_aspect:{aspect} tag (catches everything else) in
    one resolve_claims call, same most-specific-wins pattern as every
    other _resolve_*_claim helper here -- the special-pair claims'
    single feature_id naturally outranks the generic claims' three."""

    aspect = hit["display"]["aspect"]
    matches = resolve_claims(
        {}, lens_id="astrology",
        features=[hit["feature_tag"], f"transit_aspect:{aspect}"],
    )
    if not matches:
        return None
    return min(matches, key=lambda item: len(item.claim.feature_ids))


def _resolve_eclipse_type_claim(hit: dict):
    """One targeted lookup for what an eclipse hit's own (kind, type)
    combination means -- e.g. "a total solar eclipse marks the most
    complete kind of new beginning...". A full audit ("Pair meaning to
    every hit" brief) found NO eclipse-type content existed anywhere
    in this knowledge base before it -- every eclipse hit fell through
    to _computed_hit_claim's bare fact with no real interpretive
    meaning at all (a genuine content gap, unlike aspect-type hits,
    where real content existed but was disconnected -- a separate,
    already-fixed bug). Reuses astrology/daily_hits.py's own
    eclipse_type:{kind}_{type} feature_tag directly (see
    _resolve_eclipse_hit) -- no most-specific-wins needed here, there
    is exactly one claim per combination."""

    matches = resolve_claims({}, lens_id="astrology", features=[hit["feature_tag"]])
    return matches[0] if matches else None


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


_TEN_GOD_SLUGS = {
    "Friend": "friend", "Rob Wealth": "rob_wealth", "Eating God": "eating_god",
    "Hurting Officer": "hurting_officer", "Indirect Wealth": "indirect_wealth",
    "Direct Wealth": "direct_wealth", "Seven Killings": "seven_killings",
    "Direct Officer": "direct_officer", "Indirect Resource": "indirect_resource",
    "Direct Resource": "direct_resource",
}


def _resolve_ten_god_position_claim(position: str, ten_god: str):
    """Combinatorial-Meaning Expansion Phase 6: the Chinese/BaZi
    counterpart to _resolve_natal_house_claim. Same most-specific-
    wins mechanism -- the generic ten_god_{slug} claim is tagged
    across every position (chinese_zodiac.py's own established body-
    agnostic pattern), while the position-specific claim (added this
    phase) carries only the one matching tag and so always outranks
    it. `position` is a plain lowercase pillar name ("year", "month",
    "day", "hour"); "day" has no visible-stem tag (the Day Stem IS
    the Day Master, not a Ten God relative to itself) so it resolves
    via the hidden-stem tag instead -- honest by construction, not a
    special case to remember at call sites."""

    slug = _TEN_GOD_SLUGS.get(ten_god)
    if slug is None:
        return None
    tag = f"ten_god_hidden:day:{slug}" if position == "day" else f"ten_god:{position}:{slug}"
    matches = resolve_claims({}, lens_id="chinese_zodiac", features=[tag])
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


def _order_reading_claims(
    daily_claims,
    standing_claim_ids: set[str] | None = None,
    daily_mode_depth: str | None = None,
    primary_thread_claim_ids: set[str] | None = None,
):
    """
    Split the resolved daily claims into (moon_phase_item, ordered
    supporting_items), where supporting_items is ranked primarily by
    `primary_thread_claim_ids` (the real, computed claims that ground
    today's actual `_score_threads` headline thread -- see
    build_daily_reading's own `hit_claim_ids` side-channel), falling
    back to `_CLAIM_PRIORITY` (a small hardcoded list of legacy special-
    pair claim_ids) ONLY when there's no real primary thread today at
    all, with transit-aspect orb as a documented secondary tiebreak
    within either tier -- tighter orb means the aspect is more exactly
    in effect today, a real astrological quantity rather than an
    arbitrary tiebreaker.

    Fallback Headline-Wiring Fix (2026-09-01): before this,
    `_CLAIM_PRIORITY` (and, failing that, claim-construction order) was
    the ONLY ranking signal here, completely disconnected from
    `_score_threads`'s real, computed primary thread -- the same signal
    Exhibit A's Option A fix already anchors the real LLM prompt on.
    Any day landing on this deterministic path (guard rejection, or no
    API key) bypassed Option A's fix entirely and could headline
    whatever claim happened to resolve first during construction,
    regardless of real significance. `primary_thread_claim_ids` closes
    that gap: when today's real headline thread produced real, cited
    claims (the common case), those lead; `_CLAIM_PRIORITY` only
    engages as the fallback-of-the-fallback, for a genuinely near-
    silent day with no real convergence to defer to.

    Synthesis Repair Brief Part 7: standing-only claims (Big-3 sign/
    house, Vedic Dasha, Vedic sidereal Big-3, Chinese Ten-God -- the
    same set Part 6 already drops from the real synthesis prompt) are
    excluded here too, same reasoning applied to the deterministic
    fallback path -- without this, a quiet day with no real activation
    still reads as "your Sun is in Cancer, your Moon is in Libra"
    every time, exactly the "reciting natal facts with no real
    activation today" bug Part 6 fixed for the LLM path but left open
    here. A claim genuinely hit-touched today is never in
    standing_claim_ids (see build_daily_reading), so it still surfaces
    normally.

    Uncapped otherwise: every remaining resolved claim is represented
    in the fallback reading (see _assemble_reading_text) so `reading`
    and the attributed `claims` list can never go out of sync beyond
    the deliberate standing-exclusion above.

    Returns (None, []) in the degenerate case where moon phase somehow
    didn't resolve (shouldn't happen -- it's a standalone daily fact --
    but this function doesn't assume it as a precondition).
    """

    standing_claim_ids = standing_claim_ids or set()
    primary_thread_claim_ids = primary_thread_claim_ids or set()
    moon_phase_item = None
    supporting = []

    for item in daily_claims:
        if item.claim.claim_id in standing_claim_ids:
            continue
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
        if primary_thread_claim_ids:
            # A real, computed primary thread exists today -- its own
            # claims are the ONLY primary signal here; _CLAIM_PRIORITY's
            # legacy list is not consulted at all in this branch (it's
            # the fallback-of-the-fallback, only reached below when
            # there's no real primary thread to defer to at all).
            return (0, 0) if claim_id in primary_thread_claim_ids else (1, 0)
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
    cap = _MAX_FALLBACK_SUPPORTING_CLAIMS
    if daily_mode_depth in ("short", "near_silent"):
        # Synthesis Repair Brief Part 7: confidence-scaled, same as
        # real synthesis -- a day that doesn't clear the bar for a
        # full reading gets a single grounded thread, not padded with
        # up to 3 more claims to look like a fuller day than it is.
        # moon_phase_item (if any) already counts as that one thread,
        # so a genuinely quiet day with no moon-phase hit still gets
        # exactly one supporting claim, never zero-if-avoidable.
        cap = 0 if moon_phase_item is not None else min(1, _MAX_FALLBACK_SUPPORTING_CLAIMS)
    ordered_supporting = [item for _, item in ranked][:cap]

    return moon_phase_item, ordered_supporting


def _assemble_reading_text(
    daily_claims,
    standing_claim_ids: set[str] | None = None,
    daily_mode_depth: str | None = None,
    primary_thread_claim_ids: set[str] | None = None,
):
    """
    DETERMINISTIC FALLBACK ONLY -- used when _synthesize_reading()
    can't run (no ANTHROPIC_API_KEY) or its output was rejected by the
    overclaim guard (synthesis_method == "guard_rejected"). This is
    ordering + connector phrases, not real synthesis; it does not find
    a throughline or fold claims together the way the real synthesis
    path does -- but per Synthesis Repair Brief Part 7 it now follows
    the SAME two tone rules real synthesis does, applied at the level
    this deterministic path actually can:

    - Standing-only content (Big-3 sign/house, Vedic Dasha, Vedic
      sidereal Big-3, Chinese Ten-God) is excluded from consideration
      entirely (see _order_reading_claims) -- never recited here just
      because nothing else survived, matching Part 6's rule for the
      real prompt.
    - Confidence-scaled: daily_mode_depth "short"/"near_silent" caps
      this to a single grounded thread (moon phase if present,
      otherwise the single highest-priority supporting claim) instead
      of up to _MAX_FALLBACK_SUPPORTING_CLAIMS -- a thin day reads as
      thin, not padded to look like a full one. "full" (or unset, for
      backward-compatible direct callers) keeps the existing cap.

    Fallback Headline-Wiring Fix: `primary_thread_claim_ids` (build_
    daily_reading's own union of `hit_claim_ids` over today's real
    `_score_threads` headline_thread hit(s)) is now the PRIMARY
    ordering signal -- see _order_reading_claims's own docstring. This
    closes a real, confirmed gap: before this, the deterministic path
    had no way to defer to the same real primary thread Option A
    already anchors the LLM prompt on, so a guard-rejected or no-API-
    key day could headline whatever claim happened to resolve first
    during construction -- completely disconnected from real
    significance, and untouched by Option A's fix (which lives
    entirely inside the LLM prompt this path never uses).

    Moon phase, when it resolved (it's now a tiered hit like
    everything else -- present only on a New/Full Moon day, see
    astrology/daily_hits.py), anchors the reading; otherwise the
    highest-priority claim does (now the real primary thread's own
    claim, when one exists). Any further resolved claims (within the
    depth-scaled cap above) follow, ranked by priority, joined with
    rotating connector phrases instead of raw concatenation. A single
    resolved claim is returned as-is -- no connector needed for a one-
    claim day. daily_claims here only ever contains curated fragments
    (the computed-fact hit records built for hits without one are
    deliberately excluded -- see build_daily_reading -- since this
    path never calls an LLM and should only ever emit pre-written,
    already-reviewed sentences, never assemble hit-derived prose
    freely). Returns "" when nothing narrative-eligible remains
    (daily_claims was empty, or everything present was standing-only);
    build_daily_reading replaces that with _QUIET_DAY_READING -- an
    honest "today's sky isn't saying much" line, not a recitation of
    inert Big-3 content.
    """

    moon_phase_item, ordered_supporting = _order_reading_claims(
        daily_claims, standing_claim_ids, daily_mode_depth, primary_thread_claim_ids
    )

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
    hit's own transiting body, when it's genuinely relevant.
    `hit.get("aspect_meaning_note")` is what the hit's own aspect TYPE
    means (see _resolve_aspect_claim) -- paired to the specific hit
    rather than left as a disconnected, once-per-day-per-type fact the
    model would have to notice and connect on its own.
    `hit.get("eclipse_meaning_note")` is the same idea for an eclipse
    hit's own (kind, type) combination (see _resolve_eclipse_type_claim)
    -- real content authored for a gap that previously had none.
    `hit.get("ingress_sign_note")` is the body-agnostic meaning of the
    sign a sign_ingress hit's body has just entered (see
    _resolve_pure_sign_claim, called directly for these hits).
    `hit.get("recurrence_note")` (set directly by astrology/daily_hits.
    py's _resolve_return_hits, not by build_daily_reading) names a
    slow body's earlier/later passes over the same natal degree when a
    return is a multi-pass (retrograde-driven) event, not a single
    exact date. `hit.get("continuity_note")` is the same idea for an
    ordinary transit_aspect hit (see astrology/daily_hits.py's
    _attach_continuity_note) -- today's contact isn't the first time
    this slow body has crossed this exact natal degree, so synthesis
    can correctly say "this is a return visit", not imply a single
    isolated moment.

    Delegates the kind-specific base fact (aspect/orb/contact, plus
    continuity/recurrence/nodal-amplification, which are factual
    rather than interpretive) to _render_hit_core_line() -- the SAME
    text used, on its own with no meaning-notes appended, for a non-
    primary-thread hit's one-line compressed rendering (Exhibit A
    fix, see _render_daily_narrative_input's own docstring)."""

    return _render_hit_core_line(hit) + _render_hit_meaning_notes(hit)


def _render_hit_core_line(hit: dict) -> str:
    """The kind-specific base fact line for one hit -- aspect/orb/
    contact/house, plus continuity_note/recurrence_note/nodal-
    amplification (factual "this has happened before" context, not
    interpretation) -- with NO meaning-notes (sign/house/aspect/
    eclipse/ingress meaning) appended. This is the full text of a
    non-primary-thread hit's compressed rendering; _render_hit_block
    appends the meaning-notes on top of this same text for a primary-
    thread hit's full grounding block."""

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
        if hit.get("continuity_note"):
            line += f"\n    {hit['continuity_note']}"
    elif hit["kind"] == "return":
        retro = " (retrograde)" if d["retrograde"] else ""
        line = (
            f"  [{hit['tier']}] RETURN: {d['transiting_body']} returns to its own natal "
            f"degree ({d['sign']} {d['degree']:.2f}){retro}, orb {r['orb_to_nearest']:.2f} "
            f"degrees, contact: {r['contact']}. This is {d['transiting_body']}'s OWN birth "
            f"house (house {r['natal_house']})."
        )
        if hit.get("recurrence_note"):
            line += f"\n    {hit['recurrence_note']}"
    elif hit["kind"] == "station":
        motion = "retrograde" if d["retrograde"] else "direct"
        line = (
            f"  [{hit['tier']}] STATION: {d['transiting_body']} stations {motion} at "
            f"{d['sign']} {d['degree']:.2f} degrees, currently in natal house "
            f"{r['natal_house']}. Nearest natal point: {r['nearest_natal_point']} "
            f"({r['orb_to_nearest']:.2f} degrees, contact: {r['contact']})."
        )
    elif hit["kind"] == "sign_ingress":
        line = (
            f"  [{hit['tier']}] SIGN INGRESS: {d['transiting_body']} enters {d['sign']} "
            f"(from {d['from_sign']})."
        )
    elif hit["kind"] == "natal_house_ingress":
        line = (
            f"  [{hit['tier']}] HOUSE INGRESS: {d['transiting_body']} enters natal house "
            f"{r['natal_house']} (from house {d['from_house']})."
        )
    else:  # moon_phase
        phase_label = hit["hit_id"].split(":", 1)[1].replace("_", " ")
        line = (
            f"  [{hit['tier']}] moon phase: {phase_label}. Nearest natal point: "
            f"{r['nearest_natal_point']} ({r['orb_to_nearest']:.2f} degrees, contact: {r['contact']})."
        )

    return line


def _render_hit_meaning_notes(hit: dict) -> str:
    """The interpretive "what this means" grounding lines (sign/
    house/aspect/eclipse/ingress meaning) -- everything _render_hit_
    block appends on top of _render_hit_core_line's factual base line.
    Split out on its own so a compressed (non-primary-thread) hit can
    render its core line WITHOUT this detail (Exhibit A fix -- see
    _render_daily_narrative_input's docstring): the full-detail
    interpretive content is what made a minor-aspect hit look as
    prompt-legible as the day's real headline convergence, so only
    the PRIMARY THREAD's hits get it now."""

    r = hit["resolution"]
    notes = ""

    natal_sign_note = hit.get("natal_sign_note")
    if natal_sign_note:
        notes += f"\n    Natal {r['nearest_natal_point']}'s sign meaning: {natal_sign_note}"

    natal_house_note = hit.get("natal_house_note")
    if natal_house_note:
        notes += f"\n    Transiting body's current (transit-through) house meaning: {natal_house_note}"

    target_natal_house_note = hit.get("target_natal_house_note")
    if target_natal_house_note:
        notes += f"\n    Natal {r['nearest_natal_point']}'s OWN birth house: {target_natal_house_note}"

    house_cusp_sign_note = hit.get("house_cusp_sign_note")
    if house_cusp_sign_note:
        notes += f"\n    Sign on that house's cusp: {house_cusp_sign_note}"

    vedic_sign_note = hit.get("vedic_sign_note")
    if vedic_sign_note:
        notes += f"\n    Vedic (sidereal): {vedic_sign_note}"

    aspect_meaning_note = hit.get("aspect_meaning_note")
    if aspect_meaning_note:
        notes += f"\n    What this aspect means: {aspect_meaning_note}"

    eclipse_meaning_note = hit.get("eclipse_meaning_note")
    if eclipse_meaning_note:
        notes += f"\n    What this eclipse means: {eclipse_meaning_note}"

    ingress_sign_note = hit.get("ingress_sign_note")
    if ingress_sign_note:
        notes += f"\n    What entering this sign means: {ingress_sign_note}"

    return notes


def _render_daily_narrative_input(
    narrative_claims: list[NarrativeClaim],
    hits: list[dict] | None = None,
    headline_thread: dict | None = None,
    western_arc_standing: dict | None = None,
    daily_mode_depth: str | None = None,
    standing_claim_ids: set[str] | None = None,
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
    every placement in the chart.

    `headline_thread` (daily.py's own _score_threads() output) is a
    real gap this closes: without it, headline selection among
    several real hits was left entirely to synthesis's own judgment,
    with no explicit signal for aspect-type strength or convergence --
    a pile of minor-aspect hits could read as more compelling than a
    tighter major-aspect thread purely by hit count. Rendered as an
    explicit anchor naming the day's highest-scoring thread, so the
    reading's headline has a concrete deterministic basis.

    Exhibit A fix (2026-09-01 live incident): naming the anchor alone
    wasn't enough -- a real reading built its entire "partnership under
    real pressure right now" narrative on a single 0.3-weight minor
    aspect while a genuine 4-hit, 2.70-score convergence sat unused in
    the same prompt. Root cause: every standout hit got the SAME full
    grounding block (sign/house/aspect meaning) regardless of whether
    it was the primary thread, so a wall of equally-detailed evidence
    made the wrong piece look just as headline-worthy as the real one.
    Fix, applying Part 6's tier-scoping principle one tier higher: only
    the PRIMARY THREAD's own hit(s) get the full _render_hit_block
    grounding; every other hit is still shown (real, available as
    supporting texture) but compressed to _render_hit_core_line's bare
    fact only, no meaning-notes -- paired with a hard-constraint
    instruction line (not just an anchor) naming the primary thread as
    the ONLY permitted headline source. When there's no headline_thread
    at all (a day with no transit_aspect hits), every hit keeps full
    detail -- there's no primary/secondary distinction to draw.

    `western_arc_standing` and `daily_mode_depth` (daily.py's own
    _compute_western_arc_standing()/_daily_mode_depth() output,
    Synthesis Repair Brief Part 4) are the data half of "arcs as the
    primary content unit" -- the STANDING ARC section below gives
    synthesis the real, always-available multi-month story to draw on
    even on a day with no fresh headline, and the DEPTH directive
    tells it how much space today's real signal actually earns (see
    lenses/daily_narrative_style.py for the prose-level rules on HOW
    to use both -- this function only supplies the data).

    `standing_claim_ids` (Synthesis Repair Brief Part 2.5, "invented
    timeliness"; Part 6, content architecture) is the set of claim_ids
    for real, natal-only/timing content (Big-3 sign+house, Vedic
    Dasha, Vedic sidereal Big-3+bhava, Chinese Ten-God-in-position)
    that has NO real STANDOUT-tier hit backing it today. Part 2.5
    originally still sent these to the model, relabeled under their
    own "standing" header; Part 6 found that wasn't enough on its own
    -- a real reading traced back to 73 resolved claims with only ~3
    actually used, and the volume alone was real, wasted cost even
    when the labeling was respected. These are now dropped from the
    prompt entirely rather than relabeled -- they still exist in
    daily_claims/result["claims"] for full attribution (see
    build_daily_reading), they just never reach the model."""

    lines = []

    if daily_mode_depth is not None:
        lines.append(f"TODAY'S DEPTH: {daily_mode_depth}")
        lines.append("")

    if western_arc_standing is not None:
        lines.append(
            f"STANDING ARC (ongoing -- not necessarily new today): "
            f"{western_arc_standing['transiting_body']} {western_arc_standing['aspect']} "
            f"natal {western_arc_standing['target_role']}, phase: {western_arc_standing['phase']}"
            + (f" -- {western_arc_standing['recurrence_note']}" if western_arc_standing["recurrence_note"] else "")
        )
        if western_arc_standing["claim_text"]:
            lines.append(f"  What this arc means: {western_arc_standing['claim_text']}")
        lines.append("")

    # standing_claim_ids (Big-3/Vedic Dasha/Vedic sidereal Big-3/Ten-
    # God with no real standout-tier hit behind them today) are
    # dropped from the prompt entirely here -- see this function's own
    # docstring above for why (Part 6: volume itself was real, wasted
    # cost, and labeling alone didn't reliably stop present-tense
    # blending). They still exist in daily_claims/result["claims"] for
    # full attribution; this is the one place they're excluded.
    standing_claim_ids = standing_claim_ids or set()
    other_claims = [c for c in narrative_claims if c.claim_id not in standing_claim_ids]

    for claim in other_claims:
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

        # Exhibit A fix (see this function's docstring): only the
        # PRIMARY THREAD's own hit(s) get full grounding detail below;
        # every other hit is real and still shown, but compressed to
        # its bare fact line -- no sign/house/aspect-meaning detail to
        # compete with the actual headline for the model's attention.
        primary_hit_ids = set(headline_thread["hit_ids"]) if headline_thread is not None else set()

        if headline_thread is not None:
            lines.append(
                f"PRIMARY THREAD (highest combined aspect-weight + convergence score, "
                f"{headline_thread['score']:.2f}): {headline_thread['label']}."
            )
            lines.append(
                "HARD RULE: the reading's headline and dominant story MUST be built from "
                "this thread's hit(s) below, and ONLY these -- no other hit today, however "
                "real, may become the dominant story or receive full-committing present-"
                "tense language on its own. Every hit under \"other real hits today\" "
                "further below is genuine and may be woven in as brief supporting texture "
                "at most, never as the headline."
            )
            lines.append("")
            for hit_id in primary_hit_ids:
                hit = next((h for h in hits if h["hit_id"] == hit_id), None)
                if hit is not None:
                    lines.append(_render_hit_block(hit))
            lines.append("")

        other_hits = [h for h in hits if h["hit_id"] not in primary_hit_ids]
        if other_hits:
            if primary_hit_ids:
                lines.append("# Other real hits today (supporting texture only -- do not headline from these)")
                lines.append("")
                for hit in other_hits:
                    lines.append(_render_hit_core_line(hit))
            else:
                # No headline_thread at all today (no transit_aspect
                # hits) -- no primary/secondary distinction to draw,
                # every real hit keeps its full grounding detail.
                for hit in other_hits:
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


def _synthesize_reading(
    daily_claims,
    backend: NarrativeBackend,
    hits: list[dict],
    headline_thread: dict | None = None,
    western_arc_standing: dict | None = None,
    daily_mode_depth: str | None = None,
    standing_claim_ids: set[str] | None = None,
    real_house_numbers: set[int] | None = None,
    narrative_hits: list[dict] | None = None,
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
    score low on keyword overlap without that being a real bug),
    fact_check()'s findings (a real check -- catches invented
    specificity the source claims don't support), and overclaim_
    findings from check_batch_overclaims (the fix for a real live bug
    where an eclipse was called "exact" 5.69 degrees off natal MC)
    plus, per Synthesis Repair Brief Part 2.4, check_life_domain_
    overclaims/check_occasion_overclaims/check_house_number_overclaims/
    check_moon_phase_overclaims -- four more deterministic categories a
    real audit found check_batch_overclaims structurally can't catch
    (it only ever checks orb/contact/amplification, never domain,
    occasion-existence, house numbers, or named lunar phases).

    `hits` (astrology.daily_hits.compute_daily_hits output, already
    resolved and tiered, full standout+background) is used for the
    overclaim guard's own checks below, which stay deliberately
    conservative -- a real background-tier fact is still real, even on
    a day it doesn't earn narrative detail. `narrative_hits` (Synthesis
    Repair Brief Part 6) is the narrower set -- standout-tier hits,
    plus anything that won today's headline thread even at background
    tier -- actually sent to the model via _render_daily_narrative_
    input's per-hit grounding block and the OVERCLAIM CONSTRAINTS
    section. Defaults to `hits` if not given (e.g. direct/test callers)
    so this stays additive, not a required parameter.
    """

    narrative_hits = narrative_hits if narrative_hits is not None else hits
    narrative_claims = _to_narrative_claims(daily_claims)
    prompt = build_daily_synthesis_prompt(
        _render_daily_narrative_input(
            narrative_claims, narrative_hits, headline_thread, western_arc_standing,
            daily_mode_depth, standing_claim_ids,
        )
    )

    try:
        reading_text = backend.synthesize(prompt)
    except (MissingAPIKeyError, NarrativeBackendError) as exc:
        # Never shown to the reader (the caller falls back to the
        # deterministic path) -- but a real failure reason (missing
        # key, invalid key, billing/quota, a deprecated model ID, a
        # timeout) was previously discarded here with zero trace, not
        # even in the server's own log stream. A real live incident
        # (Anthropic account out of credits) was undiagnosable from
        # Render's logs specifically because of this silence -- fixed
        # by printing the real exception to stderr before degrading.
        print(f"[daily synthesis] main synthesis call failed, falling back to deterministic reading: {exc}", file=sys.stderr)
        return None, None

    coverage = check_coverage(narrative_claims, reading_text)

    try:
        fact_check_findings = fact_check(backend, narrative_claims, reading_text)
    except (MissingAPIKeyError, NarrativeBackendError) as exc:
        # The reading itself already synthesized successfully above --
        # a failure on this second, separate backend call (checking
        # the reading, not producing it) shouldn't discard a real
        # reading. Degrade to "fact-check unavailable" rather than
        # raising into an unhandled 500 -- but still log the real
        # reason, same as the main synthesis call above.
        print(f"[daily synthesis] fact-check call failed, reading kept: {exc}", file=sys.stderr)
        fact_check_findings = "(fact-check unavailable: backend call failed)"

    # Domain support must be checked against what was actually SENT to
    # the model (narrative_claims minus standing_claim_ids), not the
    # full daily_claims -- a standing-only claim (e.g. a natal Venus
    # sign claim tagged "relationships") that Part 6 now excludes from
    # the prompt shouldn't be able to retroactively "justify" the
    # model independently using relationship language it was never
    # actually grounded in.
    narrative_eligible_claims = [
        item for item in daily_claims
        if item.claim.claim_id not in (standing_claim_ids or set())
    ]

    overclaim_findings = check_batch_overclaims(reading_text, hits)
    overclaim_findings += check_life_domain_overclaims(reading_text, narrative_eligible_claims)
    overclaim_findings += check_occasion_overclaims(reading_text, hits, western_arc_standing)
    overclaim_findings += check_house_number_overclaims(reading_text, real_house_numbers or set())
    overclaim_findings += check_moon_phase_overclaims(reading_text, hits)

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

    if overclaim_findings:
        # These are the deterministic checks (exactness/connection/
        # amplification/true-exactness, plus the Part 2.4 domain/
        # occasion/house-number checks) -- real, computed violations,
        # not fact_check's softer LLM opinion. Until now overclaim_
        # findings was pure observability: computed, attached to
        # synthesis_validation, but never actually stopping the flagged
        # text from being the reading a real user sees -- web.py never
        # even reads this field, and daily.py's own CLI path only
        # prints it AFTER already printing the reading. A guard that
        # never blocks anything isn't a guard. Reject the LLM reading
        # here (validation is still returned, not discarded, so the
        # real reason is visible in result["synthesis_validation"]) --
        # the caller falls back to _assemble_reading_text, which is
        # already fully grounded in real claims with no fabrication
        # risk, the same safety net a missing/failed backend call
        # already falls back to above.
        # Logs the RAW rejected text too, not just the findings that
        # rejected it -- a real gap found the first time this fired
        # after Option A shipped: with only the findings logged, a
        # rejected run tells you NOTHING about whether the prompt-scope
        # fix actually changed what the LLM produced before the guard
        # stepped in. This is server-side only (Render's log stream via
        # stderr, same convention as every other [daily synthesis] log
        # line) -- never added to `validation`/result["synthesis_
        # validation"], which the served page can read, so a flagged,
        # possibly-fabricated draft never has a path to reaching the
        # reader even indirectly.
        print(
            f"[daily synthesis] overclaim guard rejected the LLM reading "
            f"({len(overclaim_findings)} finding(s)), falling back to deterministic reading. "
            f"Findings: {overclaim_findings}\n"
            f"Rejected raw text (server-side only, never shown to the reader): {reading_text!r}",
            file=sys.stderr,
        )
        return None, validation

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
    elif hit["kind"] == "return":
        text = (
            f"Transiting {d['transiting_body']} returns to its own natal degree "
            f"({d['sign']} {d['degree']:.1f} degrees) -- {r['contact']} "
            f"(orb {r['orb_to_nearest']:.1f} degrees, house {r['natal_house']})."
        )
    elif hit["kind"] == "station":
        motion = "retrograde" if d["retrograde"] else "direct"
        text = (
            f"{d['transiting_body']} stations {motion} at {d['sign']} {d['degree']:.1f} "
            f"degrees (house {r['natal_house']})."
        )
    elif hit["kind"] == "sign_ingress":
        text = f"{d['transiting_body']} enters {d['sign']} (from {d['from_sign']})."
    elif hit["kind"] == "natal_house_ingress":
        text = f"{d['transiting_body']} enters natal house {r['natal_house']} (from house {d['from_house']})."
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


def _score_threads(hits: list[dict]) -> dict | None:
    """Deterministic thread scoring for headline selection (Synthesis
    Repair Brief, Part 2.1) -- a real gap this closes: assign_tier()
    only ever looks at orb/body-speed, never aspect TYPE, so a pile of
    minor-aspect hits could tier identically to (and get selected over
    by synthesis) a comparable major-aspect thread that was arguably
    the day's real story. Mutates every surviving transit_aspect hit
    in place, setting hit["thread_score"] (its own contribution) and
    hit["thread_rank"] (1 for every hit belonging to the day's single
    highest-scoring thread, None otherwise); returns a small
    descriptor of the winning thread (or None if there are no
    transit_aspect hits today) for _render_daily_narrative_input to
    surface as an explicit anchor, so headline selection has a
    concrete deterministic signal instead of being left entirely to
    synthesis's own judgment.

    Two-tier grouping, confirmed with Liam: primary threads group by
    exact natal target ROLE (tighter, more defensible -- "three things
    hitting your Venus" is a clearer single story than "three things
    somewhere in house 7", which could be three unrelated points).
    Secondary house-threads only form for roles that have just ONE hit
    today (no real point-convergence already claimed that hit) -- a
    house-thread's score is weighted down (x0.5) relative to an equal
    raw-score point-thread, so real point-convergence always outranks
    a same-score house-only convergence.

    Named-occasion override (Synthesis Repair Brief Part 2.2, per
    Liam's own wording): a standout-tier return or station whose own
    contact is genuinely exact, or that lands in a confirmed natal
    house, is headline-worthy on its own merit -- "today is your
    Saturn Return" doesn't need to out-convergence a pile of minor
    aspects to earn the lead, it bypasses the score-based ranking
    above entirely rather than merely competing inside it. Checked
    LAST so it always wins over an ordinary aspect thread when it
    qualifies.
    """

    aspect_hits = [h for h in hits if h["kind"] == "transit_aspect"]

    point_thread = None
    if aspect_hits:
        for hit in aspect_hits:
            aspect = hit["display"]["aspect"]
            weight = ASPECT_WEIGHTS.get(aspect, 0.5)
            orb = hit["resolution"]["orb_to_nearest"]
            max_orb = TRANSIT_ORBS.get(aspect, 2.0)
            hit["thread_score"] = weight * max(0.0, 1.0 - (orb / max_orb))
            hit["thread_rank"] = None

        by_role: dict[str, list[dict]] = {}
        for hit in aspect_hits:
            by_role.setdefault(hit["display"]["target_role"], []).append(hit)

        threads = [
            (sum(h["thread_score"] for h in role_hits), role_hits, f"natal {role}")
            for role, role_hits in by_role.items()
        ]

        singleton_hits = [role_hits[0] for role_hits in by_role.values() if len(role_hits) == 1]
        by_house: dict[int, list[dict]] = {}
        for hit in singleton_hits:
            house = hit["resolution"]["natal_house"]
            if house is not None:
                by_house.setdefault(house, []).append(hit)

        for house, house_hits in by_house.items():
            if len(house_hits) < 2:
                continue  # not a real convergence -- one lone hit already counted as its own point-thread above
            raw_score = sum(h["thread_score"] for h in house_hits)
            threads.append((raw_score * 0.5, house_hits, f"house {house}"))

        score, winning_hits, label = max(threads, key=lambda t: t[0])
        for hit in winning_hits:
            hit["thread_rank"] = 1

        point_thread = {
            "label": label,
            "score": score,
            "hit_ids": [h["hit_id"] for h in winning_hits],
        }

    occasion_hits = [h for h in hits if h["kind"] in ("return", "station") and h["tier"] == "standout"]
    qualifying = [
        h for h in occasion_hits
        if h["resolution"]["near_exact"] or h["resolution"]["natal_house"] is not None
    ]
    if qualifying:
        winner = min(qualifying, key=lambda h: h["resolution"]["orb_to_nearest"])
        winner["thread_rank"] = 1
        return {
            "label": f"{winner['kind']}: {winner['display']['transiting_body']}",
            "score": float("inf"),
            "hit_ids": [winner["hit_id"]],
        }

    return point_thread


# EXACT_HIT_BODIES (slow + social bodies) is the same scope
# attach_continuity_note and compute_arc_status already restrict
# themselves to -- a fast body's transit doesn't produce a real
# multi-month "arc" story to stand alongside vedic_dasha.
#
# _ARC_STANDING_CANDIDATE_CAP alone (originally 3) turned out not to
# bound wall-clock cost tightly enough: compute_arc_status's real
# per-call cost varies 3-4x by body (its own search window scales
# with each body's MULTI_PASS_WINDOW_DAYS, up to 299 days for
# jupiter) -- a count-based cap assumes uniform per-call cost, which
# isn't true here. Confirmed as the actual cause of a real live
# incident: this computation runs unconditionally on every request
# (both the LLM and deterministic paths), and its true added cost
# (measured directly: ~3s for 3 calls, worse on Render's slower free-
# tier CPU) was enough to tip the live app's already-tight gunicorn-
# timeout-vs-LLM-call-budget (see the "Fix live daily-mode page"
# fix earlier this session) over the edge -- the exact same hang
# symptom that fix already solved once, reintroduced by this
# feature's own added cost. _ARC_STANDING_TIME_BUDGET_SECONDS is the
# real bound now: a wall-clock ceiling checked between calls (it
# can't preempt a single call already in progress, so the true worst
# case is "budget plus one more call," not a hard ceiling -- still a
# real, large improvement over the old count-only cap's worst case of
# CAP times the single slowest body's cost). The count cap stays as a
# secondary bound for the case where every candidate happens to
# resolve unusually fast.
_ARC_STANDING_CANDIDATE_CAP = 3
_ARC_STANDING_TIME_BUDGET_SECONDS = 1.0


def _compute_western_arc_standing(natal_chart: dict, as_of_utc_time: datetime, hits: list[dict]):
    """The real, standing Western arc -- Synthesis Repair Brief Part 4:
    "a multi-month conjunction building toward exactness... is one
    story," given its own always-present standing block the same way
    result["vedic_dasha"] already is, independent of whether it's
    today's headline (see headline_thread for what's actually NEW
    today; this is what's ALREADY ongoing).

    compute_arc_status (astrology/daily_hits.py) does the real work
    per hit, but it's expensive -- measured directly at ~1.3s/call
    average, up to 3s for some bodies, against a real 29-slow-body-hit
    date (2026-03-01; a typical day sampled across 2026 runs 15-34
    such hits, not an outlier). Calling it for every one of today's
    slow-body hits, as a literal "score every arc, keep the best"
    implementation would, costs 20-40+ seconds per request -- the same
    class of problem attach_continuity_note's own docstring already
    solved by scoping to a small hit set instead of every qualifying
    one.

    Same fix here: rank candidates first using a CHEAP proxy (today's
    own orb/aspect-weight closeness, already computed, no extra
    ephemeris calls) -- the same weight*(1-orb/max_orb) shape
    _score_threads uses for headline selection -- then only call
    compute_arc_status for candidates up to _ARC_STANDING_CANDIDATE_CAP
    OR until _ARC_STANDING_TIME_BUDGET_SECONDS of real wall-clock time
    is spent, whichever comes first, keeping whichever of THOSE
    resolves to the highest real arc score (ASPECT_WEIGHTS[aspect] *
    (1 - peak_orb/max_orb), evaluated on the arc's own peak orb, not
    today's). Candidates are also deduped to one (their own best-
    scoring) hit per transiting body first, so the search covers
    distinct stories rather than burning budget on one body's several
    simultaneous hits.

    This can, in principle, miss a real arc that's dominant on its own
    merits but weak on today's specific orb (or simply never gets
    tried because the time budget ran out first) -- an accepted,
    documented tradeoff (matching this session's established cost-
    scoping discipline), not a silent one.

    Returns None only when today has no real slow/social-body transit_
    aspect/return hit at all -- confirmed rare in real data (15-34
    such hits on every date sampled across 2026), not the common case.
    """

    candidates = [
        h for h in hits
        if h["kind"] in ("transit_aspect", "return")
        and h["display"]["transiting_body"] in EXACT_HIT_BODIES
    ]
    if not candidates:
        return None

    def _cheap_score(hit):
        aspect = hit["display"]["aspect"]
        weight = ASPECT_WEIGHTS.get(aspect, 0.5)
        max_orb = hit["resolution"]["direct_hit_orb_used"]
        if not max_orb:
            return weight
        orb = hit["resolution"]["orb_to_nearest"]
        return weight * max(0.0, 1.0 - (orb / max_orb))

    best_per_body: dict[str, dict] = {}
    for hit in candidates:
        body = hit["display"]["transiting_body"]
        if body not in best_per_body or _cheap_score(hit) > _cheap_score(best_per_body[body]):
            best_per_body[body] = hit

    ranked = sorted(best_per_body.values(), key=_cheap_score, reverse=True)

    best = None
    search_start = _time.monotonic()
    for hit in ranked[:_ARC_STANDING_CANDIDATE_CAP]:
        arc = compute_arc_status(natal_chart, hit, as_of_utc_time)
        if arc is not None:
            max_orb = TRANSIT_ORBS.get(arc["aspect"], 2.0)
            real_score = ASPECT_WEIGHTS.get(arc["aspect"], 0.5) * max(0.0, 1.0 - (arc["peak_orb"] / max_orb))
            if best is None or real_score > best[0]:
                best = (real_score, arc, hit)
        if _time.monotonic() - search_start >= _ARC_STANDING_TIME_BUDGET_SECONDS:
            # Can't preempt the call already in flight, only stop
            # trying further ones -- see the docstring above for why
            # this is the real cost bound, not the count cap alone.
            break

    if best is None:
        return None

    _, arc, source_hit = best
    return {
        "transiting_body": arc["transiting_body"],
        "target_role": arc["target_role"],
        "aspect": arc["aspect"],
        "phase": arc["phase"],
        "peak_utc_time": arc["peak_utc_time"].isoformat(),
        "peak_orb": arc["peak_orb"],
        "natal_house": arc["natal_house"],
        "is_repeating": arc["is_repeating"],
        "recurrence_note": arc["recurrence_note"],
        "claim_text": source_hit.get("aspect_meaning_note"),
        # Internal only (not itself interpretive content) -- lets
        # _daily_mode_depth tell "today's headline IS just this arc
        # continuing" apart from "today's headline is something else,
        # or this same arc just went exact" without re-deriving hit
        # identity from scratch.
        "source_hit_id": source_hit["hit_id"],
        "note": (
            "The dominant ongoing Western transit arc as of today -- "
            "standing context, not necessarily today's headline (see "
            "headline_thread for what's actually new today)."
        ),
    }


def _daily_mode_depth(
    hits: list[dict], daily_claims: list, headline_thread: dict | None, arc_standing: dict | None
) -> str:
    """How much real, non-padded content today actually supports --
    Synthesis Repair Brief Part 4: daily mode stays a real layer, but
    "restrained and confidence-scaled... a full reading, a short
    status line, or near-silent, depending on whether today's real
    data supports more." Mirrors Part 3's own confidence-scaling
    spirit (proportionate space, not padding a thin day to look like a
    rich one) at the structural level, one layer up from Part 3's
    prose-level rules.

    - "near_silent": no surviving hits AND no other real daily_claims
      content (identity/standing claims included) -- the exact same
      "genuinely nothing" condition build_daily_reading's own
      pre-existing `if use_synthesis and (daily_claims or hits)` gate
      and _assemble_reading_text([]) == "" already required to reach
      _QUIET_DAY_READING, now reached by a deliberate depth decision
      rather than only by literal emptiness. In practice this is rare
      to never (Big-3 identity claims resolve on essentially every
      real date), matching this session's own "quiet days may not
      exist" finding from the constellation-visual work -- not a new
      claim, just consistent with it.
    - "short": real content exists, but it doesn't clear the bar for a
      full reading -- either nothing converged into a headline thread
      at all (e.g. a lone moon-phase hit with no significant aspect
      thread), or the ONLY thing headline-worthy today is the standing
      arc simply continuing (same hit, non-exact phase) with nothing
      new layered on top.
    - "full": a named-occasion override (return/station going exact,
      score=inf) always qualifies; otherwise, any headline thread that
      ISN'T just the continuing standing arc restating itself -- either
      a genuinely different thread, or the standing arc itself having
      just gone exact (real news, even if it's the "same" story).

    A real judgment call, not a mechanical derivation: whether the
    standing arc going exact counts as "new" is a genuine editorial
    choice (made here: yes, an exact moment is always real news),
    flagged rather than silently baked in."""

    if not hits and not daily_claims:
        return "near_silent"

    if headline_thread is None:
        return "short"

    if headline_thread["score"] == float("inf"):
        return "full"

    if arc_standing is not None and arc_standing["phase"] != "exact":
        if set(headline_thread["hit_ids"]) == {arc_standing["source_hit_id"]}:
            return "short"

    return "full"


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
    headline_thread = _score_threads(hits)

    # Synthesis, Tone, and Content Architecture Repair Brief Part 6: a
    # real reading was traced back to 73 resolved claims with only ~3
    # actually used -- background-tier hits (real, but the loosest,
    # least narratively significant contacts; with the widened ~26-32
    # point target set, a normal day can surface 15-35 of them) were
    # getting the SAME full sign/house/cusp/aspect-meaning grounding
    # treatment as standout-tier hits, then all of it got sent to the
    # LLM twice (main synthesis + fact-check's own restated claims
    # block) whether or not any of it was ever going to be used.
    # `hits` itself (full standout+background) stays completely
    # unchanged for attribution/citation (result["claims"]) and for
    # the overclaim guard's checks, which should stay conservative --
    # standout_hits is ONLY used to scope what actually grounds and
    # reaches the synthesis prompt, mirroring "weaker threads get a
    # trailing mention, not their own paragraph" (Part 3) one level
    # up, at the data-selection stage rather than the prose stage.
    #
    # Not simply tier == "standout": a background-tier hit CAN still
    # win headline selection on real convergence (e.g. three loose
    # hits all landing on the same natal point can outscore one
    # standout hit elsewhere) -- when that happens, it genuinely is
    # today's story and needs full grounding, not the compressed
    # treatment meant for hits that lost. So standout_hits here means
    # "standout tier, OR part of today's actual headline thread."
    headline_hit_ids = set(headline_thread["hit_ids"]) if headline_thread is not None else set()
    standout_hits = [h for h in hits if h["tier"] == "standout" or h["hit_id"] in headline_hit_ids]

    # Fallback Headline-Wiring Fix: records, per hit, exactly which
    # daily_claims entries were resolved BECAUSE of that hit -- built
    # as a side effect of the existing per-hit note-setting loops below
    # (each already calls a _use_*_claim/_resolve_*_claim helper and
    # knows precisely which claim it just used). This is real
    # attribution, not a heuristic (e.g. matching on claim_id substrings
    # against a role name) -- a claim only ends up under a hit_id here
    # because that specific hit's own grounding loop resolved it.
    # _assemble_reading_text (the deterministic fallback) unions this
    # across headline_thread["hit_ids"] to know which real claims
    # belong to today's actual computed primary thread, instead of
    # falling back to _CLAIM_PRIORITY's disconnected legacy-ID list or
    # claim-construction-order as its PRIMARY signal (see Exhibit A's
    # fallback-wiring bug).
    hit_claim_ids: dict[str, set[str]] = {}

    def _track_hit_claim(hit, claim_item):
        if claim_item is not None:
            hit_claim_ids.setdefault(hit["hit_id"], set()).add(claim_item.claim.claim_id)

    # Synthesis Repair Brief Part 2.4: every real, computed house
    # number relevant today -- transit-through (a transiting body's
    # current house) to start; natal-own (Big-3, hit-touched points,
    # Vedic sidereal Big-3) are unioned in further below as each is
    # computed. Feeds check_house_number_overclaims -- a house number
    # the generated reading names that ISN'T in this set traces to
    # nothing Celeste actually computed today, tropical or sidereal
    # (both systems unioned together since the reading's own plain-
    # language prose never says which system it means, per grounding
    # rule 4 hiding backend terminology).
    real_house_numbers: set[int] = {
        h["resolution"]["natal_house"] for h in hits if h["resolution"].get("natal_house") is not None
    }

    # Continuity ("is this the first time, or a slow-moving arc I'm
    # already in?") is real, but expensive per hit -- computed only for
    # the day's headline thread's hit(s), not every surviving hit, both
    # because that's the thread the reading actually narrates and
    # because computing it for every qualifying hit measured at 15-25+
    # extra seconds per request (see astrology/daily_hits.py::
    # attach_continuity_note's own docstring for the numbers).
    if headline_thread is not None:
        winning_ids = set(headline_thread["hit_ids"])
        for hit in hits:
            if hit["hit_id"] in winning_ids and hit["kind"] == "transit_aspect":
                attach_continuity_note(natal_chart, hit, as_of_utc_time)

    # daily_transit_aspects/daily_moon_phase, fed to the existing
    # concepts->features->resolve_claims machinery below, are scoped to
    # STANDOUT-tier surviving hits only (Part 6, above) -- previously
    # this fed every SURVIVING hit (standout+background), which was
    # itself already a fix for an earlier bug (an unfiltered sweep of
    # every transiting body's every aspect and house placement,
    # regardless of significance -- see astrology/daily_hits.py's
    # docstring), but background-tier's real breadth (15-35 hits on a
    # normal day, given the widened point set) meant this generic
    # blanket sweep -- which fires a claim for every distinct aspect
    # TYPE and house NUMBER touched, regardless of how many hits share
    # one -- still flooded the prompt with content narrowly true but
    # never actually used in the output.
    aspect_hits = [h for h in standout_hits if h["kind"] == "transit_aspect"]
    moon_hit = next((h for h in standout_hits if h["kind"] == "moon_phase"), None)

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
    real_house_numbers.add(natal_chart["bodies"]["sun"]["house"])
    real_house_numbers.add(natal_chart["bodies"]["moon"]["house"])

    # Synthesis Repair Brief Part 2.5 ("invented timeliness") + Part 6
    # (content architecture): every claim resolved unconditionally
    # here (Big-3 sign/house, and further below Vedic Dasha/sidereal
    # Big-3/Chinese Ten-God) is a real, permanent chart fact -- not
    # something "activating" today. Part 2.5 originally still sent
    # these to synthesis, just relabeled under their own "standing"
    # header; Part 6 (a real reading traced to 73 resolved claims with
    # only ~3 actually used) found that wasn't enough -- the volume
    # alone was real cost, and the model still sometimes wove standing
    # content into confident present-tense language despite the
    # labeling. standing_claim_ids now means "excluded from the
    # synthesis prompt entirely" (see _render_daily_narrative_input) --
    # they still exist in daily_claims/result["claims"] for full
    # attribution, just never reach the model. A Big-3 point ALSO
    # touched by a real STANDOUT-tier hit today (role in
    # hit_touched_roles) is excluded from standing_claim_ids -- it's
    # legitimately paired to today's real activity via that hit, not
    # standing-only, even though it's the same underlying claim
    # object. hit_touched_roles itself is scoped to standout_hits, not
    # all hits, matching Part 6's own tier-gating -- a role touched
    # ONLY by a background-tier hit doesn't earn Big-3 an exemption
    # either, for the same reason background-tier hits don't get full
    # grounding themselves.
    hit_touched_roles = {
        h["resolution"].get("nearest_natal_point")
        for h in standout_hits
        if h["resolution"].get("nearest_natal_point")
    }
    standing_claim_ids: set[str] = set()
    for claim, role in (
        (sun_sign_claim, "sun"), (moon_sign_claim, "moon"), (ascendant_sign_claim, "ascendant"),
        (sun_house_claim, "sun"), (moon_house_claim, "moon"),
    ):
        if claim is not None and role not in hit_touched_roles:
            standing_claim_ids.add(claim.claim.claim_id)

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

    # real_house_numbers stays built from the FULL hit list (every
    # tier), independent of the narrative-grounding restriction below
    # -- it feeds check_house_number_overclaims, which must stay
    # conservative (a background-tier hit's real natal house is still
    # a real house, even on a day it doesn't earn narrative detail;
    # narrowing this to standout-only would make the guard MORE likely
    # to falsely flag a real number as invented, the opposite of what
    # Part 6 is trying to fix).
    for hit in hits:
        if hit["kind"] not in ("transit_aspect", "eclipse", "moon_phase", "return", "station"):
            continue
        role = hit["resolution"]["nearest_natal_point"]
        if role is None:
            continue
        real_role = natal_chart["rulership"]["chart_ruler"] if role == "chart_ruler" else role
        natal_house = natal_chart["bodies"].get(real_role, {}).get("house")
        if natal_house is not None:
            real_house_numbers.add(natal_house)

    # Sign/house/cusp-sign grounding itself (Part 6) is scoped to
    # standout_hits only -- this is the other half of the "every
    # asteroid/angle/node's sign+house, every day" bloat alongside the
    # blanket-sweep fix above: with the widened ~26-32 point target
    # set, a normal day's background-tier hits alone can touch nearly
    # every point in the chart.
    for hit in standout_hits:
        if hit["kind"] not in ("transit_aspect", "eclipse", "moon_phase", "return", "station"):
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
        _track_hit_claim(hit, claim)

        natal_house = natal_chart["bodies"].get(real_role, {}).get("house")
        natal_house_claim = _use_natal_house_claim(real_role, natal_house)
        if natal_house_claim is not None:
            hit["target_natal_house_note"] = (
                f"natal {real_role} radix is in house {natal_house} -- {natal_house_claim.claim.statement}"
            )
        _track_hit_claim(hit, natal_house_claim)

        cusp_sign_claim = _use_house_cusp_sign_claim(natal_house)
        if cusp_sign_claim is not None:
            hit["house_cusp_sign_note"] = cusp_sign_claim.claim.statement
        _track_hit_claim(hit, cusp_sign_claim)

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

    for hit in standout_hits:
        if hit["kind"] not in ("transit_aspect", "return", "station", "natal_house_ingress"):
            continue
        claim = _use_house_claim(hit["display"]["transiting_body"], hit["resolution"]["natal_house"])
        if claim is not None:
            hit["natal_house_note"] = claim.claim.statement
        _track_hit_claim(hit, claim)

    # Aspect-meaning content: what the hit's own aspect TYPE means
    # (e.g. "a trine lets the two placements involved flow together
    # smoothly..."), paired to the specific hit -- same targeted-
    # lookup discipline as every fact type above, closing a real gap:
    # this meaning already existed and was already being cited once
    # per day per aspect type, but never paired to the hit that earned
    # it, so every transit_aspect hit fell through to a bare,
    # meaningless computed-fact fallback in the citation list even
    # when real interpretive content for its aspect type existed
    # elsewhere in the very same list. See _resolve_aspect_claim.
    aspect_meaning_claims_used: dict[str, object] = {}

    for hit in standout_hits:
        # "return" reuses this lookup too -- a return's own display.
        # aspect is always "conjunction" (see astrology/daily_hits.py's
        # _resolve_return_hits), so it resolves the same generic
        # conjunction-meaning content an ordinary transit_aspect hit
        # would, no bespoke return content needed.
        if hit["kind"] not in ("transit_aspect", "return"):
            continue
        claim = _resolve_aspect_claim(hit)
        if claim is None:
            continue
        if claim.claim.claim_id not in aspect_meaning_claims_used:
            aspect_meaning_claims_used[claim.claim.claim_id] = claim
            daily_claims.append(claim)
        hit["aspect_meaning_note"] = claim.claim.statement
        _track_hit_claim(hit, claim)

    # Synthesis Repair Brief Part 4: the standing Western arc (always
    # computed, like vedic_dasha, independent of today's headline) and
    # the depth decision it feeds into -- run after the aspect-meaning
    # loop above so a real arc's citation (claim_text) reuses the same
    # already-resolved, already-deduped claim rather than a second
    # resolve_claims call.
    western_arc_standing = _compute_western_arc_standing(natal_chart, as_of_utc_time, hits)
    daily_mode_depth = _daily_mode_depth(hits, daily_claims, headline_thread, western_arc_standing)

    # Eclipse-type meaning content: what the hit's own (kind, type)
    # combination means (e.g. "a total solar eclipse marks the most
    # complete kind of new beginning..."). A full audit found NO
    # eclipse-type content existed anywhere before this -- a genuine
    # content gap, not a wiring gap like the aspect-meaning fix above.
    # See _resolve_eclipse_type_claim.
    eclipse_meaning_claims_used: dict[str, object] = {}

    for hit in standout_hits:
        if hit["kind"] != "eclipse":
            continue
        claim = _resolve_eclipse_type_claim(hit)
        if claim is None:
            continue
        if claim.claim.claim_id not in eclipse_meaning_claims_used:
            eclipse_meaning_claims_used[claim.claim.claim_id] = claim
            daily_claims.append(claim)
        hit["eclipse_meaning_note"] = claim.claim.statement
        _track_hit_claim(hit, claim)

    # Sign-ingress meaning content: the body-agnostic pure-sign meaning
    # of the sign a body has just entered (Synthesis Repair Brief Part
    # 2.2) -- reuses the same pure_sign:{sign} claim family
    # _resolve_pure_sign_claim already serves as an honest last-resort
    # fallback for role-specific sign content elsewhere in this
    # function; here it's the PRIMARY content for a sign_ingress hit,
    # since the fact being grounded is "which sign was just entered",
    # not "which body's natal sign". Shares sign_claims_used's dedupe
    # cache -- the same claim family, so a sign a natal point is
    # already grounded in today shouldn't be cited twice.
    for hit in standout_hits:
        if hit["kind"] != "sign_ingress":
            continue
        item = _resolve_pure_sign_claim(hit["display"]["sign"])
        if item is None:
            continue
        if item.claim.claim_id not in sign_claims_used:
            sign_claims_used[item.claim.claim_id] = item
            daily_claims.append(item)
        hit["ingress_sign_note"] = item.claim.statement
        _track_hit_claim(hit, item)

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
    real_house_numbers.add(vedic_sun_house)
    real_house_numbers.add(vedic_moon_house)
    vedic_sun_house_claim = _resolve_vedic_house_claim("sun", vedic_sun_house)
    vedic_moon_house_claim = _resolve_vedic_house_claim("moon", vedic_moon_house)
    if vedic_sun_house_claim is not None:
        _use_vedic_claims([vedic_sun_house_claim])
    if vedic_moon_house_claim is not None:
        _use_vedic_claims([vedic_moon_house_claim])

    # Today's transiting sidereal sign -- only for a body already part
    # of a real STANDOUT-tier hit today (Part 6 -- never an
    # unconditional sweep over all 10 transiting bodies, and not for a
    # merely background-tier touch either, same discipline as the
    # natal-sign grounding above).
    for hit in standout_hits:
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
            for c in fused:
                _track_hit_claim(hit, c)

    # Chinese/BaZi Ten-God-in-position -- Combinatorial-Meaning
    # Expansion Phase 6. Confirmed by direct search: this pipeline
    # cited zero Four Pillars natal structure before this (only the
    # day-pillar-vs-natal-day-pillar RELATIONSHIP claims, a different
    # mechanism entirely) -- Chinese daily mode had no Big-3-style
    # standing identity content the way Western/Vedic do. This is
    # that: the Year/Month/Hour Pillars' visible-stem Ten God, always
    # shown (a fixed natal fact, doesn't change day to day, same
    # framing as the tropical/sidereal Big-3 and Vedic Dasha standing
    # above). Day Pillar excluded -- the Day Stem IS the Day Master,
    # not a Ten God relative to itself.
    ten_gods = build_ten_gods(four_pillars, four_pillars.day_master_element, four_pillars.day_master_polarity)
    ten_god_claims_used: dict[str, object] = {}
    chinese_pillar_ten_gods = {}

    for _position in ("year", "month", "hour"):
        _ten_god = ten_gods["stems"][_position]["ten_god"]
        _claim = _resolve_ten_god_position_claim(_position, _ten_god)
        if _claim is not None and _claim.claim.claim_id not in ten_god_claims_used:
            ten_god_claims_used[_claim.claim.claim_id] = _claim
            daily_claims.append(_claim)
        chinese_pillar_ten_gods[_position] = {"ten_god": _ten_god, "claim": _claim}

    # Continuing the standing-content collection started above: Vedic
    # Dasha timing, natal sidereal Big-3/bhava, and Chinese Ten-God-in-
    # position have NO hit-pairing equivalent at all (nothing in this
    # pipeline ever produces a "Dasha lord activated today" or "Ten-
    # God activated today" hit) -- always standing, no exclusion check
    # needed, unlike the tropical Big-3 above.
    for item in dasha_lord_claims.values():
        standing_claim_ids.add(item.claim.claim_id)
    if chara_sign_claim is not None:
        standing_claim_ids.add(chara_sign_claim.claim.claim_id)
    for item in vedic_sun_claims + vedic_moon_claims + vedic_ascendant_claims:
        standing_claim_ids.add(item.claim.claim_id)
    if vedic_sun_house_claim is not None:
        standing_claim_ids.add(vedic_sun_house_claim.claim.claim_id)
    if vedic_moon_house_claim is not None:
        standing_claim_ids.add(vedic_moon_house_claim.claim.claim_id)
    for item in ten_god_claims_used.values():
        standing_claim_ids.add(item.claim.claim_id)

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
    #
    # transit_aspect/return hits are also considered cited when
    # aspect_meaning_note is set: _resolve_aspect_claim (above) is a
    # targeted lookup, not the blanket sweep this matched_tags check
    # was built for, so its matched_features reflects whichever tag
    # (the hit's own hyper-specific one, or the generic transit_aspect:
    # {type} fallback) the resolved claim actually carries -- for the
    # generic case that's never equal to hit["feature_tag"] itself, so
    # without this a hit whose aspect type DOES have real meaning
    # would still fall through to the bare computed-fact record below.
    #
    # station/natal_house_ingress hits (Synthesis Repair Brief Part
    # 2.2) carry feature_tag=None by design -- their real content is
    # the paired natal_house_note set by the _use_house_claim loop
    # above (a targeted lookup, same reasoning as aspect_meaning_note)
    # -- so they're exempted the same way whenever that note resolved.
    matched_tags = {fid for item in daily_claims for fid in item.matched_features}
    uncited_hits = [
        h for h in hits
        if h["feature_tag"] not in matched_tags
        and not h.get("aspect_meaning_note")
        and not h.get("natal_house_note")
    ]
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
            headline_thread,
            western_arc_standing,
            daily_mode_depth,
            standing_claim_ids,
            real_house_numbers,
            standout_hits,
        )
        if reading_text is not None:
            synthesis_method = "llm"
        elif synthesis_validation is not None and synthesis_validation.get("overclaim_findings"):
            # Distinct from the other deterministic_fallback causes
            # (no API key, backend error) -- here the LLM call
            # succeeded but its own output was rejected by the
            # overclaim guard. Worth its own label: this is a real,
            # detected fabrication being caught, not an unavailable
            # backend.
            synthesis_method = "guard_rejected"

    if reading_text is None:
        # Fallback Headline-Wiring Fix: the same real, computed primary
        # thread Option A already anchors the LLM prompt on -- unioned
        # from hit_claim_ids (recorded above as each per-hit grounding
        # loop resolved its own claims) over headline_thread's own
        # hit(s). Empty when there's no real headline thread today at
        # all (e.g. no transit_aspect/named-occasion hits), in which
        # case _order_reading_claims correctly falls back to
        # _CLAIM_PRIORITY as its own fallback-of-the-fallback.
        primary_thread_claim_ids: set[str] = set()
        if headline_thread is not None:
            for hid in headline_thread["hit_ids"]:
                primary_thread_claim_ids |= hit_claim_ids.get(hid, set())
        reading_text = _assemble_reading_text(daily_claims, standing_claim_ids, daily_mode_depth, primary_thread_claim_ids)

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
        "headline_thread": headline_thread,
        "western_arc_standing": western_arc_standing,
        "daily_mode_depth": daily_mode_depth,
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
        "chinese_year_ten_god": _identity_field(
            chinese_pillar_ten_gods["year"]["ten_god"], chinese_pillar_ten_gods["year"]["claim"],
            "Your Year Pillar's Ten God (relative to your Day Master) -- standing identity context, not today's sky.",
        ),
        "chinese_month_ten_god": _identity_field(
            chinese_pillar_ten_gods["month"]["ten_god"], chinese_pillar_ten_gods["month"]["claim"],
            "Your Month Pillar's Ten God (relative to your Day Master) -- standing identity context, not today's sky.",
        ),
        "chinese_hour_ten_god": _identity_field(
            chinese_pillar_ten_gods["hour"]["ten_god"], chinese_pillar_ten_gods["hour"]["claim"],
            "Your Hour Pillar's Ten God (relative to your Day Master) -- standing identity context, not today's sky.",
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
