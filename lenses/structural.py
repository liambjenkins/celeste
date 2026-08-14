"""
Celeste structural interpretation layer.

For each catalogued tradition, this module derives a small set of
deterministic, tradition-specific themes from the SAME shared
feature bundle (lenses/features.py) — including the chart's
elemental balance (astrology.elemental_balance: which classical
element, fire/earth/air/water, the chart's planets fall in most,
by sign — not environmental/weather data).

Important — read before extending this file:

    These interpreters are NOT sourced doctrinal claims. They are
    structural pattern-matching: mapping physical observations onto
    a tradition's own descriptive vocabulary (e.g. the classical
    elements, lunar phase, yin/yang polarity), using associations
    that are historically documented as part of that tradition's own
    symbolic language (e.g. the four classical elements in Greco-Roman
    thought and Western astrology; the pancha mahabhuta in Hindu and
    Buddhist thought; the four elements in Jungian/alchemical
    psychology). They do not assert what the tradition teaches is
    true, and they are never presented as equivalent to a claim
    reviewed and approved through the knowledge/claims pipeline.

    Every interpreter output is combined, in lenses/pipeline.py, with
    any actual source-backed approved claims for that lens. The two
    are always kept visibly distinct in the final interpretation.

Each interpreter returns a dict:
    {
        "themes": [...],           # tradition-vocabulary theme labels
        "macro_themes": [...],     # tags from the shared taxonomy below,
                                    # used for cross-tradition comparison
        "elemental_focus": [...],  # elemental domains this tradition's
                                    # reading foregrounds
        "notes": [...],            # short structural sentences
    }
"""

from lenses.features import FeatureBundle

# ------------------------------------------------------------
# Shared macro-theme taxonomy.
#
# A small controlled vocabulary so that different traditions'
# structural readings can be compared: two lenses sharing a
# macro-theme are, for this moment, structurally convergent.
# ------------------------------------------------------------

CYCLICALITY = "cyclicality"
DUALITY = "duality_and_polarity"
ELEMENTAL = "elemental_correspondence"
BALANCE = "balance_and_order"
IMPERMANENCE = "impermanence"
STILLNESS_OR_TURBULENCE = "inner_stillness_or_turbulence"
CREATION_AND_SIGNS = "creation_and_signs"
ARCHETYPE = "archetypal_symbolism"
VITALITY = "vitality_and_transformation"
TIMEKEEPING = "sacred_timekeeping"


def _ordinal(number):
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def _result(themes=None, macro_themes=None, elemental_focus=None, notes=None):
    return {
        "themes": themes or [],
        "macro_themes": macro_themes or [],
        "elemental_focus": elemental_focus or [],
        "notes": notes or [],
    }


def _has(features: FeatureBundle, tag):
    return tag in features.tags


def _turbulent(features: FeatureBundle):
    return _has(features, "precipitation:active") or _has(features, "pressure:low")


def _still(features: FeatureBundle):
    return _has(features, "cloud:clear") and _has(features, "precipitation:none")


def _yin_yang_tilt(features: FeatureBundle):
    yang_tags = {
        "temperature:warm",
        "cloud:clear",
        "pressure:high",
        "precipitation:none",
    }
    yin_tags = {
        "temperature:cool",
        "cloud:overcast",
        "pressure:low",
        "precipitation:active",
        "humidity:high",
    }

    present = set(features.tags)

    yang = len(present & yang_tags)
    yin = len(present & yin_tags)

    if yang == 0 and yin == 0:
        return None

    if yang > yin:
        return "yang_leaning"

    if yin > yang:
        return "yin_leaning"

    return "balanced"


# ------------------------------------------------------------
# Astrology
# ------------------------------------------------------------

