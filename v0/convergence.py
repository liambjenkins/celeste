"""
V0 convergence layer.

Compares Western, Vedic, and Chinese readings by THEME, not by forced
placement equivalence. Western and Vedic both speak to identity
(Sun), emotion (Moon), and persona (Ascendant). Chinese has no native
Moon or Ascendant equivalent, so it only enters the identity
comparison, via the Day Master — see v0/chinese/calculate.py for why
that boundary is deliberate, not a gap to be silently filled.

Classification is a small, transparent keyword-cluster heuristic
(reused directly from lenses/narrative.py, which already does this
for combining Western's own Sun/Moon/Ascendant) — no LLM, fully
inspectable. For each theme, every pair of available traditions is
classified as:
    - CONTRADICTION: the two readings hit clusters this module
      already knows are opposed (e.g. warmth vs. assertive).
    - AGREEMENT: they share a cluster, with no opposition detected.
    - DIVERGENCE: neither — the two readings simply aren't talking
      about the same quality, without being opposed either. This is
      a real, distinct outcome, not a fallback for "unclear."
"""

from dataclasses import dataclass, field
from datetime import datetime
from itertools import combinations

from lenses.narrative import _clusters_in, _has_tension

from v0.western.calculate import calculate as calculate_western
from v0.western.interpret import interpret as interpret_western
from v0.vedic.calculate import calculate as calculate_vedic
from v0.vedic.interpret import interpret as interpret_vedic
from v0.chinese.calculate import calculate as calculate_chinese
from v0.chinese.interpret import interpret as interpret_chinese


@dataclass(frozen=True)
class TraditionReading:
    tradition: str
    label: str  # e.g. "Cancer Sun", "Geng Day Master"
    statement: str


@dataclass(frozen=True)
class PairRelationship:
    tradition_a: str
    tradition_b: str
    verdict: str  # "agreement" | "divergence" | "contradiction"


@dataclass(frozen=True)
class ThemeComparison:
    theme: str
    readings: list[TraditionReading]
    pairs: list[PairRelationship] = field(default_factory=list)


def _classify_pair(text_a: str, text_b: str) -> str:
    clusters_a = _clusters_in(text_a)
    clusters_b = _clusters_in(text_b)

    if _has_tension(clusters_a, clusters_b):
        return "contradiction"

    if clusters_a & clusters_b:
        return "agreement"

    return "divergence"


def _compare_theme(theme: str, readings: list[TraditionReading]) -> ThemeComparison:
    pairs = []

    for a, b in combinations(readings, 2):
        verdict = _classify_pair(a.statement, b.statement)
        pairs.append(
            PairRelationship(
                tradition_a=a.tradition, tradition_b=b.tradition, verdict=verdict
            )
        )

    return ThemeComparison(theme=theme, readings=readings, pairs=pairs)


def _theme_paragraph(comparison: ThemeComparison) -> str:
    labels = {r.tradition: r.label for r in comparison.readings}

    if len(comparison.readings) == 1:
        only = comparison.readings[0]
        return (
            f"On {comparison.theme}, only {only.tradition} speaks directly "
            f"({only.label}) — the other traditions in this reading don't "
            f"have a native placement here, so there's nothing to compare."
        )

    contradictions = [p for p in comparison.pairs if p.verdict == "contradiction"]
    agreements = [p for p in comparison.pairs if p.verdict == "agreement"]
    divergences = [p for p in comparison.pairs if p.verdict == "divergence"]

    reading_list = "; ".join(
        f"{r.tradition} ({r.label})" for r in comparison.readings
    )

    if contradictions:
        pair = contradictions[0]
        return (
            f"On {comparison.theme}, {reading_list} pull in real tension: "
            f"{labels[pair.tradition_a]} and {labels[pair.tradition_b]} point "
            f"toward opposing qualities. This isn't a system being 'wrong' — "
            f"it's three independent lenses on the same person surfacing a "
            f"genuine internal contrast worth sitting with, not resolving away."
        )

    if agreements and not divergences:
        return (
            f"On {comparison.theme}, {reading_list} converge: independently "
            f"computed, working from entirely different calendars and "
            f"reference frames, they land on the same underlying quality."
        )

    if agreements and divergences:
        return (
            f"On {comparison.theme}, {reading_list} partially align: some "
            f"traditions echo each other, while others simply emphasize a "
            f"different facet rather than disagreeing outright."
        )

    return (
        f"On {comparison.theme}, {reading_list} each highlight a different "
        f"facet without echoing or opposing one another — separate angles "
        f"on the same theme, not yet one shared answer."
    )


def build_convergence():
    local_time_args = dict(
        local_time=datetime(1996, 7, 22, 3, 10),
        timezone_name="Australia/Melbourne",
        latitude=-37.7392,
        longitude=144.7967,
    )

    western = interpret_western(calculate_western(**local_time_args))
    vedic_data = calculate_vedic(**local_time_args)
    vedic = interpret_vedic(vedic_data)
    chinese_data = calculate_chinese(**local_time_args)
    chinese = interpret_chinese(chinese_data)

    identity = _compare_theme(
        "identity",
        [
            TraditionReading("Western", "Cancer Sun", western.sun_statement),
            TraditionReading(
                "Vedic", f"sidereal {vedic_data.sun.sign} Sun", vedic.sun_statement
            ),
            TraditionReading(
                "Chinese",
                f"{chinese_data.day_master} Day Master",
                chinese.day_master_statement,
            ),
        ],
    )

    emotion = _compare_theme(
        "emotional nature",
        [
            TraditionReading("Western", "Libra Moon", western.moon_statement),
            TraditionReading(
                "Vedic", f"sidereal {vedic_data.moon.sign} Moon", vedic.moon_statement
            ),
        ],
    )

    persona = _compare_theme(
        "outward persona",
        [
            TraditionReading("Western", "Taurus Ascendant", western.ascendant_statement),
            TraditionReading(
                "Vedic",
                f"sidereal {vedic_data.ascendant.sign} Ascendant",
                vedic.ascendant_statement,
            ),
        ],
    )

    themes = [identity, emotion, persona]
    narrative = "\n\n".join(_theme_paragraph(theme) for theme in themes)

    return themes, narrative


if __name__ == "__main__":
    themes, narrative = build_convergence()

    for theme in themes:
        print(f"=== {theme.theme.upper()} ===")
        for reading in theme.readings:
            print(f"  {reading.tradition}: {reading.label}")
        for pair in theme.pairs:
            print(f"  {pair.tradition_a} vs {pair.tradition_b}: {pair.verdict}")
        print()

    print("=== NARRATIVE ===")
    print(narrative)
