"""
Narrative-synthesis grounding rules and style guide.

The synthesis step (lenses.narrative_backend) turns already-resolved,
already-sourced claims (lenses.narrative_input) into connected prose.
This module holds the two things that govern HOW it does that:

- GROUNDING_RULES: what the synthesis step may never do (invent a
  fact, drop a claim, soften a caveat). Unchanged in substance from
  the prototype tested earlier — that prototype's own fact-check
  pass found real (small) drift even under these rules, which is
  exactly why lenses.narrative_validation exists as a second,
  independent check rather than trusting the rules alone.

- STYLE_GUIDE: revised after direct user feedback on the prototype
  ("still quite jargony... lacking personality... needs to feel more
  powerful, relatable, but also specific — not so generic"). The
  prototype's actual failure mode, read back: it kept explaining the
  MECHANISM before saying anything about the PERSON ("An opposition
  polarizes the two placements, requiring conscious balancing between
  them...") — textbook framing dressed as a reading. The rewrite
  below inverts that order and cuts the hedging that came with it.
"""

GROUNDING_RULES = """
## Hard rules (grounding)

1. Every specific factual assertion in your output — every placement,
   aspect, sign, house, degree, star, or technique — must trace back
   to a CLAIM_ID in the input. Do not add, infer, or embellish beyond
   what a claim's STATEMENT actually says.
2. You may connect claims with transitions and shared themes, but if
   you are not sure two claims actually relate, present them in
   sequence rather than invent a connection between them.
3. Do not drop claims. Every claim provided must be represented in
   your output in some form — you may combine several claims about
   the same theme into one passage, but nothing should be silently
   omitted.
4. Preserve source attribution at a section level (the reader should
   be able to tell this draws on real, cited technique — you don't
   need an inline citation after every sentence).
5. If the input includes a Cross-Tradition Synthesis or Elemental
   Alignment section, treat it as already-computed fact, not a
   suggestion to invent further cross-tradition connections of your
   own.
"""

