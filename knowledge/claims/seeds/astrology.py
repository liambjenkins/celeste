"""
Celeste astrology knowledge seed.

Curated, source-attributed claims for the astrology lens, structured
as BUILDING BLOCKS (what each planet/sign/house/aspect means) rather
than a combinatorial claim for every planet x sign x house
combination. lenses/narrative.py combines matched claims at read
time — this mirrors how real astrology references are structured
(a "houses" book, a "planets" book, etc.; combination is the
practitioner's job, not something pre-written for every permutation).

Sources cited per section below are real, independently verifiable
texts (checked against web search during curation, not just recalled
from training). Attribution reflects the *tradition* documented by
that text, not a claim of verbatim quotation — noted explicitly in
each claim's `notes` field.

Run as a script to write ApprovedClaim JSON into
knowledge/claims/approved/. Nothing here is "approved" by virtue of
existing in this file — it reflects claims the user reviewed and
approved in conversation before this file was written.
"""

import json
from dataclasses import asdict
from pathlib import Path

from knowledge.claims.model import ApprovedClaim

APPROVED_DIR = Path(__file__).resolve().parent.parent / "approved"

GENERAL_NOTE = (
    "Reflects a widely-repeated interpretation found throughout "
    "standard astrological literature, exemplified by (not claimed "
    "as a verbatim quotation of) the cited source."
)

ZODIAC_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

claims: list[ApprovedClaim] = []


def _article(word):
    return "An" if word[0].upper() in "AEIOU" else "A"


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
            claim_id=f"astrology_{claim_id}",
            lens_id="astrology",
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
# Standalone sign meanings (element/modality/rulership) --
# Combinatorial-Meaning Expansion, Phase 3. What a sign means
# independent of any body -- distinct from the 219 planet-in-sign
# claims elsewhere in this file, which already carry plenty of sign
# flavor IN CONTEXT. This family exists as an honest last-resort
# fallback for a natal point that has no body-specific sign-claim
# family at all: lilith_true is a real PRIMARY_NATAL_ROLES member
# (astrology/event_significance.py) -- a genuine possible hit target
# -- that had zero sign-meaning content before this. daily.py's
# _use_sign_claim falls back here only when no role-specific claim
# resolves, so a natal point can never go completely silent on sign
# meaning when it's genuinely relevant that day.
# Source: Demetra George & Douglas Bloch, Astrology for Yourself
# (1987) -- covers element/modality/rulership as foundational content.
# ------------------------------------------------------------

_SIGN_CORE = {
    "Aries": ("cardinal", "fire", "Mars", "initiative, courage, and new beginnings"),
    "Taurus": ("fixed", "earth", "Venus", "stability, sensuality, and persistence"),
    "Gemini": ("mutable", "air", "Mercury", "curiosity, communication, and adaptability"),
    "Cancer": ("cardinal", "water", "the Moon", "nurturing, emotional depth, and home"),
    "Leo": ("fixed", "fire", "the Sun", "self-expression, warmth, and creative confidence"),
    "Virgo": ("mutable", "earth", "Mercury", "discernment, service, and practical refinement"),
    "Libra": ("cardinal", "air", "Venus", "balance, partnership, and aesthetic harmony"),
    "Scorpio": ("fixed", "water", "Mars (traditionally) and Pluto (in modern astrology)", "intensity, transformation, and depth"),
    "Sagittarius": ("mutable", "fire", "Jupiter", "expansion, exploration, and belief"),
    "Capricorn": ("cardinal", "earth", "Saturn", "discipline, ambition, and long-term structure"),
    "Aquarius": ("fixed", "air", "Saturn (traditionally) and Uranus (in modern astrology)", "originality, independence, and collective ideals"),
    "Pisces": ("mutable", "water", "Jupiter (traditionally) and Neptune (in modern astrology)", "imagination, compassion, and spiritual sensitivity"),
}

for _sign, (_modality, _element, _ruler, _qualities) in _SIGN_CORE.items():
    _add(
        f"sign_core_{_sign.lower()}",
        f"{_sign} is a {_modality} {_element} sign, ruled by {_ruler}, associated with {_qualities}.",
        feature_ids=[f"pure_sign:{_sign}"],
        theme_tags=["sign_core"],
        source_id="george_bloch_astrology_for_yourself_1987",
    )


# ------------------------------------------------------------
# Planet core meanings
# Source: Alan Oken, Alan Oken's Complete Astrology (1980)
# ------------------------------------------------------------

_PLANET_CORE = {
    "sun": (
        "The Sun represents core identity, vitality, and the "
        "conscious sense of self.",
        "identity", ["identity", "vitality"],
    ),
    "moon": (
        "The Moon represents emotional nature, instinctive "
        "reaction, and inner needs.",
        "emotion", ["emotional_depth", "instinct"],
    ),
    "mercury": (
        "Mercury represents communication style, thought process, "
        "and how information is gathered and exchanged.",
        "communication", ["communication", "intellect"],
    ),
    "venus": (
        "Venus represents personal values, attraction, and what is "
        "found pleasurable or beautiful.",
        "values_and_desire", ["relationships", "aesthetics"],
    ),
    "mars": (
        "Mars represents drive, assertion, and how desire is "
        "actively pursued.",
        "drive_and_ambition", ["drive", "assertiveness"],
    ),
    "jupiter": (
        "Jupiter represents expansion, belief, and where growth "
        "and opportunity are sought.",
        "expansion_and_meaning", ["growth", "optimism"],
    ),
    "saturn": (
        "Saturn represents structure, responsibility, and where "
        "discipline and mastery are ultimately earned.",
        "discipline", ["discipline", "resilience"],
    ),
    "uranus": (
        "Uranus represents individuation, sudden change, and "
        "resistance to convention.",
        "transformation", ["independence", "innovation"],
    ),
    "neptune": (
        "Neptune represents imagination, idealism, and the "
        "dissolving of boundaries.",
        "transformation", ["intuition", "spirituality"],
    ),
    "pluto": (
        "Pluto represents deep transformation, power, and what is "
        "hidden until it demands to be faced.",
        "transformation", ["transformation", "intensity"],
    ),
}

for _planet, (_statement, _domain, _themes) in _PLANET_CORE.items():
    _add(
        f"planet_core_{_planet}",
        _statement,
        concept_ids=(
            ["sun"] if _planet == "sun"
            else ["moon"] if _planet == "moon"
            else ["planetary_positions"]
        ),
        feature_ids=[f"sign:{_planet}:{sign}" for sign in ZODIAC_SIGNS],
        theme_tags=_themes,
        life_domain=_domain,
        source_id="oken_complete_astrology_1980",
    )


# ------------------------------------------------------------
# Sun sign
# Source: Linda Goodman, Sun Signs (1968)
# ------------------------------------------------------------

_SUN_SIGNS = {
    "Aries": "initiating, courageous, and direct, with a competitive drive to act first",
    "Taurus": "steady and patient, valuing security, comfort, and sensory experience",
    "Gemini": "curious and communicative, adaptable, with a dual, quick-shifting nature",
    "Cancer": "nurturing and emotionally attuned, protective of home and family",
    "Leo": "warm and expressive, drawn to recognition, generous with affection",
    "Virgo": "analytical and precise, oriented toward service and practical improvement",
    "Libra": "relationship-oriented and diplomatic, seeking balance and fairness",
    "Scorpio": "intense and probing, private, drawn to depth and transformation",
    "Sagittarius": "adventurous and philosophical, freedom-loving, optimistic",
    "Capricorn": "disciplined and ambitious, patient, oriented toward achievement",
    "Aquarius": "independent and unconventional, idea-driven, humanitarian in outlook",
    "Pisces": "imaginative and empathetic, spiritually inclined, emotionally porous",
}

for _sign, _trait in _SUN_SIGNS.items():
    _add(
        f"sun_sign_{_sign.lower()}",
        f"{_article(_sign)} {_sign} Sun tends to be {_trait}.",
        feature_ids=[f"sign:sun:{_sign}"],
        theme_tags=["identity"],
        life_domain="identity",
        source_id="goodman_sun_signs_1968",
    )


# ------------------------------------------------------------
# Moon sign
# Source: Demetra George & Douglas Bloch, Astrology for Yourself (1987)
# ------------------------------------------------------------

_MOON_SIGNS = {
    "Aries": "emotionally direct and quick to react; needs independence, impatient with delay",
    "Taurus": "emotionally steady; needs security and consistency, slow to change",
    "Gemini": "emotionally curious; needs variety and mental stimulation, processes feelings by talking them through",
    "Cancer": "deeply feeling; needs emotional safety and nurturing, with a tidal emotional rhythm",
    "Leo": "emotionally warm; needs appreciation and recognition, dramatic in expression",
    "Virgo": "emotionally reserved; needs order and usefulness, processes feelings through analysis",
    "Libra": "emotionally attuned to others; needs harmony and partnership, dislikes conflict",
    "Scorpio": "emotionally intense and guarded; needs depth and trust before opening up",
    "Sagittarius": "emotionally optimistic; needs freedom and space, restless with routine",
    "Capricorn": "emotionally controlled; needs achievement and structure, reserved about vulnerability",
    "Aquarius": "emotionally detached; needs independence and uniqueness, intellectualizes feelings",
    "Pisces": "emotionally porous and deeply empathetic; needs solitude and creative outlet",
}

for _sign, _trait in _MOON_SIGNS.items():
    _add(
        f"moon_sign_{_sign.lower()}",
        f"{_article(_sign)} {_sign} Moon tends to be {_trait}.",
        feature_ids=[f"sign:moon:{_sign}"],
        theme_tags=["emotional_depth"],
        life_domain="emotion",
        source_id="george_bloch_astrology_for_yourself_1987",
    )


# ------------------------------------------------------------
# Ascendant sign
# Source: Demetra George & Douglas Bloch, Astrology for Yourself (1987)
# ------------------------------------------------------------

_ASCENDANT_SIGNS = {
    "Aries": "assertive, energetic, and direct",
    "Taurus": "calm, grounded, and deliberate",
    "Gemini": "curious, talkative, and quick",
    "Cancer": "warm and protective, reserved with strangers",
    "Leo": "confident, magnetic, and warm",
    "Virgo": "modest, attentive, and precise",
    "Libra": "charming, agreeable, and poised",
    "Scorpio": "intense, private, and magnetic",
    "Sagittarius": "open, enthusiastic, and direct",
    "Capricorn": "composed, serious, and capable",
    "Aquarius": "unique and friendly, but somewhat detached",
    "Pisces": "gentle, dreamy, and adaptable",
}

