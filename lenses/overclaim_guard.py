"""
Overclaim guard (brief 2c): bounds how strongly the synthesis step is
allowed to phrase an event's contact with the natal chart, based on
the actual numbers K7's resolve_event_to_natal() and K3's
check_eclipse_nodal_relationship() computed -- a rule the synthesis
step is checked against, not a style preference.

Two halves, mirroring lenses/narrative_validation.py's pre/post-check
split:
- build_overclaim_constraints(): a PRE-generation instruction block,
  injected into the synthesis prompt, naming exactly which language
  is and isn't permitted for this specific event's actual contact
  level.
- check_overclaims(): a POST-generation, deterministic (no API call)
  scan of the generated text against the same rules -- findings are
  returned, never silently discarded, matching how narrative_
  validation.py's fact_check() findings are surfaced rather than
  swallowed.

Batch extension (Query-Answering/Daily-Reading Repair phase):
build_batch_overclaim_constraints()/check_batch_overclaims() apply
the same rules across MULTIPLE simultaneous hits (daily.py's
resolve->tier->guard->write rebuild needs this -- a day can have
several active hits at once, not just one named event). Additive:
the single-event functions above are untouched, still exactly what
lenses/query_answer.py's one-event pipeline uses.

Both batch functions also layer one NEW check on top of the existing
direct_hit rule: direct_hit's own language allowance ("exact",
"directly on", ... all permitted anywhere within the 3-6 degree
direct-hit band) is real astrology but too generous for genuine
exactness language specifically -- the locked eclipse worked example
(5.69 degrees from natal MC) is a real direct_hit, and got called
"exact" in a live test even though 5.69 degrees isn't actually exact.
_TRUE_EXACT_PHRASES is the subset of _EXACTNESS_PHRASES that asserts
genuine exactness (not just a real, wider direct contact) --
additionally banned whenever a hit's own near_exact flag (astrology.
event_significance.is_near_exact, the same 1.0-degree boundary
STANDOUT_SLOW_EXACT_ORB/LUNATION_CONTACT_ORB already use) is False.
"""

import re

from astrology.event_significance import EXACT_LANGUAGE_ORB

# Phrases that assert exactness/direct contact -- banned whenever the
# actual computed contact is NOT a direct hit.
_EXACTNESS_PHRASES = (
    "exact", "exactly", "precisely", "directly on", "conjunct",
    "lands on", "hits your", "dead on", "spot on", "right on",
)

# Phrases that assert a real connection at all -- banned when there's
# genuinely no_contact (not even a shared house).
_CONNECTION_PHRASES = _EXACTNESS_PHRASES + ("activates", "triggers", "lights up")

# Phrases that assert the nodal axis is amplifying an eclipse --
# banned whenever check_eclipse_nodal_relationship() found amplified=False.
_AMPLIFICATION_PHRASES = (
    "amplifies", "amplified", "amplifying", "intensifies", "intensified",
    "supercharges", "heightens its effect", "makes this eclipse stronger",
)

_NOT_AMPLIFIED_ACKNOWLEDGEMENT = re.compile(
    r"\b(not\s+amplif\w*|doesn'?t\s+amplif\w*|no\s+amplification|isn'?t\s+amplif\w*)\b",
    re.IGNORECASE,
)


# The subset of _EXACTNESS_PHRASES that asserts TRUE exactness, as
# opposed to a real-but-wider direct hit -- see module docstring's
# batch-extension note. "directly on", "conjunct", "lands on", "hits
# your" stay permitted anywhere within the direct-hit band; only
# these are additionally banned when a hit isn't near_exact.
_TRUE_EXACT_PHRASES = ("exact", "exactly", "precisely", "dead on", "spot on", "right on")

_NEGATION_WORDS = ("not", "n't", "isn't", "doesn't", "wasn't", "aren't", "never", "without", "no ")
_NEGATION_WINDOW_CHARS = 25


