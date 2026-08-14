"""
Shadbala (partial): the classical Vedic six-fold planetary strength
system -- Sthana, Dig, Kala, Chesta, Naisargika, and Drik Bala.

Deliberately scoped to the components a dedicated research pass
confirmed have a single, uncontested classical formula, with no
reliance on unverified extensions: Uchcha Bala, Ojayugma Bala,
Kendradi Bala, and Drekkana Bala (four of Sthana Bala's five
sub-parts), Dig Bala, and Naisargika Bala.

Deliberately EXCLUDED from this pass, and not silently approximated:
  - Saptavargaja Bala (Sthana Bala's largest sub-part, typically its
    biggest single contributor): needs the Panchadha Maitri five-fold
    (natural + temporary) relationship system, which this project has
    not independently verified via search; its point-value table also
    has a genuine, unresolved fork across sources (7.5/3.75/1.875 vs.
    10/4/2 for the middle three tiers). Implementing either without
    further verification risked exactly the "silently-wrong content"
    this project's sourcing discipline exists to prevent.
  - Kala Bala (temporal strength) in full: Nathonnata Bala's precise
    time-reference-point definition, Varsha/Masa Bala's year/month
    lord determination algorithm, and Yuddha Bala's (planetary war)
    winner-determination logic were all found genuinely under-sourced
    or contested even across dedicated technical Jyotish references
    during curation.
  - Chesta Bala: the classical 8-tier motion classification (Vakra/
    Anuvakra/Vikala/Manda/Mandatara/Sama/Chara/Atichara) has no
    sourced numeric speed thresholds to classify a planet's daily
    motion into a tier.
  - Drik Bala: the anchor-point aspect-strength table (0/25/50/75/
    100% at 60/90/120/180 degrees) is solid, but the continuous
    interpolation formula between those anchor points was not found.

BECAUSE of this scoping, this module does NOT compute a true Shadbala
grand total and does NOT compare against the classical Rashmana
(minimum required strength) thresholds -- those are defined for the
complete six-component system, and comparing a partial sum against
them would misrepresent a planet's classical strength. What this
module DOES provide: a real, source-verified relative-strength
comparison among the 7 classical planets, using only the well-
verified components, reported per component and as a subtotal
explicitly labeled partial.

Dig Bala's classical formula measures degree-distance from a house
CUSP (Bhava Madhya), but this project's houses are whole-sign
elsewhere. Here, cusps are approximated as exactly 30 degrees apart
starting from the Ascendant's own precise degree (an equal-house-
style construction used ONLY for this one calculation) -- documented
in dig_bala()'s docstring as a deliberate adaptation, not a hidden
inconsistency.

Source: cross-referenced during curation against Saravali's technical
Shadbala pages, B.V. Raman's "Graha and Bhava Balas" (via a technical
summary of it), and independent technical Jyotish sources, with
component-by-component confidence noted per function below. Points
expressed in Virupas (Shashtiamsas); 60 Virupas = 1 Rupa.

Operates on an already-built sidereal chart (astrology.sidereal.
build_sidereal_chart's output).
"""

from astrology.navamsa import navamsa_sign_index

ZODIAC_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

CLASSICAL_PLANETS = (
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
)

# (exaltation sign, exact exaltation degree) -- same table as
# astrology.dignity, duplicated here (small, 7-entry) rather than
# importing a private symbol.
_EXALTATION = {
    "sun": ("Aries", 10.0), "moon": ("Taurus", 3.0), "mars": ("Capricorn", 28.0),
    "mercury": ("Virgo", 15.0), "jupiter": ("Cancer", 5.0), "venus": ("Pisces", 27.0),
    "saturn": ("Libra", 20.0),
}
_SIGN_INDEX = {name: i for i, name in enumerate(ZODIAC_SIGNS)}