def _astrology(concepts, features: FeatureBundle):
    themes = []
    notes = []
    macro = []

    if features.moon_phase_name:
        themes.append(f"lunar_phase:{features.moon_phase_name}")
        notes.append(
            f"The Moon is in its {features.moon_phase_name.replace('_', ' ')} "
            "phase relative to the Sun."
        )
        macro.append(CYCLICALITY)

    if features.sun_moon_aspect:
        themes.append(f"sun_moon_aspect:{features.sun_moon_aspect}")

        if features.sun_moon_aspect_orb is not None:
            notes.append(
                f"Sun and Moon form a {features.sun_moon_aspect} "
                f"({features.sun_moon_aspect_strength or 'computed'}, "
                f"orb {features.sun_moon_aspect_orb:.2f}°) in "
                "traditional aspect terms."
            )
        else:
            notes.append(
                f"Sun and Moon form an approximate "
                f"{features.sun_moon_aspect} in traditional aspect "
                "terms."
            )

        macro.append(DUALITY)

    if features.harmonic_sun_signs:
        for harmonic_n, sign in sorted(features.harmonic_sun_signs.items()):
            themes.append(f"harmonic_sun:{harmonic_n}:{sign}")
        notes.append(
            "Harmonic Sun position(s): "
            + ", ".join(
                f"H{n} Sun in {sign}"
                for n, sign in sorted(features.harmonic_sun_signs.items())
            )
            + " — the same birth moment viewed through the "
            "quintile/septile/novile harmonic lenses."
        )
        macro.append(ARCHETYPE)

    if features.aspect_patterns_present:
        for pattern in sorted(features.aspect_patterns_present):
            themes.append(f"aspect_pattern:{pattern}")
        notes.append(
            "Aspect pattern(s) present: "
            + ", ".join(sorted(features.aspect_patterns_present))
            + " — a specific geometric configuration, read as more "
            "than the sum of its individual aspects."
        )
        macro.append(ARCHETYPE)

    if features.chart_shape:
        themes.append(f"chart_shape:{features.chart_shape}")
        notes.append(
            f"The chart's overall shape is {features.chart_shape} "
            "(Marc Edmund Jones' classification, based on how the "
            "bodies are distributed around the wheel)."
        )
        macro.append(ARCHETYPE)

    if features.chart_ruler:
        themes.append(f"chart_ruler:{features.chart_ruler}")
        notes.append(
            f"The chart ruler (traditional ruler of the Ascendant) "
            f"is {features.chart_ruler}, in house "
            f"{features.chart_ruler_house} — a personal significator "
            "describing how the outward persona actually moves "
            "through the world."
        )
        macro.append(ARCHETYPE)

        if features.final_dispositor:
            notes.append(
                f"{features.final_dispositor} is this chart's final "
                "dispositor — every planet's rulership chain "
                "eventually leads back to it, a real organizing "
                "anchor most charts don't have."
            )

    if features.antiscion_sun_sign:
        themes.append(f"antiscion:sun:{features.antiscion_sun_sign}")
        notes.append(
            f"The Sun's antiscion (its solstice-axis mirror point) "
            f"falls in {features.antiscion_sun_sign} — a 'hidden "
            "axis' point some traditions read as a quiet, secondary "
            "expression of the Sun's themes."
        )
        macro.append(ARCHETYPE)

    if features.declination_aspects_present:
        for decl in sorted(features.declination_aspects_present):
            themes.append(f"declination_aspect:{decl}")
        notes.append(
            "Declination aspects present: "
            + ", ".join(sorted(features.declination_aspects_present))
            + " — a different coordinate axis (distance from the "
            "celestial equator) from the longitude-based aspects "
            "above, traditionally read as an additional, often "
            "reinforcing layer."
        )
        macro.append(DUALITY)

    if features.minor_aspects_present:
        for minor in sorted(features.minor_aspects_present):
            themes.append(f"minor_aspect:{minor}")
        notes.append(
            "Minor aspects present in this chart: "
            + ", ".join(sorted(features.minor_aspects_present))
            + " — subtler harmonics, read as texture alongside (not "
            "instead of) the major aspects above."
        )
        macro.append(DUALITY)

    if features.ascendant_sign:
        themes.append(f"ascendant:{features.ascendant_sign}")
        notes.append(
            f"The Ascendant (rising sign) is {features.ascendant_sign}, "
            "traditionally read as the chart's outward persona and "
            "the lens through which the moment first meets the world."
        )
        macro.append(ARCHETYPE)

    if features.vertex_sign:
        themes.append(f"vertex:{features.vertex_sign}")
        notes.append(
            f"The Vertex is in {features.vertex_sign} — a calculated "
            "point traditionally read as an 'auxiliary Descendant' "
            "marking fated or karmic encounters."
        )
        macro.append(ARCHETYPE)

    if features.fortune_sign:
        themes.append(f"fortune:{features.fortune_sign}")
        sect = "day" if features.day_chart else "night"
        notes.append(
            f"The Part of Fortune is in {features.fortune_sign} "
            f"(a {sect} chart), the classical Hellenistic lot marking "
            "where wellbeing and circumstance most readily align."
        )
        macro.append(ARCHETYPE)

    if features.spirit_sign:
        themes.append(f"spirit:{features.spirit_sign}")
        notes.append(
            f"The Part of Spirit is in {features.spirit_sign}, the "
            "counterpart lot marking where deliberate will and "
            "purposeful action are focused."
        )
        macro.append(ARCHETYPE)

    if features.star_conjunction_star:
        themes.append(
            f"star_conjunction:{features.star_conjunction_body}:"
            f"{features.star_conjunction_star}"
        )
        magnitude_note = (
            f", magnitude {features.star_conjunction_magnitude:.2f}"
            if features.star_conjunction_magnitude is not None
            else ""
        )
        notes.append(
            f"{features.star_conjunction_body} forms a tight "
            f"conjunction (orb {features.star_conjunction_orb:.2f}°) "
            f"with the fixed star {features.star_conjunction_star}"
            f"{magnitude_note} — fixed stars are traditionally only "
            "read as significant this close."
        )
        macro.append(ARCHETYPE)

    if features.has_transits:
        themes.append("timing:transits")
        outer_transits = [
            f"{body} in your {_ordinal(house)} house"
            for body, house in features.transit_houses.items()
            if body in ("jupiter", "saturn", "uranus", "neptune", "pluto")
        ]
        if outer_transits:
            notes.append(
                "Currently transiting: " + ", ".join(sorted(outer_transits))
                + " — the slower-moving planets whose house transit "
                "marks the broadest current period, in traditional "
                "predictive technique."
            )
        macro.append(CYCLICALITY)

    if features.has_progressions:
        themes.append("timing:secondary_progressions")
        if features.progressed_moon_sign:
            notes.append(
                f"The progressed Moon is currently in "
                f"{features.progressed_moon_sign} — the 'day for a "
                "year' technique's classical focus, changing sign "
                "roughly every two and a half years to mark the "
                "current emotional chapter."
            )
        macro.append(CYCLICALITY)

    if features.has_tertiary:
        themes.append("timing:tertiary_progressions")
        if features.tertiary_moon_sign:
            notes.append(
                f"The tertiary-progressed Moon is currently in "
                f"{features.tertiary_moon_sign} — the faster, "
                "month-by-month resolution tertiary progressions "
                "add alongside secondary progressions' year-by-year "
                "view."
            )
        macro.append(CYCLICALITY)

    if features.season:
        themes.append(f"season:{features.season}")
        macro.append(CYCLICALITY)

    if features.dominant_domains:
        themes.append(
            "elemental_emphasis:" + "_".join(features.dominant_domains)
        )
        notes.append(
            "The chart's planets fall most heavily in "
            f"{', '.join(features.dominant_domains)} sign(s), the "
            "classical element(s) traditional astrology considers "
            "most emphasised in this chart."
        )
        macro.append(ELEMENTAL)

    return _result(themes, macro, list(features.dominant_domains), notes)


