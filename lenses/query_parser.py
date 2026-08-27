"""
Query parser (brief 2d): free-text question -> structured intent,
via a hybrid, three-stage cascade -- confirmed with Liam as the
architecture over pure-rule or pure-LLM alternatives.

1. Deterministic pattern bank (regex) for the common, unambiguous
   factual-lookup families -- fully offline, zero hallucination
   surface, and (per Q10) MUST work with no ANTHROPIC_API_KEY at all.
2. LLM fallback (reuses lenses.narrative_backend.NarrativeBackend
   unmodified) only for genuinely open-ended text the pattern bank
   doesn't recognize.
3. Strict closed-vocabulary JSON validation on the LLM's output --
   never trusted as free text. Any value outside the enumerated
   vocabulary, any malformed date, any missing required field ->
   rejected, degrading to intent="unparseable" rather than a guess.

Date parsing is deliberately minimal (ISO dates plus a small set of
relative phrases) rather than a general NLP date grammar or a new
dependency -- sufficient for the query families this parser targets,
scope noted explicitly rather than silently underbuilt.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from lenses.narrative_backend import (
    AnthropicNarrativeBackend,
    MissingAPIKeyError,
    NarrativeBackend,
    NarrativeBackendError,
)

BODY_VOCAB = (
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
    "uranus", "neptune", "pluto", "chiron", "north_node_true",
)
NATAL_ROLE_VOCAB = ("ascendant", "mc", "chart_ruler")
EVENT_KIND_VOCAB = (
    "eclipse", "new_moon", "full_moon", "station", "return",
    "transit_aspect", "sign_ingress", "natal_house_ingress", "dasha_change",
)
SIGN_VOCAB = (
    "aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra",
    "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
)
LOOKUP_VOCAB = (
    "natal_placement", "natal_house", "retrograde_status", "next_event",
    "date_snapshot", "range_highlights", "event_impact",
)
INTENT_VOCAB = ("factual", "interpretive", "unparseable")

_BODY_ALIASES = {"rising": "ascendant", "ascendant": "ascendant", "midheaven": "mc", "mc": "mc"}


@dataclass(frozen=True)
class ParsedQuery:
    intent: str
    lookup: str | None
    bodies: tuple[str, ...] = ()
    natal_roles: tuple[str, ...] = ()
    event_kinds: tuple[str, ...] = ()
    sign: str | None = None
    date_start: str | None = None
    date_end: str | None = None
    parse_method: str = "deterministic"
    raw_question: str = ""


@dataclass(frozen=True)
class ParseFailure:
    reason: str
    raw_question: str = ""


def _find_body(text: str) -> str | None:
    for body in BODY_VOCAB:
        if re.search(rf"\b{body}\b", text):
            return body
    return None


def _find_natal_role(text: str) -> str | None:
    for alias, role in _BODY_ALIASES.items():
        if re.search(rf"\b{alias}\b", text):
            return role
    return None


def _find_sign(text: str) -> str | None:
    for sign in SIGN_VOCAB:
        if re.search(rf"\b{sign}\b", text):
            return sign
    return None


def _parse_relative_date(text: str, today: date) -> tuple[str | None, str | None]:
    """Minimal date parsing: ISO dates, and a small set of relative
    phrases. Returns (date_start, date_end) as ISO strings, or
    (None, None) if nothing recognizable is present."""

    iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if iso_match:
        return iso_match.group(1), iso_match.group(1)

    if "tomorrow" in text:
        d = today + timedelta(days=1)
        return d.isoformat(), d.isoformat()
    if "today" in text:
        return today.isoformat(), today.isoformat()
    if "this month" in text:
        start = today.replace(day=1)
        next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        return start.isoformat(), (next_month - timedelta(days=1)).isoformat()
    if "next month" in text:
        start_of_this_month = today.replace(day=1)
        start = (start_of_this_month.replace(day=28) + timedelta(days=4)).replace(day=1)
        next_next = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        return start.isoformat(), (next_next - timedelta(days=1)).isoformat()

    return None, None


# Ordered (pattern, builder) pairs -- first match wins. Each builder
# takes the lowercased question text and returns a ParsedQuery.
def _build_natal_placement(text: str, today: date) -> ParsedQuery:
    body = _find_body(text)
    role = _find_natal_role(text)
    return ParsedQuery(
        intent="factual", lookup="natal_placement",
        bodies=(body,) if body else (), natal_roles=(role,) if role else (),
        parse_method="deterministic", raw_question=text,
    )


def _build_natal_house(text: str, today: date) -> ParsedQuery:
    body = _find_body(text)
    return ParsedQuery(
        intent="factual", lookup="natal_house",
        bodies=(body,) if body else (),
        parse_method="deterministic", raw_question=text,
    )


def _build_retrograde_status(text: str, today: date) -> ParsedQuery:
    body = _find_body(text)
    return ParsedQuery(
        intent="factual", lookup="retrograde_status",
        bodies=(body,) if body else (),
        parse_method="deterministic", raw_question=text,
    )


def _build_next_lunation(kind):
    def builder(text: str, today: date) -> ParsedQuery:
        return ParsedQuery(
            intent="factual", lookup="next_event", event_kinds=(kind,),
            parse_method="deterministic", raw_question=text,
        )
    return builder


def _build_next_eclipse(text: str, today: date) -> ParsedQuery:
    return ParsedQuery(
        intent="factual", lookup="next_event", event_kinds=("eclipse",),
        parse_method="deterministic", raw_question=text,
    )


def _build_next_return(text: str, today: date) -> ParsedQuery:
    body = _find_body(text)
    return ParsedQuery(
        intent="factual", lookup="next_event", event_kinds=("return",),
        bodies=(body,) if body else (),
        parse_method="deterministic", raw_question=text,
    )


def _build_date_snapshot(text: str, today: date) -> ParsedQuery:
    start, end = _parse_relative_date(text, today)
    return ParsedQuery(
        intent="factual", lookup="date_snapshot", date_start=start, date_end=end,
        parse_method="deterministic", raw_question=text,
    )


def _build_range_highlights(text: str, today: date) -> ParsedQuery:
    start, end = _parse_relative_date(text, today)
    return ParsedQuery(
        intent="interpretive", lookup="range_highlights", date_start=start, date_end=end,
        parse_method="deterministic", raw_question=text,
    )


def _build_event_impact(text: str, today: date) -> ParsedQuery:
    sign = _find_sign(text)
    event_kinds = ("eclipse",) if "eclipse" in text else ()
    body = _find_body(text)
    return ParsedQuery(
        intent="interpretive", lookup="event_impact",
        event_kinds=event_kinds, sign=sign, bodies=(body,) if body else (),
        parse_method="deterministic", raw_question=text,
    )


_PATTERN_BANK = (
    (re.compile(r"\bwhat\s+sign\s+is\s+my\b"), _build_natal_placement),
    (re.compile(r"\bwhat'?s\s+my\s+(rising|ascendant|midheaven|mc)\b"), _build_natal_placement),
    (re.compile(r"\bwhat\s+house\s+is\s+my\b"), _build_natal_house),
    (re.compile(r"\bis\s+\w+\s+retrograde\b"), _build_retrograde_status),
    (re.compile(r"\bwhen\s+does\s+\w+\s+(go|turn)\s+(direct|retrograde)\b"), _build_retrograde_status),
    (re.compile(r"\bnext\s+full\s+moon\b"), _build_next_lunation("full_moon")),
    (re.compile(r"\bnext\s+new\s+moon\b"), _build_next_lunation("new_moon")),
    (re.compile(r"\bnext\s+eclipse\b"), _build_next_eclipse),
    (re.compile(r"\b\w+\s+return\b"), _build_next_return),
    (re.compile(r"\bwhat'?s\s+happening\s+on\b"), _build_date_snapshot),
    (re.compile(r"\bwhat\s+is\s+happening\s+on\b"), _build_date_snapshot),
    (re.compile(r"\banything\s+(big|major|significant)\b"), _build_range_highlights),
    (re.compile(r"\bhow\s+will\s+.*\bAFFECT\b"), _build_event_impact),  # placeholder, replaced below
)

# Case-insensitive fix: rebuild the last pattern properly (kept
# separate for readability above).
_PATTERN_BANK = _PATTERN_BANK[:-1] + (
    (re.compile(r"\bhow\s+will\b.*\baffect\s+me\b"), _build_event_impact),
    (re.compile(r"\bhow\s+does\b.*\baffect\s+me\b"), _build_event_impact),
)


def _try_deterministic(question: str, today: date) -> ParsedQuery | None:
    lowered = question.lower().strip()
    for pattern, builder in _PATTERN_BANK:
        if pattern.search(lowered):
            return builder(lowered, today)
    return None


_LLM_SYSTEM_PROMPT = f"""You parse a free-text astrology question into a single JSON object.
Respond with ONLY the JSON object, no other text.