for _sign, _trait in _ASCENDANT_SIGNS.items():
    _add(
        f"ascendant_sign_{_sign.lower()}",
        f"{_article(_sign)} {_sign} Ascendant tends to come across as {_trait}.",
        concept_ids=["ascendant"],
        feature_ids=[f"ascendant:{_sign}"],
        theme_tags=["persona"],
        life_domain="persona",
        source_id="george_bloch_astrology_for_yourself_1987",
    )


# ------------------------------------------------------------
# MC / IC / Descendant by sign -- previously the only angle with any
# sign-meaning content was the Ascendant. A hit CAN genuinely land on
# natal MC/IC/Descendant (confirmed: the locked eclipse example is a
# direct hit on natal MC), and role_longitudes (natal_targets()) has
# always carried a real sign for all three -- this was missing
# content, not a wiring gap. Tagged sign:{role}:{sign} -- the SAME
# generic pattern _resolve_sign_claim already builds for any
# non-ascendant role, so no code changes were needed to surface these
# once written.
# Source: Demetra George & Douglas Bloch, Astrology for Yourself
# (1987) -- covers all four angles by sign, same book as Ascendant.
# ------------------------------------------------------------

_MC_SIGNS = {
    "Aries": "pursues a public role through initiative and direct action, drawn to pioneering or competitive work",
    "Taurus": "pursues a public role through steady, tangible effort, drawn to work that builds lasting value",
    "Gemini": "pursues a public role through communication and versatility, drawn to work involving ideas or information",
    "Cancer": "pursues a public role through nurturing and care, drawn to work that protects or provides for others",
    "Leo": "pursues a public role through visibility and creative expression, drawn to work that earns recognition",
    "Virgo": "pursues a public role through precision and service, drawn to work that improves or refines systems",
    "Libra": "pursues a public role through diplomacy and partnership, drawn to work involving fairness or aesthetics",
    "Scorpio": "pursues a public role through depth and strategy, drawn to work involving transformation or the hidden",
    "Sagittarius": "pursues a public role through vision and exploration, drawn to work involving teaching or travel",
    "Capricorn": "pursues a public role through discipline and long-term ambition, at home in structures of authority",
    "Aquarius": "pursues a public role through originality and reform, drawn to work serving a collective or cause",
    "Pisces": "pursues a public role through imagination and compassion, drawn to work involving healing or the arts",
}

_IC_SIGNS = {
    "Aries": "builds an emotional foundation through independence, needing a home base that lets action happen freely",
    "Taurus": "builds an emotional foundation through stability, needing a home base that feels physically secure",
    "Gemini": "builds an emotional foundation through variety and conversation, needing a home base that stays mentally alive",
    "Cancer": "builds an emotional foundation through close family bonds, needing a home base that feels nurturing",
    "Leo": "builds an emotional foundation through warmth and pride of place, needing a home base that feels like a stage of its own",
    "Virgo": "builds an emotional foundation through order and routine, needing a home base that runs smoothly",
    "Libra": "builds an emotional foundation through harmony and companionship, needing a home base that feels balanced",
    "Scorpio": "builds an emotional foundation through privacy and trust, needing a home base that feels safe to be unguarded in",
    "Sagittarius": "builds an emotional foundation through freedom and belief, needing a home base that doesn't feel confining",
    "Capricorn": "builds an emotional foundation through responsibility and tradition, needing a home base with clear structure",
    "Aquarius": "builds an emotional foundation through independence and ideals, needing a home base that allows individuality",
    "Pisces": "builds an emotional foundation through feeling and imagination, needing a home base that feels emotionally soft",
}

_DESCENDANT_SIGNS = {
    "Aries": "is drawn to partners who are direct and assertive, and learns partnership through balancing self with other",
    "Taurus": "is drawn to partners who are steady and reliable, valuing loyalty and shared material security",
    "Gemini": "is drawn to partners who are communicative and curious, valuing mental connection and variety",
    "Cancer": "is drawn to partners who are nurturing and protective, valuing emotional closeness and care",
    "Leo": "is drawn to partners who are confident and generous, valuing warmth and mutual admiration",
    "Virgo": "is drawn to partners who are attentive and capable, valuing reliability and practical support",
    "Libra": "is drawn to partners who are diplomatic and fair, valuing harmony and equal give-and-take",
    "Scorpio": "is drawn to partners who are intense and deep, valuing total honesty and emotional depth",
    "Sagittarius": "is drawn to partners who are open and adventurous, valuing freedom and shared belief",
    "Capricorn": "is drawn to partners who are ambitious and dependable, valuing commitment and long-term stability",
    "Aquarius": "is drawn to partners who are independent and original, valuing friendship and shared ideals",
    "Pisces": "is drawn to partners who are compassionate and imaginative, valuing empathy and emotional attunement",
}

_ANGLE_BATCHES = (
    ("mc", _MC_SIGNS, "MC", "drive_and_ambition", ["public_role"]),
    ("ic", _IC_SIGNS, "IC", "foundation_and_security", ["home_and_roots"]),
    ("descendant", _DESCENDANT_SIGNS, "Descendant", "relationships", ["partnership_style"]),
)

for _role, _signs, _label, _domain, _themes in _ANGLE_BATCHES:
    for _sign, _trait in _signs.items():
        _add(
            f"{_role}_sign_{_sign.lower()}",
            f"{_article(_sign)} {_sign} {_label} {_trait}.",
            feature_ids=[f"sign:{_role}:{_sign}"],
            theme_tags=_themes,
            life_domain=_domain,
            source_id="george_bloch_astrology_for_yourself_1987",
        )


# ------------------------------------------------------------
# Mercury / Venus / Mars / Jupiter / Saturn by sign
# Source: Alan Oken, Alan Oken's Complete Astrology (1980)
# ------------------------------------------------------------

_MERCURY_SIGNS = {
    "Aries": "is quick and direct in thought, speaking first and thinking after",
    "Taurus": "is deliberate and practical in thought, slow to change its mind",
    "Gemini": "is versatile and curious, naturally quick with words and ideas",
    "Cancer": "is intuitive and memory-driven, communicating through feeling",
    "Leo": "is confident and dramatic, communicating with warmth and flair",
    "Virgo": "is precise and analytical, naturally skilled at critique and detail",
    "Libra": "is diplomatic, weighing all sides before deciding",
    "Scorpio": "is penetrating and investigative, drawn to what's hidden",
    "Sagittarius": "is broad and philosophical, favoring the big picture over detail",
    "Capricorn": "is methodical and strategic, communicating with authority",
    "Aquarius": "is original and detached, drawn to unconventional ideas",
    "Pisces": "is imaginative and impressionistic, absorbing more than it states",
}

_VENUS_SIGNS = {
    "Aries": "is drawn to excitement and pursuit; values directness in relationships",
    "Taurus": "is drawn to comfort and sensory pleasure; values loyalty and stability",
    "Gemini": "is drawn to wit and variety; values mental connection",
    "Cancer": "is drawn to emotional security; values nurturing and closeness",
    "Leo": "is drawn to admiration and romance; values generosity and being adored",
    "Virgo": "is drawn to helpfulness and refinement; values reliability",
    "Libra": "is drawn to harmony and beauty; values partnership and fairness",
    "Scorpio": "is drawn to intensity; values depth and total honesty",
    "Sagittarius": "is drawn to adventure; values freedom within relationship",
    "Capricorn": "is drawn to commitment and status; values loyalty and long-term investment",
    "Aquarius": "is drawn to uniqueness; values friendship-based connection",
    "Pisces": "is drawn to romance and fantasy; values compassion and unconditional acceptance",
}

_MARS_SIGNS = {
    "Aries": "acts immediately and competitively, direct in pursuit of desire",
    "Taurus": "acts steadily and persistently, slow to anger but hard to stop once moving",
    "Gemini": "acts through words and ideas, with mentally restless energy",
    "Cancer": "acts indirectly and protectively, asserting through emotional means",
    "Leo": "acts boldly and dramatically, driven by pride and recognition",
    "Virgo": "acts through precision and service, energy directed toward improvement",
    "Libra": "acts through negotiation, uncomfortable with direct confrontation",
    "Scorpio": "acts with intensity and control, strategic and slow to reveal its hand",
    "Sagittarius": "acts impulsively toward growth, energy directed at expanding horizons",
    "Capricorn": "acts with discipline and patience, energy directed at long-term goals",
    "Aquarius": "acts unpredictably, energy directed toward causes and principles",
    "Pisces": "acts diffusely, energy easily redirected or dissolved by emotion",
}

_JUPITER_SIGNS = {
    "Aries": "grows through initiative and courage, with optimism fueled by action",
    "Taurus": "grows through building material security, with belief in steady accumulation",
    "Gemini": "grows through learning and communication, finding opportunity in ideas and networks",
    "Cancer": "grows through emotional and familial roots, with belief in nurturing",
    "Leo": "grows through self-expression and creativity, finding opportunity in visibility",
    "Virgo": "grows through refinement and service, with belief in usefulness",
    "Libra": "grows through partnership and fairness, finding opportunity in relationships",
    "Scorpio": "grows through transformation and depth, with belief in facing what's hidden",
    "Sagittarius": "grows through exploration and philosophy, with belief in expanding horizons",
    "Capricorn": "grows through structure and achievement, with belief in earned success",
    "Aquarius": "grows through innovation and community, with belief in collective progress",
    "Pisces": "grows through compassion and imagination, with belief in something beyond the material",
}

_SATURN_SIGNS = {
    "Aries": "learns discipline through patience, tempering impulsiveness",
    "Taurus": "learns discipline through managing material security and self-worth",
    "Gemini": "learns discipline through structured thought and consistent communication",
    "Cancer": "learns discipline through emotional boundaries and family responsibility",
    "Leo": "learns discipline through earning recognition rather than demanding it",
    "Virgo": "learns discipline through accepting imperfection rather than over-correcting it",
    "Libra": "learns discipline through fair, sustained commitment in relationships",
    "Scorpio": "learns discipline through controlled transformation rather than avoidance",
    "Sagittarius": "learns discipline through grounding belief in realistic structure",
    "Capricorn": "is on home territory here — mastery earned through sustained effort",
    "Aquarius": "learns discipline through translating ideals into workable structures",
    "Pisces": "learns discipline through giving compassion form and boundary",
}