# ------------------------------------------------------------
# Islamic cosmology
# ------------------------------------------------------------

def _islamic_cosmology(concepts, features: FeatureBundle):
    themes = []
    notes = []
    macro = [CREATION_AND_SIGNS]

    observed_domains = [d for d, c in features.elemental_strength.items() if c > 0]

    if observed_domains:
        themes.append("signs_in_creation:" + "_".join(sorted(observed_domains)))
        notes.append(
            "The chart's planets occupy signs across "
            f"{len(observed_domains)} classical element(s) "
            f"({', '.join(sorted(observed_domains))}), read here as "
            "'signs' (ayat) within the created, patterned natural order."
        )

    if features.moon_phase_name:
        themes.append(f"lunar_timekeeping:{features.moon_phase_name}")
        notes.append(
            "The lunar phase marks a specific point in the lunar "
            "calendar used for Islamic timekeeping."
        )
        macro.append(TIMEKEEPING)

    return _result(themes, macro, observed_domains, notes)


# ------------------------------------------------------------
# Islamic mysticism (Sufism)
# ------------------------------------------------------------

def _islamic_mysticism(concepts, features: FeatureBundle):
    themes = []
    notes = []
    macro = []

    if _turbulent(features):
        themes.append("state:turbulence")
        notes.append(
            "Active/unsettled atmospheric conditions are read structurally "
            "as an outward turbulence motif, echoing the mystical theme "
            "of the heart's states moving between constriction and ease."
        )
        macro.append(STILLNESS_OR_TURBULENCE)
    elif _still(features):
        themes.append("state:stillness")
        notes.append(
            "Clear, calm conditions are read structurally as a stillness "
            "motif, echoing the mystical theme of presence and "
            "remembrance (dhikr)."
        )
        macro.append(STILLNESS_OR_TURBULENCE)

    return _result(themes, macro, [], notes)


# ------------------------------------------------------------
# Christian mysticism
# ------------------------------------------------------------

def _christian_mysticism(concepts, features: FeatureBundle):
    themes = []
    notes = []
    macro = [CREATION_AND_SIGNS]

    if features.dominant_domains:
        themes.append(
            "creation_attention:" + "_".join(features.dominant_domains)
        )
        notes.append(
            "The chart's dominant element(s) "
            f"({', '.join(features.dominant_domains)}) are read as the "
            "focus of contemplative attention to creation, in the "
            "spirit of traditions such as the Canticle of the Creatures."
        )

    if features.season:
        themes.append(f"season:{features.season}")
        macro.append(CYCLICALITY)

    return _result(themes, macro, list(features.dominant_domains), notes)


# ------------------------------------------------------------
# Jewish mysticism (Kabbalah)
# ------------------------------------------------------------