def _find_unnegated(text: str, phrases: tuple[str, ...]) -> list[str]:
    """Every phrase in `phrases` that appears in `text` WITHOUT a
    negation word shortly before it -- "not amplified" or "not
    exactly" must never be flagged as claiming amplification or
    exactness, since they're saying the opposite. Checks every
    occurrence of each phrase, not just the first, so a genuinely
    unnegated instance later in the text is still caught even if an
    earlier instance was correctly negated."""

    lowered = text.lower()
    found = []
    for phrase in phrases:
        for match in re.finditer(re.escape(phrase), lowered):
            preceding = lowered[max(0, match.start() - _NEGATION_WINDOW_CHARS):match.start()]
            if any(neg in preceding for neg in _NEGATION_WORDS):
                continue
            found.append(phrase)
            break
    return found


def build_overclaim_constraints(resolution: dict | None, nodal: dict | None) -> str:
    """A prompt-injectable instruction block naming exactly what
    language is permitted for THIS event, given its real computed
    contact level. Returns an empty string only when there's
    genuinely nothing to constrain (both inputs absent)."""

    lines = []

    if resolution is not None:
        contact = resolution["contact"]
        if contact == "direct_hit" and resolution["nearest_natal_point"] is None:
            # A named-occasion hit with no specific natal point being
            # touched (e.g. a sign/house ingress -- the fact being
            # stated is "this body entered X", not "this body is
            # conjunct natal point Y") -- orb 0.0 here is genuinely
            # exact, so there's no overclaim risk to guard against;
            # nothing to constrain.
            pass
        elif contact == "direct_hit":
            lines.append(
                f"This event is a DIRECT HIT on your {resolution['nearest_natal_point']} "
                f"(orb {resolution['orb_to_nearest']:.2f} degrees, house {resolution['natal_house']}) -- "
                "language like 'exact', 'directly on', or naming the specific point is accurate and allowed."
            )
        elif contact == "thematically_adjacent":
            occupants = ", ".join(resolution["house_occupants"]) or "something"
            lines.append(
                f"This event is NOT an exact hit -- it falls in house {resolution['natal_house']}, "
                f"which also contains your {occupants}, but the nearest point "
                f"({resolution['nearest_natal_point']}) is {resolution['orb_to_nearest']:.2f} degrees away, "
                f"outside the {resolution['direct_hit_orb_used']}-degree direct-hit threshold. "
                "Do NOT say 'exact', 'exactly', 'directly on', 'conjunct', 'precisely', 'lands on', or "
                "'hits your' -- say something like 'in the area of' or 'the same part of your chart' instead."
            )
        else:  # no_contact
            lines.append(
                f"This event has NO meaningful contact with your chart -- house {resolution['natal_house']} "
                f"has no significant natal points in it, and the nearest point is "
                f"{resolution['orb_to_nearest']:.2f} degrees away. Do not imply a real connection at all -- "
                "no 'exact', 'conjunct', 'activates', 'triggers', or similar language."
            )

    if nodal is not None:
        if nodal["amplified"]:
            lines.append(
                f"This eclipse IS amplified by your natal nodal axis ({nodal['relationship']}, "
                f"{min(nodal['separation_to_north_node'], nodal['separation_to_south_node']):.2f} degrees) -- "
                "language describing it as amplified or intensified is accurate here."
            )
        else:
            lines.append(
                f"This eclipse is NOT amplified by your natal nodal axis (relationship: "
                f"{nodal['relationship']}). You MUST explicitly state that it is not amplified -- "
                "do not omit this, and do not use 'amplifies', 'amplified', 'intensifies', or similar language."
            )

    return "\n".join(lines)