_PERSONAL_PLANET_BATCHES = (
    ("mercury", _MERCURY_SIGNS, "Mercury", "communication", ["communication"]),
    ("venus", _VENUS_SIGNS, "Venus", "values_and_desire", ["relationships", "aesthetics"]),
    ("mars", _MARS_SIGNS, "Mars", "drive_and_ambition", ["drive", "assertiveness"]),
    ("jupiter", _JUPITER_SIGNS, "Jupiter", "expansion_and_meaning", ["growth", "optimism"]),
    ("saturn", _SATURN_SIGNS, "Saturn", "discipline", ["discipline", "resilience"]),
)

for _planet, _signs, _label, _domain, _themes in _PERSONAL_PLANET_BATCHES:
    for _sign, _trait in _signs.items():
        _add(
            f"{_planet}_sign_{_sign.lower()}",
            f"{_label} in {_sign} {_trait}.",
            feature_ids=[f"sign:{_planet}:{_sign}"],
            theme_tags=_themes,
            life_domain=_domain,
            source_id="oken_complete_astrology_1980",
        )


# ------------------------------------------------------------
# Uranus / Neptune / Pluto — generational framing
# Source: Alan Oken, Alan Oken's Complete Astrology (1980)
# ------------------------------------------------------------

_OUTER_PLANETS = {
    "uranus": (
        "Uranus moves through one sign for roughly 7 years, so its sign "
        "reflects a generational context rather than individual "
        "character — its house placement and any aspects it makes to "
        "personal planets are what carry individual significance.",
        "transformation",
    ),
    "neptune": (
        "Neptune moves through one sign for roughly 14 years, so its "
        "sign reflects a generational context rather than individual "
        "character — its house placement and any aspects it makes to "
        "personal planets are what carry individual significance.",
        "transformation",
    ),
    "pluto": (
        "Pluto moves through one sign for periods ranging from about "
        "12 to 30 years, so its sign reflects a generational context "
        "rather than individual character — its house placement and "
        "any aspects it makes to personal planets are what carry "
        "individual significance.",
        "transformation",
    ),
}

for _planet, (_statement, _domain) in _OUTER_PLANETS.items():
    _add(
        f"outer_planet_generational_{_planet}",
        _statement,
        feature_ids=[f"sign:{_planet}:{sign}" for sign in ZODIAC_SIGNS],
        theme_tags=["generational_context"],
        life_domain=_domain,
        source_id="oken_complete_astrology_1980",
        notes=(
            "Standard astrological convention distinguishing "
            "generational (outer) from personal planets — not a "
            "cut corner, a documented interpretive distinction."
        ),
    )


# ------------------------------------------------------------
# Uranus by sign — the generational-context claim above is real but
# insufficient alone: when a transit (e.g. a Pluto station) lands
# exactly on natal Uranus, the natal sign IS individually relevant
# that day (it's this person's own placement, not a cohort trait),
# and _resolve_sign_claim had nothing more specific to return.
# _resolve_sign_claim's existing tie-break (fewest feature_ids wins)
# means this single-sign claim naturally outranks the 12-sign
# generational one without any code change.
# Source: Alan Oken, Alan Oken's Complete Astrology (1980)
# ------------------------------------------------------------

_URANUS_SIGNS = {
    "Aries": "breaks new ground through bold, sudden action, rebelling against anything that limits personal freedom",
    "Taurus": "seeks freedom through slow, deliberate upheaval, disrupting security only once the old structure stops serving it",
    "Gemini": "breaks convention through restless curiosity, rebelling against fixed ideas and rigid routine",
    "Cancer": "disrupts inherited emotional patterns, seeking freedom within or from family roles and tradition",
    "Leo": "asserts individuality through bold, unconventional self-expression, rebelling against anonymity",
    "Virgo": "reforms through unconventional method, rebelling against inefficient or outdated systems",
    "Libra": "seeks freedom within partnership, disrupting relationships that become too confining or unequal",
    "Scorpio": "transforms through sudden, radical upheaval, rebelling against control and hidden power structures",
    "Sagittarius": "seeks freedom through belief and exploration, rebelling against dogma and narrow philosophy",
    "Capricorn": "reforms structure and authority from within, rebelling against outdated tradition while building new order",
    "Aquarius": "is on home territory here — individuality and reform expressed with natural fluency",
    "Pisces": "seeks freedom through imagination and dissolution, rebelling against rigid material boundaries",
}

for _sign, _trait in _URANUS_SIGNS.items():
    _add(
        f"uranus_sign_{_sign.lower()}",
        f"Uranus in {_sign} {_trait}.",
        feature_ids=[f"sign:uranus:{_sign}"],
        theme_tags=["individuality", "disruption_and_change"],
        life_domain="transformation",
        source_id="oken_complete_astrology_1980",
    )


# ------------------------------------------------------------
# Houses
# Source: Howard Sasportas, The Twelve Houses (1985)
# ------------------------------------------------------------

_HOUSES = {
    1: ("self, body, and outward approach to life", "identity"),
    2: ("personal resources, money, values, and self-worth", "values_and_desire"),
    3: ("communication, siblings, and everyday learning", "communication"),
    4: ("home, family, roots, and emotional foundation", "foundation_and_security"),
    5: ("creativity, romance, pleasure, and self-expression", "values_and_desire"),
    6: ("work, daily routine, health, and service", "discipline"),
    7: ("partnership, marriage, and open relationships", "relationships"),
    8: ("shared resources, intimacy, and transformation", "transformation"),
    9: ("philosophy, higher learning, travel, and belief", "expansion_and_meaning"),
    10: ("career, public role, and reputation", "drive_and_ambition"),
    11: ("community, friendship, and group belonging", "relationships"),
    12: ("the unconscious, solitude, and spirituality", "transformation"),
}

_PLANETS_FOR_HOUSE_TAGS = (
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
    "uranus", "neptune", "pluto",
)

# NATAL-only roles for the plain house:{role}:{house} tag -- nodes,
# Chiron, Lilith, and the four asteroids are all real direct entries
# in natal_chart["bodies"] with a correctly computed natal house
# already (confirmed by direct query), so a hit touching one of them
# should get its own natal-house citation the same way a classical
# planet does. Deliberately NOT added to _PLANETS_FOR_HOUSE_TAGS
# itself -- that constant also drives transit_house:/
# daily_transit_house: (a TRANSITING body's current house), and none
# of these points ever appear as a transiting body in this pipeline's
# TRANSIT_BODIES, so extending those two families for them would just
# be dead tags no code path can ever produce.
_EXTRA_ROLES_FOR_NATAL_HOUSE_TAG = (
    "chiron", "lilith_mean", "lilith_true",
    "north_node_true", "north_node_mean", "south_node_true", "south_node_mean",
    "ceres", "pallas", "juno", "vesta",
)

for _house, (_meaning, _domain) in _HOUSES.items():
    _add(
        f"house_{_house}",
        f"The {_house}{'st' if _house == 1 else 'nd' if _house == 2 else 'rd' if _house == 3 else 'th'} "
        f"house governs {_meaning}.",
        # feature_ids extended per the Daily-Mode Scope Expansion
        # brief to also match a TRANSITING planet currently placed in
        # this natal house, not just a planet natally placed there --
        # the house's meaning doesn't change based on natal vs.
        # transit, only the framing. Two families: transit_house:
        # (the natal "current transits" --as-of feature, which
        # lenses/features.py already tags but which had zero matching
        # claims until now -- a real pre-existing gap, not new scope)
        # and daily_transit_house: (the daily sweep, new this brief).
        #
        # NOT tagged daily_mode (unlike the original Aug-21 version of
        # this claim): the plain "house:{planet}:{house}" tag fires
        # unconditionally for every natal placement on every run (the
        # full natal chart is always in concepts), so daily_mode here
        # would flood every reading with every natal placement's house
        # every day regardless of relevance -- the exact "unfiltered
        # spray" bug this codebase already fixed once, for houses.
        # daily.py's _resolve_house_claim does the same targeted,
        # non-blanket single-tag lookup used for sign-meaning claims,
        # called once per hit that actually survived resolve->tier.
        feature_ids=(
            [f"house:{planet}:{_house}" for planet in _PLANETS_FOR_HOUSE_TAGS]
            + [f"transit_house:{planet}:{_house}" for planet in _PLANETS_FOR_HOUSE_TAGS]
            + [f"daily_transit_house:{planet}:{_house}" for planet in _PLANETS_FOR_HOUSE_TAGS]
            + [f"house:{role}:{_house}" for role in _EXTRA_ROLES_FOR_NATAL_HOUSE_TAG]
        ),
        theme_tags=["life_area"],
        life_domain=_domain,
        source_id="sasportas_twelve_houses_1985",
    )


# ------------------------------------------------------------
# Planet-in-house (natal only) — Combinatorial-Meaning Expansion,
# Phase 1. Where the generic per-house claim above says "the 10th
# house governs career," these say what THIS planet specifically
# does there (e.g. "Saturn in the 10th house..."). Deliberately
# NATAL-ONLY: tagged house:{planet}:{house} (the natal tag) but NOT
# transit_house:/daily_transit_house: -- a specific "Saturn in your
# 10th house" statement describes a fixed, lifelong trait, and must
# never be silently reused for a TRANSITING body temporarily passing
# through someone's 10th house (a dated, temporary influence) -- the
# exact natal/transit conflation this session's fabrication-guard
# work spent all night closing elsewhere. Transit-through framing
# stays on the existing generic per-house text; a transit-specific
# "planet passing through a house" layer, if ever wanted, would need
# its own separate content and its own framing, not this.
#
# Needs NO changes to daily.py: _resolve_natal_house_claim already
# picks the most specific match (fewest feature_ids), so a single-tag
# claim here automatically outranks the generic 10-tag house claim
# above the moment it exists.
# Source: Howard Sasportas, The Twelve Houses (1985) -- planet-by-
# house synthesis is that book's core subject.
# ------------------------------------------------------------