def uchcha_bala(planet: str, sidereal_longitude: float) -> float:
    """
    Exaltation strength: degree-distance from the planet's exact
    DEBILITATION point (folded to <=180 degrees), divided by 3. Max
    60 at exact exaltation, 0 at exact debilitation. High confidence
    -- consistent across every source checked during curation.
    """

    exalt_sign, exalt_degree = _EXALTATION[planet]
    exalt_absolute = _SIGN_INDEX[exalt_sign] * 30.0 + exalt_degree
    debil_absolute = (exalt_absolute + 180.0) % 360.0

    distance = abs(sidereal_longitude - debil_absolute) % 360.0
    distance = min(distance, 360.0 - distance)

    return distance / 3.0


_FEMALE_NATURED = {"moon", "venus"}


def ojayugma_bala(planet: str, sign_index: int, navamsa_index: int) -> float:
    """
    Odd/even sign strength: female-natured planets (Moon, Venus) get
    15 Virupas for occupying an even sign, and 15 more for an even
    Navamsa sign (max 30). Male/neutral-natured planets (the other 5)
    get the same for ODD signs. High confidence -- consistent across
    every source checked during curation.
    """

    is_female = planet in _FEMALE_NATURED
    total = 0.0

    for idx in (sign_index, navamsa_index):
        is_even_sign = idx % 2 == 1  # Taurus (index 1) is the 2nd, an even sign

        if is_female and is_even_sign:
            total += 15.0
        elif not is_female and not is_even_sign:
            total += 15.0

    return total


_KENDRA_HOUSES = {1, 4, 7, 10}
_PANAPARA_HOUSES = {2, 5, 8, 11}


def kendradi_bala(house_number: int) -> float:
    """
    House-type strength (whole-sign, directly compatible with this
    project's house system): kendra houses 60, panapara 30, apoklima
    15. High confidence.
    """

    if house_number in _KENDRA_HOUSES:
        return 60.0
    if house_number in _PANAPARA_HOUSES:
        return 30.0
    return 15.0


# Male planets take the 1st decanate, neuter the 2nd, female the 3rd
# -- verified via search against 3 independent sources during
# curation. Note this order (male-first) contradicts at least one
# popular technical site's table, which the research flagged as
# likely erroneous (outlier vs. 3 agreeing sources).
_MALE_PLANETS = {"sun", "mars", "jupiter"}
_NEUTER_PLANETS = {"mercury", "saturn"}
_FEMALE_PLANETS = {"moon", "venus"}


