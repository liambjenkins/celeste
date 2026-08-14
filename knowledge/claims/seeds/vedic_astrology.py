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
        # (Rasi) and D9 (Navamsa) charts — only the domain of life
        # the divisional chart is being read for does. Same claim,
        # matched against both vedic_sign: (D1) and navamsa_sign:
        # (D9) tags rather than duplicated.
        feature_ids=(
            [f"vedic_sign:{body}:{_sign}" for body in _ALL_BODIES]
            + [f"navamsa_sign:{body}:{_sign}" for body in _ALL_BODIES]
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