_PLANET_HOUSE_MEANINGS = {
    "sun": {
        1: "a strong, visible sense of self, with vitality and identity projected directly outward",
        2: "identity bound up with personal resources and self-worth, vitality expressed through building material security",
        3: "identity expressed through communication and everyday learning, vitality flowing through curiosity and exchange",
        4: "identity rooted in home and family, purpose tied to building a secure emotional foundation",
        5: "identity expressed through creativity and self-expression, vitality shining through romance, play, or children",
        6: "identity tied to work and daily routine, purpose found through being useful and keeping order",
        7: "identity strongly shaped through partnership, self-discovery often mirrored through significant relationships",
        8: "identity forged through intensity and transformation, vitality drawn to what is hidden or shared with others",
        9: "identity expressed through belief, philosophy, and expanding horizons, purpose tied to meaning-making",
        10: "identity strongly tied to public role and reputation, vitality directed toward achievement and authority",
        11: "identity expressed through community and group ideals, purpose found through collective belonging",
        12: "a more private, introspective identity, vitality processed inwardly and purpose tied to solitude or quiet service",
    },
    "moon": {
        1: "an emotional nature worn openly, moods visible and instinctive reactions shaping how one comes across",
        2: "emotional security tied to material resources and stable habits, comfort found in what can be held onto",
        3: "emotional life expressed through communication and everyday connection, moods shifting with mental stimulation",
        4: "a deep pull toward home and family, a natural nurturer with a strong need for emotional roots",
        5: "emotional expression through creativity, romance, and play, nurturing others through warmth and generosity",
        6: "emotional wellbeing tied to routine and being useful, sensitive to the daily environment and to health",
        7: "emotional needs met through close partnership, instinctively seeking connection and reflection through others",
        8: "deep emotional intensity, drawn to psychological depth, transformation, and shared intimacy",
        9: "emotional fulfillment through belief and exploration, moods responding to a sense of meaning",
        10: "emotional life intertwined with public role and reputation, nurturing expressed through responsibility",
        11: "emotional needs met through friendship and community, nurturing group ideals and a sense of belonging",
        12: "a private, introspective emotional life, instincts operating quietly and sensitive to unseen influences",
    },
    "mercury": {
        1: "a quick, communicative persona, with thinking style shaping how one is outwardly perceived",
        2: "a mind engaged with practical and material matters, communication focused on values and resources",
        3: "a sharp, curious, natural communicator, very much at home here, engaged with everyday learning and exchange",
        4: "a mind that turns inward toward family and home matters, communication centered on roots and private life",
        5: "a mind engaged creatively, communication flowing through self-expression, play, and romance",
        6: "a detail-oriented, service-minded mind, communication focused on work and routine",
        7: "a mind sharpened through dialogue and partnership, thinking clarified in conversation with others",
        8: "a mind drawn to what's hidden, naturally investigative and probing beneath the surface",
        9: "an expansive, philosophical mind, communication turning toward belief, travel, and big ideas",
        10: "a mind focused on career and public matters, communicating with authority and purpose",
        11: "a mind engaged with groups and ideals, communication flowing through networks and shared causes",
        12: "a more private, intuitive mind, thinking processes often working beneath conscious awareness",
    },
    "venus": {
        1: "personal charm and magnetism defining the outward identity, an easy, likable presence",
        2: "values centered on comfort, beauty, and financial security, love expressed through tangible pleasures",
        3: "relating expressed through conversation, charm carried into everyday exchanges and sociable learning",
        4: "values placed on home and family harmony, seeking beauty and comfort in domestic life",
        5: "a natural love of romance, creativity, and pleasure, drawn to self-expression through art",
        6: "values placed on order and service, pleasure found in helpful routines and refined work",
        7: "relationships central here, a natural, harmony-seeking approach to partnership",
        8: "a nature drawn to intensity in intimacy, valuing deep, transformative bonds over surface connection",
        9: "values placed on philosophy, travel, and expansive experience, love expressed through shared belief",
        10: "values placed on public recognition and reputation, charm put in service of career and status",
        11: "values placed on friendship and community, love expressed through shared ideals",
        12: "love expressed privately or self-sacrificially, values centered on compassion and hidden connection",
    },
    "mars": {
        1: "an assertive, direct, energetic outward identity, quick to act on impulse",
        2: "drive directed toward material security, asserting the self through building resources",
        3: "energy expressed through communication, sometimes quick-tempered or argumentative",
        4: "assertion tied to home and family, sometimes acting protectively or clashing within domestic life",
        5: "energy expressed through creativity, competition, and romance",
        6: "drive channeled into work, service, and discipline, energetic about routine and health",
        7: "assertion playing out through partnership, sometimes as healthy challenge, sometimes as conflict",
        8: "an intense drive toward transformation, power, and shared resources",
        9: "energy directed at expanding horizons, belief, and adventure",
        10: "ambition and drive focused squarely on career and public achievement",
        11: "energy directed toward group goals and collective causes",
        12: "drive turned inward or hidden, energy expressed privately or through subconscious patterns",
    },
    "jupiter": {
        1: "an expansive, optimistic, confident outward identity",
        2: "growth pursued through material resources, a generous relationship with money",
        3: "an expansive mind, love of learning carried into broad-minded, generous communication",
        4: "growth rooted in home and family, an expansive, generous domestic life",
        5: "growth pursued through creativity, romance, and self-expression, luck often found in pleasure and play",
        6: "growth pursued through work and service, an expansive approach to daily routine and health",
        7: "growth pursued through partnership, a generous, expansive approach to relating",
        8: "growth pursued through transformation and shared resources, deep engagement with intensity",
        9: "a philosophical, expansive nature very much at home here, drawn to belief, travel, and higher learning",
        10: "growth pursued through career and public role, expansive ambition and reputation",
        11: "growth pursued through community and group ideals, generous toward shared causes",
        12: "growth pursued through spirituality and solitude, generosity expressed through quiet service",
    },
    "saturn": {
        1: "a serious, reserved outward identity, discipline and responsibility central to the self",
        2: "caution and discipline around resources, security earned through sustained effort",
        3: "a disciplined mind, early learning or communication that may feel restricted but matures with effort",
        4: "structure and responsibility rooted in home and family, often carrying the weight of family duty",
        5: "discipline around creativity and romance, self-expression that matures slowly through sustained effort",
        6: "a strong sense of duty in work and routine, discipline central to daily life",
        7: "structure and responsibility taken seriously in partnership, commitment approached with gravity",
        8: "a disciplined approach to intensity and transformation, mastery earned by facing what is hidden",
        9: "a structured approach to belief and philosophy, wisdom earned through disciplined study",
        10: "career and public role central, very much at home here, disciplined ambition and authority earned over time",
        11: "discipline brought to friendship and community, responsibility taken toward group goals",
        12: "structure and discipline turned inward, mastery earned through solitude or spiritual discipline",
    },
    "uranus": {
        1: "an original, unconventional outward identity, unpredictable and freedom-seeking",
        2: "an unconventional relationship with resources and values, sudden shifts in security",
        3: "a quick, original mind, unconventional in communication and learning style",
        4: "an unconventional home life, often seeking freedom from inherited family patterns",
        5: "original creative expression, an unconventional approach to romance and self-expression",
        6: "an unconventional approach to work and routine, sudden changes in daily life or health",
        7: "unconventional partnerships, needing real freedom within relationship",
        8: "sudden transformation, an unconventional approach to shared resources and intimacy",
        9: "original beliefs, drawn to unconventional philosophy and sudden expansion of horizons",
        10: "an unconventional career path, sudden shifts in public role or reputation",
        11: "an original, freedom-loving approach to community and group ideals, very much at home here",
        12: "unconventional, hidden individuality, sudden insight arising from the unconscious",
    },
    "neptune": {
        1: "a dreamy, impressionable outward identity, idealistic and sometimes elusive",
        2: "an idealistic or unclear relationship with resources and values, drawn to intangible worth",
        3: "an imaginative mind, communication that can be poetic but sometimes vague",
        4: "an idealized or elusive sense of home and family, a deep spiritual connection to roots",
        5: "imaginative, romantic creative expression, an idealized approach to love and play",
        6: "an idealistic approach to service, boundaries between work and compassion often blurred",
        7: "idealized, sometimes elusive partnerships, drawn to spiritual or compassionate connection",
        8: "a deep spiritual engagement with intensity and transformation",
        9: "an expansive spiritual and philosophical imagination, idealistic beliefs",
        10: "an idealistic or elusive public role, a career tied to compassion, art, or spirituality",
        11: "an idealistic approach to community, drawn to humanitarian causes",
        12: "a deeply spiritual and private nature very much at home here, boundaries between self and other tending to dissolve",
    },
    "pluto": {
        1: "an intense, powerful outward identity, a transformative sense of self",
        2: "an intense relationship with resources and values, a drive toward control over security",
        3: "a probing, intense mind, communication that can uncover hidden truths",
        4: "an intense, transformative relationship with home and family, deep-rooted family patterns",
        5: "intense creative or romantic expression, a transformative approach to self-expression",
        6: "intense engagement with work and routine, a transformative approach to health and service",
        7: "intense, transformative partnerships, power dynamics central to relating",
        8: "a deep, transformative engagement with intensity, shared resources, and mortality, very much at home here",
        9: "intense engagement with belief and philosophy, a transformative expansion of worldview",
        10: "an intense drive for power in career and public role, a transformative relationship with authority",
        11: "intense engagement with community, a transformative approach to group ideals",
        12: "a deeply hidden, transformative inner life, power processed privately in the subconscious depths",
    },
}

for _planet, _house_meanings in _PLANET_HOUSE_MEANINGS.items():
    for _house, _trait in _house_meanings.items():
        _ordinal = f"{_house}{'st' if _house == 1 else 'nd' if _house == 2 else 'rd' if _house == 3 else 'th'}"
        _add(
            f"{_planet}_house_{_house}",
            f"{_planet.capitalize()} in the {_ordinal} house tends to give {_trait}.",
            feature_ids=[f"house:{_planet}:{_house}"],
            theme_tags=["planet_in_house"],
            life_domain=_HOUSES[_house][1],
            source_id="sasportas_twelve_houses_1985",
        )


# ------------------------------------------------------------
# Extended-point-in-house (natal only) — Combinatorial-Meaning
# Expansion, Phase 4: the same treatment as Phase 1 above, for the
# points already covered by _EXTRA_ROLES_FOR_NATAL_HOUSE_TAG (nodes,
# Chiron, Lilith, the four asteroids) -- all real PRIMARY_NATAL_ROLES
# members, so all real possible hit targets, that previously only had
# the generic per-house fallback like every other role.
#
# One written text per SYMBOLIC point (8), not per role (11) -- "true"
# vs "mean" node/Lilith is a calculation-method nuance, not a
# difference in interpretive meaning, so the same claim is tagged with
# both role variants where applicable (matching this codebase's own
# established pattern of one claim, many tags -- see the generic house
# claims above). No new code needed, same mechanism as Phase 1: single-
# tag claims automatically outrank the generic house claim.
#
# Sources: Chiron -- Melanie Reinhart, Chiron and the Healing Journey
# (1989). Nodes -- Martin Schulman, Karmic Astrology (1975). Lilith --
# Demetra George, Asteroid Goddesses (1986; also covers Ceres/Pallas/
# Juno/Vesta, the same book already cited for the natal claims'
# tradition elsewhere in this codebase's asteroid content).
# ------------------------------------------------------------