def _jewish_mysticism(concepts, features: FeatureBundle):
    themes = []
    notes = []
    macro = []

    if features.dominant_domains:
        themes.append(
            "elemental_emphasis:" + "_".join(features.dominant_domains)
        )
        notes.append(
            "The dominant elemental domain(s) "
            f"({', '.join(features.dominant_domains)}) correspond to "
            "the classical fire/water/air/earth grouping used in some "
            "later Kabbalistic frameworks."
        )
        macro.append(ELEMENTAL)

    if features.moon_phase_name in ("new_moon", "full_moon"):
        themes.append(f"lunar_marker:{features.moon_phase_name}")
        notes.append(
            "The Moon is at a marker point (new or full) relevant to "
            "the Jewish lunar calendar."
        )
        macro.append(TIMEKEEPING)

    return _result(themes, macro, list(features.dominant_domains), notes)


# ------------------------------------------------------------
# Hindu cosmology
# ------------------------------------------------------------

_PANCHA_BHUTA = {
    "fire": "agni/tejas",
    "water": "apas/jala",
    "earth": "prithvi",
    "air": "vayu",
}


def _hindu_cosmology(concepts, features: FeatureBundle):
    themes = []
    notes = []
    macro = [ELEMENTAL]

    if features.ascendant_sign:
        themes.append(f"lagna:{features.ascendant_sign}")
        notes.append(
            f"The Lagna (ascendant) falls in {features.ascendant_sign}, "
            "the reference point Vedic astrology uses to anchor the "
            "rest of the chart."
        )
        macro.append(ARCHETYPE)

    if features.dominant_domains:
        labels = [
            f"{domain} ({_PANCHA_BHUTA.get(domain, domain)})"
            for domain in features.dominant_domains
        ]
        themes.append(
            "pancha_bhuta_emphasis:" + "_".join(features.dominant_domains)
        )
        notes.append(
            "Within the pancha mahabhuta (five great elements), the "
            f"chart's planets fall most heavily in: {', '.join(labels)}."
        )

    if features.season:
        themes.append(f"season:{features.season}")
        macro.append(CYCLICALITY)
        notes.append(
            "The seasonal position situates the moment within a "
            "recurring cosmic cycle."
        )

    return _result(themes, macro, list(features.dominant_domains), notes)


# ------------------------------------------------------------
# Buddhist cosmology
# ------------------------------------------------------------

def _buddhist_cosmology(concepts, features: FeatureBundle):
    themes = []
    notes = []
    macro = [IMPERMANENCE]

    populated = [d for d, c in features.elemental_strength.items() if c > 0]
    empty = [d for d, c in features.elemental_strength.items() if c == 0]

    if empty:
        themes.append("unoccupied_elements:" + "_".join(sorted(empty)))
        notes.append(
            "No chart planets fall in "
            f"{', '.join(sorted(empty))} sign(s) — read structurally "
            "as a reminder that any single chart is a partial "
            "configuration, not a complete or fixed state."
        )

    if features.season:
        themes.append(f"season:{features.season}")
        macro.append(CYCLICALITY)
        notes.append(
            "The seasonal position reflects dependent, conditioned "
            "change (the annual cycle) rather than a fixed state."
        )

    return _result(themes, macro, populated, notes)


# ------------------------------------------------------------
# Taoist cosmology
# ------------------------------------------------------------

def _taoist_cosmology(concepts, features: FeatureBundle):
    themes = []
    notes = []
    macro = [DUALITY]

    tilt = _yin_yang_tilt(features)

    if tilt:
        themes.append(f"yin_yang:{tilt}")
        notes.append(
            f"The observed signals lean {tilt.replace('_', ' ')} "
            "under a classical yin/yang reading (warmth, clear sky, "
            "and high pressure read as yang; cool, damp, overcast, "
            "low-pressure conditions read as yin)."
        )

    if features.season:
        themes.append(f"season:{features.season}")
        macro.append(CYCLICALITY)
        notes.append(
            "The seasonal position marks a point in the turning of "
            "the natural cycle."
        )

    return _result(themes, macro, [], notes)


# ------------------------------------------------------------
# Pagan / Wiccan
# ------------------------------------------------------------

def _pagan_wiccan(concepts, features: FeatureBundle):
    themes = []
    notes = []
    macro = [ELEMENTAL]

    if features.dominant_domains:
        themes.append(
            "elemental_correspondence:" + "_".join(features.dominant_domains)
        )
        notes.append(
            "The dominant elemental domain(s) "
            f"({', '.join(features.dominant_domains)}) correspond to "
            "the fire/water/earth/air/spirit correspondences used in "
            "modern Pagan and Wiccan elemental symbolism."
        )

    if features.moon_phase_name:
        themes.append(f"lunar_phase:{features.moon_phase_name}")
        notes.append(
            f"The Moon's {features.moon_phase_name.replace('_', ' ')} "
            "phase marks a point on the esbat cycle."
        )
        macro.append(CYCLICALITY)

    if features.sabbat:
        themes.append(f"sabbat:{features.sabbat}")
        macro.append(CYCLICALITY)

        if features.sabbat_days_away == 0:
            notes.append(
                f"The moment falls exactly on {features.sabbat}, one "
                "of the eight sabbats on the Wheel of the Year."
            )
        else:
            notes.append(
                f"The moment falls nearest {features.sabbat} "
                f"({features.sabbat_days_away} day"
                f"{'s' if features.sabbat_days_away != 1 else ''} away) "
                "on the Wheel of the Year, adjusted for hemisphere so "
                "the sabbat's seasonal meaning matches the season "
                "actually occurring at this latitude."
            )
    elif features.season:
        themes.append(f"season:{features.season}")
        macro.append(CYCLICALITY)
        notes.append("The season marks a point on the Wheel of the Year.")

    return _result(themes, macro, list(features.dominant_domains), notes)