def check_overclaims(answer_text: str, resolution: dict | None, nodal: dict | None) -> list[dict]:
    """Deterministic, no-API scan of already-generated text against
    the same rules build_overclaim_constraints() stated. Returns a
    list of findings -- empty if nothing is wrong, never silently
    dropped by the caller."""

    findings = []

    if resolution is not None:
        contact = resolution["contact"]
        if contact == "thematically_adjacent":
            hits = _find_unnegated(answer_text, _EXACTNESS_PHRASES)
            if hits:
                findings.append({
                    "type": "overclaimed_exactness",
                    "phrases_found": hits,
                    "reason": (
                        f"Event is thematically_adjacent (orb {resolution['orb_to_nearest']:.2f} deg, "
                        f"outside the {resolution['direct_hit_orb_used']}-deg direct-hit threshold), "
                        "but the text uses exactness language."
                    ),
                })
        elif contact == "no_contact":
            hits = _find_unnegated(answer_text, _CONNECTION_PHRASES)
            if hits:
                findings.append({
                    "type": "overclaimed_connection",
                    "phrases_found": hits,
                    "reason": "Event has no_contact with the natal chart, but the text implies a real connection.",
                })

    if nodal is not None and not nodal["amplified"]:
        hits = _find_unnegated(answer_text, _AMPLIFICATION_PHRASES)
        if hits:
            findings.append({
                "type": "overclaimed_amplification",
                "phrases_found": hits,
                "reason": f"Nodal relationship is '{nodal['relationship']}' (not amplified), "
                          "but the text uses amplification language.",
            })
        if not _NOT_AMPLIFIED_ACKNOWLEDGEMENT.search(answer_text):
            findings.append({
                "type": "missing_required_statement",
                "reason": "Nodal axis is not amplified, and the text never says so -- "
                           "the brief requires this be stated explicitly, not omitted.",
            })

    return findings


def _resolution_constraint_line(resolution: dict | None) -> str | None:
    """Like build_overclaim_constraints()'s resolution half, but safe
    for a hit with no house (moon-phase hits: a lunation isn't "in" a
    house -- resolution["natal_house"] is None) -- the single-event
    function's house-oriented phrasing ("falls in house X, which also
    contains...") doesn't fit that case and would print "house None"."""

    if resolution is None:
        return None

    if resolution["natal_house"] is not None:
        return build_overclaim_constraints(resolution, None) or None

    contact = resolution["contact"]
    point = resolution["nearest_natal_point"]
    orb = resolution["orb_to_nearest"]

    if contact == "direct_hit" and point is None:
        # Same "nothing to constrain" case as build_overclaim_
        # constraints' own direct_hit branch -- a named-occasion hit
        # with no house AND no specific natal point (a sign ingress)
        # isn't claiming contact with any particular placement.
        return None

    if contact == "direct_hit":
        return (
            f"This touches your {point} directly (orb {orb:.2f} degrees) -- language like "
            "'directly on' or naming the specific point is accurate and allowed."
        )
    return (
        f"This does NOT meaningfully touch your chart -- the nearest point ({point}) is "
        f"{orb:.2f} degrees away. Do not imply a real connection at all -- no 'conjunct', "
        "'activates', 'triggers', or similar language."
    )


def _near_exact_constraint_line(resolution: dict) -> str | None:
    """The new true-exactness-language rule -- only applies to a real
    direct_hit that isn't near_exact (see module docstring)."""

    if resolution is None or resolution["contact"] != "direct_hit" or resolution.get("near_exact"):
        return None

    return (
        f"This is a real direct hit (orb {resolution['orb_to_nearest']:.2f} degrees) but NOT exact -- "
        f"do not use 'exact', 'exactly', 'precisely', 'dead on', 'spot on', or 'right on' (that "
        f"language is only accurate within {EXACT_LANGUAGE_ORB} degrees). 'Directly on', 'conjunct', "
        "or naming the specific point is still accurate."
    )