_CHIRON_HOUSE_MEANINGS = {
    1: "a wound tied to identity and self-worth, with healing found through embracing rather than hiding vulnerability",
    2: "a wound tied to resources and self-worth, with healing found through redefining what security actually means",
    3: "a wound tied to communication or early learning, with healing found through finding one's own authentic voice",
    4: "a wound tied to home or family, with healing found through making peace with one's roots",
    5: "a wound tied to creative or romantic self-expression, with healing found through reclaiming joy and play",
    6: "a wound tied to health or daily routine, with healing found through gentler, more sustainable self-care",
    7: "a wound tied to partnership, with healing found through learning to be truly seen by another",
    8: "a wound tied to intimacy or loss, with healing found through facing what was buried",
    9: "a wound tied to belief or meaning, with healing found through rebuilding a personal philosophy",
    10: "a wound tied to public role or authority, with healing found through redefining what success means",
    11: "a wound tied to belonging or friendship, with healing found through finding a genuine community",
    12: "a wound tied to the unseen or unconscious, with healing found through quiet, private integration",
}

_NORTH_NODE_HOUSE_MEANINGS = {
    1: "growth found in developing independence and a stronger sense of self, moving away from over-reliance on others",
    2: "growth found in building genuine self-worth and personal resources, moving away from dependence on others' values",
    3: "growth found in open communication and curiosity, moving away from rigid or isolated certainty",
    4: "growth found in emotional roots and inner security, moving away from an overextended public focus",
    5: "growth found in creative self-expression and joy, moving away from excessive self-sacrifice",
    6: "growth found in daily discipline and practical service, moving away from ungrounded idealism",
    7: "growth found in genuine partnership and compromise, moving away from excessive self-focus",
    8: "growth found in deep intimacy and shared vulnerability, moving away from excessive self-sufficiency",
    9: "growth found in expanding belief and worldview, moving away from over-attachment to small details",
    10: "growth found in public responsibility and achievement, moving away from over-reliance on family or home",
    11: "growth found in community and shared ideals, moving away from an overly personal, romantic focus",
    12: "growth found in surrender and spiritual trust, moving away from rigid control",
}

_SOUTH_NODE_HOUSE_MEANINGS = {
    1: "an innate comfort with independence, prone to over-relying on self-sufficiency at the expense of connection",
    2: "an innate comfort with personal resources, prone to over-relying on material security alone",
    3: "an innate comfort with communication and information, prone to over-relying on facts over deeper meaning",
    4: "an innate comfort with home and family, prone to over-relying on the past for security",
    5: "an innate comfort with self-expression, prone to over-relying on personal drama or romance",
    6: "an innate comfort with routine and service, prone to over-relying on being needed by others",
    7: "an innate comfort with partnership, prone to over-relying on others for identity",
    8: "an innate comfort with self-sufficiency, prone to over-relying on control to feel safe",
    9: "an innate comfort with detail and practicality, prone to over-relying on narrow certainty",
    10: "an innate comfort with home and privacy, prone to over-relying on family rather than public life",
    11: "an innate comfort with romance and personal creativity, prone to over-relying on individual recognition",
    12: "an innate comfort with control and visible achievement, prone to over-relying on external validation",
}

_LILITH_HOUSE_MEANINGS = {
    1: "raw, unfiltered instinct expressed through identity, a rebellious streak against others' expectations of who to be",
    2: "raw, unfiltered instinct around resources and self-worth, resistant to conventional definitions of value",
    3: "raw, unfiltered instinct in communication, drawn to saying what others leave unsaid",
    4: "raw, unfiltered instinct around home and family, resistant to inherited domestic expectations",
    5: "raw, unfiltered instinct in creativity and romance, resistant to conventional expression of desire",
    6: "raw, unfiltered instinct around service and routine, resistant to being controlled by daily obligation",
    7: "raw, unfiltered instinct in partnership, resistant to conventional relationship roles",
    8: "raw, unfiltered instinct around intimacy and power very much at home here, deeply resistant to being controlled",
    9: "raw, unfiltered instinct in belief, resistant to imposed philosophies or dogma",
    10: "raw, unfiltered instinct around public role, resistant to conventional definitions of success",
    11: "raw, unfiltered instinct in community, resistant to group pressure to conform",
    12: "raw, unfiltered instinct in the unconscious, deeply private and easily misunderstood by others",
}

_CERES_HOUSE_MEANINGS = {
    1: "nurturance through direct, active care, showing love by taking charge of others' needs",
    2: "nurturance through providing material security, showing love by building tangible stability for others",
    3: "nurturance through communication and teaching, showing love by sharing knowledge and staying in touch",
    4: "nurturance through home and family very much at home here, showing love by creating a safe, warm household",
    5: "nurturance through creative encouragement, showing love by celebrating others' self-expression",
    6: "nurturance through practical daily care, showing love by attending to others' health and routine",
    7: "nurturance through partnership, showing love by prioritizing another's needs alongside one's own",
    8: "nurturance through deep emotional support, showing love by staying present through hardship",
    9: "nurturance through shared belief or teaching, showing love by encouraging others to grow and explore",
    10: "nurturance through guidance and public responsibility, showing love by mentoring or providing for others' futures",
    11: "nurturance through community care, showing love by supporting friends and shared causes",
    12: "quiet, private nurturance, showing love through selfless, often unseen sacrifice",
}

_PALLAS_HOUSE_MEANINGS = {
    1: "strategic intelligence expressed through personal identity, a natural problem-solver in how one presents to the world",
    2: "strategic intelligence applied to resources, skilled at seeing patterns in what builds real security",
    3: "strategic intelligence expressed through communication very much at home here, a natural gift for pattern recognition in ideas",
    4: "strategic intelligence applied to home and family, skilled at navigating complex family dynamics",
    5: "strategic intelligence applied to creativity, skilled at intentional, well-crafted self-expression",
    6: "strategic intelligence applied to daily work, skilled at designing efficient systems and routines",
    7: "strategic intelligence applied to partnership, skilled at fair, well-reasoned negotiation",
    8: "strategic intelligence applied to shared resources, skilled at navigating complex or hidden dynamics",
    9: "strategic intelligence applied to belief, skilled at building coherent, well-reasoned philosophies",
    10: "strategic intelligence applied to career, skilled at long-term planning and public strategy",
    11: "strategic intelligence applied to community, skilled at organizing groups toward shared goals",
    12: "strategic intelligence applied inwardly, skilled at recognizing unconscious patterns others miss",
}

_JUNO_HOUSE_MEANINGS = {
    1: "a search for a partner who supports and mirrors one's own sense of identity",
    2: "a search for a partner who provides material stability and shares similar values",
    3: "a search for a partner who communicates openly and shares intellectual connection",
    4: "a search for a partner who feels like home, prioritizing emotional security in commitment",
    5: "a search for a partner who brings romance, creativity, and playfulness to the bond",
    6: "a search for a partner who shares practical daily life and mutual reliability",
    7: "equal, committed partnership very much at home here, a central and natural life theme",
    8: "a search for a partner capable of deep intimacy and shared transformation",
    9: "a search for a partner who shares beliefs and a sense of adventure",
    10: "a search for a partner who supports shared ambition and public standing",
    11: "a search for a partner who is also a genuine friend, built on shared ideals",
    12: "a search for a partnership that feels private, spiritual, or even fated",
}

_VESTA_HOUSE_MEANINGS = {
    1: "devotion expressed through personal discipline, focus centered on self-development",
    2: "devotion expressed through building material security, focus centered on sustained, dedicated effort toward resources",
    3: "devotion expressed through communication or learning, focus centered on mastering ideas",
    4: "devotion expressed through home and family, focus centered on maintaining a sacred domestic space",
    5: "devotion expressed through creative work, focus centered on disciplined self-expression",
    6: "devotion expressed through work and service very much at home here, a natural dedication to daily discipline",
    7: "devotion expressed through partnership, focus centered on sustained commitment to another",
    8: "devotion expressed through deep transformation, focus centered on facing what's hidden",
    9: "devotion expressed through belief, focus centered on a dedicated philosophical or spiritual path",
    10: "devotion expressed through career, focus centered on sustained public dedication",
    11: "devotion expressed through community, focus centered on service to shared causes",
    12: "devotion expressed through solitude, focus centered on spiritual or contemplative practice",
}

_EXTENDED_POINT_HOUSE_BATCHES = (
    ("chiron", "Chiron", ("chiron",), _CHIRON_HOUSE_MEANINGS, "reinhart_chiron_healing_journey_1989"),
    ("north_node", "The North Node", ("north_node_true", "north_node_mean"), _NORTH_NODE_HOUSE_MEANINGS, "schulman_karmic_astrology_1975"),
    ("south_node", "The South Node", ("south_node_true", "south_node_mean"), _SOUTH_NODE_HOUSE_MEANINGS, "schulman_karmic_astrology_1975"),
    ("lilith", "Lilith", ("lilith_mean", "lilith_true"), _LILITH_HOUSE_MEANINGS, "demetra_george_asteroid_goddesses_1986"),
    ("ceres", "Ceres", ("ceres",), _CERES_HOUSE_MEANINGS, "demetra_george_asteroid_goddesses_1986"),
    ("pallas", "Pallas", ("pallas",), _PALLAS_HOUSE_MEANINGS, "demetra_george_asteroid_goddesses_1986"),
    ("juno", "Juno", ("juno",), _JUNO_HOUSE_MEANINGS, "demetra_george_asteroid_goddesses_1986"),
    ("vesta", "Vesta", ("vesta",), _VESTA_HOUSE_MEANINGS, "demetra_george_asteroid_goddesses_1986"),
)

for _claim_key, _label, _roles, _house_meanings, _source in _EXTENDED_POINT_HOUSE_BATCHES:
    for _house, _trait in _house_meanings.items():
        _ordinal = f"{_house}{'st' if _house == 1 else 'nd' if _house == 2 else 'rd' if _house == 3 else 'th'}"
        _add(
            f"{_claim_key}_house_{_house}",
            f"{_label} in the {_ordinal} house tends to give {_trait}.",
            feature_ids=[f"house:{_role}:{_house}" for _role in _roles],
            theme_tags=["planet_in_house"],
            life_domain=_HOUSES[_house][1],
            source_id=_source,
        )


