"""
Static reference tables for Hellenistic/traditional Western technique:
essential dignity (domicile, exaltation, triplicity, bound, decan),
planetary sect, gender, and joy. Nothing here is chart-dependent --
every table is a fixed lookup, verified against independent published
sources during this build (see each table's own note for what was
cross-checked and against what).

This module is deliberately independent of astrology/dignity.py and
astrology/rulership.py, which implement the VEDIC (sidereal,
Parashari) dignity system for Celeste's existing sidereal pipeline --
a genuinely different technique with different exaltation degrees,
different own-sign assignments are the same, but triplicity/bounds/
decans have no Vedic equivalent used elsewhere in this codebase.
Duplicating TRADITIONAL_RULERS here (identical values to
astrology/rulership.py's copy) is intentional: this package must not
import from astrology/ or depend on its sidereal-oriented conventions.
"""

ZODIAC_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

SIGN_INDEX = {name: index for index, name in enumerate(ZODIAC_SIGNS)}

CLASSICAL_PLANETS = ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn")

# Traditional (single-ruler-per-sign) domicile lords -- identical
# values to astrology/rulership.py's TRADITIONAL_RULERS, duplicated
# rather than imported (see module docstring).
DOMICILE_LORDS = {
    "Aries": "mars", "Taurus": "venus", "Gemini": "mercury",
    "Cancer": "moon", "Leo": "sun", "Virgo": "mercury",
    "Libra": "venus", "Scorpio": "mars", "Sagittarius": "jupiter",
    "Capricorn": "saturn", "Aquarius": "saturn", "Pisces": "jupiter",
}

# Sign(s) each planet has domicile in (inverse of DOMICILE_LORDS).
DOMICILE_SIGNS = {
    "sun": ("Leo",),
    "moon": ("Cancer",),
    "mercury": ("Gemini", "Virgo"),
    "venus": ("Taurus", "Libra"),
    "mars": ("Aries", "Scorpio"),
    "jupiter": ("Sagittarius", "Pisces"),
    "saturn": ("Capricorn", "Aquarius"),
}

# Single exaltation sign per planet (classical 7-planet exaltations;
# the Moon's North Node exaltation in Gemini/Cancer nodal doctrine and
# outer-planet "modern" exaltations are not part of this table --
# out of scope, only the 7 classical planets are modeled).
EXALTATION_SIGNS = {
    "sun": "Aries",
    "moon": "Taurus",
    "venus": "Pisces",
    "mars": "Capricorn",
    "jupiter": "Cancer",
    "saturn": "Libra",
    "mercury": "Virgo",
}

EXALTATION_LORD_BY_SIGN = {sign: planet for planet, sign in EXALTATION_SIGNS.items()}

# Detriment = sign opposite domicile; fall = sign opposite exaltation.
# Derived rather than hand-tabulated so they can never drift out of
# sync with DOMICILE_SIGNS/EXALTATION_SIGNS above.
def _opposite(sign: str) -> str:
    return ZODIAC_SIGNS[(SIGN_INDEX[sign] + 6) % 12]


DETRIMENT_SIGNS = {
    planet: tuple(_opposite(sign) for sign in signs)
    for planet, signs in DOMICILE_SIGNS.items()
}

FALL_SIGNS = {planet: _opposite(sign) for planet, sign in EXALTATION_SIGNS.items()}
FALL_LORD_BY_SIGN = {sign: planet for planet, sign in FALL_SIGNS.items()}


# Dorothean/Valens triplicity rulers (day / night / participating),
# one set per triplicity (fire/earth/air/water), applying to all
# three signs of that triplicity alike. Verified via web search
# during this build against two independent technical sources
# (Augurine's triplicity reference and cross-referenced discussion of
# Dorotheus's own table); matches the commonly cited Hellenistic-
# revival table (e.g. as reproduced in Brennan's "Hellenistic
# Astrology"). This is the Dorothean/Valens scheme, not Ptolemy's
# competing (single-ruler, no participating lord) table.
TRIPLICITY_RULERS = {
    "fire": {"day": "sun", "night": "jupiter", "participating": "saturn"},
    "earth": {"day": "venus", "night": "moon", "participating": "mars"},
    "air": {"day": "saturn", "night": "mercury", "participating": "jupiter"},
    "water": {"day": "venus", "night": "mars", "participating": "moon"},
}

