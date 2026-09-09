"""
Essential dignity resolution for the 7 classical planets: domicile,
exaltation, Dorothean/Valens triplicity (day/night/participating),
Egyptian bound, and Chaldean decan lords, resolved to a single status
enum.

Status resolution order (strongest to weakest, per standard
Hellenistic practice -- a planet gets the STRONGEST dignity it holds,
not a list of all of them): domicile > exalted > triplicity > bound >
decan > peregrine. Detriment and fall are reported instead of
peregiore/any positive dignity when they apply and no positive
dignity is also present in the same sign (a planet can be, e.g., in
its fall sign but still in its own bound -- classical practice calls
that "in its fall" for the headline status while the bound lordship
is preserved separately in the `lords` breakdown, since fall/detriment
describe the SIGN placement specifically and take priority as the
notable condition when no stronger positive dignity offsets them).
"""

from hellenistic.constants import (
    CLASSICAL_PLANETS,
    DETRIMENT_SIGNS,
    DOMICILE_LORDS,
    EXALTATION_LORD_BY_SIGN,
    EXALTATION_SIGNS,
    FALL_SIGNS,
    SIGN_TRIPLICITY,
    TRIPLICITY_RULERS,
    bound_lord,
    decan_lord,
)


def triplicity_lords(sign: str) -> dict:
    element = SIGN_TRIPLICITY[sign]
    return dict(TRIPLICITY_RULERS[element])


def _is_in_own_triplicity(planet: str, sign: str, chart_sect: str) -> bool:
    lords = triplicity_lords(sign)
    return planet in (lords["day"], lords["night"], lords["participating"]) and (
        (chart_sect == "day" and planet == lords["day"])
        or (chart_sect == "night" and planet == lords["night"])
        or planet == lords["participating"]
    )


def resolve_dignity(planet: str, sign: str, degree_in_sign: float, chart_sect: str) -> dict:
    """
    All lordships for this planet's placement, plus the single
    resolved `status` enum: domicile | exalted | triplicity | bound |
    decan | peregrine | detriment | fall.
    """

    domicile_lord = DOMICILE_LORDS[sign]
    exaltation_lord = EXALTATION_LORD_BY_SIGN.get(sign)
    triplicity = triplicity_lords(sign)
    bound = bound_lord(sign, degree_in_sign)
    decan = decan_lord(sign, degree_in_sign)

    lords = {
        "domicile": domicile_lord,
        "exaltation": exaltation_lord,
        "triplicity_day": triplicity["day"],
        "triplicity_night": triplicity["night"],
        "triplicity_participating": triplicity["participating"],
        "bound": bound,
        "decan": decan,
    }

    is_domicile = planet == domicile_lord
    is_exalted = planet == exaltation_lord
    is_triplicity = _is_in_own_triplicity(planet, sign, chart_sect)
    is_bound = planet == bound
    is_decan = planet == decan
    is_detriment = sign in DETRIMENT_SIGNS.get(planet, ())
    is_fall = sign == FALL_SIGNS.get(planet)

    if is_domicile:
        status = "domicile"
    elif is_exalted:
        status = "exalted"
    elif is_triplicity:
        status = "triplicity"
    elif is_bound:
        status = "bound"
    elif is_decan:
        status = "decan"
    elif is_detriment:
        status = "detriment"
    elif is_fall:
        status = "fall"
    else:
        status = "peregrine"

    return {
        "status": status,
        "lords": lords,
        "in_own_domicile": is_domicile,
        "in_own_exaltation": is_exalted,
        "in_own_triplicity": is_triplicity,
        "in_own_bound": is_bound,
        "in_own_decan": is_decan,
        "in_detriment": is_detriment,
        "in_fall": is_fall,
    }


def build_all_dignity(bodies: dict, chart_sect: str) -> dict:
    return {
        planet: resolve_dignity(
            planet, bodies[planet]["sign"], bodies[planet]["degree_in_sign"], chart_sect
        )
        for planet in CLASSICAL_PLANETS
        if planet in bodies
    }
