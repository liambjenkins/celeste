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
