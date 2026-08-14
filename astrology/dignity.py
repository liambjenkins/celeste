"""
Vedic (Jyotish) planetary dignity and Avasthas (Baladi degree-states).

Covers the seven classical planets (Sun, Moon, Mars, Mercury, Jupiter,
Venus, Saturn) only -- Rahu/Ketu and the outer planets have no
classical dignity system in Parashari astrology (later/popular
tradition assigns them exaltation/debilitation signs, but sources
disagree on which, so this is deliberately left out rather than
picking a contested answer -- "requires curation" per this project's
sourcing discipline).

Dignity classification (six levels, strongest to weakest: exalted,
moolatrikona, own sign, friendly sign, neutral sign, enemy sign, plus
debilitated as a distinct low state) uses degree-precise boundaries
for exaltation vs. moolatrikona vs. own-sign *within a single sign*
where those coincide (this happens for every planet except the Sun,
whose moolatrikona sign, Leo, is not its exaltation sign, Aries), and
sign-level friend/neutral/enemy classification (Naisargika/natural
Maitri only -- the simpler, static classical relationships; the
chart-dependent Panchadha Maitri five-fold refinement is a Shadbala-
tier technique, deferred to that phase) elsewhere.

Sources, verified via web search during curation:
  - Exaltation degrees and Moolatrikona degree ranges: cross-referenced
    technical compilations of Brihat Parashara Hora Shastra.
  - Own signs, debilitation (always exactly opposite the exaltation
    sign, same degree): standard, undisputed classical convention.
  - Natural friend/neutral/enemy table (Naisargika Maitri): BPHS,
    cross-referenced across independent technical sources.
  - Baladi Avastha (five degree-based states): BPHS, cross-referenced;
    odd signs count 0->30 in the stated order, even signs reverse it.

Operates on an already-built sidereal chart (astrology.sidereal.
build_sidereal_chart's output).
"""

ZODIAC_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

_SIGN_INDEX = {name: index for index, name in enumerate(ZODIAC_SIGNS)}

CLASSICAL_PLANETS = (
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
)

TRADITIONAL_RULERS = {
    "Aries": "mars", "Taurus": "venus", "Gemini": "mercury",
    "Cancer": "moon", "Leo": "sun", "Virgo": "mercury",
    "Libra": "venus", "Scorpio": "mars", "Sagittarius": "jupiter",
    "Capricorn": "saturn", "Aquarius": "saturn", "Pisces": "jupiter",
}

_OWN_SIGNS = {
    "sun": ("Leo",),
    "moon": ("Cancer",),
    "mars": ("Aries", "Scorpio"),
    "mercury": ("Gemini", "Virgo"),
    "jupiter": ("Sagittarius", "Pisces"),
    "venus": ("Taurus", "Libra"),
    "saturn": ("Capricorn", "Aquarius"),
}

# (exaltation sign, exact exaltation degree within that sign)
_EXALTATION = {
    "sun": ("Aries", 10.0),
    "moon": ("Taurus", 3.0),
    "mars": ("Capricorn", 28.0),
    "mercury": ("Virgo", 15.0),
    "jupiter": ("Cancer", 5.0),
    "venus": ("Pisces", 27.0),
    "saturn": ("Libra", 20.0),
}

# (moolatrikona sign, low degree, high degree)
_MOOLATRIKONA = {
    "sun": ("Leo", 0.0, 20.0),
    "moon": ("Taurus", 4.0, 20.0),
    "mars": ("Aries", 0.0, 12.0),
    "mercury": ("Virgo", 16.0, 20.0),
    "jupiter": ("Sagittarius", 0.0, 10.0),
    "venus": ("Libra", 0.0, 15.0),
    "saturn": ("Aquarius", 0.0, 20.0),
}

_NATURAL_RELATIONSHIPS = {
    "sun": {"friends": {"moon", "mars", "jupiter"}, "enemies": {"venus", "saturn"}},
    "moon": {"friends": {"sun", "mercury"}, "enemies": set()},
    "mars": {"friends": {"sun", "moon", "jupiter"}, "enemies": {"mercury"}},
    "mercury": {"friends": {"sun", "venus"}, "enemies": {"moon"}},
    "jupiter": {"friends": {"sun", "moon", "mars"}, "enemies": {"mercury", "venus"}},
    "venus": {"friends": {"mercury", "saturn"}, "enemies": {"sun", "moon"}},
    "saturn": {"friends": {"mercury", "venus"}, "enemies": {"sun", "moon"}},
}


def _debilitation_sign(planet: str) -> str:
    exalt_sign, _ = _EXALTATION[planet]
    return ZODIAC_SIGNS[(_SIGN_INDEX[exalt_sign] + 6) % 12]