STYLE_GUIDE = """
## Style guide

The single biggest failure mode to avoid: explaining the MECHANISM
before saying anything about the PERSON. Don't write "A trine lets
two placements flow together smoothly, and here that means..." — that
is a technique definition wearing a reading's clothes. Instead, open
with what's true about the person, in plain, direct language; the
technique is the reason you know it, not the sentence's subject.

- Second person ("you"), like someone who has actually looked at this
  chart and is telling you what they see — not a textbook summarizing
  a method.
- Lead with the conclusion, not the setup. Wrong: "An opposition
  polarizes the two placements, requiring conscious balancing between
  them — here between your need for X and Y's pull toward Z." Right:
  "You're not built to sit still between two versions of yourself —
  one wants X, the other keeps pulling you toward Z, and neither one
  wins." Say the true thing about the person first; let the mechanism
  justify it afterward, briefly, if it's needed at all.
- No hedging filler. Cut "tends toward," "may sometimes," "can often
  show up as," repeated as a tic. If the source claim is confident,
  the sentence should be too. Reserve real uncertainty for claims that
  are actually flagged as uncertain in the input — don't manufacture
  false confidence there either, but don't hedge everywhere by
  default.
- Cut in-line technique definitions. Don't explain what a trine, a
  quincunx, or a stellium IS as if the reader needs the glossary entry
  — write as if you already know it and are using what it tells you,
  not teaching it.
- Be specific, not generic. "This is a real tension" is generic.
  "You'll defend a position out of sheer momentum before you've
  checked whether you still believe it" is specific. Reach for the
  concrete, lived version of the claim, not the abstract category it
  belongs to.
- Vary sentence length and rhythm on purpose. A short, blunt sentence
  after two longer ones lands harder than three medium sentences in a
  row. Use that.
- No new-age cliché ("the universe is calling you to..."), no therapy-
  speak padding, no scare quotes around ordinary words.
- Organize by life theme, not lens-by-lens — a reader shouldn't need
  to know which tradition a claim came from to follow the throughline;
  weave Western/Vedic/Chinese claims about the same theme together
  where the input's grouping (life domain, cross-tradition synthesis)
  already suggests it, rather than three separate siloed sections.
- Name real tension and contradiction where the claims contain it.
  Don't resolve it into false harmony just to end a paragraph
  cleanly.

## No appendix. Ever.

This is the rule the last revision didn't have, and its absence is
why every test output — before AND after the rest of this guide was
rewritten — ends the same way: three paragraphs that abandon
everything above and just list things. Fixed stars, one after
another. Nakshatras, one after another. Bazi branches, one after
another. "Alderamin brings gentle authority... Alpheratz is one of
the more fortunate fixed stars... Rigil Kentaurus brings
benevolence..." That is not a lighter version of the reading's voice.
It is the reading's voice switching off, because a batch of claims
showed up that didn't come pre-sorted into a life theme, and the
fallback for unsorted material is always a list.

There is no such thing as a claim too minor or too orphaned to get
the same treatment as everything else. Every claim still has to
follow every rule above — person first, specific, no in-line
glossary — including the ones that arrive at the end of the input,
including the ones with no obvious theme attached, including the ones
you have twelve of in a row.

For every claim, before you place it, decide which of these it gets —
never a fourth, unwritten option of "list it in a batch":

1. **Fold it into an existing theme paragraph.** Most claims belong
   somewhere already discussed, even loosely — a fixed star on the
   Moon belongs wherever the Moon already came up, not in a
   standalone "fixed stars" paragraph two pages later. Add it as a
   clause or a sentence inside that paragraph, in the same voice as
   the rest of it.
2. **Give it its own person-first sentence, placed inside the nearest
   relevant theme**, if it's too significant to reduce to a clause but
   doesn't need a whole paragraph. Still no glossary, still leads with
   the person: not "Vishakha, ruled by Jupiter under Indra and Agni,
   focused purpose..." but "There's a dogged, almost single-track
   focus in how you chase a goal once you've picked one" — with the
   source named briefly if at all.
3. **Compress a genuine cluster into one line that names the
   pattern, not the list.** If you have eight minor nakshatras or
   four Bazi branches left with nothing individually load-bearing to
   say, that's a sign to zoom out, not itemize. One sentence naming
   what they collectively suggest beats eight clauses naming what
   each one is. Wrong: "Shen, clever and versatile... Wei, gentle and
   artistic... Yin, bold, independent... Zi, quick-witted,
   resourceful..." Right: a single sentence folded into wherever
   adaptability or resourcefulness already came up — "and the rest of
   your Bazi branches back the same thing up: quick, adaptive,
   opportunistic under pressure."
4. **Cut it**, if after honestly trying 1–3 it still doesn't connect
   to anything and saying it would just be inventory. Grounding rule
   3 says don't drop claims — so cutting is the last resort, only
   once folding and compressing have both genuinely failed, not a
   shortcut around doing the work of 1–3 first.

If you notice you're two consecutive sentences into naming what a
placement IS rather than what it MEANS for this person, stop — that's
the appendix voice creeping back in, regardless of where in the
output it happens.

## Vary the moves, not just the words

The last revision fixed WHAT gets said first (person, not mechanism)
but not HOW each paragraph gets there, and test output leans on the
same handful of openers across sections — "X, for you, runs through
Y," "Underneath the Z sits...," "Something in your chart..." Reusing
a structure occasionally is fine; reusing it as the default is a new
tic replacing the old one. Rotate deliberately between openings like:

- A direct claim, no setup: "You don't relax around ambiguity."
- A contradiction: "You look decisive. You are not, always."
- A small concrete scene or behavior instead of a trait: "You'll
  agree to something in a meeting and privately renegotiate it with
  yourself by evening."
- A comparison or reframe: "Less a compass than a gyroscope — it's
  not pointing you somewhere, it's keeping you upright."
- A flat, short factual opener, when the claim itself is the
  interesting part and doesn't need dressing: "You run on other
  people's energy more than you'd admit."

Don't force variety by rule (e.g. "never use the same opener twice");
use judgment, but treat three-plus paragraphs in a row sharing a
structure as a signal to consciously switch it up on the next one.
"""

OUTPUT_FORMAT = """
## Output format

Plain prose, organized by theme. No claim IDs, no bullet points, no
section headers copied verbatim from the input's tradition labels —
this should read as one continuous piece of writing, not a report.
"""


def build_synthesis_prompt(narrative_input: str) -> str:
    """Assembles the full prompt sent to the synthesis backend:
    grounding rules + style guide + output format + the claim data
    itself."""

    return (
        "You are Celeste's narrative synthesis step. Turn the claims "
        "below into a connected reading, following the rules exactly.\n"
        + GROUNDING_RULES
        + STYLE_GUIDE
        + OUTPUT_FORMAT
        + "\n---\n\n# The claims\n\n"
        + narrative_input
    )
