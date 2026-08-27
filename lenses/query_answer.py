"""
Answer assembly (brief 2d/2e): the orchestrator that ties everything
in Part 2 together -- natal completeness (2a) gates everything;
factual queries get a direct data pull, no synthesis; interpretive
queries run the full 2a-2c pipeline (resolve -> nodal check ->
overclaim constraints -> synthesis -> overclaim check); and a query
resolving to nothing significant returns NO_HIGHLIGHTS_MESSAGE as a
first-class result (2e), the same honesty principle
astrology.key_events's own quiet flag already embodies -- both key
off the same absence of a standout/matching event, so they can never
drift apart from each other.

Interpretive answers require a working LLM backend; when one isn't
available (MissingAPIKeyError/NarrativeBackendError -- confirmed a
real, live failure mode this session, not just theoretical), this
degrades to a deterministic, still-honest answer built directly from
the resolution/nodal facts, never a crash, matching the same
labeled-fallback posture daily.py already established.
"""

from datetime import date, datetime, timezone

from astrology.eclipses import check_eclipse_nodal_relationship
from astrology.event_resolution import resolve_event_to_natal
from astrology.normaliser import longitude_in_house, longitude_to_zodiac
from astrology.sky_snapshot import build_sky_snapshot
from lenses.narrative_backend import AnthropicNarrativeBackend, MissingAPIKeyError, NarrativeBackend, NarrativeBackendError
from lenses.natal_completeness import check_natal_completeness
from lenses.overclaim_guard import build_overclaim_constraints, check_overclaims
from lenses.query_narrative_style import build_query_synthesis_prompt
from lenses.query_parser import ParseFailure, ParsedQuery, parse_query

NO_HIGHLIGHTS_MESSAGE = "Nothing in this range rises above routine background noise -- no standout events to flag."


def _natal_placement_answer(parsed: ParsedQuery, natal_chart: dict) -> str:
    lines = []
    for body in parsed.bodies:
        lon = natal_chart["bodies"][body]["longitude"]
        z = longitude_to_zodiac(lon)
        lines.append(f"Your {body} is in {z['sign']} ({z['degree']} deg{z['minute']:02d}').")
    for role in parsed.natal_roles:
        if role == "ascendant":
            lon = natal_chart["houses"]["angles"]["ascendant"]
            label = "rising sign"
        elif role == "mc":
            lon = natal_chart["houses"]["angles"]["mc"]
            label = "MC"
        else:
            chart_ruler = natal_chart["rulership"]["chart_ruler"]
            lon = natal_chart["bodies"][chart_ruler]["longitude"]
            label = "chart ruler"
        z = longitude_to_zodiac(lon)
        lines.append(f"Your {label} is {z['sign']} ({z['degree']} deg{z['minute']:02d}').")
    return " ".join(lines) if lines else "I couldn't tell which placement you're asking about."


def _natal_house_answer(parsed: ParsedQuery, natal_chart: dict) -> str:
    lines = []
    for body in parsed.bodies:
        lon = natal_chart["bodies"][body]["longitude"]
        house = longitude_in_house(lon, natal_chart["houses"]["cusps"])
        lines.append(f"Your {body} is in your {house}th house.")
    return " ".join(lines) if lines else "I couldn't tell which placement you're asking about."


def _retrograde_status_answer(parsed: ParsedQuery, natal_chart: dict, as_of: datetime) -> str:
    if not parsed.bodies:
        return "I couldn't tell which planet you're asking about."
    body = parsed.bodies[0]
    snap = build_sky_snapshot(natal_chart, as_of)
    direction = snap["bodies"][body]["direction"]
    return f"{body.capitalize()} is currently {direction}."


def _date_snapshot_answer(parsed: ParsedQuery, natal_chart: dict) -> str:
    if not parsed.date_start:
        return "I couldn't tell which date you're asking about."
    when = datetime.strptime(parsed.date_start, "%Y-%m-%d").replace(hour=12, tzinfo=timezone.utc)
    snap = build_sky_snapshot(natal_chart, when)
    lines = [f"On {parsed.date_start}: Moon phase is {snap['moon_phase']['phase_name']}."]
    if snap["eclipse"]:
        # sky_snapshot's own eclipse dict uses "kind" for solar/lunar
        # directly (its own schema, unlike key_events.py's assembled
        # event list, where "kind" is normalized to "eclipse" and the
        # solar/lunar distinction lives in "eclipse_kind" instead).
        lines.append(f"There's a {snap['eclipse']['kind']} eclipse "
                      f"({snap['eclipse']['type']}) in {snap['eclipse']['sign']}.")
    if snap["aspects_active"]:
        lines.append(f"{len(snap['aspects_active'])} transit-to-natal aspects are active.")
    return " ".join(lines)


