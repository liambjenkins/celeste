"""
V0 Western interpretation layer.

Turns structured placements (v0/western/calculate.py) into prose.
This layer knows nothing about how positions were calculated — it
only reads sign names off the structured data.

Reuses what's already built and reviewed: the approved Western
astrology claims in knowledge/claims/approved/ and the Sun/Moon/
Ascendant synthesis in lenses/narrative.py. No new interpretation
content for Western — it already exists.
"""

from dataclasses import dataclass

from knowledge.claims.store import load_approved_claims
from lenses.model import RelevantClaim
from lenses.narrative import build_big_three_narrative
from v0.western.calculate import WesternBigThree

_SIGN_CLAIM_PREFIX = {
    "sun": "astrology_sun_sign_",
    "moon": "astrology_moon_sign_",
    "ascendant": "astrology_ascendant_sign_",
}


@dataclass(frozen=True)
class WesternInterpretation:
    sun_statement: str
    moon_statement: str
    ascendant_statement: str
    sun_house_statement: str
    moon_house_statement: str
    narrative: str
    relationship: str  # "reinforcement" or "tension"


def _find_claim(all_claims, body, sign):
    claim_id = f"{_SIGN_CLAIM_PREFIX[body]}{sign.lower()}"

    for claim in all_claims:
        if claim.claim_id == claim_id:
            return claim

    raise LookupError(
        f"No approved claim found for {body} in {sign} "
        f"(expected claim_id={claim_id})"
    )


def _ordinal(n):
    return f"{n}{'st' if n == 1 else 'nd' if n == 2 else 'rd' if n == 3 else 'th'}"


def _find_house_claim(all_claims, house_number):
    claim_id = f"astrology_house_{house_number}"

    for claim in all_claims:
        if claim.claim_id == claim_id:
            return claim

    raise LookupError(f"No approved claim found for house {house_number}")


def interpret(big_three: WesternBigThree) -> WesternInterpretation:
    all_claims = load_approved_claims(lens_id="astrology")

    sun_claim = _find_claim(all_claims, "sun", big_three.sun.sign)
    moon_claim = _find_claim(all_claims, "moon", big_three.moon.sign)
    ascendant_claim = _find_claim(all_claims, "ascendant", big_three.ascendant.sign)

    # The Ascendant's own house is always the 1st by definition — its
    # sign meaning already covers persona, so there's no separate
    # "Ascendant's house" statement worth adding on top of that.
    sun_house_claim = _find_house_claim(all_claims, big_three.sun.house)
    moon_house_claim = _find_house_claim(all_claims, big_three.moon.house)

    relevant = [
        RelevantClaim(claim=sun_claim, matched_concepts=()),
        RelevantClaim(claim=moon_claim, matched_concepts=()),
        RelevantClaim(claim=ascendant_claim, matched_concepts=()),
    ]

    narrative = build_big_three_narrative(relevant)

    return WesternInterpretation(
        sun_statement=sun_claim.statement,
        moon_statement=moon_claim.statement,
        ascendant_statement=ascendant_claim.statement,
        sun_house_statement=(
            f"The Sun falls in the {_ordinal(big_three.sun.house)} house. "
            f"{sun_house_claim.statement}"
        ),
        moon_house_statement=(
            f"The Moon falls in the {_ordinal(big_three.moon.house)} house. "
            f"{moon_house_claim.statement}"
        ),
        narrative=narrative.paragraph,
        relationship=narrative.relationship,
    )


if __name__ == "__main__":
    from datetime import datetime
    from v0.western.calculate import calculate

    big_three = calculate(
        datetime(1996, 7, 22, 3, 10),
        "Australia/Melbourne",
        -37.7392,
        144.7967,
    )
    result = interpret(big_three)
    print(result.narrative)
    print()
    print("Relationship:", result.relationship)
    print()
    print(result.sun_house_statement)
    print()
    print(result.moon_house_statement)