SIGN_TRIPLICITY = {
    "Aries": "fire", "Leo": "fire", "Sagittarius": "fire",
    "Taurus": "earth", "Virgo": "earth", "Capricorn": "earth",
    "Gemini": "air", "Libra": "air", "Aquarius": "air",
    "Cancer": "water", "Scorpio": "water", "Pisces": "water",
}

SIGN_ELEMENT = SIGN_TRIPLICITY  # same partition, kept as an alias for readability at call sites


# Egyptian bounds (terms): each sign divided into 5 unequal segments,
# each ruled by one of the 5 non-luminary planets. This is the
# "Egyptian" bounds table (as opposed to the rival Ptolemaic-terms
# table) -- the default in Hellenistic practice and the one George's
# material assumes. Verified via web search during this build against
# THREE independent sources (Augurine, kerykeion.net, and a targeted
# re-check of Virgo specifically after an initial discrepancy) --
# all three now agree exactly, including Virgo's 7-17 Venus segment
# (an earlier recollection had this at 7-13, which turned out to be
# wrong; the cross-check caught it).
#
# Each entry: (low_degree_inclusive, high_degree_exclusive_except_30, planet)
EGYPTIAN_BOUNDS = {
    "Aries": [(0, 6, "jupiter"), (6, 12, "venus"), (12, 20, "mercury"), (20, 25, "mars"), (25, 30, "saturn")],
    "Taurus": [(0, 8, "venus"), (8, 14, "mercury"), (14, 22, "jupiter"), (22, 27, "saturn"), (27, 30, "mars")],
    "Gemini": [(0, 6, "mercury"), (6, 12, "jupiter"), (12, 17, "venus"), (17, 24, "mars"), (24, 30, "saturn")],
    "Cancer": [(0, 7, "mars"), (7, 13, "venus"), (13, 19, "mercury"), (19, 26, "jupiter"), (26, 30, "saturn")],
    "Leo": [(0, 6, "jupiter"), (6, 11, "venus"), (11, 18, "saturn"), (18, 24, "mercury"), (24, 30, "mars")],
    "Virgo": [(0, 7, "mercury"), (7, 17, "venus"), (17, 21, "jupiter"), (21, 28, "mars"), (28, 30, "saturn")],
    "Libra": [(0, 6, "saturn"), (6, 14, "mercury"), (14, 21, "jupiter"), (21, 28, "venus"), (28, 30, "mars")],
    "Scorpio": [(0, 7, "mars"), (7, 11, "venus"), (11, 19, "mercury"), (19, 24, "jupiter"), (24, 30, "saturn")],
    "Sagittarius": [(0, 12, "jupiter"), (12, 17, "venus"), (17, 21, "mercury"), (21, 26, "saturn"), (26, 30, "mars")],
    "Capricorn": [(0, 7, "mercury"), (7, 14, "jupiter"), (14, 22, "venus"), (22, 26, "saturn"), (26, 30, "mars")],
    "Aquarius": [(0, 7, "mercury"), (7, 13, "venus"), (13, 20, "jupiter"), (20, 25, "mars"), (25, 30, "saturn")],
    "Pisces": [(0, 12, "venus"), (12, 16, "jupiter"), (16, 19, "mercury"), (19, 28, "mars"), (28, 30, "saturn")],
}


def bound_lord(sign: str, degree_in_sign: float) -> str:
    for low, high, planet in EGYPTIAN_BOUNDS[sign]:
        if low <= degree_in_sign < high or (high == 30 and degree_in_sign == 30):
            return planet
    raise ValueError(f"degree_in_sign {degree_in_sign} out of range for bounds lookup")


