"""
Celeste Vedic (Jyotish) astrology knowledge seed.

Same compositional building-block structure and sourcing discipline
as knowledge/claims/seeds/astrology.py: curate what each sidereal
sign, nakshatra, and bhava (house) means, then let
lenses/narrative.py-style synthesis combine matched claims at read
time — not a claim for every body x sign x house combination.

Promoted from V0 (this session's hardcoded single-person prototype),
with two real corrections made in the process:
    - Sign meanings and bhava (house) meanings are body-agnostic
      here (one claim per sign/house, matched against whichever body
      actually has it) rather than body-specific like Western's Sun/
      Moon/Ascendant claims. This is a deliberate simplification,
      documented rather than silently made: real Jyotish does carry
      body-specific nuance (Sun in Aries reads differently from Moon
      in Aries), which is a natural candidate for later depth, not
      built here.
    - V0's nakshatra text for Pushya said it was "ruled by Brihaspati"
      — conflating the RULING PLANET (the Vimshottari dasha lord,
      which for Pushya is actually Saturn) with the PRESIDING DEITY
      (Brihaspati/Jupiter as guru of the gods, a separate attribute).
      Fixed here, and the ruling-planet/deity distinction is kept
      explicit for all 27 to avoid repeating that error.

Sources: Brihat Parashara Hora Shastra (Sage Parashara; R. Santhanam's
1984 translation is the standard English edition) for sign character
and bhava significations; standard nakshatra deity/symbol/ruling-
planet tradition (the Vimshottari dasha lord sequence — Ketu, Venus,
Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury, repeating three times
across the 27 nakshatras — is itself a documented classical structure,
not an editorial choice), cross-referenced via search during curation,
not recalled from training alone.

Run as a script to write ApprovedClaim JSON into
knowledge/claims/approved/.
"""

import json
from dataclasses import asdict
from pathlib import Path

from knowledge.claims.model import ApprovedClaim

APPROVED_DIR = Path(__file__).resolve().parent.parent / "approved"

GENERAL_NOTE = (
    "Reflects a widely-repeated interpretation found throughout "
    "standard Vedic astrological literature, exemplified by (not "
    "claimed as a verbatim quotation of) the cited source."
)

ZODIAC_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# All bodies whose sidereal placement can appear in a chart (mirrors
# astrology.py's expanded star-conjunction body list) — sign/house/
# nakshatra claims are body-agnostic, so they should match on any of
# these, not just the classical ten.
_ALL_BODIES = (
    "sun", "moon", "ascendant", "mercury", "venus", "mars", "jupiter",
    "saturn", "uranus", "neptune", "pluto", "lilith_mean", "lilith_true",
    "chiron", "ceres", "pallas", "juno", "vesta", "north_node_true",
    "north_node_mean", "south_node_true", "south_node_mean",
)

claims: list[ApprovedClaim] = []


def _add(
    claim_id,
    statement,
    concept_ids=(),
    feature_ids=(),
    theme_tags=(),
    life_domain=None,
    source_id="",
    notes=GENERAL_NOTE,
):
    claims.append(
        ApprovedClaim(
            claim_id=f"vedic_astrology_{claim_id}",
            lens_id="vedic_astrology",
            statement=statement,
            concept_ids=tuple(concept_ids),
            feature_ids=tuple(feature_ids),
            source_ids=(source_id,),
            theme_tags=tuple(theme_tags),
            life_domain=life_domain,
            editorial_note=notes,
        )
    )


# ------------------------------------------------------------
# Sidereal sign meanings — body-agnostic (see module docstring).
# Source: Brihat Parashara Hora Shastra
# ------------------------------------------------------------