# ------------------------------------------------------------
# Juno core signification (placement-independent) -- Celeste — Two
# Deliverables, One Pass, 2026-09-02, Deliverable 2. Real gap found
# during a content-narrowness audit: Juno's existing 24 sign/house
# claims all cluster around one theme (what kind of partner is
# sought), because that's genuinely the only angle the sign/house
# combinatorial structure captures -- it says nothing about what Juno
# signifies independent of placement. Checked the cited source
# directly (demetra_george_asteroid_goddesses_1986, already cited for
# two existing Juno claims) via a legitimate secondary description of
# the book's actual content before writing anything: it explicitly
# covers (1) Juno's association with steadfast, cyclical commitment --
# "steadfast loyalty to relationship-for-the-sake-of-relationship,"
# with the myth's own separation-and-return pattern read as the
# archetype of recommitment rather than a single vow; (2) Juno as "a
# union of intimate equals... the perfect balancing of... energies,"
# i.e. a power-balance/equality signification distinct from any single
# sign or house; (3) a documented "special sensitivity to the double
# standard, and by extension, to the underdog in relationships where
# there is a power imbalance" -- the real basis for Juno's association
# with betrayal-sensitivity, not just a modern gloss. All three are
# genuinely in the source, not paraphrased from the non-cited general
# gloss that prompted this check.
#
# A 4th claim added on a same-session follow-up check, prompted by a
# non-cited website's sharper "insecurity-driven need to be first,
# trickery when threatened" framing for Juno in Aries specifically
# (also not citable as-is). That exact framing did NOT turn up in any
# authored source checked -- only on other astrology websites, same
# uncitable category, not added. But the check surfaced real,
# independently-confirmed material on a DIFFERENT, genuine facet: dark/
# shadow Juno's own capacity for jealousy, possessiveness, and rivalry
# toward a perceived threat -- "infidelity and the anger it inspires,
# jealousy and possessiveness and sexual rivalry all are potentials of
# dark Juno," with the same distortion elsewhere described as turning
# feminine bonding "into jealousy, competitiveness, and suspicion."
# Distinct from the betrayal_sensitivity claim above (sensitivity to a
# PARTNER'S unfairness) -- this is Juno's own shadow-side reactivity, a
# real, separately-sourced facet, not a duplicate.
#
# These are placement-independent, so they don't fit the sign/house
# combinatorial pattern above -- feature-tagged separately
# (juno_signification:*) and resolved by daily.py's own
# _resolve_juno_signification_claims, called once per Juno hit
# alongside (not instead of) the existing sign/house lookups.
# ------------------------------------------------------------

_add(
    "juno_core_commitment",
    (
        "Juno signifies a capacity for steadfast, renewed commitment -- "
        "returning to and recommitting to a relationship again and "
        "again, not a single vow made once and left unexamined."
    ),
    feature_ids=["juno_signification:commitment"],
    theme_tags=["commitment", "partnership"],
    life_domain="relationships",
    source_id="demetra_george_asteroid_goddesses_1986",
)

_add(
    "juno_core_equality",
    (
        "Juno signifies a union of equals -- power, voice, and give-"
        "and-take staying genuinely balanced between both partners, "
        "rather than settling toward one side."
    ),
    feature_ids=["juno_signification:equality"],
    theme_tags=["equality", "partnership"],
    life_domain="relationships",
    source_id="demetra_george_asteroid_goddesses_1986",
)

_add(
    "juno_core_betrayal_sensitivity",
    (
        "Juno carries a heightened sensitivity to double standards and "
        "unfairness in a relationship, especially where one partner "
        "holds more power than the other."
    ),
    feature_ids=["juno_signification:betrayal_sensitivity"],
    theme_tags=["fairness", "partnership"],
    life_domain="relationships",
    source_id="demetra_george_asteroid_goddesses_1986",
)

_add(
    "juno_core_rivalry",
    (
        "Juno's shadow side can surface as jealousy, possessiveness, "
        "or rivalry toward a perceived threat to the relationship, "
        "especially when the partnership's equality or security feels "
        "at risk."
    ),
    feature_ids=["juno_signification:rivalry"],
    theme_tags=["jealousy", "partnership"],
    life_domain="relationships",
    source_id="demetra_george_asteroid_goddesses_1986",
)


# ------------------------------------------------------------
# Sign-on-house-cusp (natal only) — Combinatorial-Meaning Expansion,
# Phase 2. What sign colors a given house's affairs in THIS chart --
# a distinct fact from "which planet occupies the house" (Phase 1
# above): a house can have real, personalized sign-cusp content even
# with no planet in it at all.
#
# Deliberately covers only houses 2, 3, 5, 6, 8, 9, 11, 12 -- houses
# 1, 4, 7, 10 are angular, and in this engine's house systems
# (confirmed by direct query: cusp longitudes match exactly) their
# cusps ARE the Ascendant/IC/Descendant/MC. That content already
# exists (the Ascendant/MC/IC/Descendant-by-sign families above), so
# authoring it again here would be duplicate content for the same
# underlying chart fact, not new scope.
#
# Source: Howard Sasportas, The Twelve Houses (1985).
# ------------------------------------------------------------

_SIGN_IN_HOUSE_MEANINGS = {
    2: {
        "Aries": "an assertive, impulsive pursuit of resources, quick to earn but just as quick to spend",
        "Taurus": "a natural, patient accumulation of resources, very much at home here, valuing steady security and tangible possessions",
        "Gemini": "resourcefulness through variety -- multiple income streams, communication-based earning, and a changeable relationship with money",
        "Cancer": "security tied to emotional safety, resources protected carefully, often saved for family",
        "Leo": "generosity with resources, a love of spending on quality and status, self-worth tied to how resources are displayed",
        "Virgo": "meticulous, practical management of resources, careful budgeting and real attention to value for money",
        "Libra": "resources gained through partnership or aesthetic pursuits, a value placed on balance and fairness in finances",
        "Scorpio": "an intense, private relationship with resources, drawn to shared or inherited wealth and a deep need for financial control",
        "Sagittarius": "an expansive, sometimes reckless relationship with money, resources gained through travel, teaching, or risk-taking",
        "Capricorn": "a disciplined, long-term approach to building resources, self-worth tied to security earned through effort",
        "Aquarius": "an unconventional relationship with money, resources gained through group ventures or original ideas",
        "Pisces": "an idealistic, sometimes imprecise relationship with resources, prone to financial sacrifice for others and intuitive about value",
    },
    3: {
        "Aries": "a quick, direct communication style, learning best through action and immediate experience",
        "Taurus": "a deliberate, practical communication style, learning at a steady pace and retaining what's useful",
        "Gemini": "natural curiosity and quick wit, very much at home here, a versatile communicator and learner",
        "Cancer": "communication colored by emotional sensitivity, learning best in a nurturing, familiar environment",
        "Leo": "an expressive, dramatic communication style, often taking a leading role among siblings or peers",
        "Virgo": "a precise, analytical communication style, learning through careful study and attention to detail",
        "Libra": "a diplomatic communication style, learning well through dialogue and weighing different perspectives",
        "Scorpio": "a probing, intense communication style, drawn to uncovering what's hidden in everyday exchanges",
        "Sagittarius": "a broad, enthusiastic communication style, learning best through big-picture thinking rather than rote detail",
        "Capricorn": "a serious, disciplined communication style, taking early learning and daily exchange seriously",
        "Aquarius": "an original, unconventional communication style, drawn to unusual ideas and independent learning",
        "Pisces": "an imaginative, impressionistic communication style, learning intuitively and sensitive to unspoken meaning",
    },
    5: {
        "Aries": "bold, spontaneous creative expression, pursuing romance and pleasure with enthusiasm and directness",
        "Taurus": "sensual, steady creative expression, enjoying romance and pleasure through the physical senses",
        "Gemini": "playful, versatile creative expression, drawn to flirtation and mentally stimulating romance",
        "Cancer": "emotionally nurturing creative expression, romance colored by tenderness and a need for security",
        "Leo": "dramatic, generous creative expression, very much at home here, thriving on romance, play, and being admired",
        "Virgo": "careful, refined creative expression, approaching romance and pleasure with modesty and discernment",
        "Libra": "graceful, harmony-seeking creative expression, romance colored by partnership and aesthetic appreciation",
        "Scorpio": "intense, transformative creative expression, romance approached with passion and emotional depth",
        "Sagittarius": "expansive, adventurous creative expression, romance pursued with enthusiasm and a need for freedom",
        "Capricorn": "disciplined, ambitious creative expression, romance approached seriously and with long-term intent",
        "Aquarius": "original, unconventional creative expression, romance colored by friendship and independence",
        "Pisces": "dreamy, imaginative creative expression, romance approached idealistically and with deep empathy",
    },
    6: {
        "Aries": "an energetic, fast-paced approach to work, prone to impatience with routine but effective under pressure",
        "Taurus": "a steady, reliable approach to work, valuing a consistent, comfortable daily routine",
        "Gemini": "a varied, mentally engaged approach to work, thriving on variety in daily tasks and communication-based service",
        "Cancer": "a nurturing approach to work, service often expressed through care for others, sensitive to the work environment",
        "Leo": "a proud, engaged approach to work, wanting recognition for effort and bringing warmth to service",
        "Virgo": "meticulous, dedicated work habits, very much at home here, a natural gift for refining systems and daily discipline",
        "Libra": "a cooperative approach to work, valuing harmony and fairness in the workplace, service through diplomacy",
        "Scorpio": "an intense, thorough approach to work, drawn to uncovering problems and solving them at the root",
        "Sagittarius": "an enthusiastic, big-picture approach to work, chafing against overly repetitive routine",
        "Capricorn": "a disciplined, responsible approach to work, taking duty and daily structure seriously",
        "Aquarius": "an original, independent approach to work, drawn to unconventional methods or humanitarian service",
        "Pisces": "a compassionate, sometimes disorganized approach to work, service expressed through empathy and self-sacrifice",
    },
    8: {
        "Aries": "an assertive approach to intimacy and shared resources, direct about desires and drawn to intensity",
        "Taurus": "a need for security and stability in shared resources and intimacy, slow to trust but deeply loyal once bonded",
        "Gemini": "a curious, communicative approach to intimacy, sometimes intellectualizing deep emotional or financial matters",
        "Cancer": "a deeply protective, cautious approach to intimacy, shared resources tied to emotional trust",
        "Leo": "intimacy approached with warmth and drama, wanting generosity and loyalty in shared resources",
        "Virgo": "a careful, discerning approach to intimacy and shared resources, attentive to the practical details of partnership",
        "Libra": "a search for balance and fairness in shared resources, intimacy approached through partnership and harmony",
        "Scorpio": "profound, transformative engagement with intimacy, very much at home here, a natural depth in facing what is hidden",
        "Sagittarius": "a philosophical, expansive approach to intimacy, seeking meaning and freedom within deep bonds",
        "Capricorn": "a disciplined, cautious approach to shared resources, intimacy built slowly through earned trust",
        "Aquarius": "an unconventional approach to intimacy, valuing independence even within deep bonds",
        "Pisces": "a deeply empathetic, sometimes boundary-less approach to intimacy, drawn to the spiritual dimensions of merging",
    },
    9: {
        "Aries": "an assertive pursuit of belief and philosophy, drawn to pioneering ideas and adventurous travel",
        "Taurus": "a steady, practical approach to belief, valuing philosophies that offer tangible, lasting truth",
        "Gemini": "a curious, wide-ranging approach to belief, enjoying many philosophies and varied styles of travel",
        "Cancer": "belief tied to emotional and familial roots, philosophy approached through personal, nurturing meaning",
        "Leo": "a confident, expressive approach to belief, drawn to philosophies that celebrate personal significance",
        "Virgo": "an analytical, discerning approach to belief, valuing philosophies that are practical and well-reasoned",
        "Libra": "a search for balance and fairness in belief systems, philosophy approached through dialogue and partnership",
        "Scorpio": "an intense, probing approach to belief, drawn to philosophies that explore what's hidden or taboo",
        "Sagittarius": "expansive, enthusiastic belief, very much at home here, a natural love of travel and higher learning",
        "Capricorn": "a disciplined, structured approach to belief, valuing philosophies with proven, traditional authority",
        "Aquarius": "an original, progressive approach to belief, drawn to unconventional or humanitarian philosophies",
        "Pisces": "an intuitive, spiritual approach to belief, philosophy approached through faith and compassion",
    },
    11: {
        "Aries": "a pioneering role in groups, drawn to friendships that involve action and shared challenges",
        "Taurus": "steady, loyal friendships, community engagement centered on shared practical goals",
        "Gemini": "a wide social network, friendships built through communication and shared ideas",
        "Cancer": "a nurturing role in groups, friendships that feel like family, protective of community",
        "Leo": "a warm, generous role in groups, often a leading or celebrated position among friends",
        "Virgo": "a helpful, practical role in groups, friendships built through mutual usefulness and reliability",
        "Libra": "a harmonizing role in groups, a value placed on fairness and balance within friendships and community",
        "Scorpio": "intense, selective friendships, community engagement approached with depth and loyalty",
        "Sagittarius": "an expansive social network, friendships built through shared beliefs or a love of adventure",
        "Capricorn": "a responsible, goal-oriented role in groups, friendships built through shared ambition",
        "Aquarius": "a natural sense of belonging in groups, very much at home here, friendships built around shared ideals and causes",
        "Pisces": "a compassionate, idealistic role in groups, friendships that offer emotional or spiritual connection",
    },
    12: {
        "Aries": "unconscious drives toward action and assertion, solitude used to recharge before re-engaging",
        "Taurus": "an unconscious need for security, solitude found through quiet, sensory comfort",
        "Gemini": "unconscious mental restlessness, solitude processed through inner dialogue or private writing",
        "Cancer": "an unconscious tie to deep emotional memory, solitude used for emotional healing and retreat",
        "Leo": "an unconscious need for validation, solitude used to reconnect with inner creative confidence",
        "Virgo": "unconscious perfectionism, solitude used for quiet refinement and self-improvement",
        "Libra": "an unconscious longing for connection, solitude used to restore inner balance",
        "Scorpio": "an unconscious pull toward what's hidden or taboo, solitude used for deep psychological processing",
        "Sagittarius": "an unconscious yearning for meaning, solitude used for philosophical reflection",
        "Capricorn": "an unconscious sense of duty or old burdens, solitude used to quietly regroup before responsibility resumes",
        "Aquarius": "unconscious individuality, solitude used to process ideals apart from group expectation",
        "Pisces": "a natural attunement to the unconscious and spiritual, very much at home here, solitude a genuine source of renewal",
    },
}

