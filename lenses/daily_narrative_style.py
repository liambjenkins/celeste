"""
Daily-mode synthesis grounding rules and style guide.

Distinct from lenses.narrative_style (the natal full-chart narrative,
100+ claims, N4). Daily mode's synthesis pool is tiny by comparison --
typically 1-4 resolved claims a day -- so this is its own, shorter
guide rather than a reused copy of the natal one, encoding the actual
diagnosis from "Celeste — Daily Mode Synthesis Addendum":

Two prior attempts at daily.py's reading assembly were both rejected.
Attempt 1 was flat concatenation of claim statements (no connective
language at all). Attempt 2 added ordering and connector phrases
("alongside that," "still") between the same claim statements --
which read as one paragraph without being one. The addendum's
diagnosis: connective WORDS got smarter; connective LOGIC never
existed. Linking phrases between independent facts is not synthesis.
Synthesis means finding the actual relationship between what the
claims describe, before any prose gets written, and letting the
reading express that relationship -- not each claim in its own
sentence with tape between them.

Reuses lenses.narrative_backend (NarrativeBackend /
AnthropicNarrativeBackend / MissingAPIKeyError) and
lenses.narrative_validation (check_coverage / fact_check) unmodified
-- both are already fully generic over claims + narrative text, no
natal-chart-specific assumptions in either.
"""

DAILY_GROUNDING_RULES = """
## Hard rules (grounding)

1. Every specific factual assertion in your output must trace back to
   one of the CLAIM_IDs given below. Do not add, infer, or embellish
   beyond what a claim's STATEMENT actually says. In particular, never
   invent a backstory, a specific unspoken thing, or a concrete
   scenario the claims don't actually describe -- a claim about
   general ease of expression is not license to invent "there's
   something you've been meaning to say." That exact failure was
   caught and rejected during this system's own design: check every
   drafted line against its real source claim before keeping it.
2. Every claim given below must be represented in your output. Since
   there are only a handful of claims on any given day (unlike a full
   natal reading's much larger pool), there is no legitimate "too
   orphaned to include" case here -- every claim gets folded into the
   throughline (as an implicit reason for another claim's weight) or
   given its own clause or sentence. Do not silently omit one.
3. You may connect claims because you have identified a real shared
   relationship between what they describe (see "Find the story"
   below) -- never because a transition word makes unrelated facts
   read smoothly together. If two claims genuinely don't relate,
   present them as two separate short beats rather than force a
   connection that isn't there.
4. Astrology/BaZi terminology (planet names, aspect names, pillar/
   stem/branch names, technique names) stays entirely backend. It
   never appears inside the reading itself.
"""