# Chaldean-order decans: the 36 decans (3 per sign x 12 signs) are
# assigned by cycling continuously through the "Chaldean order" of
# the planets (Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon --
# their traditional descending-speed ordering, the same sequence
# behind planetary-hour assignment), starting the cycle at Mars for
# Aries's first decan. This generative rule reproduces the standard
# published decan-ruler table exactly (cross-checked by hand for
# several signs against the well-known table, e.g. Cancer's decans
# running Venus/Mercury/Moon, Capricorn's running Jupiter/Mars/Sun) --
# implemented generatively rather than as 36 hand-typed entries so it
# can't have a typo\'d entry silently disagree with its own pattern.
_CHALDEAN_ORDER = ("saturn", "jupiter", "mars", "sun", "venus", "mercury", "moon")
_ARIES_DECAN_1_OFFSET = _CHALDEAN_ORDER.index("mars")


def decan_lord(sign: str, degree_in_sign: float) -> str:
    if not (0 <= degree_in_sign <= 30):
        raise ValueError(f"degree_in_sign {degree_in_sign} out of range")
    decan_within_sign = min(int(degree_in_sign // 10), 2)  # 0,1,2 -- guards the degree==30 edge
    absolute_decan = SIGN_INDEX[sign] * 3 + decan_within_sign
    return _CHALDEAN_ORDER[(_ARIES_DECAN_1_OFFSET + absolute_decan) % 7]


# Fixed planetary gender. Six of the seven are fixed and uncontested
# (Sun/Mars/Jupiter masculine; Moon/Venus feminine). Mercury is the
# traditional exception -- classical sources (Valens, Firmicus) call
# it "common"/adaptable rather than fixed, most specifically saying it
# takes a masculine nature when oriental (rising before the Sun) and a
# feminine nature when occidental (rising/setting after the Sun). The
# variable spec's gender enum is binary only (no "common" option), so
# Mercury's value here is deliberately left unresolved (None) -- see
# hellenistic.solar_phase.mercury_gender(), which resolves it from the
# already-computed oriental/occidental status instead of guessing a
# static default.
FIXED_GENDER = {
    "sun": "masculine",
    "moon": "feminine",
    "venus": "feminine",
    "mars": "masculine",
    "jupiter": "masculine",
    "saturn": "masculine",
    "mercury": None,
}

# Classical planetary joys by whole-sign house. Uncontested across
# the tradition (Valens, Dorotheus, Firmicus all agree on this table).
JOY_HOUSE = {
    "mercury": 1,
    "moon": 3,
    "venus": 5,
    "mars": 6,
    "sun": 9,
    "jupiter": 11,
    "saturn": 12,
}

# Sect-of-hemisphere joy: the diurnal planets (Sun, Jupiter, Saturn)
# joy by being above the horizon (houses 7-12) in a day chart / below
# it in a night chart; the nocturnal planets (Moon, Venus, Mars) joy
# by the reverse. Mercury has no fixed hemisphere joy (its "common"
# status again) and is excluded. This is the classical sect-based
# hemisphere joy referenced alongside house joy in the tradition
# (e.g. Paulus Alexandrinus), distinct from and additional to
# JOY_HOUSE above.
SECT_OF_HEMISPHERE = {
    "sun": "diurnal", "jupiter": "diurnal", "saturn": "diurnal",
    "moon": "nocturnal", "venus": "nocturnal", "mars": "nocturnal",
}

# A planet's own sect (independent of the chart's sect) -- used to
# derive sect_status (of_sect / contrary_to_sect) by comparing this to
# the chart's day/night sect, and to decide which triplicity ruler
# (day/night) governs a diurnal vs nocturnal chart at all. Mercury is
# sect-neutral in the strictest classical doctrine (it joins whichever
# sect the chart is, or is judged by its solar phase) -- for
# sect_status purposes it is conventionally treated as joining
# whichever sect it is configured toward (oriental -> joins the sect
# in effect; here, simplified per common modern-Hellenistic practice,
# Mercury is of_sect whenever oriental and matches the same
# oriental/occidental-derived logic as its gender). See
# hellenistic.sect for the actual resolution.
PLANET_SECT = {
    "sun": "day", "jupiter": "day", "saturn": "day",
    "moon": "night", "venus": "night", "mars": "night",
}