# ------------------------------------------------------------
# Greco-Roman cosmology
# ------------------------------------------------------------

def _greco_roman(concepts, features: FeatureBundle):
    themes = []
    notes = []
    macro = [ELEMENTAL]

    if features.dominant_domains:
        themes.append(
            "classical_element_emphasis:" + "_".join(features.dominant_domains)
        )
        notes.append(
            "The dominant elemental domain(s) "
            f"({', '.join(features.dominant_domains)}) correspond "
            "directly to the classical Greek four/five-element system "
            "(fire, water, earth, air, aether)."
        )

    planetary = concepts.get("planetary_positions")

    if planetary and planetary.get("observations"):
        themes.append("planetary_bodies_named_for_deities")
        notes.append(
            "The observed planetary bodies carry the names of "
            "Greco-Roman deities (Mars, Venus, Jupiter, Saturn, "
            "Mercury), a direct historical link between the "
            "astronomical and mythological."
        )
        macro.append(ARCHETYPE)

    return _result(themes, macro, list(features.dominant_domains), notes)


# ------------------------------------------------------------
# Ancient Egyptian cosmology
# ------------------------------------------------------------

def _egyptian_cosmology(concepts, features: FeatureBundle):
    themes = []
    notes = []
    macro = [BALANCE]

    counts = list(features.elemental_strength.values())

    if counts:
        spread = max(counts) - min(counts)

        if spread <= 1:
            themes.append("balance:even")
            notes.append(
                "The chart's planets are evenly spread across the "
                "classical elements — read structurally as an image "
                "of Ma'at (balance/order)."
            )
        else:
            themes.append("balance:skewed")
            notes.append(
                "The chart's planets are concentrated in certain "
                "classical elements rather than evenly spread — read "
                "structurally as an image of imbalance against Ma'at."
            )

    return _result(themes, macro, list(features.dominant_domains), notes)


# ------------------------------------------------------------
# Depth psychology (Jungian)
# ------------------------------------------------------------

_JUNGIAN_ARCHETYPE = {
    "fire": "spirit / animating drive",
    "water": "the unconscious / emotion",
    "earth": "the body / the shadow",
    "air": "intellect / persona",
}


def _depth_psychology(concepts, features: FeatureBundle):
    themes = []
    notes = []
    macro = [ARCHETYPE]

    if features.dominant_domains:
        for domain in features.dominant_domains:
            archetype = _JUNGIAN_ARCHETYPE.get(domain, domain)
            themes.append(f"archetype:{domain}:{archetype}")

        notes.append(
            "In the Jungian/alchemical convention that associates each "
            "classical element with a psychic function, this moment "
            "foregrounds: "
            + ", ".join(
                f"{domain} ({_JUNGIAN_ARCHETYPE.get(domain, domain)})"
                for domain in features.dominant_domains
            )
            + "."
        )
        macro.append(VITALITY)

    return _result(themes, macro, list(features.dominant_domains), notes)


# ------------------------------------------------------------
# Philosophy (Stoic / Aristotelian)
# ------------------------------------------------------------

# ------------------------------------------------------------
# Vedic astrology (Jyotish)
# ------------------------------------------------------------