for _house, _sign_meanings in _SIGN_IN_HOUSE_MEANINGS.items():
    _ordinal = f"{_house}{'st' if _house == 1 else 'nd' if _house == 2 else 'rd' if _house == 3 else 'th'}"
    for _sign, _trait in _sign_meanings.items():
        _add(
            f"sign_{_sign.lower()}_house_{_house}",
            f"{_sign} on the {_ordinal} house cusp brings {_trait}.",
            feature_ids=[f"house_cusp_sign:{_house}:{_sign}"],
            theme_tags=["sign_in_house"],
            life_domain=_HOUSES[_house][1],
            source_id="sasportas_twelve_houses_1985",
        )


# ------------------------------------------------------------
# Aspect types (generic — combinable with whichever two placements
# are actually in aspect via the synthesis pass, not one claim per
# planet pair)
# Source: William Lilly, Christian Astrology (1647)
# ------------------------------------------------------------

_ASPECTS = {
    "conjunction": "unifies the two placements involved into a single, undivided expression",
    "sextile": "lets the two placements involved cooperate with relative ease",
    "square": "pulls the two placements involved in different directions, producing tension that calls for conscious effort to resolve",
    "trine": "lets the two placements involved flow together smoothly and supportively",
    "opposition": "polarizes the two placements involved, requiring conscious balancing between them",
    "quincunx": "puts the two placements involved in an awkward relationship requiring ongoing adjustment",
}

for _aspect, _meaning in _ASPECTS.items():
    _add(
        f"aspect_{_aspect}",
        f"{_article(_aspect)} {_aspect} {_meaning}.",
        # Matches this aspect wherever it's found: natal-to-natal
        # (aspect:), a current transit to the natal chart
        # (transit_aspect:), or a secondary-progressed placement to
        # the natal chart (progression_aspect:) — the meaning of a
        # square or trine doesn't change with which two moments the
        # two ends belong to.
        feature_ids=[
            f"aspect:{_aspect}",
            f"transit_aspect:{_aspect}",
            f"progression_aspect:{_aspect}",
        ],
        # No "daily_mode" theme_tag: resolved for daily mode via
        # daily.py's _resolve_aspect_claim() targeted lookup (paired
        # per hit, not a once-per-day disconnected fact), NOT the
        # blanket sweep. "Pair meaning to every hit" fix -- these
        # claims briefly carried daily_mode (Daily-Mode Scope
        # Expansion brief) so the blanket sweep's generic fallback
        # could reach them at all, but that sweep only ever cited the
        # aspect type once per day, never tied to the specific hit
        # that earned it; leaving daily_mode here now would double-
        # cite the same claim via both mechanisms.
        theme_tags=["relationship_between_placements"],
        source_id="lilly_christian_astrology_1647",
    )


# ------------------------------------------------------------
# Eclipse type meaning
# Source: standard modern eclipse-astrology convention (solar =
# external/identity-facing new beginning, lunar = internal/emotional
# culmination or release -- the base solar/lunar distinction; total/
# partial/annular/penumbral distinguish how COMPLETE that beginning or
# culmination is, per Swiss Ephemeris's own classify_eclipse_type()
# categories), cross-referenced across multiple sources during
# curation, not recalled from training alone -- same sourcing
# discipline as the minor-aspect content above.
#
# Real content gap this closes: a full audit ("Pair meaning to every
# hit" brief) found NO eclipse-type content existed anywhere in this
# knowledge base -- every eclipse hit fell through to a bare computed
# fact with no interpretive meaning at all, unlike aspect-type hits
# (which had real content, just disconnected -- a different, already-
# fixed bug). Resolved via daily.py's _resolve_eclipse_type_claim()
# targeted lookup, tagged eclipse_type:{kind}_{type} -- no daily_mode
# theme_tag, matching the targeted-lookup-not-blanket-sweep pattern
# every other fact type in this file now uses.
# ------------------------------------------------------------

_ECLIPSE_TYPES = {
    "solar_partial": (
        "a partial solar eclipse marks a new beginning that only partially clears "
        "view -- something starts, but not everything about it is visible yet"
    ),
    "solar_annular": (
        "an annular solar eclipse marks a new beginning held in tension between "
        "control and surrender -- the old situation isn't fully eclipsed, so the "
        "new one can't fully take over either"
    ),
    "solar_total": (
        "a total solar eclipse marks the most complete kind of new beginning this "
        "cycle offers -- the old situation is fully obscured, clearing the way for "
        "something genuinely new"
    ),
    "solar_hybrid": (
        "a hybrid solar eclipse (shifting between annular and total along its "
        "path) marks a new beginning whose character isn't settled yet -- what "
        "starts now may keep changing shape before it's fully underway"
    ),
    "lunar_penumbral": (
        "a penumbral lunar eclipse marks a subtle, easy-to-miss emotional "
        "undercurrent -- something is shifting internally, but faintly enough "
        "that it may not register as a turning point until later"
    ),
    "lunar_partial": (
        "a partial lunar eclipse marks an emotional culmination that's only "
        "partly complete -- something comes to a head, but not everything about "
        "it resolves at once"
    ),
    "lunar_total": (
        "a total lunar eclipse marks the most complete kind of emotional "
        "culmination or release this cycle offers -- whatever's been building "
        "comes fully into view, ready to be let go of or fully felt"
    ),
}

for _eclipse_key, _eclipse_meaning in _ECLIPSE_TYPES.items():
    _add(
        f"eclipse_type_{_eclipse_key}",
        f"{_eclipse_meaning.capitalize()}.",
        feature_ids=[f"eclipse_type:{_eclipse_key}"],
        theme_tags=["turning_point"],
        source_id="eclipse_astrology_modern_convention",
    )


# ------------------------------------------------------------
# Elemental balance
# Source: Claudius Ptolemy, Tetrabiblos (c. 150 CE)
# ------------------------------------------------------------

_ELEMENTS = {
    "fire": "an energetic, spirited, and action-oriented temperament",
    "earth": "a practical, grounded, and stability-seeking temperament",
    "air": "an intellectual, communicative, and idea-oriented temperament",
    "water": "an emotional, intuitive, and sensitivity-oriented temperament",
}

for _element, _meaning in _ELEMENTS.items():
    _add(
        f"element_{_element}_dominant",
        f"{_article(_element)} {_element}-dominant chart tends toward {_meaning}.",
        concept_ids=["elemental_balance"],
        feature_ids=[f"element_dominant:{_element}"],
        theme_tags=["temperament"],
        source_id="ptolemy_tetrabiblos_c150",
    )


