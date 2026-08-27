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
"""

import re

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
        if contact == "direct_hit":
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