def _find_matching_event(parsed: ParsedQuery, key_events: dict | None, today: date) -> dict | None:
    if not key_events:
        return None
    candidates = [
        e for e in key_events["events"]
        if (not parsed.event_kinds or e["kind"] in parsed.event_kinds)
        and (not parsed.bodies or e.get("transiting_body") in parsed.bodies)
        and (not parsed.sign or e.get("sign", "").lower() == parsed.sign)
    ]
    if not candidates:
        return None

    def relevant_date(e):
        # A multi-pass event's PEAK (tightest orb) can already be in
        # the past while the group is still ongoing (e.g. an exact
        # hit already happened, with a later, looser station pass
        # still ahead) -- end_date is what actually determines
        # whether the event is still relevant to "next", not peak.
        return e.get("end_date") or e.get("peak_utc_time") or e["utc_time"]

    candidates.sort(key=relevant_date)
    upcoming = [e for e in candidates if relevant_date(e).date() >= today]
    return upcoming[0] if upcoming else candidates[0]


def _next_event_answer(parsed: ParsedQuery, key_events: dict | None, today: date) -> str:
    if key_events is None:
        return "I don't have upcoming events computed for this yet."
    event = _find_matching_event(parsed, key_events, today)
    if event is None:
        return "Nothing matching that in the computed range."
    if event.get("is_repeating") and event.get("recurrence_note"):
        # Naming only the peak date would be misleading/stale for a
        # multi-pass event whose exact hit already happened but which
        # is still ongoing -- the recurrence note gives the honest
        # full picture instead of one potentially-past date.
        return event["recurrence_note"]
    when = event.get("peak_utc_time") or event["utc_time"]
    return f"The next one is on {when.date().isoformat()}."


def _resolve_event(event: dict, natal_chart: dict) -> tuple[dict, dict | None]:
    """(resolution, nodal) for one KeyEvent -- an eclipse resolves via
    its own degree + nodal check; a transit_aspect/return event is
    already, by construction, a hit on a specific natal point within
    a tight orb, so its resolution is built directly from the
    already-known fields rather than re-deriving it."""

    if event["kind"] == "eclipse":
        resolution = resolve_event_to_natal(event["longitude"], natal_chart)
        return resolution, event.get("nodal")

    if event["kind"] in ("transit_aspect", "return"):
        orb = event["peak_orb"]
        resolution = {
            "natal_house": event["natal_house"], "house_occupants": [event["target_role"]],
            "nearest_natal_point": event["target_role"], "orb_to_nearest": orb,
            "direct_hit_orb_used": orb + 0.01,  # these events are found precisely because they ARE hits
            "contact": "direct_hit",
        }
        return resolution, None

    # Stations/ingresses/lunations: resolve against the event's own longitude if present.
    longitude = event.get("longitude") or event.get("moon_longitude")
    if longitude is not None:
        return resolve_event_to_natal(longitude, natal_chart), None

    return {"natal_house": None, "house_occupants": [], "nearest_natal_point": None,
            "orb_to_nearest": None, "direct_hit_orb_used": None, "contact": "no_contact"}, None


def _deterministic_interpretive_fallback(event: dict, resolution: dict, nodal: dict | None) -> str:
    parts = [f"This is a {event['tier']} event ({', '.join(event['tier_reasons'])})."]
    if resolution["contact"] == "direct_hit":
        parts.append(f"It's a direct hit on your {resolution['nearest_natal_point']} "
                      f"(house {resolution['natal_house']}).")
    elif resolution["contact"] == "thematically_adjacent":
        parts.append(f"It falls in your house {resolution['natal_house']}, the same area as your "
                      f"{', '.join(resolution['house_occupants'])}, though not an exact hit.")
    else:
        parts.append("It doesn't make meaningful contact with your chart.")
    if nodal is not None:
        parts.append(nodal["amplification_note"])
    return " ".join(parts)