def build_batch_overclaim_constraints(hits: list[dict]) -> str:
    """The multi-hit sibling of build_overclaim_constraints() -- one
    labeled block per hit, so daily.py's synthesis prompt can gate
    language for every currently-active hit at once, not just one
    named event. Reuses the single-event function for each hit's base
    contact/nodal rules (unchanged behavior), then layers the new
    near_exact rule on top."""

    blocks = []

    for hit in hits:
        resolution = hit.get("resolution")
        nodal = hit.get("nodal")

        lines = []
        resolution_line = _resolution_constraint_line(resolution)
        if resolution_line:
            lines.append(resolution_line)
        nodal_line = build_overclaim_constraints(None, nodal)
        if nodal_line:
            lines.append(nodal_line)

        near_exact_line = _near_exact_constraint_line(resolution)
        if near_exact_line:
            lines.append(near_exact_line)

        if lines:
            blocks.append(f"Regarding {hit['hit_id']}:\n" + "\n".join(lines))

    return "\n\n".join(blocks)


def check_batch_overclaims(answer_text: str, hits: list[dict]) -> list[dict]:
    """The multi-hit sibling of check_overclaims() -- every finding
    is tagged with the hit_id whose RULE it violates, not necessarily
    the hit the offending phrase was actually written about (a plain
    text scan can't do that attribution -- same limitation the single-
    event function already has, just more visible with several hits
    in one prompt). One real violation can therefore surface as
    several same-phrase findings across multiple non-near-exact hits;
    treat findings as "something to review", not "this exact hit was
    misdescribed". Never silently drops anything, same discipline as
    the single-event function."""

    findings = []

    for hit in hits:
        resolution = hit.get("resolution")
        nodal = hit.get("nodal")

        for finding in check_overclaims(answer_text, resolution, nodal):
            findings.append({**finding, "hit_id": hit["hit_id"]})

        if resolution is not None and resolution["contact"] == "direct_hit" and not resolution.get("near_exact"):
            true_exact_hits = _find_unnegated(answer_text, _TRUE_EXACT_PHRASES)
            if true_exact_hits:
                findings.append({
                    "type": "overclaimed_true_exactness",
                    "phrases_found": true_exact_hits,
                    "reason": (
                        f"Hit is a direct_hit (orb {resolution['orb_to_nearest']:.2f} deg) but not "
                        f"near-exact (within {EXACT_LANGUAGE_ORB} deg) -- the text uses true-exactness "
                        "language ('exact', 'precisely', ...)."
                    ),
                    "hit_id": hit["hit_id"],
                })

    return findings


# --- Part 2.4: three additional overclaim categories a real audit
# found the exactness/connection/amplification checks above structurally
# can't catch -- they're keyed to a single hit's orb/nodal data, with
# zero domain-matching, zero occasion-existence checking against the
# real hits list, and zero house-number extraction. All three below are
# best-effort, deterministic (no API call), phrase/keyword-based checks
# -- real natural-language coverage, not exhaustive fact-checking (that
# remains lenses.narrative_validation.fact_check's job, which reads the
# generated text against the actual source claims via a second LLM call
# and has no backend-terminology blind spot a phrase-matcher does).

# A small, precise keyword set per real life_domain value (the 13
# actually in use across the claims knowledge base -- see
# knowledge/claims/model.py's life_domain field). Deliberately narrow:
# favors missing a genuine domain-invention (a false negative) over
# flagging an incidental word overlap (a false positive) -- a life
# domain is an abstract psychological category, not a keyword, so this
# can only ever be an approximate signal, not a real classifier.
_LIFE_DOMAIN_KEYWORDS = {
    "identity": ("your identity", "who you are", "your sense of self"),
    "relationships": ("your relationship", "your partner", "your closest relationship", "someone close to you"),
    "emotion": ("your feelings", "how you feel", "emotionally"),
    "communication": ("what you say", "how you communicate", "the conversation"),
    "values_and_desire": ("your self-worth", "what you value", "what you truly want"),
    "drive_and_ambition": ("your ambition", "your drive", "your career"),
    "expansion_and_meaning": ("your beliefs", "a new opportunity", "your sense of meaning"),
    "foundation_and_security": ("your home", "your family", "your sense of security"),
    "discipline": ("your responsibilities", "your discipline", "your duty"),
    "transformation": ("letting go of", "a real transformation", "releasing"),
    "persona": ("how others see you", "your public image", "your reputation"),
    "cyclicality": ("this cycle", "this phase", "the rhythm of"),
    "underlying_strength": ("your inner strength", "your resilience"),
}