def classify_dignity(planet: str, sign: str, degree_in_sign: float) -> str:
    """
    Classify one of the 7 classical planets' dignity in a sign.
    Returns one of: "exalted", "moolatrikona", "own_sign",
    "friendly_sign", "neutral_sign", "enemy_sign", "debilitated".
    """

    exalt_sign, _ = _EXALTATION[planet]
    debil_sign = _debilitation_sign(planet)
    mt_sign, mt_low, mt_high = _MOOLATRIKONA[planet]
    own_signs = _OWN_SIGNS[planet]

    if sign == debil_sign:
        return "debilitated"

    if sign == mt_sign and mt_low <= degree_in_sign <= mt_high:
        return "moolatrikona"

    # Exaltation covers the whole sign UNLESS the moolatrikona range
    # (which, for every planet but the Sun, sits inside this same
    # sign) has already been passed -- past that point the degree
    # belongs to plain own-sign or the sign's ordinary friend/enemy
    # classification instead, not exaltation.
    if sign == exalt_sign and not (sign == mt_sign and degree_in_sign > mt_high):
        return "exalted"

    if sign in own_signs:
        return "own_sign"

    ruler = TRADITIONAL_RULERS[sign]
    relationships = _NATURAL_RELATIONSHIPS[planet]

    if ruler in relationships["friends"]:
        return "friendly_sign"
    if ruler in relationships["enemies"]:
        return "enemy_sign"
    return "neutral_sign"


_BALADI_ORDER = ("Bala", "Kumara", "Yuva", "Vriddha", "Mrita")


def baladi_avastha(sign_index: int, degree_in_sign: float) -> str:
    """
    Five-fold Baladi Avastha (degree-based "age" state): Bala (infant),
    Kumara (youth), Yuva (adult), Vriddha (old), Mrita (dead) -- each a
    6-degree band. Odd signs count in this order from 0 degrees; even
    signs reverse it.
    """

    band = min(int(degree_in_sign // 6.0), 4)
    is_odd_sign = sign_index % 2 == 0  # Aries (index 0) is an odd sign

    order = _BALADI_ORDER if is_odd_sign else tuple(reversed(_BALADI_ORDER))
    return order[band]


def build_dignity(sidereal_chart: dict) -> dict:
    """
    Dignity + Avastha for each of the 7 classical planets, keyed by
    planet name.
    """

    bodies = sidereal_chart.get("bodies", {})
    result = {}

    for planet in CLASSICAL_PLANETS:
        body = bodies.get(planet)

        if not isinstance(body, dict) or not body.get("sign"):
            continue

        degree_in_sign = body["longitude"] % 30.0

        result[planet] = {
            "dignity": classify_dignity(planet, body["sign"], degree_in_sign),
            "avastha": baladi_avastha(body["sign_index"], degree_in_sign),
        }

    return result


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.sidereal import build_sidereal_chart
    from astrology.time import local_to_utc

    # Worked-example checks from the research pass:
    #   Mercury at 10 deg Virgo -> exalted (before the 16-20 MT band).
    #   Mercury at 18 deg Virgo -> moolatrikona.
    #   Mercury at 25 deg Virgo -> own sign (past the MT band).
    assert classify_dignity("mercury", "Virgo", 10.0) == "exalted"
    assert classify_dignity("mercury", "Virgo", 18.0) == "moolatrikona"
    assert classify_dignity("mercury", "Virgo", 25.0) == "own_sign"
    #   Moon at 2 deg Taurus -> exalted; 10 deg -> moolatrikona;
    #   25 deg -> neutral (Taurus is Venus-ruled, Moon/Venus neutral,
    #   Taurus is NOT one of the Moon's own signs -- Cancer is).
    assert classify_dignity("moon", "Taurus", 2.0) == "exalted"
    assert classify_dignity("moon", "Taurus", 10.0) == "moolatrikona"
    assert classify_dignity("moon", "Taurus", 25.0) == "neutral_sign"
    #   Sun in Libra (its debilitation sign) -> debilitated regardless
    #   of degree.
    assert classify_dignity("sun", "Libra", 15.0) == "debilitated"
    #   Baladi: odd sign (Aries) ascends Bala->Mrita; even sign
    #   (Taurus) reverses it.
    assert baladi_avastha(0, 1.0) == "Bala"
    assert baladi_avastha(0, 29.0) == "Mrita"
    assert baladi_avastha(1, 1.0) == "Mrita"
    assert baladi_avastha(1, 29.0) == "Bala"

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
    dignity = build_dignity(sidereal)

    for planet, info in dignity.items():
        body = sidereal["bodies"][planet]
        print(
            f"{planet:8s} {body['sign']:12s} {body['degree']:2d}deg  "
            f"{info['dignity']:14s} {info['avastha']}"
        )
