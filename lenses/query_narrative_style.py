"""
Query synthesis style guide + prompt builder (brief 2d/2e) --
mirrors lenses/daily_narrative_style.py's shape (grounding rules +
build_*_prompt()), scoped to answering one question about one event
rather than a whole-day reading.
"""

QUERY_GROUNDING_RULES = """
GROUNDING RULES -- these are not stylistic preferences, they are hard constraints:

1. Use ONLY the facts given below (the question, the event data, the resolution
   geometry). Never invent a date, a degree, a house, or a relationship that
   isn't stated.
2. Follow the OVERCLAIM CONSTRAINTS exactly -- they state, in plain language,
   what this specific event's real numbers do and don't support. Do not use
   language stronger than what they permit, and do not omit a required
   statement (e.g. "not amplified") they call for.
3. Never mention your own method, sourcing, or how this answer was produced
   ("based on the data provided", "according to the resolution"). Answer as
   if you simply know this about the person's chart.
4. No astrology jargon dumped without context -- name the placement/point
   plainly and explain what it means for them, not just what it's called.
5. If the event data shows genuinely nothing significant, say so plainly.
   Do not manufacture drama or significance that the numbers don't support.
""".strip()


def build_query_synthesis_prompt(question: str, event_summary: str, overclaim_constraints: str) -> str:
    return f"""{QUERY_GROUNDING_RULES}

QUESTION: {question}

EVENT DATA:
{event_summary}

OVERCLAIM CONSTRAINTS (follow exactly):
{overclaim_constraints}

Write a direct, plain-language answer to the question, grounded only in the
event data above and respecting the overclaim constraints exactly. A few
sentences, not a full reading."""