def answer_query(
    question: str,
    natal_chart: dict,
    key_events: dict | None = None,
    backend: NarrativeBackend | None = None,
    today: date | None = None,
    as_of: datetime | None = None,
) -> dict:
    today = today or date.today()
    as_of = as_of or datetime.now(timezone.utc)

    completeness = check_natal_completeness(natal_chart)
    if not completeness.complete:
        return {"answer": completeness.message, "method": "incomplete_chart", "parsed_query": None}

    parsed = parse_query(question, backend=backend, today=today)
    if isinstance(parsed, ParseFailure) or parsed.intent == "unparseable":
        reason = parsed.reason if isinstance(parsed, ParseFailure) else "unparseable question"
        return {
            "answer": "I couldn't work out what you're asking -- try naming a body, a date, or an event.",
            "method": "unparseable", "reason": reason, "parsed_query": None,
        }

    if parsed.intent == "factual":
        lookups = {
            "natal_placement": lambda: _natal_placement_answer(parsed, natal_chart),
            "natal_house": lambda: _natal_house_answer(parsed, natal_chart),
            "retrograde_status": lambda: _retrograde_status_answer(parsed, natal_chart, as_of),
            "date_snapshot": lambda: _date_snapshot_answer(parsed, natal_chart),
            "next_event": lambda: _next_event_answer(parsed, key_events, today),
        }
        handler = lookups.get(parsed.lookup)
        answer = handler() if handler else "I don't have a way to answer that factual question yet."
        return {"answer": answer, "method": "factual_lookup", "parsed_query": parsed}

    # Interpretive.
    if parsed.lookup == "range_highlights":
        if key_events is None:
            return {"answer": "I don't have events computed for this range yet.",
                     "method": "no_data", "parsed_query": parsed}
        standout = [e for e in key_events["events"] if e["tier"] == "standout"]
        if not standout:
            return {"answer": NO_HIGHLIGHTS_MESSAGE, "method": "no_highlights", "parsed_query": parsed}
        # Real synthesis for a range summary is a K10-follow-on; for now, list them plainly.
        summary = "; ".join(f"{e['kind']} on {(e.get('peak_utc_time') or e['utc_time']).date()}" for e in standout[:5])
        return {"answer": f"Standout events: {summary}.", "method": "factual_lookup", "parsed_query": parsed}

    event = _find_matching_event(parsed, key_events, today)
    if event is None:
        return {"answer": NO_HIGHLIGHTS_MESSAGE, "method": "no_highlights", "parsed_query": parsed}

    resolution, nodal = _resolve_event(event, natal_chart)
    constraints = build_overclaim_constraints(resolution, nodal)

    backend = backend or AnthropicNarrativeBackend()
    event_summary = f"Event: {event['kind']} ({', '.join(event.get('tier_reasons', []))}), tier={event['tier']}."
    prompt = build_query_synthesis_prompt(question, event_summary, constraints)

    try:
        answer_text = backend.synthesize(prompt)
        overclaim_findings = check_overclaims(answer_text, resolution, nodal)
        return {
            "answer": answer_text, "method": "llm", "parsed_query": parsed,
            "resolution": resolution, "nodal": nodal, "overclaim_findings": overclaim_findings,
        }
    except (MissingAPIKeyError, NarrativeBackendError):
        fallback_text = _deterministic_interpretive_fallback(event, resolution, nodal)
        return {
            "answer": fallback_text, "method": "deterministic_fallback", "parsed_query": parsed,
            "resolution": resolution, "nodal": nodal, "overclaim_findings": [],
        }


if __name__ == "__main__":
    from astrology.chart import build_chart
    from astrology.key_events import build_key_events
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    birth_utc = aware_utc.replace(tzinfo=timezone.utc) if aware_utc.tzinfo is None else aware_utc
    natal = build_chart(birth_utc, -37.7392, 144.7967, house_system="placidus")

    print("=== Factual queries (no LLM needed) ===")
    for q in ("what sign is my venus in", "what house is my moon in", "what's happening on 2026-08-28"):
        result = answer_query(q, natal)
        print(f"{q!r} -> [{result['method']}] {result['answer']}")

    print("\n=== Incomplete chart ===")
    result = answer_query("what sign is my venus in", {})
    print(f"-> [{result['method']}] {result['answer']}")
