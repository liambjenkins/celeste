"""
Jaimini Chara Karakas and Marak (2nd/7th lord) planet identification.

Chara Karakas: the classical 7-karaka scheme (Rahu excluded -- the
more traditional and widely-used of the two competing schemes;
Parashara describes both a 7- and 8-karaka version, verified via
search during curation). The seven classical planets are ranked by
their degree WITHIN their sign, highest first -- ties are vanishingly
rare with real ephemeris precision and are broken by list order
(matching the natural "greater strength" tiebreak classical texts
describe only qualitatively). Rank 1 (highest degree) is Atmakaraka
("soul" significator, the chart's single most emphasized planet in
Jaimini technique); rank 7 (lowest) is Darakaraka (spouse).

Marak ("killer") planets: the lords of the 2nd and 7th houses from
the Ascendant, EXCEPT when a single planet rules both houses (the
"Dwi Marak Na Marak" rule -- a planet ruling both maraka houses loses
its maraka status), verified via search during curation. Traditionally
consulted for timing periods of vulnerability via Dasha, not literal
prediction of death.

Both operate on an already-built sidereal chart (astrology.sidereal.
build_sidereal_chart's output); Marak also needs the traditional
sign-lord table already used by astrology.dignity.
"""

from astrology.dignity import TRADITIONAL_RULERS

CHARA_KARAKA_PLANETS = (
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
)

CHARA_KARAKA_NAMES = (
    "Atmakaraka",     # rank 1 (highest degree) -- soul
    "Amatyakaraka",   # rank 2 -- career/minister
    "Bhratrikaraka",  # rank 3 -- siblings
    "Matrikaraka",    # rank 4 -- mother
    "Putrakaraka",    # rank 5 -- children
    "Gnatikaraka",    # rank 6 -- kin/obstacles
    "Darakaraka",     # rank 7 (lowest degree) -- spouse
)


def build_chara_karakas(sidereal_chart: dict) -> dict:
    """
    Return {karaka_name: {"planet": ..., "degree_in_sign": ...}} for
    the 7 classical Chara Karakas, ranked by degree-within-sign.
    """

    bodies = sidereal_chart.get("bodies", {})

    ranked = sorted(
        (
            (planet, bodies[planet]["longitude"] % 30.0)
            for planet in CHARA_KARAKA_PLANETS
            if planet in bodies
        ),
        key=lambda entry: entry[1],
        reverse=True,
    )

    return {
        CHARA_KARAKA_NAMES[rank]: {"planet": planet, "degree_in_sign": degree}
        for rank, (planet, degree) in enumerate(ranked)
        if rank < len(CHARA_KARAKA_NAMES)
    }


def build_marak_planets(sidereal_chart: dict) -> list:
    """
    Return the list of Marak ("killer") planets: the lords of the
    2nd and 7th houses from the Ascendant, excluding a single planet
    that rules both (Dwi Marak Na Marak).
    """

    ascendant_sign_index = sidereal_chart["ascendant"]["sign_index"]

    zodiac_signs = (
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    )

    second_house_sign = zodiac_signs[(ascendant_sign_index + 1) % 12]
    seventh_house_sign = zodiac_signs[(ascendant_sign_index + 6) % 12]

    second_lord = TRADITIONAL_RULERS[second_house_sign]
    seventh_lord = TRADITIONAL_RULERS[seventh_house_sign]

    if second_lord == seventh_lord:
        return []

    return [second_lord, seventh_lord]


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.sidereal import build_sidereal_chart
    from astrology.time import local_to_utc

    # Worked-example check: Aries Ascendant -> 2nd house Taurus
    # (Venus), 7th house Libra (Venus) -- both ruled by Venus, so no
    # Marak per Dwi Marak Na Marak.
    aries_asc_chart = {"ascendant": {"sign_index": 0}}
    assert build_marak_planets(aries_asc_chart) == []
    # Taurus Ascendant -> 2nd house Gemini (Mercury), 7th house
    # Scorpio (Mars) -- distinct lords, both Marak.
    taurus_asc_chart = {"ascendant": {"sign_index": 1}}
    assert set(build_marak_planets(taurus_asc_chart)) == {"mercury", "mars"}

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

    karakas = build_chara_karakas(sidereal)
    for name, info in karakas.items():
        print(f"{name:14s} {info['planet']:8s} {info['degree_in_sign']:.2f} deg")

    print()
    print("Marak planets:", build_marak_planets(sidereal))