def _find_domain_mentions(text: str) -> dict[str, list[str]]:
    lowered = text.lower()
    found = {}
    for domain, phrases in _LIFE_DOMAIN_KEYWORDS.items():
        hits = [p for p in phrases if p in lowered]
        if hits:
            found[domain] = hits
    return found


def check_life_domain_overclaims(answer_text: str, daily_claims: list) -> list[dict]:
    """Flags the reading invoking a life_domain (career/ambition,
    relationships, home/security, ...) that NO claim resolved today
    actually carries -- the "invented life-domain" fabrication case: a
    real gap since none of check_batch_overclaims' rules ever inspect
    domain/topic at all. `daily_claims` is the same resolved-claims
    list build_daily_reading already has (each item's `.claim.
    life_domain` is the real, already-curated domain tag) -- best-
    effort: a domain invoked without using any of _LIFE_DOMAIN_KEYWORDS'
    specific phrases won't be caught, same honest limitation every
    keyword-based check in this codebase (e.g. narrative_validation.
    check_coverage) already has."""

    supported_domains = {
        item.claim.life_domain for item in daily_claims if item.claim.life_domain
    }

    findings = []
    for domain, phrases in _find_domain_mentions(answer_text).items():
        if domain not in supported_domains:
            findings.append({
                "type": "invented_life_domain",
                "domain": domain,
                "phrases_found": phrases,
                "reason": (
                    f"Text invokes the '{domain}' life domain ({', '.join(phrases)}), "
                    "but no claim resolved today carries that life_domain."
                ),
            })
    return findings


# Phrases that assert today is a special/significant MOMENT -- a real
# named occasion (return/station/ingress/eclipse, or a standing arc at
# its own exact peak) earns this kind of language; an ordinary day of
# background/appendix-tier hits does not. Deliberately NOT astrology
# terminology (grounding rule 4 already bans planet/aspect/technique
# names from the reading itself, so a fabricated occasion wouldn't
# name itself -- these are the plain-language "big day" phrases that
# terminology-hiding still allows through).
_OCCASION_LANGUAGE_PHRASES = (
    "marks a", "marks the", "today marks", "this cycle completes",
    "comes full circle", "a new chapter", "a turning point",
    "a real milestone", "returns to where it began", "closes a chapter",
    "begins a new era", "a once-in-a-lifetime",
)

_NAMED_OCCASION_KINDS = ("return", "station", "sign_ingress", "natal_house_ingress", "eclipse")


def check_occasion_overclaims(answer_text: str, hits: list[dict], western_arc_standing: dict | None = None) -> list[dict]:
    """Flags the reading using "big occasion" language with no real
    named-occasion hit (or an exact standing arc) behind it today --
    the "invented occasion" fabrication case. Best-effort and
    genuinely weaker than the other two Part 2.4 checks: grounding
    rule 4 already keeps backend terminology (the actual event name --
    "Saturn return", "this eclipse") out of the reading, so a
    fabricated occasion is described in the SAME plain feeling-
    language a real one would be -- there is real, accepted false-
    negative risk here that a sufficiently generic fabrication evades
    every phrase in _OCCASION_LANGUAGE_PHRASES. Flagged honestly
    rather than oversold; lenses.narrative_validation.fact_check (a
    live LLM comparison against the real source claims) is the
    stronger backstop for this specific category."""

    lowered = answer_text.lower()
    used_phrases = [p for p in _OCCASION_LANGUAGE_PHRASES if p in lowered]
    if not used_phrases:
        return []

    real_occasion_today = any(h["kind"] in _NAMED_OCCASION_KINDS for h in hits)
    arc_exact = western_arc_standing is not None and western_arc_standing.get("phase") == "exact"
    if real_occasion_today or arc_exact:
        return []

    return [{
        "type": "invented_occasion_language",
        "phrases_found": used_phrases,
        "reason": (
            "Text uses occasion/milestone language ('marks a', 'turning point', ...), "
            "but today has no real named-occasion hit (return/station/ingress/eclipse) "
            "and no standing arc at its own exact peak to back it."
        ),
    }]


