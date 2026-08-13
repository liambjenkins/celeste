"""
V0 Vedic interpretation layer.

Turns structured sidereal placements (v0/vedic/calculate.py) into
prose. Knows nothing about how positions were calculated.

Hardcoded directly in this module, not routed through the JSON
claims-approval pipeline used for Western — per current scope, this
is a single-tradition, single-person prototype, not a reusable
content library yet. Sign meanings cover all 12 signs (parallel
structure to Western); nakshatra meanings are written only for the
three that actually appear in this chart (Pushya, Hasta, Krittika),
verified against real sources rather than curating all 27 speculatively.

Source: Brihat Parashara Hora Shastra (Sage Parashara; R. Santhanam's
1984 translation is the standard English edition) for sign character;
standard nakshatra deity/symbol tradition (cross-referenced via search,
not recalled from training alone) for the three nakshatra readings.
"""

from dataclasses import dataclass

from v0.vedic.calculate import VedicBigThree

_SIDEREAL_SIGN_MEANINGS = {
    "Aries": "direct, courageous, and quick to act, with a pioneering instinct",
    "Taurus": "steady, patient, and grounded, valuing security and sensory comfort",
    "Gemini": "curious, communicative, and adaptable, with a quick, dual-natured mind",
    "Cancer": "nurturing and emotionally attuned, deeply tied to home and family",
    "Leo": "confident and warm, with a natural authority and need for recognition",
    "Virgo": "analytical and precise, oriented toward service and careful discernment",
    "Libra": "diplomatic and relationship-oriented, seeking balance and fairness",
    "Scorpio": "intense and private, drawn to depth, transformation, and hidden truth",
    "Sagittarius": "philosophical and freedom-loving, guided by belief and higher learning",
    "Capricorn": "disciplined and ambitious, patient in building toward long-term achievement",
    "Aquarius": "independent and unconventional, oriented toward community and ideas",
    "Pisces": "compassionate and intuitive, porous to emotion and spiritually inclined",
}

_NAKSHATRA_MEANINGS = {
    "Pushya": (
        "Pushya, ruled by Brihaspati (Jupiter as guru of the gods), is "
        "traditionally considered one of the most nourishing and "
        "auspicious nakshatras — its symbol is the cow's udder, "
        "representing sustenance and abundance. It carries a strong "
        "association with dharmic steadiness: honesty, discipline, "
        "and the capacity to nourish and provide for others."
    ),
    "Hasta": (
        "Hasta, ruled by the Moon and presided over by Savitar (a "
        "solar deity of skill and inspiration), takes its name from "
        "the Sanskrit word for 'hand.' It is traditionally associated "
        "with dexterity, precision, and the ability to turn intention "
        "into skilled action — a hands-on capacity to build, refine, "
        "and heal."
    ),
    "Krittika": (
        "Krittika, ruled by the Sun and presided over by Agni (the "
        "god of fire), means 'the cutter' and is traditionally "
        "symbolized by a blade. It carries associations with "
        "purification, sharp intellect, and a decisive willingness to "
        "cut away what doesn't serve — alongside a fierce, protective "
        "intensity."
    ),
}


@dataclass(frozen=True)
class VedicInterpretation:
    sun_statement: str
    moon_statement: str
    ascendant_statement: str


def _sign_statement(body_label: str, sign: str) -> str:
    return f"{body_label} in sidereal {sign} is {_SIDEREAL_SIGN_MEANINGS[sign]}."


def _nakshatra_statement(body_label: str, nakshatra: str, pada: int) -> str:
    return (
        f"{body_label} falls in {nakshatra} nakshatra (pada {pada}). "
        f"{_NAKSHATRA_MEANINGS[nakshatra]}"
    )


def interpret(big_three: VedicBigThree) -> VedicInterpretation:
    sun_text = (
        _sign_statement("Sun", big_three.sun.sign)
        + " "
        + _nakshatra_statement("The Sun", big_three.sun.nakshatra, big_three.sun.pada)
    )
    moon_text = (
        _sign_statement("Moon", big_three.moon.sign)
        + " "
        + _nakshatra_statement("The Moon", big_three.moon.nakshatra, big_three.moon.pada)
    )
    ascendant_text = (
        _sign_statement("Ascendant", big_three.ascendant.sign)
        + " "
        + _nakshatra_statement(
            "The Ascendant", big_three.ascendant.nakshatra, big_three.ascendant.pada
        )
    )

    return VedicInterpretation(
        sun_statement=sun_text,
        moon_statement=moon_text,
        ascendant_statement=ascendant_text,
    )


if __name__ == "__main__":
    from datetime import datetime
    from v0.vedic.calculate import calculate

    big_three = calculate(
        datetime(1996, 7, 22, 3, 10),
        "Australia/Melbourne",
        -37.7392,
        144.7967,
    )
    result = interpret(big_three)
    print(result.sun_statement)
    print()
    print(result.moon_statement)
    print()
    print(result.ascendant_statement)