# ------------------------------------------------------------
# Retrograde
# Source: William Lilly, Christian Astrology (1647)
# ------------------------------------------------------------

_add(
    "retrograde_general",
    "A retrograde planet's energy is turned inward, reworked, and "
    "expressed less directly than when the same planet moves direct.",
    feature_ids=[f"retrograde:{p}" for p in _PLANETS_FOR_HOUSE_TAGS],
    theme_tags=["introspection"],
    source_id="lilly_christian_astrology_1647",
)

_add(
    "retrograde_mercury",
    "Mercury retrograde is traditionally treated as a period where "
    "communication, technology, and decisions are more prone to "
    "misunderstanding or delay — commonly read as a time to review "
    "rather than launch.",
    feature_ids=["retrograde:mercury"],
    theme_tags=["introspection", "communication"],
    life_domain="communication",
    source_id="lilly_christian_astrology_1647",
    notes=(
        "The specific 'review, don't launch' framing is a widely "
        "repeated modern popular convention built on the traditional "
        "retrograde principle documented in Lilly, not a direct "
        "17th-century citation."
    ),
)


# ------------------------------------------------------------
# Fixed stars — scoped to traditionally well-documented stars only.
# Most of the 735-star catalog has no real astrological tradition
# behind it; claiming meaning for those would be fabrication.
# Source: Vivian Robson, Fixed Stars and Constellations in Astrology
# (1923)
# ------------------------------------------------------------

_STAR_CONJUNCTION_BODIES = _PLANETS_FOR_HOUSE_TAGS + (
    "lilith_mean", "lilith_true", "chiron", "ceres", "pallas", "juno",
    "vesta", "north_node_true", "north_node_mean", "south_node_true",
    "south_node_mean",
)

_FIXED_STARS = {
    "Aldebaran": (
        "one of the four Persian Royal Stars ('Watcher of the "
        "East'), traditionally associated with honor and integrity, "
        "with a traditional warning against misusing power once gained"
    ),
    "Regulus": (
        "one of the four Persian Royal Stars ('Watcher of the "
        "North'), traditionally associated with ambition and "
        "leadership, with a traditional warning against downfall if "
        "honor is abused"
    ),
    "Antares": (
        "one of the four Persian Royal Stars ('Watcher of the "
        "West'), traditionally associated with intensity and "
        "courage carrying a self-destructive edge"
    ),
    "Fomalhaut": (
        "one of the four Persian Royal Stars ('Watcher of the "
        "South'), traditionally associated with idealism and "
        "mysticism, and with fame that can fade"
    ),
    "Spica": (
        "traditionally considered one of the most fortunate fixed "
        "stars, associated with talent, success, and protection"
    ),
    "Algol": (
        "traditionally considered the most ill-omened fixed star, "
        "associated with intensity, loss of control, or violent "
        "passions"
    ),
    "Sirius": (
        "traditionally associated with honor, ambition, and renown"
    ),
    "Vega": (
        "traditionally associated with idealism and artistic or "
        "musical talent"
    ),
    "Arcturus": (
        "traditionally associated with pathfinding and prosperity "
        "gained through pioneering new ways"
    ),
    "Rigel": (
        "traditionally associated with technical skill, ingenuity, "
        "and public success"
    ),
    "Betelgeuse": (
        "traditionally associated with honor and riches gained "
        "through unexpected fortune"
    ),
    "Capella": (
        "traditionally associated with curiosity, learning, and "
        "love of exploration"
    ),
    "Polaris": (
        "traditionally associated with sickness, trouble, and "
        "affliction, but also with spiritual orientation and a fixed "
        "sense of direction"
    ),
    "Alcyone": (
        "the traditional representative of the Pleiades cluster, "
        "associated with prominence and intensity, alongside a "
        "traditional caution about the eyes"
    ),
    "Castor": (
        "traditionally associated with mental brilliance and sharp "
        "wit, alongside a traditional caution about sudden prominence "
        "followed by reversal"
    ),
    "Pollux": (
        "traditionally associated with physical courage and "
        "competitive strength, alongside a traditional caution about "
        "excess or self-destructive intensity"
    ),
    "Procyon": (
        "traditionally associated with a swift rise to activity and "
        "prominence, alongside a traditional caution against haste"
    ),
    "Denebola": (
        "traditionally associated with standing apart from "
        "convention — a nonconformist relationship to the mainstream"
    ),
    "Altair": (
        "traditionally associated with boldness, ambition, and "
        "sudden but changeable fortune"
    ),
    "Deneb": (
        "traditionally associated with intelligence, originality, "
        "and creative or literary talent"
    ),
    # Phase F2 expansion (27 more stars, verified via search against
    # Robson and cross-referenced modern compilations during
    # curation) — bringing the curated catalog to 47 traditionally
    # documented stars, short of the 50+ aspiration stated for this
    # phase but each entry genuinely sourced rather than padded to
    # hit a round number.
    "Bellatrix": (
        "of the nature of Mars and Mercury, traditionally associated "
        "with civil or military honor, renown, and wealth, alongside "
        "a traditional warning of sudden dishonor"
    ),
    "Alphecca": (
        "traditionally associated with honor, dignity, and artistic "
        "or occult ability"
    ),
    "Menkar": (
        "traditionally associated with turbulence and insight — the "
        "capacity to understand collective needs, which can also "
        "bring disturbance and isolation if not well handled"
    ),
    "Markab": (
        "of the nature of Mars and Mercury, traditionally associated "
        "with honor, riches, and fortune, alongside a traditional "
        "warning of injury or danger from fire or blows"
    ),
    "Scheat": (
        "of the nature of Mars and Mercury, traditionally a "
        "challenging star that can nonetheless bring 'great mastery' "
        "when its difficulties are consciously worked with"
    ),
    "Algenib": (
        "of the nature of Mars and Mercury, traditionally associated "
        "with a penetrating mind, strong will, and determination"
    ),
    "Alpheratz": (
        "of the nature of Jupiter and Venus, traditionally one of "
        "the more fortunate fixed stars, associated with a contented, "
        "honorable, and philosophical disposition"
    ),
    "Alnilam": (
        "one of the three stars of Orion's Belt, traditionally "
        "associated with public honor and the capacity for great "
        "achievement when well aspected"
    ),
    "Alnitak": (
        "one of the three stars of Orion's Belt, of the nature of "
        "the Moon and Jupiter, traditionally associated with "
        "notoriety, good fortune, and lasting happiness"
    ),
    "Mintaka": (
        "one of the three stars of Orion's Belt, sharing with "
        "Alnilam and Alnitak a traditional association with "
        "strength, organizing ability, and a sharp mind"
    ),
    "Saiph": (
        "part of the Orion constellation's traditional significance "
        "for strength, industry, and a sharp, well-organized mind"
    ),
    "Zuben Elgenubi": (
        "traditionally associated with social reform and tireless "
        "work on behalf of groups or associations, favoring careers "
        "in politics or community affairs"
    ),
    "Zuben Eschamali": (
        "traditionally associated with social reform pursued for "
        "personal gain — working on behalf of groups specifically "
        "where it brings power, influence, or financial benefit"
    ),
    "Unukalhai": (
        "traditionally associated with early success followed by "
        "reversal, and a warning around accidents and difficulties "
        "in love"
    ),
    "Toliman": (
        "traditionally associated with occult and philosophical "
        "learning, self-analysis, and honors, alongside a tendency "
        "toward stubbornness"
    ),
    "Sabik": (
        "traditionally associated with a capacity to overcome "
        "difficulty and danger through one's own resourcefulness, "
        "though sometimes at some moral cost"
    ),
    "Sadalsuud": (
        "traditionally considered one of the most fortunate fixed "
        "stars, associated with great fortune, astrology, the "
        "occult, and visionary or psychic ability"
    ),
    "Sadalmelek": (
        "traditionally associated with a fortunate mind, honors, and "
        "success in astrology, occult study, and government"
    ),
    "Deneb Algedi": (
        "traditionally associated with wise leadership and finding "
        "purpose through sorrow — glory and fame if difficulty is "
        "navigated well, with a warning about betrayal"
    ),
    "Zosma": (
        "traditionally associated with a period of hard work and "
        "toil, sometimes through being victimized or pressured, or "
        "through working directly with people in difficult "
        "circumstances"
    ),
    "Alnair": (
        "traditionally associated with good fortune, generosity, and "
        "a strong sense of honor"
    ),
    "Rigil Kentaurus": (
        "of the nature of Venus and Jupiter, traditionally a "
        "beneficial star associated with benevolence, friendship, "
        "refinement, and an honorable position"
    ),
    "Acrux": (
        "the head of the Southern Cross, traditionally associated "
        "with religious devotion, ceremony, justice, and an interest "
        "in mystery and the occult"
    ),
    "Alkaid": (
        "traditionally associated with creativity, high preferment "
        "in business or government, a fondness for power, and "
        "victory over rivals"
    ),
    "Alderamin": (
        "traditionally associated with gentle authority and "
        "strength — the capacity to make reasoned decisions without "
        "resorting to force"
    ),
    "Rasalgethi": (
        "traditionally associated with a need for order and balance, "
        "a deep love of nature, and — when well aspected — high "
        "public preferment, courage, and fame"
    ),
    "Rasalhague": (
        "traditionally associated with facility for working with "
        "symbols and systems, from science and engineering to "
        "astrology and psychoanalysis, with a Saturnine character "
        "and some Neptunian sensitivity"
    ),
}

for _star, _meaning in _FIXED_STARS.items():
    _add(
        f"fixed_star_{_star.lower().replace(' ', '_')}",
        f"{_star} is {_meaning}.",
        concept_ids=["fixed_star_conjunctions"],
        feature_ids=[
            f"star_conjunction:{planet}:{_star.lower().replace(' ', '_')}"
            for planet in _STAR_CONJUNCTION_BODIES
        ],
        theme_tags=["fixed_star"],
        source_id="robson_fixed_stars_1923",
        notes=(
            GENERAL_NOTE
            + " Only traditionally well-documented stars are "
            "included — most of the full catalog has no real "
            "astrological tradition behind it."
        ),
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
        source = claim.source_ids[0] if claim.source_ids else "none"
        by_source[source] = by_source.get(source, 0) + 1

    for source, count in sorted(by_source.items()):
        print(f"  {count:3} claims — {source}")