_SIGN_MEANINGS = {
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

for _sign, _meaning in _SIGN_MEANINGS.items():
    _add(
        f"sign_{_sign.lower()}",
        f"A placement in sidereal {_sign} tends to be {_meaning}.",
        concept_ids=["vedic_positions"],
        # A sign's inherent nature doesn't change between the D1
        # (Rasi), D9 (Navamsa), or any other divisional chart — only
        # the domain of life the divisional chart is being read for
        # does. Same claim, matched against vedic_sign: (D1),
        # navamsa_sign: (D9), and varga:{n}: (the remaining
        # Shodasavarga charts) tags rather than duplicated per chart.
        feature_ids=(
            [f"vedic_sign:{body}:{_sign}" for body in _ALL_BODIES]
            + [f"navamsa_sign:{body}:{_sign}" for body in _ALL_BODIES]
            + [
                f"varga:{_n}:{body}:{_sign}"
                for _n in (2, 3, 4, 7, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60)
                for body in ("sun", "moon", "ascendant")
            ]
            + [f"chara_dasha_sign:{_sign}"]
        ),
        theme_tags=["temperament"],
        source_id="parashara_bphs_1984",
    )


# ------------------------------------------------------------
# Nakshatras — ruling planet (Vimshottari dasha lord) and presiding
# deity are distinct attributes, kept explicit throughout.
# Source: classical nakshatra tradition, cross-referenced via search.
# ------------------------------------------------------------

_NAKSHATRAS = {
    "Ashwini": ("Ketu", "the Ashwini Kumaras (divine physicians)", "a horse's head", "swiftness, healing, and being first to act"),
    "Bharani": ("Venus", "Yama (god of death and dharma)", "the yoni", "bearing difficulty with discipline, and transformation through what must be carried"),
    "Krittika": ("Sun", "Agni (the god of fire)", "a razor or flame", "sharp intellect and purification — a decisive willingness to cut away what doesn't serve"),
    "Rohini": ("Moon", "Brahma (the creator)", "an ox-cart", "growth, beauty, and fertility, favoring what is nurtured and made to flourish"),
    "Mrigashira": ("Mars", "Soma (the moon deity)", "a deer's head", "gentle searching — a restless, curious quest for something just out of reach"),
    "Ardra": ("Rahu", "Rudra (the storm god)", "a teardrop", "upheaval that clears the way for renewal, intensity that isn't comfortable but is transformative"),
    "Punarvasu": ("Jupiter", "Aditi (mother of the gods)", "a quiver of arrows", "return and restoration — resourcefulness after loss, renewal of what was scattered"),
    "Pushya": ("Saturn", "Brihaspati (Jupiter as guru of the gods)", "the cow's udder", "nourishment and abundance, with a strong association with dharmic steadiness: honesty, discipline, and the capacity to provide for others"),
    "Ashlesha": ("Mercury", "the Nagas (serpent deities)", "a coiled serpent", "penetrating insight and intensity, a hypnotic or entangling quality that can heal or ensnare"),
    "Magha": ("Ketu", "the Pitris (ancestral spirits)", "a throne", "ancestry and authority — power inherited or earned through lineage and legacy"),
    "Purva Phalguni": ("Venus", "Bhaga (god of fortune and enjoyment)", "the front legs of a bed", "pleasure, rest, and creative enjoyment, favoring relaxation and romance"),
    "Uttara Phalguni": ("Sun", "Aryaman (god of patronage and contracts)", "the back legs of a bed", "patronage, partnership, and the honoring of agreements and commitments"),
    "Hasta": ("Moon", "Savitar (a solar deity of skill and inspiration)", "a hand", "dexterity, precision, and the ability to turn intention into skilled action — a hands-on capacity to build, refine, and heal"),
    "Chitra": ("Mars", "Vishwakarma (the divine architect)", "a bright jewel", "creativity and design, a gift for shaping something visually striking out of raw material"),
    "Swati": ("Rahu", "Vayu (the wind god)", "a shoot of new growth blown by the wind", "independence and self-directed movement, adapting quickly rather than holding a fixed course"),
    "Vishakha": ("Jupiter", "Indra and Agni (twin deities)", "a triumphal archway", "focused purpose and determined achievement, pursuing a goal with steady intensity"),
    "Anuradha": ("Saturn", "Mitra (god of friendship and alliance)", "a lotus", "devotion and friendship, success built through cooperation and loyal alliance"),
    "Jyeshtha": ("Mercury", "Indra (king of the gods)", "an umbrella or earring", "seniority and protection, a natural, sometimes burdensome, position of responsibility over others"),
    "Mula": ("Ketu", "Nirriti (goddess of destruction)", "a bundle of tied roots", "getting to the root of things, even destructively — investigation and transformation that starts by tearing down"),
    "Purva Ashadha": ("Venus", "Apas (the water deities)", "a winnowing basket or elephant tusk", "early-stage invigoration and the confidence to declare victory before it's fully secured"),
    "Uttara Ashadha": ("Sun", "the Vishwadevas (universal gods)", "an elephant tusk", "lasting, hard-won victory — achievement that endures because it was built to last"),
    "Shravana": ("Moon", "Vishnu (the preserver)", "an ear, or three footprints", "listening and learning, absorbing knowledge and connecting people through what's heard and passed on"),
    "Dhanishtha": ("Mars", "the Vasus (gods of material abundance)", "a drum", "rhythm, music, and material abundance, favoring group effort and celebration"),
    "Shatabhisha": ("Rahu", "Varuna (god of cosmic law and the ocean)", "an empty circle", "healing and seclusion — a solitary, often unconventional capacity to repair what's broken"),
    "Purva Bhadrapada": ("Jupiter", "Aja Ekapada (the one-footed goat, a fierce form of Rudra)", "the front legs of a funeral cot", "intensity and vision, a penetrating, sometimes uncomfortable clarity about what must end"),
    "Uttara Bhadrapada": ("Saturn", "Ahir Budhnya (serpent of the deep)", "the back legs of a funeral cot", "depth and quiet wisdom, a still, grounded capacity to hold difficult truths"),
    "Revati": ("Mercury", "Pushan (nurturer and guide of souls)", "a fish, or a drum", "completion and nourishment, gently guiding a journey — or a cycle — to its close"),
}

for _name, (_ruling_planet, _deity, _symbol, _meaning) in _NAKSHATRAS.items():
    _add(
        f"nakshatra_{_name.lower().replace(' ', '_')}",
        (
            f"{_name}'s ruling planet (Vimshottari dasha lord) is "
            f"{_ruling_planet}; its presiding deity is {_deity}, "
            f"symbolized by {_symbol}. It is traditionally associated "
            f"with {_meaning}."
        ),
        concept_ids=["vedic_positions"],
        feature_ids=[f"nakshatra:{body}:{_name}" for body in _ALL_BODIES],
        theme_tags=["nakshatra"],
        source_id="parashara_bphs_1984",
    )


# ------------------------------------------------------------
# Bhavas (houses) — body-agnostic, same simplification as signs.
# Source: Brihat Parashara Hora Shastra
# ------------------------------------------------------------

_BHAVAS = {
    1: ("Tanu Bhava", "the body, personality, and overall vitality — the self as it begins"),
    2: ("Dhana Bhava", "wealth, accumulated resources, family, speech, and personal values"),
    3: ("Sahaja Bhava", "courage, effort, siblings, and communication — what's achieved through initiative"),
    4: ("Sukha Bhava", "home, mother, emotional foundation, property, and inner happiness"),
    5: ("Putra Bhava", "children, intelligence, creativity, and merit carried in from past effort"),
    6: ("Ripu Bhava", "obstacles, disease, debt, and service — what must be worked through, not avoided"),
    7: ("Yuvati Bhava", "marriage, partnership, and open relationships with others as equals"),
    8: ("Randhra Bhava", "longevity, sudden transformation, inheritance, and the occult — what's hidden until it isn't"),
    9: ("Dharma Bhava", "fortune, higher learning, the father, and one's larger sense of purpose"),
    10: ("Karma Bhava", "career, public status, authority, and action taken in the world"),
    11: ("Labha Bhava", "gains, income, friendships, and the fulfillment of aspirations"),
    12: ("Vyaya Bhava", "loss, expenditure, foreign lands, isolation, and spiritual liberation"),
}

_BHAVA_LIFE_DOMAINS = {
    1: "identity", 2: "values_and_desire", 3: "communication",
    4: "foundation_and_security", 5: "values_and_desire", 6: "discipline",
    7: "relationships", 8: "transformation", 9: "expansion_and_meaning",
    10: "drive_and_ambition", 11: "relationships", 12: "transformation",
}

for _house, (_name, _meaning) in _BHAVAS.items():
    _ordinal = f"{_house}{'st' if _house == 1 else 'nd' if _house == 2 else 'rd' if _house == 3 else 'th'}"
    _add(
        f"bhava_{_house}",
        f"The {_ordinal} house ({_name}) governs {_meaning}.",
        concept_ids=["vedic_positions"],
        feature_ids=[f"vedic_house:{body}:{_house}" for body in _ALL_BODIES],
        theme_tags=["life_area"],
        life_domain=_BHAVA_LIFE_DOMAINS[_house],
        source_id="parashara_bphs_1984",
    )


# ------------------------------------------------------------
# Navamsa (D9) core meaning
# Source: Brihat Parashara Hora Shastra, ch. 6 (divisional charts)
# ------------------------------------------------------------

_add(
    "navamsa_core",
    "The Navamsa (D9) is traditionally read as the 'soul' of the "
    "birth chart — a subtler confirmation of what the D1 (Rasi) "
    "chart promises, consulted above all for marriage and dharma "
    "(one's deeper life direction), and for whether a placement's "
    "apparent strength in the D1 chart actually holds up under this "
    "finer subdivision.",
    concept_ids=["navamsa_ascendant"],
    theme_tags=["marriage_and_dharma", "underlying_strength"],
    life_domain="relationships",
    source_id="parashara_bphs_1984",
)


# ------------------------------------------------------------
# Remaining Shodasavarga divisional charts (D2, D3, D4, D7, D10,
# D12, D16, D20, D24, D27, D30, D40, D45, D60). Core meaning only,
# per divisional chart — matched via varga_present:{n}, generic
# across any chart. Each chart's own sign-by-sign reading reuses the
# _SIGN_MEANINGS claims above (extended to match varga:{n}: tags),
# same as Navamsa already does, rather than duplicating 12 sign
# entries per chart.
# Source: Brihat Parashara Hora Shastra, ch. 6 (verified via search
# during curation, cross-referenced against multiple independent
# technical sources for the calculation rule; theme/usage per
# standard Vedic astrological convention).
# ------------------------------------------------------------

_VARGAS = {
    2: (
        "The Hora (D2) is read for wealth and material resources — "
        "which of the two hora lords, Sun or Moon, a placement falls "
        "under colors whether that resource shows up as actively "
        "earned or passively accumulated.",
        "values_and_desire",
    ),
    3: (
        "The Drekkana (D3) is read for siblings, courage, and "
        "self-initiated effort — the capacity to act on one's own "
        "resources rather than through others.",
        "drive_and_ambition",
    ),
    4: (
        "The Chaturthamsa (D4) is read for property, fixed assets, "
        "home, and general fortune — what one comes to own and "
        "settle into over a lifetime.",
        "foundation_and_security",
    ),
    7: (
        "The Saptamsa (D7) is read for children and creative "
        "legacy — what a person brings into being and passes "
        "forward, whether offspring or lasting creative work.",
        "values_and_desire",
    ),
    10: (
        "The Dasamsa (D10) is read for career, public status, and "
        "professional achievement — the second most consulted "
        "divisional chart after Navamsa, and the primary one for "
        "questions of vocation.",
        "drive_and_ambition",
    ),
    12: (
        "The Dwadasamsa (D12) is read for parents and ancestry — "
        "the inherited circumstances and family lineage a person is "
        "born into.",
        "foundation_and_security",
    ),
    16: (
        "The Shodasamsa (D16) is read for vehicles, comforts, and "
        "material happiness — the ease and pleasure available in "
        "day-to-day material life.",
        "values_and_desire",
    ),
    20: (
        "The Vimshamsa (D20) is read for spiritual practice and "
        "religious inclination — a person's capacity for devotion "
        "and inner discipline distinct from outward achievement.",
        "expansion_and_meaning",
    ),
    24: (
        "The Chaturvimshamsa (D24, also called Siddhamsa) is read "
        "for learning, education, and accumulated knowledge — "
        "formal study as well as the deeper wisdom gained through it.",
        "expansion_and_meaning",
    ),
    27: (
        "The Saptavimshamsa (D27, also called Nakshatramsa or "
        "Bhamsa) is read for inherent strengths and weaknesses of "
        "character — the chart's own account of what a person is "
        "fundamentally built of.",
        "identity",
    ),
    30: (
        "The Trimshamsa (D30) is read for misfortune, vulnerability "
        "to harm, and moral conduct — traditionally the chart "
        "consulted for a placement's darker, more difficult "
        "potentials, uniquely built from planetary lordship rather "
        "than equal sign-division like the other Shodasavarga charts.",
        "discipline",
    ),
    40: (
        "The Khavedamsa (D40) is read for auspicious and "
        "inauspicious effects inherited through the maternal line — "
        "general life conditions handed down independent of one's "
        "own effort.",
        "foundation_and_security",
    ),
    45: (
        "The Akshavedamsa (D45) is read for general conduct and "
        "character across a lifetime, inherited through the "
        "paternal line — a broad, cumulative picture of how a "
        "person carries themselves.",
        "identity",
    ),
    60: (
        "The Shashtyamsa (D60) is read as the most granular of the "
        "Shodasavarga charts — traditionally tied to karma carried "
        "in from past lives, and consulted last, to fine-tune or "
        "resolve ambiguity left by the coarser divisional charts.",
        "expansion_and_meaning",
    ),
}

for _n, (_meaning, _domain) in _VARGAS.items():
    _add(
        f"varga_{_n}_core",
        _meaning,
        concept_ids=["vedic_vargas"],
        feature_ids=[f"varga_present:{_n}"],
        theme_tags=["divisional_chart"],
        life_domain=_domain,
        source_id="parashara_bphs_1984",
    )


# ------------------------------------------------------------
# Yogas (classical planetary combinations) — curated set: Gajakesari,
# Budhaditya, and the five Pancha Mahapurusha yogas.
# Source: Brihat Parashara Hora Shastra (verified via search).
# ------------------------------------------------------------

_add(
    "yoga_gajakesari",
    "Gajakesari Yoga (Jupiter in a kendra from the Moon) combines "
    "the Moon's receptivity with Jupiter's wisdom and expansiveness "
    "— traditionally associated with a strong, quick mind, good "
    "reputation, and a generally fortunate, respected life.",
    concept_ids=["vedic_yogas"],
    feature_ids=["yoga:gajakesari"],
    theme_tags=["yoga", "expansion_and_meaning"],
    life_domain="expansion_and_meaning",
    source_id="parashara_bphs_1984",
)

_add(
    "yoga_budhaditya",
    "Budhaditya Yoga (Sun and Mercury sharing a sign) combines solar "
    "authority with Mercury's analytical sharpness — traditionally "
    "associated with intelligence, clear communication, and an "
    "aptitude for teaching, writing, or business.",
    concept_ids=["vedic_yogas"],
    feature_ids=["yoga:budhaditya"],
    theme_tags=["yoga", "communication"],
    life_domain="communication",
    source_id="parashara_bphs_1984",
)

_MAHAPURUSHA_MEANINGS = {
    "ruchaka": (
        "Ruchaka Yoga (Mars in its own or exaltation sign, in a "
        "kendra from the Ascendant)",
        "physical courage, leadership, and a pioneering, "
        "action-oriented drive — traditionally read as favoring "
        "fields that call for strength or decisive action.",
        "drive",
        ["drive", "assertiveness"],
    ),
    "bhadra": (
        "Bhadra Yoga (Mercury in its own or exaltation sign, in a "
        "kendra from the Ascendant)",
        "eloquence, sharp intellect, and commercial or diplomatic "
        "skill — traditionally read as favoring communication, "
        "writing, or business.",
        "communication",
        ["communication", "intellect"],
    ),
    "hamsa": (
        "Hamsa Yoga (Jupiter in its own or exaltation sign, in a "
        "kendra from the Ascendant)",
        "spiritual wisdom, benevolence, and a dignified, respected "
        "bearing — traditionally read as favoring teaching or "
        "guidance roles.",
        "expansion_and_meaning",
        ["spirituality", "growth"],
    ),
    "malavya": (
        "Malavya Yoga (Venus in its own or exaltation sign, in a "
        "kendra from the Ascendant)",
        "artistic sensibility, appreciation of beauty, and "
        "comfortable, harmonious circumstances — traditionally read "
        "as favoring the arts and relationships.",
        "values_and_desire",
        ["aesthetics", "relationships"],
    ),
    "shasha": (
        "Shasha Yoga (Saturn in its own or exaltation sign, in a "
        "kendra from the Ascendant)",
        "disciplined persistence that outlasts more impulsive "
        "competitors — traditionally read as favoring achievement "
        "earned slowly, through structure and endurance, rather "
        "than given easily.",
        "discipline",
        ["discipline", "resilience"],
    ),
}

for _yoga_id, (_definition, _trait, _domain, _themes) in _MAHAPURUSHA_MEANINGS.items():
    _add(
        f"yoga_{_yoga_id}",
        f"{_definition} carries {_trait}",
        concept_ids=["vedic_yogas"],
        feature_ids=[f"yoga:{_yoga_id}"],
        theme_tags=["yoga"] + _themes,
        life_domain=_domain,
        source_id="parashara_bphs_1984",
    )


# ------------------------------------------------------------
# Vimshottari Dasha — general (non-dignity-conditional) effects per
# planet's Mahadasha/Antardasha. BPHS distinguishes "general" effects
# (from a planet's natural characteristics) from "distinctive"
# effects (from its specific dignity/placement in this chart) — only
# the general tier is claimed here, honestly scoped short of the
# dignity-conditional layer, which this pass's Dasha computation
# doesn't evaluate.
# Source: Brihat Parashara Hora Shastra (verified via search).
# ------------------------------------------------------------

_DASHA_GENERAL_EFFECTS = {
    "sun": (
        "brings a period of increased authority, status, and vitality "
        "— favorable for recognition from those in positions of power, "
        "though it can also bring friction with authority figures.",
        "identity",
        ["identity", "drive"],
    ),
    "moon": (
        "brings a period centered on emotional life, home, and the "
        "mind — attentive to domestic matters and inner state, with "
        "the Moon's own changeable nature making this a more "
        "fluctuating period than most.",
        "emotion",
        ["emotional_depth"],
    ),
    "mars": (
        "brings a period of heightened energy, courage, and drive — "
        "favorable for decisive action and matters of property or "
        "siblings, with a real risk of conflict or injury if that "
        "energy isn't channeled constructively.",
        "drive_and_ambition",
        ["drive", "assertiveness"],
    ),
    "rahu": (
        "brings a period of intensified worldly ambition and "
        "unconventional opportunity — often bringing sudden, "
        "significant change and material gain, alongside a "
        "restlessness that isn't easily satisfied.",
        "drive_and_ambition",
        ["ambition", "transformation"],
    ),
    "jupiter": (
        "brings a period of growth, wisdom, and expansion — "
        "favorable for prosperity, higher learning, teachers or "
        "mentors, and matters concerning children.",
        "expansion_and_meaning",
        ["growth", "optimism"],
    ),
    "saturn": (
        "brings a period of discipline, delay, and hard-won "
        "achievement — favors are earned slowly through sustained "
        "effort rather than given easily, a genuine test of "
        "endurance rather than a purely difficult period.",
        "discipline",
        ["discipline", "resilience"],
    ),
    "mercury": (
        "brings a period of sharpened intellect and communication — "
        "favorable for education, business, and adaptability, with "
        "an emphasis on how information and ideas are exchanged.",
        "communication",
        ["communication", "intellect"],
    ),
    "ketu": (
        "brings a period of detachment and introspection — often "
        "marked by loss of what no longer serves alongside genuine "
        "spiritual insight, a period more inward and reflective than "
        "outwardly acquisitive.",
        "transformation",
        ["spirituality", "introspection"],
    ),
    "venus": (
        "brings a period centered on relationships, comfort, and "
        "the arts — favorable for marriage, pleasure, and material "
        "enjoyment.",
        "values_and_desire",
        ["relationships", "aesthetics"],
    ),
}

_YOGINI_LORD_TO_NAME = {
    "moon": "Mangala", "sun": "Pingala", "jupiter": "Dhanya",
    "mars": "Bhramari", "mercury": "Bhadrika", "saturn": "Ulka",
    "venus": "Siddha", "rahu": "Sankata",
}

for _lord, (_effect, _domain, _themes) in _DASHA_GENERAL_EFFECTS.items():
    # Same planetary theme applies across every timescale this
    # project computes for that lord — Mahadasha, Antardasha,
    # Pratyantardasha, Sookshma Dasha, and (where the 8-Yogini scheme
    # includes that planet at all) Yogini Dasha aren't different
    # qualities, just different durations/systems built on the same
    # underlying planetary nature.
    _feature_ids = [
        f"dasha_mahadasha:{_lord}",
        f"dasha_antardasha:{_lord}",
        f"dasha_pratyantardasha:{_lord}",
        f"dasha_sookshma:{_lord}",
    ]
    if _lord in _YOGINI_LORD_TO_NAME:
        _feature_ids.append(f"yogini_dasha:{_YOGINI_LORD_TO_NAME[_lord]}")

    _add(
        f"dasha_general_{_lord}",
        f"A {_lord.capitalize()} Dasha (at any timescale — Mahadasha, "
        f"Antardasha, or finer) generally {_effect}",
        concept_ids=["vedic_dasha"],
        feature_ids=_feature_ids,
        theme_tags=["dasha"] + _themes,
        life_domain=_domain,
        source_id="parashara_bphs_1984",
        notes=(
            "BPHS distinguishes general effects (a planet's natural "
            "characteristics) from distinctive effects (its specific "
            "dignity/placement in a given chart) — only the general "
            "tier is claimed here; this pass's Dasha computation "
            "doesn't evaluate planetary dignity or strength."
        ),
    )


# ------------------------------------------------------------
# Yogini Dasha and Chara Dasha (Jaimini) — technique-overview claims.
# Yogini period effects reuse the planetary-effect claims above (see
# yogini_dasha:{name} tags added to _feature_ids); Chara Dasha's
# per-sign period reuses the sign-meaning claims (feature_ids
# extended below), the same compositional pattern D9/vargas already
# use rather than duplicating content.
# Source: standard classical Yogini Dasha and Jaimini Chara Dasha
# convention, verified via search during curation.
# ------------------------------------------------------------

_add(
    "yogini_dasha_core",
    "Yogini Dasha is a distinct, faster 36-year Vedic timing cycle, "
    "entered via the Moon's birth nakshatra — read alongside "
    "Vimshottari Dasha for a second, independent timing perspective, "
    "prized for its comparative simplicity and quick applicability.",
    concept_ids=["vedic_yogini_dasha"],
    theme_tags=["dasha", "timing_and_technique"],
    life_domain="cyclicality",
    source_id="parashara_bphs_1984",
)

_add(
    "chara_dasha_core",
    "Chara Dasha is the Jaimini school's sign-based (not planet-"
    "based) timing technique — each of the 12 signs rules a period "
    "of 1 to 12 years, its length set by counting from the sign to "
    "wherever its own ruling planet currently sits. Read alongside "
    "Vimshottari Dasha for a second, structurally different timing "
    "perspective, since it tracks houses/life-areas through the sign "
    "period rather than planetary periods directly.",
    concept_ids=["vedic_chara_dasha"],
    theme_tags=["dasha", "timing_and_technique", "jaimini"],
    life_domain="cyclicality",
    source_id="jaimini_sutras",
)


# ------------------------------------------------------------
# Planetary dignity (6 levels + debilitation) and Baladi Avastha
# (5 degree-based states) — body-agnostic, matched via
# dignity:{planet}:{level} and avastha:{planet}:{state} tags for any
# of the 7 classical planets (astrology/dignity.py).
# Source: Brihat Parashara Hora Shastra (verified via search during
# curation — exaltation degrees, Moolatrikona ranges, and the
# Naisargika/natural friend-enemy table all cross-referenced against
# multiple independent technical sources).
# ------------------------------------------------------------

_CLASSICAL_PLANETS = (
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
)

_DIGNITY_LEVELS = {
    "exalted": (
        "Exalted — the strongest classical dignity. A planet here "
        "expresses its natural significations at their fullest and "
        "most confident, largely free of the difficulty a weaker "
        "placement would carry.",
        "underlying_strength",
    ),
    "moolatrikona": (
        "Moolatrikona (\"root triangle\") — a specific degree range, "
        "almost as strong as exaltation, where a planet is "
        "particularly comfortable and effective, distinct from its "
        "plain own sign.",
        "underlying_strength",
    ),
    "own_sign": (
        "Own sign (Swakshetra) — a planet here is naturally "
        "comfortable and stable, expressing its significations "
        "steadily without needing to compensate for foreign terrain.",
        "underlying_strength",
    ),
    "friendly_sign": (
        "Friendly sign — a planet placed in a sign ruled by a "
        "natural friend, lending it a supportive, cooperative "
        "quality even though the terrain isn't fully its own.",
        "underlying_strength",
    ),
    "neutral_sign": (
        "Neutral sign — a planet placed in a sign ruled by neither "
        "friend nor enemy, expressing its significations in a "
        "fairly even, unmodified way.",
        "underlying_strength",
    ),
    "enemy_sign": (
        "Enemy sign — a planet placed in a sign ruled by a natural "
        "enemy, complicating its expression with friction that has "
        "to be worked through rather than flowing naturally.",
        "underlying_strength",
    ),
    "debilitated": (
        "Debilitated — the weakest classical dignity, directly "
        "opposite the planet's exaltation. Its significations are "
        "hardest to access here, though classical technique also "
        "allows for Neecha Bhanga (debilitation-cancellation) under "
        "specific chart conditions not evaluated by this dignity "
        "computation.",
        "underlying_strength",
    ),
}

for _level, (_meaning, _domain) in _DIGNITY_LEVELS.items():
    _add(
        f"dignity_{_level}",
        _meaning,
        concept_ids=["vedic_dignity"],
        feature_ids=[
            f"dignity:{_planet}:{_level}" for _planet in _CLASSICAL_PLANETS
        ],
        theme_tags=["planetary_dignity"],
        source_id="parashara_bphs_1984",
    )

_BALADI_AVASTHAS = {
    "Bala": "Bala (infant) — early, undeveloped strength; results connected to this planet tend to be slow to mature and only partially realized.",
    "Kumara": "Kumara (youth) — growing strength; results connected to this planet are emerging but not yet at full capacity.",
    "Yuva": "Yuva (young adult) — peak strength; results connected to this planet are at their fullest and most capable expression.",
    "Vriddha": "Vriddha (old age) — declining strength; results connected to this planet are fading, past their most capable phase.",
    "Mrita": "Mrita (dead) — minimal strength; results connected to this planet are the hardest to access in this state.",
}

for _state, _meaning in _BALADI_AVASTHAS.items():
    _add(
        f"avastha_{_state.lower()}",
        _meaning,
        concept_ids=["vedic_dignity"],
        feature_ids=[
            f"avastha:{_planet}:{_state}" for _planet in _CLASSICAL_PLANETS
        ],
        theme_tags=["baladi_avastha"],
        source_id="parashara_bphs_1984",
    )


# ------------------------------------------------------------
# Jaimini Chara Karakas (7-karaka scheme) — body-agnostic, matched
# via karaka:{name}:{planet} tags for any of the 7 classical planets
# (astrology/jaimini.py).
# Source: Jaimini Sutras, as documented in classical/modern Jaimini
# astrology references, cross-referenced via search during curation.
# ------------------------------------------------------------

_CHARA_KARAKAS = {
    "Atmakaraka": (
        "Atmakaraka (\"soul significator\") — the planet at the "
        "highest degree within its sign, traditionally read as the "
        "single most important indicator of the soul's own agenda "
        "and deepest motivation in this lifetime.",
        "identity",
    ),
    "Amatyakaraka": (
        "Amatyakaraka (\"minister significator\") — indicates career, "
        "counsel, and the guiding influences a person turns to for "
        "direction.",
        "drive_and_ambition",
    ),
    "Bhratrikaraka": (
        "Bhratrikaraka (\"sibling significator\") — indicates "
        "siblings and courage, the capacity to act alongside or in "
        "support of others.",
        "relationships",
    ),
    "Matrikaraka": (
        "Matrikaraka (\"mother significator\") — indicates the "
        "mother and nurturing, emotionally foundational influences.",
        "foundation_and_security",
    ),
    "Putrakaraka": (
        "Putrakaraka (\"children significator\") — indicates "
        "children and creative or intellectual legacy.",
        "values_and_desire",
    ),
    "Gnatikaraka": (
        "Gnatikaraka (\"kin/obstacles significator\") — indicates "
        "extended relatives, competition, and obstacles to be worked "
        "through.",
        "discipline",
    ),
    "Darakaraka": (
        "Darakaraka (\"spouse significator\") — the planet at the "
        "lowest degree within its sign, traditionally read as the "
        "chart's primary indicator of marriage and spouse.",
        "relationships",
    ),
}

for _karaka_name, (_meaning, _domain) in _CHARA_KARAKAS.items():
    _add(
        f"karaka_{_karaka_name.lower()}",
        _meaning,
        concept_ids=["vedic_karakas"],
        feature_ids=[
            f"karaka:{_karaka_name}:{_planet}" for _planet in _CLASSICAL_PLANETS
        ],
        theme_tags=["chara_karaka"],
        life_domain=_domain,
        source_id="jaimini_sutras",
    )


# ------------------------------------------------------------
# Marak (2nd/7th house lord) planets — matched via marak:{planet}
# tags for any of the 7 classical planets (astrology/jaimini.py).
# Source: standard classical Maraka doctrine (2nd/7th house lordship
# from the Ascendant, with the "Dwi Marak Na Marak" exception when a
# single planet rules both), cross-referenced via search during
# curation.
# ------------------------------------------------------------

_add(
    "marak_core",
    "A Marak (\"killer\") planet is a lord of the 2nd or 7th house "
    "from the Ascendant — traditionally consulted, especially via "
    "its Dasha or Antardasha periods, as a timing significator for "
    "periods of vulnerability, illness, or major transition, not as "
    "a literal prediction of death.",
    concept_ids=["vedic_marak"],
    feature_ids=[f"marak:{_planet}" for _planet in _CLASSICAL_PLANETS],
    theme_tags=["maraka", "timing_and_technique"],
    life_domain="cyclicality",
    source_id="parashara_bphs_1984",
    notes=(
        "A single planet ruling both the 2nd and 7th house loses "
        "Marak status entirely (\"Dwi Marak Na Marak\") — this "
        "chart's Marak computation already applies that exception, "
        "so an empty Marak list is a real, meaningful result, not a "
        "gap in the data."
    ),
)


# ------------------------------------------------------------
# Ashtakavarga — body-agnostic, matched via ashtakavarga_own_sign:
# and sarvashtakavarga: tags for any of the 7 classical planets /
# Sun/Moon/Ascendant respectively.
# Source: Brihat Parashara Hora Shastra ch. 66-72, cross-referenced
# via search during curation for the standard strength thresholds
# (own-sign Bindu: 0-3 weak, 4 medium, 5-8 strong; Sarvashtakavarga:
# <25 weak, 25-28 medium, >28 strong).
# ------------------------------------------------------------

_add(
    "ashtakavarga_core",
    "Ashtakavarga is a classical point-scoring system mapping "
    "relative strength across all 12 signs: eight reference points "
    "(the seven classical planets plus the Ascendant) each "
    "contribute a fixed set of favorable house positions toward "
    "every planet's Bindu (point) total in each sign — a "
    "cross-check on strength distinct from sign dignity or house "
    "placement alone.",
    concept_ids=["vedic_ashtakavarga"],
    theme_tags=["ashtakavarga"],
    life_domain="underlying_strength",
    source_id="parashara_bphs_1984",
)

_OWN_SIGN_BINDU_STRENGTH = {
    "weak": (
        "A planet with 0-3 Bindus in the sign it occupies is "
        "considered weak by Ashtakavarga's own-sign measure — its "
        "results in this chart tend to need more effort to realize, "
        "regardless of its dignity by sign lordship alone."
    ),
    "medium": (
        "A planet with exactly 4 Bindus in the sign it occupies "
        "sits at Ashtakavarga's critical threshold — a turning "
        "point where its results begin to activate reliably."
    ),
    "strong": (
        "A planet with 5 or more Bindus in the sign it occupies is "
        "considered strong by Ashtakavarga's own-sign measure — "
        "well-supported results, reinforcing (or, if its sign "
        "dignity is weak, partially offsetting) its placement by "
        "sign lordship alone."
    ),
}

for _strength, _meaning in _OWN_SIGN_BINDU_STRENGTH.items():
    _add(
        f"ashtakavarga_own_sign_{_strength}",
        _meaning,
        concept_ids=["vedic_ashtakavarga"],
        feature_ids=[
            f"ashtakavarga_own_sign:{_planet}:{_strength}"
            for _planet in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn")
        ],
        theme_tags=["ashtakavarga"],
        life_domain="underlying_strength",
        source_id="parashara_bphs_1984",
    )

_SARVASHTAKAVARGA_STRENGTH = {
    "weak": (
        "A sign with fewer than 25 Sarvashtakavarga Bindus (the "
        "combined score across all seven planets) is considered a "
        "generally weaker area of the chart — matters tied to that "
        "sign tend to move with more friction and require more "
        "sustained effort."
    ),
    "medium": (
        "A sign with 25-28 Sarvashtakavarga Bindus sits at moderate, "
        "workable strength — neither a notably easy nor notably "
        "difficult area of the chart."
    ),
    "strong": (
        "A sign with more than 28 Sarvashtakavarga Bindus is "
        "considered a generally favorable, well-supported area of "
        "the chart — matters tied to that sign tend to move with "
        "comparative ease."
    ),
}

for _strength, _meaning in _SARVASHTAKAVARGA_STRENGTH.items():
    _add(
        f"sarvashtakavarga_{_strength}",
        _meaning,
        concept_ids=["vedic_ashtakavarga"],
        feature_ids=[
            f"sarvashtakavarga:{_point}:{_strength}"
            for _point in ("sun", "moon", "ascendant")
        ],
        theme_tags=["ashtakavarga"],
        life_domain="underlying_strength",
        source_id="parashara_bphs_1984",
    )


def write_claims():
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)

    written = []

    for claim in claims:
        path = APPROVED_DIR / f"{claim.claim_id}.json"

        data = asdict(claim)
        data["status"] = "approved"

        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        written.append(path)

    return written


if __name__ == "__main__":
    print(f"Prepared {len(claims)} claims.")

    by_source = {}
    for claim in claims:
        for source_id in claim.source_ids:
            by_source[source_id] = by_source.get(source_id, 0) + 1

    for source_id, count in sorted(by_source.items()):
        print(f"  {source_id}: {count}")
