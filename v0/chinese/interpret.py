"""
V0 Chinese interpretation layer.

Turns structured Four Pillars (v0/chinese/calculate.py) into prose, in
BaZi's own native terms. Knows nothing about how the pillars were
calculated. Does NOT map onto Sun/Moon/Ascendant — see
v0/chinese/calculate.py's module docstring for why, and
v0/convergence.py for how Chinese enters comparison anyway (only via
Day Master, on the identity theme).

Hardcoded directly in this module, not routed through a claims
pipeline — a single-tradition, single-person prototype, not a reusable
content library yet. Stem and Branch meanings cover all 10/12 (small,
complete tables, parallel to how Western/Vedic sign tables are
complete); pillar-role framing (what Year/Month/Day/Hour each
traditionally govern) and the combined reading are specific to this
chart's actual four pillars.

Source: Serge Augier, Ba Zi: The Four Pillars of Destiny (2010),
cross-referenced against standard Stem/Branch archetype descriptions
repeated across BaZi literature.
"""

from dataclasses import dataclass

from v0.chinese.calculate import FourPillars, Pillar

_STEM_MEANINGS = {
    "Jia": "towering, upright wood — like a great tree: principled, direct, and a natural leader, sometimes rigid",
    "Yi": "flexible wood — like a vine or grass: adaptable and gentle, resilient by bending rather than breaking",
    "Bing": "the sun's fire — radiant, warm, and visible: generous and expressive, drawn to being seen",
    "Ding": "a candle's fire — focused, intimate warmth: perceptive and refined, quietly illuminating",
    "Wu": "mountain earth — solid, stable, and enduring: dependable and steady, sometimes slow to change",
    "Ji": "field earth — receptive and fertile: adaptable and nurturing, absorbing what's needed to grow",
    "Geng": "raw, unrefined metal — like ore or a blade: strong-willed, decisive, and direct, valuing justice",
    "Xin": "refined metal — like jewelry: precise, elegant, and sensitive to being handled carelessly",
    "Ren": "the ocean — vast, powerful, and moving: adventurous and broad-minded, hard to contain",
    "Gui": "rain or mist — subtle and pervasive: intuitive and adaptive, quiet but far-reaching influence",
}

_BRANCH_MEANINGS = {
    "Zi": "the Rat — quick-witted, resourceful, and adaptable, thriving by seizing opportunity",
    "Chou": "the Ox — patient, methodical, and enduring, building slowly toward long-term goals",
    "Yin": "the Tiger — bold, independent, and pioneering, drawn to leading rather than following",
    "Mao": "the Rabbit — gentle, diplomatic, and quick, skilled at navigating around conflict",
    "Chen": "the Dragon — ambitious and dynamic, carrying natural authority and a taste for the grand",
    "Si": "the Snake — perceptive and strategic, working quietly beneath the surface",
    "Wu": "the Horse — energetic and independent, restless when confined",
    "Wei": "the Goat — gentle and artistic, calm on the surface with quiet resilience underneath",
    "Shen": "the Monkey — clever and versatile, quick to find an unconventional solution",
    "You": "the Rooster — precise, observant, and outspoken, holding high standards",
    "Xu": "the Dog — loyal and protective, guided by a strong sense of duty",
    "Hai": "the Pig — generous and easygoing, sincere and diplomatic in relationships",
}

_PILLAR_ROLE = {
    "year": "governs ancestry, early life, and public/social face — the self as it meets the wider world",
    "month": "governs the environment one grows up and works within, and relationship to parents — often considered, alongside the Day, the most influential pillar",
    "day": "IS the self — the Day Stem is the Day Master, the reading's central reference point",
    "hour": "governs later life, children, and the private inner world beneath the public self",
}


@dataclass(frozen=True)
class PillarInterpretation:
    position: str
    statement: str


@dataclass(frozen=True)
class ChineseInterpretation:
    year: PillarInterpretation
    month: PillarInterpretation
    day: PillarInterpretation
    hour: PillarInterpretation
    day_master_statement: str


def _pillar_statement(position: str, pillar: Pillar) -> str:
    stem_text = _STEM_MEANINGS[pillar.stem]
    branch_text = _BRANCH_MEANINGS[pillar.branch]
    role = _PILLAR_ROLE[position]
    return (
        f"The {position.capitalize()} Pillar ({pillar.name}) {role}. "
        f"Its stem, {pillar.stem}, is {stem_text}. "
        f"Its branch, {pillar.branch} ({pillar.branch_animal}), is {branch_text}."
    )


def interpret(pillars: FourPillars) -> ChineseInterpretation:
    day_master_text = (
        f"The Day Master is {pillars.day_master} "
        f"({pillars.day_master_polarity} {pillars.day_master_element}) — "
        f"{_STEM_MEANINGS[pillars.day_master]}. Everything else in a "
        f"BaZi reading is ultimately read in relation to this."
    )

    return ChineseInterpretation(
        year=PillarInterpretation("year", _pillar_statement("year", pillars.year)),
        month=PillarInterpretation("month", _pillar_statement("month", pillars.month)),
        day=PillarInterpretation("day", _pillar_statement("day", pillars.day)),
        hour=PillarInterpretation("hour", _pillar_statement("hour", pillars.hour)),
        day_master_statement=day_master_text,
    )


if __name__ == "__main__":
    from datetime import datetime
    from v0.chinese.calculate import calculate

    pillars = calculate(
        datetime(1996, 7, 22, 3, 10),
        "Australia/Melbourne",
        -37.7392,
        144.7967,
    )
    result = interpret(pillars)
    print(result.day_master_statement)
    print()
    for p in (result.year, result.month, result.day, result.hour):
        print(p.statement)
        print()