_ORDINAL_HOUSE_WORDS = {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
    "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10, "eleventh": 11, "twelfth": 12,
}

_HOUSE_NUMBER_RE = re.compile(
    r"\b(?:(\d{1,2})(?:st|nd|rd|th)?|(" + "|".join(_ORDINAL_HOUSE_WORDS) + r"))\s+house\b",
    re.IGNORECASE,
)


def _extract_house_numbers(text: str) -> set[int]:
    numbers = set()
    for match in _HOUSE_NUMBER_RE.finditer(text.lower()):
        if match.group(1):
            n = int(match.group(1))
            if 1 <= n <= 12:
                numbers.add(n)
        elif match.group(2):
            numbers.add(_ORDINAL_HOUSE_WORDS[match.group(2)])
    return numbers


def check_house_number_overclaims(answer_text: str, real_house_numbers: set[int]) -> list[dict]:
    """Flags a house number named in the reading that matches NO real,
    computed house number from today's context -- the "wrong/invented
    house number" fabrication case. `real_house_numbers` is the union
    of every transit-through house (a transiting body's current house,
    from hits) and every natal-own house relevant today (Big-3, any
    hit-touched point, Vedic sidereal Big-3) -- both tropical and
    sidereal systems unioned together, since the reading's own plain-
    language prose never states which system it means (grounding rule
    4 hides that distinction along with everything else backend).
    Silent (by design) on whether a house number should appear in the
    reading text AT ALL -- that's grounding rule 4's own scope, a
    separate question from whether a number that DOES appear is real."""

    mentioned = _extract_house_numbers(answer_text)
    invented = mentioned - set(real_house_numbers)
    if not invented:
        return []

    return [{
        "type": "invented_house_number",
        "houses_found": sorted(invented),
        "reason": (
            f"Text names house number(s) {sorted(invented)}, but no real, computed "
            "house number from today's context (transit-through or natal-own, "
            "tropical or sidereal) matches."
        ),
    }]


if __name__ == "__main__":
    # The locked eclipse worked example: thematically_adjacent + not amplified.
    resolution = {
        "natal_house": 9, "house_occupants": [], "nearest_natal_point": "mc",
        "orb_to_nearest": 5.69, "direct_hit_orb_used": 6.0, "contact": "direct_hit",
    }
    # Force the thematically_adjacent branch to demonstrate the guard (a flat 3-deg orb would land here).
    adjacent_resolution = {**resolution, "contact": "thematically_adjacent",
                            "house_occupants": ["moon"], "direct_hit_orb_used": 3.0}
    nodal = {
        "relationship": "unrelated", "amplified": False,
        "separation_to_north_node": 144.23, "separation_to_south_node": 35.77,
    }

    print("=== Constraints for the locked example (thematically_adjacent + not amplified) ===")
    print(build_overclaim_constraints(adjacent_resolution, nodal))

    print("\n=== check_overclaims on a BAD draft (violates both rules) ===")
    bad_draft = "This eclipse lands exactly on your Moon, and the nodal axis amplifies its effect."
    for f in check_overclaims(bad_draft, adjacent_resolution, nodal):
        print(f"  {f['type']}: {f['reason']}")

    print("\n=== check_overclaims on a GOOD draft ===")
    good_draft = "This eclipse falls in the same part of your chart as your Moon, though not exactly on it. It's not amplified by your nodal axis."
    findings = check_overclaims(good_draft, adjacent_resolution, nodal)
    print(f"  findings: {findings}")