def _vedic_astrology(concepts, features: FeatureBundle):
    themes = []
    notes = []
    macro = []

    if features.vedic_ascendant_sign:
        themes.append(f"lagna:{features.vedic_ascendant_sign}")
        notes.append(
            f"The Lagna (rising sign) is sidereal "
            f"{features.vedic_ascendant_sign}, the reference point "
            "Vedic whole-sign houses are counted from."
        )
        macro.append(ARCHETYPE)

    if features.vedic_sun_nakshatra:
        themes.append(f"nakshatra:sun:{features.vedic_sun_nakshatra}")
        notes.append(
            f"The Sun falls in {features.vedic_sun_nakshatra} "
            "nakshatra, the lunar-mansion subdivision unique to "
            "Jyotish."
        )
        macro.append(CYCLICALITY)

    if features.vedic_moon_nakshatra:
        themes.append(f"nakshatra:moon:{features.vedic_moon_nakshatra}")
        notes.append(
            f"The Moon falls in {features.vedic_moon_nakshatra} "
            "nakshatra — in Jyotish the Moon's nakshatra is "
            "traditionally considered the single most important "
            "placement in the chart."
        )
        macro.append(CYCLICALITY)

    if features.navamsa_ascendant_sign:
        themes.append(f"navamsa_ascendant:{features.navamsa_ascendant_sign}")
        notes.append(
            f"The D9 (Navamsa) Ascendant is {features.navamsa_ascendant_sign} "
            "— the reference point the Navamsa's own whole-sign "
            "houses are counted from, distinct from the D1 chart's "
            "Ascendant above."
        )
        macro.append(ARCHETYPE)

    if features.navamsa_sun_sign:
        agree = features.navamsa_sun_sign == features.vedic_sun_sign
        themes.append(f"navamsa_sign:sun:{features.navamsa_sun_sign}")
        notes.append(
            f"The Sun's Navamsa sign is {features.navamsa_sun_sign}"
            + (
                ", the same sign as its D1 placement — traditionally "
                "read as a placement whose strength is confirmed "
                "rather than complicated by this deeper subdivision."
                if agree
                else f" (its D1 sign is {features.vedic_sun_sign}) — "
                "traditionally read alongside the D1 sign rather "
                "than in place of it, for a subtler picture of the "
                "placement's underlying strength."
            )
        )
        macro.append(ARCHETYPE)

    if features.navamsa_moon_sign:
        agree = features.navamsa_moon_sign == features.vedic_moon_sign
        themes.append(f"navamsa_sign:moon:{features.navamsa_moon_sign}")
        notes.append(
            f"The Moon's Navamsa sign is {features.navamsa_moon_sign}"
            + (
                ", the same sign as its D1 placement."
                if agree
                else f" (its D1 sign is {features.vedic_moon_sign})."
            )
        )
        macro.append(ARCHETYPE)

    if features.varga_ascendant_signs:
        for varga_n, sign in sorted(features.varga_ascendant_signs.items()):
            themes.append(f"varga_ascendant:{varga_n}:{sign}")
        notes.append(
            "Divisional chart (varga) Ascendant(s): "
            + ", ".join(
                f"D{n} in {sign}"
                for n, sign in sorted(features.varga_ascendant_signs.items())
            )
            + " — each divisional chart's own Ascendant, the reference "
            "point its own domain-specific reading (D10 career, D12 "
            "parents, D7 children, and so on) is built from."
        )
        macro.append(ARCHETYPE)

    if features.exalted_planets or features.debilitated_planets:
        for planet in features.exalted_planets:
            themes.append(f"dignity_exalted:{planet}")
        for planet in features.debilitated_planets:
            themes.append(f"dignity_debilitated:{planet}")

        parts = []
        if features.exalted_planets:
            parts.append(f"exalted: {', '.join(sorted(features.exalted_planets))}")
        if features.debilitated_planets:
            parts.append(f"debilitated: {', '.join(sorted(features.debilitated_planets))}")

        notes.append(
            "Planetary dignity extremes present — "
            + "; ".join(parts)
            + " — a placement's strength (exalted) or difficulty "
            "(debilitated) by classical sign lordship, the strongest "
            "and weakest of the six dignity levels."
        )
        macro.append(ARCHETYPE)

    if features.atmakaraka_planet:
        themes.append(f"atmakaraka:{features.atmakaraka_planet}")
        notes.append(
            f"The Atmakaraka (soul significator, Jaimini technique) is "
            f"{features.atmakaraka_planet} — the planet at the highest "
            "degree within its sign, traditionally read as the chart's "
            "single most emphasized indicator of the soul's own agenda."
        )
        macro.append(ARCHETYPE)

    if features.marak_planets:
        for planet in features.marak_planets:
            themes.append(f"marak:{planet}")
        notes.append(
            "Marak (2nd/7th house lord) planet(s): "
            + ", ".join(sorted(features.marak_planets))
            + " — traditional timing significators for periods of "
            "vulnerability via Dasha, not literal predictions."
        )
        macro.append(CYCLICALITY)

    if features.ashtakavarga_own_sign_strength:
        for planet, strength in sorted(features.ashtakavarga_own_sign_strength.items()):
            themes.append(f"ashtakavarga_own_sign:{planet}:{strength}")
        notable = {
            planet: strength
            for planet, strength in features.ashtakavarga_own_sign_strength.items()
            if strength != "medium"
        }
        if notable:
            notes.append(
                "Ashtakavarga own-sign Bindu strength — "
                + ", ".join(
                    f"{planet} {strength}" for planet, strength in sorted(notable.items())
                )
                + " — how much classical point-support each planet "
                "has in the sign it currently occupies."
            )
            macro.append(ARCHETYPE)

    if features.sarvashtakavarga_strength:
        for point, strength in sorted(features.sarvashtakavarga_strength.items()):
            themes.append(f"sarvashtakavarga:{point}:{strength}")

    if features.shadbala_strongest_planet and features.shadbala_weakest_planet:
        themes.append(f"shadbala_strongest:{features.shadbala_strongest_planet}")
        themes.append(f"shadbala_weakest:{features.shadbala_weakest_planet}")
        notes.append(
            f"By Shadbala's well-verified positional/directional/"
            f"natural-strength factors (a deliberately partial "
            f"reading, not the full six-fold classical total), "
            f"{features.shadbala_strongest_planet} is comparatively "
            f"the strongest placement in this chart and "
            f"{features.shadbala_weakest_planet} the comparatively "
            "weakest."
        )
        macro.append(ARCHETYPE)

    if features.vedic_yogas:
        for yoga_id in features.vedic_yogas:
            themes.append(f"yoga:{yoga_id}")
        notes.append(
            f"{len(features.vedic_yogas)} classical yoga(s) "
            "(planetary combination) from the curated set are "
            "present in this chart — specific configurations, not "
            "just individual sign or house placements."
        )
        macro.append(ARCHETYPE)

    if features.has_dasha:
        themes.append(f"dasha_mahadasha:{features.dasha_mahadasha_lord}")
        themes.append(f"dasha_antardasha:{features.dasha_antardasha_lord}")
        notes.append(
            f"Currently running: {features.dasha_mahadasha_lord} "
            f"Mahadasha, {features.dasha_antardasha_lord} Antardasha "
            "— the Vimshottari Dasha's major period and its "
            "sub-period, the classical Jyotish timing technique for "
            "which planet's themes are most active right now."
        )
        macro.append(CYCLICALITY)

    if features.has_yogini_dasha:
        themes.append(f"yogini_dasha:{features.yogini_dasha_current}")
        notes.append(
            f"The current Yogini Dasha period is {features.yogini_dasha_current} "
            "— a distinct, faster 36-year Vedic timing cycle read "
            "alongside (not instead of) Vimshottari Dasha."
        )
        macro.append(CYCLICALITY)

    if features.has_chara_dasha:
        themes.append(f"chara_dasha_sign:{features.chara_dasha_current_sign}")
        notes.append(
            f"The current Chara Dasha sign period is "
            f"{features.chara_dasha_current_sign} — the Jaimini "
            "school's sign-based (not planet-based) timing technique, "
            "read alongside Vimshottari Dasha for a second, "
            "independent timing perspective."
        )
        macro.append(CYCLICALITY)

    if features.dominant_domains:
        themes.append(
            "elemental_emphasis:" + "_".join(features.dominant_domains)
        )
        macro.append(ELEMENTAL)

    return _result(themes, macro, list(features.dominant_domains), notes)