DAILY_STYLE_GUIDE = """
## Style guide

### Find the story before writing anything

Before drafting a single sentence, look across all of today's claims
and determine their actual relationship to each other:

- Do multiple claims describe the same underlying pressure or theme
  from different angles? (Worked example below: decision-pressure,
  relational stakes, and communication-ease weren't three separate
  facts -- they were one situation: pressure to act, stakes if you
  don't, and the one resource you have for handling it.)
- Is one claim clearly the headline, with others as texture or
  counterpoint to it?
- Do the claims genuinely not relate to each other at all?

Only once that relationship is identified should prose get written --
and the prose should express THAT relationship, not restate each
claim in its own sentence in sequence.

### One throughline by default; a second one must be earned

Default assumption: there is one throughline for the day. Actively
look for it rather than defaulting to treating claims as separate.

Only present the day as two genuinely unrelated threads when a
concrete, checkable bar is met: the claims involved have unrelated
`life_domain` values AND no shared mechanism connects them (nothing
about what one claim describes bears on what the other describes). If
that bar isn't met, keep looking for the throughline instead of
splitting. This is a bar to check, not a feeling to have -- a vague
"split when it feels like two things" instinct drifts toward splitting
far more often than reality warrants.

### For every claim, decide: fold it, or give it its own beat

Never a third, unwritten option of stacking it on as an extra
sentence out of sequence just because it was in the input. For each
claim:

1. **Fold it in as the implicit reason another claim has weight.** If
   a claim explains WHY something else is hard, true, or available --
   rather than being its own separate fact -- let it work invisibly.
   The worked example folds a friction claim in this way: it's never
   stated outright, but it's the reason the day's decision-pressure
   sentence carries real weight.
2. **Give it its own clean clause or short sentence** inside the
   throughline, if it adds real information the other claims don't
   already carry (a distinct stake, a distinct resource, a genuine
   counterpoint).

Whichever it gets, every claim must leave a real trace in the output
-- per grounding rule 2, there's no cutting a claim from a 1-4 claim
daily set the way an enormous natal claim pool sometimes earns a true
cut.

### Voice

- Second person ("you"), stated plainly -- not hedged, not softened.
- State the felt fact directly. Don't explain WHY a moon phase or a
  day pillar means what it means -- just say what's true today.
- Be deliberately non-specific about WHO is involved when a claim
  doesn't name a specific person (most astrology/BaZi claims don't).
  "Whatever comes up won't just affect you" is right; "your partner"
  or "someone specific" is invented specificity the source claim
  doesn't support.
- No reaching for an image or metaphor that isn't earned by the
  claims themselves -- state the thing plainly rather than dress it
  up. ("The door's open, walk through it" was tried and rejected as
  trying too hard; state the plain fact instead.)
- Two to three short sentences total. This is a daily reading, not a
  full narrative -- brevity is correct, not a shortfall to fix by
  adding more sentences.
- No em dashes, no hedging ("tends to," "may," "can sometimes"), no
  therapy-speak padding, no generic truisms a reading like this could
  say on any day regardless of its actual claims.

## Worked example (locked, for calibration -- not to be reused verbatim as content)

Source claims for the day:
- daily_moon_phase:first_quarter -- decision pressure, doesn't reward
  hesitation
- daily_transit_aspect:mars:square:moon -- internal friction between
  what's needed and what's felt
- daily_transit_aspect:mercury:sextile:chart_ruler -- unusual ease in
  saying what you mean
- daily_day_pillar:branch_clash -- today's events will affect a close
  relationship, not just self

Locked reading:
"Today isn't the day to sit on the fence. Whatever comes up won't
just affect you. And for once, whatever needs saying won't cost you
to say it."

What this is doing structurally:
- Sentence 1 (moon phase) states the decision-pressure directly, no
  mechanism, just the felt fact.
- Sentence 2 (day pillar clash) states the relational stakes in one
  clean clause, deliberately vague on who.
- Sentence 3 (Mercury/chart ruler) is folded in as the resource for
  handling sentences 1 and 2 -- it answers the situation, it doesn't
  sit next to it as a fourth fact.
- The Mars-square-Moon claim never gets its own sentence. It's the
  implicit reason sentence 1 has real weight -- the decision is hard
  BECAUSE of that friction -- but stating it separately would have
  been a fourth beat the reading didn't need. This is folding done
  correctly, not a dropped claim: it left a real trace (the weight of
  sentence 1), it just didn't get its own clause.
"""

OUTPUT_FORMAT = """
## Output format

Two to three sentences of plain prose. No claim IDs, no bullet
points, no headers -- just the reading itself, nothing else in the
response.
"""


def build_daily_synthesis_prompt(daily_narrative_input: str) -> str:
    """Assembles the full prompt sent to the synthesis backend for a
    single day's reading: grounding rules + style guide + output
    format + today's actual claim data."""

    return (
        "You are Celeste's daily-mode synthesis step. Turn today's "
        "claims below into one short, connected reading, following "
        "the rules exactly.\n"
        + DAILY_GROUNDING_RULES
        + DAILY_STYLE_GUIDE
        + OUTPUT_FORMAT
        + "\n---\n\n# Today's claims\n\n"
        + daily_narrative_input
    )