Fields (all required, use null or [] when not applicable):
- "intent": one of {list(INTENT_VOCAB)}
- "lookup": one of {list(LOOKUP_VOCAB)} or null
- "bodies": array, each value one of {list(BODY_VOCAB)}
- "natal_roles": array, each value one of {list(NATAL_ROLE_VOCAB)}
- "event_kinds": array, each value one of {list(EVENT_KIND_VOCAB)}
- "sign": one of {list(SIGN_VOCAB)} or null
- "date_start": an ISO date string (YYYY-MM-DD) or null
- "date_end": an ISO date string (YYYY-MM-DD) or null

Use ONLY values from the lists above -- never invent a value outside them.
If the question doesn't map to any of these fields, use intent="unparseable" and
lookup=null with empty arrays and null dates.
"""


def _validate_llm_json(raw: str, question: str) -> ParsedQuery | ParseFailure:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return ParseFailure("LLM did not return valid JSON", question)

    if not isinstance(data, dict):
        return ParseFailure("LLM JSON was not an object", question)

    intent = data.get("intent")
    if intent not in INTENT_VOCAB:
        return ParseFailure(f"intent {intent!r} not in closed vocabulary", question)

    lookup = data.get("lookup")
    if lookup is not None and lookup not in LOOKUP_VOCAB:
        return ParseFailure(f"lookup {lookup!r} not in closed vocabulary", question)

    bodies = data.get("bodies") or []
    if not isinstance(bodies, list) or any(b not in BODY_VOCAB for b in bodies):
        return ParseFailure(f"bodies {bodies!r} contains a value outside the closed vocabulary", question)

    natal_roles = data.get("natal_roles") or []
    if not isinstance(natal_roles, list) or any(r not in NATAL_ROLE_VOCAB for r in natal_roles):
        return ParseFailure(f"natal_roles {natal_roles!r} contains a value outside the closed vocabulary", question)

    event_kinds = data.get("event_kinds") or []
    if not isinstance(event_kinds, list) or any(k not in EVENT_KIND_VOCAB for k in event_kinds):
        return ParseFailure(f"event_kinds {event_kinds!r} contains a value outside the closed vocabulary", question)

    sign = data.get("sign")
    if sign is not None and sign not in SIGN_VOCAB:
        return ParseFailure(f"sign {sign!r} not in closed vocabulary", question)

    for date_field in ("date_start", "date_end"):
        value = data.get(date_field)
        if value is not None:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except (ValueError, TypeError):
                return ParseFailure(f"{date_field} {value!r} is not a valid ISO date", question)

    return ParsedQuery(
        intent=intent, lookup=lookup, bodies=tuple(bodies), natal_roles=tuple(natal_roles),
        event_kinds=tuple(event_kinds), sign=sign,
        date_start=data.get("date_start"), date_end=data.get("date_end"),
        parse_method="llm", raw_question=question,
    )


def parse_query(
    question: str,
    backend: NarrativeBackend | None = None,
    today: date | None = None,
) -> ParsedQuery | ParseFailure:
    """The full 3-stage cascade. Stage 1 (deterministic) always runs
    and needs no API key -- per Q10, factual lookups must fully work
    offline. Stage 2/3 (LLM + validation) only run when stage 1 finds
    no match; a missing/failing API key degrades to ParseFailure,
    never a crash, matching the MissingAPIKeyError -> labeled-
    fallback posture already established in daily.py."""

    today = today or date.today()

    deterministic = _try_deterministic(question, today)
    if deterministic is not None:
        return deterministic

    backend = backend or AnthropicNarrativeBackend()
    try:
        raw = backend.synthesize(f"{_LLM_SYSTEM_PROMPT}\n\nQuestion: {question}")
    except (MissingAPIKeyError, NarrativeBackendError) as error:
        return ParseFailure(f"LLM fallback unavailable: {error}", question)

    return _validate_llm_json(raw.strip(), question)


if __name__ == "__main__":
    examples = [
        "what sign is my venus in",
        "what house is my moon in",
        "what's my rising sign",
        "when's the next full moon",
        "when is the next eclipse",
        "is mercury retrograde",
        "when does saturn go direct",
        "when is my saturn return",
        "what's happening on 2026-08-28",
        "anything big next month",
        "how will the eclipse in pisces affect me",
    ]
    for q in examples:
        result = parse_query(q)
        print(f"{q!r} ->")
        print(f"  {result}")