# ------------------------------------------------------------
# Chinese astrology (BaZi)
# ------------------------------------------------------------

def _chinese_zodiac(concepts, features: FeatureBundle):
    themes = []
    notes = []
    macro = []

    if features.chinese_day_master:
        themes.append(f"day_master:{features.chinese_day_master}")
        notes.append(
            f"The Day Master is {features.chinese_day_master} "
            f"({features.chinese_day_master_element}) — the reading's "
            "central reference point; everything else in a BaZi "
            "chart is ultimately read in relation to it."
        )
        macro.append(ARCHETYPE)

    if features.chinese_year_animal:
        themes.append(f"year_animal:{features.chinese_year_animal}")
        notes.append(
            f"The Year Pillar's branch animal is "
            f"{features.chinese_year_animal}, governing ancestry, "
            "early life, and public/social face."
        )
        macro.append(CYCLICALITY)

    if features.chinese_pillar_names:
        themes.append(
            "four_pillars:"
            + "_".join(features.chinese_pillar_names.get(p, "?") for p in ("year", "month", "day", "hour"))
        )
        macro.append(TIMEKEEPING)

    if features.chinese_ten_gods:
        themes.append("ten_gods_present:" + "_".join(sorted(set(features.chinese_ten_gods))))
        notes.append(
            f"{len(set(features.chinese_ten_gods))} distinct Ten God "
            "role(s) appear across the chart's visible and hidden "
            "stems — the BaZi-native classification of each stem's "
            "elemental relationship to the Day Master."
        )
        macro.append(ARCHETYPE)

    if features.has_dayun:
        themes.append(f"dayun_current:{features.dayun_current_pillar}")
        notes.append(
            f"The current Da Yun (Luck Pillar) is "
            f"{features.dayun_current_pillar} — the 10-year period "
            "presently overlaid on the Four Pillars."
        )
        macro.append(CYCLICALITY)

    if features.has_liu_nian:
        themes.append(f"liu_nian_current:{features.liu_nian_pillar_name}")
        notes.append(
            f"The current Liu Nian (Flowing Year) pillar is "
            f"{features.liu_nian_pillar_name} — the finer, "
            "year-by-year layer of BaZi timing, read alongside the "
            "current Da Yun."
        )
        macro.append(CYCLICALITY)

    if features.chinese_shen_sha_present:
        for star_id in features.chinese_shen_sha_present:
            themes.append(f"shen_sha:{star_id}")
        notes.append(
            f"{len(features.chinese_shen_sha_present)} Shen Sha "
            "(symbolic star) placement(s) from the curated set are "
            "present — specific classical stem/branch patterns, "
            "distinct from the Ten Gods classification."
        )
        macro.append(ARCHETYPE)

    if features.chinese_na_yin_day_element:
        themes.append(f"na_yin_day_element:{features.chinese_na_yin_day_element}")
        notes.append(
            f"The Day Pillar's Na Yin element is "
            f"{features.chinese_na_yin_day_element} — an older, "
            "sound-derived elemental reading of the core self, "
            "distinct from the Day Master stem's own element."
        )
        macro.append(ELEMENTAL)

    if features.chinese_interactions_present:
        for interaction in features.chinese_interactions_present:
            themes.append(f"chinese_interaction:{interaction}")
        notes.append(
            "Stem/branch interaction(s) present between pillars: "
            + ", ".join(sorted(features.chinese_interactions_present))
            + " — structural relationships between two or more "
            "pillars, distinct from any single pillar's own meaning."
        )
        macro.append(ARCHETYPE)

    if features.chinese_missing_elements or features.chinese_dominant_elements:
        if features.chinese_dominant_elements:
            themes.append(
                "chinese_element_dominant:" + "_".join(sorted(features.chinese_dominant_elements))
            )
        if features.chinese_missing_elements:
            themes.append(
                "chinese_element_missing:" + "_".join(sorted(features.chinese_missing_elements))
            )

        parts = []
        if features.chinese_dominant_elements:
            parts.append(f"dominant: {', '.join(sorted(features.chinese_dominant_elements))}")
        if features.chinese_missing_elements:
            parts.append(f"missing: {', '.join(sorted(features.chinese_missing_elements))}")

        notes.append(
            "Elemental balance across all 8 stem positions (visible "
            "+ hidden) — " + "; ".join(parts) + "."
        )
        macro.append(ELEMENTAL)

    return _result(themes, macro, [], notes)