def drekkana_bala(planet: str, degree_in_sign: float) -> float:
    """
    Decanate strength: 15 Virupas if the planet's gender/nature
    matches its decanate (1st=male, 2nd=neuter, 3rd=female), else 0.
    High confidence (3 independent sources agree on this ordering).
    """

    decanate = min(int(degree_in_sign // 10.0), 2)

    if planet in _MALE_PLANETS and decanate == 0:
        return 15.0
    if planet in _NEUTER_PLANETS and decanate == 1:
        return 15.0
    if planet in _FEMALE_PLANETS and decanate == 2:
        return 15.0
    return 0.0


def sthana_bala_partial(
    planet: str, sidereal_longitude: float, sign_index: int, house_number: int
) -> dict:
    """
    Sum of the four well-verified Sthana Bala sub-parts (Uchcha,
    Ojayugma, Kendradi, Drekkana). Excludes Saptavargaja Bala -- see
    module docstring.
    """

    degree_in_sign = sidereal_longitude % 30.0
    navamsa_index = navamsa_sign_index(sidereal_longitude)

    uchcha = uchcha_bala(planet, sidereal_longitude)
    ojayugma = ojayugma_bala(planet, sign_index, navamsa_index)
    kendradi = kendradi_bala(house_number)
    drekkana = drekkana_bala(planet, degree_in_sign)

    return {
        "uchcha_bala": uchcha,
        "ojayugma_bala": ojayugma,
        "kendradi_bala": kendradi,
        "drekkana_bala": drekkana,
        "sthana_bala_partial": uchcha + ojayugma + kendradi + drekkana,
    }


# Strongest house (from the Ascendant) for each planet's Dig Bala.
_DIG_BALA_STRONGEST_HOUSE = {
    "sun": 10, "mars": 10, "jupiter": 1, "mercury": 1,
    "saturn": 7, "moon": 4, "venus": 4,
}


def dig_bala(planet: str, sidereal_longitude: float, ascendant_longitude: float) -> float:
    """
    Directional strength: degree-distance from the planet's weakest
    point (the house cusp opposite its strongest house), divided by
    3. Cusps are approximated here as exactly 30 degrees apart
    starting from the Ascendant's own precise degree -- an equal-
    house-style construction used only for this calculation, since
    the classical formula is cuspal-degree-based but this project's
    house system is whole-sign elsewhere. High confidence on the
    formula itself; this cuspal adaptation is a documented, deliberate
    simplification.
    """

    strongest_house = _DIG_BALA_STRONGEST_HOUSE[planet]
    strongest_point = (ascendant_longitude + (strongest_house - 1) * 30.0) % 360.0
    weakest_point = (strongest_point + 180.0) % 360.0

    distance = abs(sidereal_longitude - weakest_point) % 360.0
    distance = min(distance, 360.0 - distance)

    return distance / 3.0


# Naisargika Bala: fixed, chart-independent values -- each planet's
# rank (Sun=7 ... Saturn=1) in the classical strength order, times
# 60/7. High confidence -- identical across every source checked,
# no variant found.
_NAISARGIKA_RANK = {
    "sun": 7, "moon": 6, "venus": 5, "jupiter": 4,
    "mercury": 3, "mars": 2, "saturn": 1,
}


def naisargika_bala(planet: str) -> float:
    return _NAISARGIKA_RANK[planet] * 60.0 / 7.0


def build_shadbala_partial(sidereal_chart: dict) -> dict:
    """
    Per-planet component scores (Sthana Bala's 4 verified sub-parts,
    Dig Bala, Naisargika Bala) plus a "partial_total" -- NOT a true
    Shadbala grand total, see module docstring -- for each of the 7
    classical planets.
    """

    bodies = sidereal_chart["bodies"]
    ascendant_longitude = sidereal_chart["ascendant"]["longitude"]

    result = {}

    for planet in CLASSICAL_PLANETS:
        body = bodies.get(planet)
        if not body:
            continue

        sthana = sthana_bala_partial(
            planet, body["longitude"], body["sign_index"], body["house"]
        )
        dig = dig_bala(planet, body["longitude"], ascendant_longitude)
        naisargika = naisargika_bala(planet)

        result[planet] = {
            **sthana,
            "dig_bala": dig,
            "naisargika_bala": naisargika,
            "partial_total": sthana["sthana_bala_partial"] + dig + naisargika,
        }

    return result


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.sidereal import build_sidereal_chart
    from astrology.time import local_to_utc

    # Worked-example checks:
    #   Uchcha Bala: Sun at its exact exaltation degree (10 Aries,
    #   absolute longitude 10) -> max strength 60.
    assert abs(uchcha_bala("sun", 10.0) - 60.0) < 1e-9
    #   Sun at its exact debilitation degree (10 Libra, absolute
    #   longitude 190) -> zero strength.
    assert abs(uchcha_bala("sun", 190.0) - 0.0) < 1e-9
    #   Naisargika Bala: Sun strongest (60), Saturn weakest (~8.57).
    assert naisargika_bala("sun") == 60.0
    assert abs(naisargika_bala("saturn") - 60.0 / 7.0) < 1e-9

    print("Worked-example checks passed.")
    print()

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")
    sidereal = build_sidereal_chart(tropical)
    shadbala = build_shadbala_partial(sidereal)

    ranked = sorted(shadbala.items(), key=lambda item: item[1]["partial_total"], reverse=True)
    for planet, scores in ranked:
        print(f"{planet:8s} partial_total={scores['partial_total']:6.2f}  "
              f"(uchcha={scores['uchcha_bala']:5.2f} ojayugma={scores['ojayugma_bala']:5.2f} "
              f"kendradi={scores['kendradi_bala']:5.2f} drekkana={scores['drekkana_bala']:5.2f} "
              f"dig={scores['dig_bala']:5.2f} naisargika={scores['naisargika_bala']:5.2f})")