def _philosophy(concepts, features: FeatureBundle):
    themes = []
    notes = []
    macro = []

    if features.dominant_domains:
        themes.append(
            "material_element_emphasis:" + "_".join(features.dominant_domains)
        )
        notes.append(
            "The chart's dominant element(s) "
            f"({', '.join(features.dominant_domains)}) correspond to "
            "Aristotle's own material elements (earth, water, air, "
            "fire), which his physics used as the substrate of the "
            "natural world."
        )
        macro.append(ELEMENTAL)

    if features.season:
        themes.append(f"season:{features.season}")
        notes.append(
            f"The moment falls in {features.season} — in Stoic terms "
            "an example of what Epictetus's Enchiridion calls a "
            "thing 'not up to us': the turning of the seasons "
            "proceeds regardless of preference, the classic Stoic "
            "illustration of the dichotomy of control."
        )
        macro.append(IMPERMANENCE)

    return _result(themes, macro, list(features.dominant_domains), notes)


STRUCTURAL_INTERPRETERS = {
    "astrology": _astrology,
    "islamic_cosmology": _islamic_cosmology,
    "islamic_mysticism": _islamic_mysticism,
    "christian_mysticism": _christian_mysticism,
    "jewish_mysticism": _jewish_mysticism,
    "hindu_cosmology": _hindu_cosmology,
    "buddhist_cosmology": _buddhist_cosmology,
    "taoist_cosmology": _taoist_cosmology,
    "pagan_wiccan": _pagan_wiccan,
    "greco_roman": _greco_roman,
    "egyptian_cosmology": _egyptian_cosmology,
    "depth_psychology": _depth_psychology,
    "philosophy": _philosophy,
    "vedic_astrology": _vedic_astrology,
    "chinese_zodiac": _chinese_zodiac,
}


def build_structural_interpretation(lens_id, concepts, features: FeatureBundle):
    """
    Produce the structural (non-doctrinal) interpretation for one
    lens. Falls back to an empty-but-honest result for any lens not
    yet covered.
    """

    interpreter = STRUCTURAL_INTERPRETERS.get(lens_id)

    if interpreter is None:
        return _result()

    return interpreter(concepts, features)


if __name__ == "__main__":
    from lenses.features import build_features

    concepts = {
        "sun": {
            "observations": [{"value": {"longitude": 119.6}, "source": "t"}]
        },
        "moon": {
            "observations": [{"value": {"longitude": 209.6}, "source": "t"}]
        },
        "temperature": {"observations": [{"value": 8.0, "source": "t"}]},
        "season": {"observations": [{"value": "winter", "source": "t"}]},
        "elemental_balance": {
            "observations": [
                {
                    "value": {"fire": 3, "earth": 2, "air": 4, "water": 1},
                    "source": "t",
                }
            ]
        },
    }

    features = build_features(concepts)

    for lens_id in STRUCTURAL_INTERPRETERS:
        result = build_structural_interpretation(lens_id, concepts, features)
        print(f"[{lens_id}]")
        for note in result["notes"]:
            print("  -", note)

    print()
    print("structural.py: OK")
