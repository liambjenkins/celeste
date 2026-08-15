"""
Celeste shared feature extraction.

Turns canonical concepts into a small set of derived, machine-readable
feature tags that any lens can draw on:

    - environmental signal tags (temperature, humidity, pressure, ...)
    - the actual lunar phase, derived from Sun/Moon ecliptic longitude
    - a Sun-Moon aspect tag, for claim resolution (e.g. "aspect:square")
    - the tightest fixed-star conjunction, if any chart body is within
    orb of a named star (fixed stars are only traditionally read as
    meaningful in tight conjunction, unlike wide planet-to-planet
    aspect orbs)
    - which classical element (fire/water/earth/air) is dominant in the
    chart, from the elemental_balance concept (sign triplicities —
    astrology.elemental_balance) — deliberately NOT derived from
    environmental/weather data. There's no principled way to make
    "it was raining" mean "this chart is water-dominant"; the only
    honest source for a chart's elemental balance is which signs its
    planets actually occupy.

This module does not interpret. It only derives structured,
tradition-neutral features that lens-specific code (structural.py,
the knowledge claim resolver) can consume.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from astrology.normaliser import longitude_to_zodiac


@dataclass
class FeatureBundle:
    tags: list[str] = field(default_factory=list)

    season: Optional[str] = None
    sabbat: Optional[str] = None
    sabbat_days_away: Optional[int] = None

    sun_longitude: Optional[float] = None
    moon_longitude: Optional[float] = None
    moon_phase_angle: Optional[float] = None
    moon_phase_name: Optional[str] = None
    sun_moon_aspect: Optional[str] = None
    sun_moon_aspect_orb: Optional[float] = None
    sun_moon_aspect_strength: Optional[str] = None

    ascendant_longitude: Optional[float] = None
    ascendant_sign: Optional[str] = None

    vertex_sign: Optional[str] = None
    vertex_house: Optional[int] = None

    minor_aspects_present: set = field(default_factory=set)

    declination_aspects_present: set = field(default_factory=set)

    antiscion_sun_sign: Optional[str] = None
    antiscion_moon_sign: Optional[str] = None

    chart_ruler: Optional[str] = None
    chart_ruler_house: Optional[int] = None
    final_dispositor: Optional[str] = None

    aspect_patterns_present: set = field(default_factory=set)
    chart_shape: Optional[str] = None

    harmonic_sun_signs: dict[int, str] = field(default_factory=dict)

    day_chart: Optional[bool] = None
    fortune_sign: Optional[str] = None
    fortune_house: Optional[int] = None
    spirit_sign: Optional[str] = None
    spirit_house: Optional[int] = None

    sun_sign: Optional[str] = None
    moon_sign: Optional[str] = None
    planet_signs: dict[str, str] = field(default_factory=dict)
    retrograde_planets: list[str] = field(default_factory=list)

    sun_house: Optional[int] = None
    moon_house: Optional[int] = None
    planet_houses: dict[str, int] = field(default_factory=dict)

    star_conjunction_body: Optional[str] = None
    star_conjunction_star: Optional[str] = None
    star_conjunction_orb: Optional[float] = None
    star_conjunction_magnitude: Optional[float] = None

    elemental_strength: dict[str, int] = field(default_factory=dict)
    dominant_domains: list[str] = field(default_factory=list)

    vedic_sun_sign: Optional[str] = None
    vedic_moon_sign: Optional[str] = None
    vedic_ascendant_sign: Optional[str] = None
    vedic_planet_signs: dict[str, str] = field(default_factory=dict)

    vedic_sun_nakshatra: Optional[str] = None
    vedic_moon_nakshatra: Optional[str] = None
    vedic_ascendant_nakshatra: Optional[str] = None
    vedic_planet_nakshatras: dict[str, str] = field(default_factory=dict)

    vedic_sun_house: Optional[int] = None
    vedic_moon_house: Optional[int] = None
    vedic_planet_houses: dict[str, int] = field(default_factory=dict)

    navamsa_sun_sign: Optional[str] = None
    navamsa_moon_sign: Optional[str] = None
    navamsa_ascendant_sign: Optional[str] = None
    navamsa_planet_signs: dict[str, str] = field(default_factory=dict)

    varga_ascendant_signs: dict[int, str] = field(default_factory=dict)

    exalted_planets: list[str] = field(default_factory=list)
    debilitated_planets: list[str] = field(default_factory=list)
    atmakaraka_planet: Optional[str] = None
    marak_planets: list[str] = field(default_factory=list)

    ashtakavarga_own_sign_strength: dict[str, str] = field(default_factory=dict)
    sarvashtakavarga_strength: dict[str, str] = field(default_factory=dict)

    shadbala_strongest_planet: Optional[str] = None
    shadbala_weakest_planet: Optional[str] = None

    vedic_yogas: list[str] = field(default_factory=list)

    has_dasha: bool = False
    dasha_mahadasha_lord: Optional[str] = None
    dasha_antardasha_lord: Optional[str] = None

    has_yogini_dasha: bool = False
    yogini_dasha_current: Optional[str] = None
    has_chara_dasha: bool = False
    chara_dasha_current_sign: Optional[str] = None

    chinese_day_master: Optional[str] = None
    chinese_day_master_element: Optional[str] = None
    chinese_year_animal: Optional[str] = None
    chinese_pillar_names: dict[str, str] = field(default_factory=dict)

    chinese_ten_gods: list[str] = field(default_factory=list)
    has_liu_nian: bool = False
    liu_nian_pillar_name: Optional[str] = None
    chinese_shen_sha_present: list[str] = field(default_factory=list)
    chinese_na_yin_day_element: Optional[str] = None
    chinese_interactions_present: list[str] = field(default_factory=list)
    chinese_missing_elements: list[str] = field(default_factory=list)
    chinese_dominant_elements: list[str] = field(default_factory=list)

    has_dayun: bool = False
    dayun_current_pillar: Optional[str] = None

    has_transits: bool = False
    transit_signs: dict[str, str] = field(default_factory=dict)
    transit_houses: dict[str, int] = field(default_factory=dict)
    transit_retrograde: list[str] = field(default_factory=list)

    has_progressions: bool = False
    progressed_signs: dict[str, str] = field(default_factory=dict)
    progressed_houses: dict[str, int] = field(default_factory=dict)
    progressed_moon_sign: Optional[str] = None

    has_tertiary: bool = False
    tertiary_moon_sign: Optional[str] = None


def _single_value(concept):
    if not concept:
        return None

    for observation in concept.get("observations", []):
        if observation.get("value") is not None:
            return observation["value"]

    return None


def _mean(concept):
    values = [
        value
        for value in (
            observation.get("value")
            for observation in (concept or {}).get("observations", [])
        )
        if isinstance(value, (int, float))
    ]

    if not values:
        return None

    return sum(values) / len(values)


def _longitude(concept):
    value = _single_value(concept)

    if isinstance(value, dict):
        return value.get("longitude")

    return None


# ------------------------------------------------------------
# Environmental signal tags
# ------------------------------------------------------------
#
# Thresholds are deliberately simple, deterministic buckets, not
# scientific claims about what counts as "high" or "low" in general.

def _signal_tags(concepts):
    tags = []

    humidity = _mean(concepts.get("atmospheric_moisture"))
    temperature = _mean(concepts.get("temperature"))
    pressure = _mean(concepts.get("pressure"))
    cloud = _mean(concepts.get("cloud"))
    precipitation = _mean(concepts.get("precipitation"))
    vegetation = _mean(concepts.get("vegetation"))

    if humidity is not None:
        if humidity >= 80:
            tags.append("humidity:high")
        elif humidity <= 30:
            tags.append("humidity:low")
        else:
            tags.append("humidity:moderate")

    if temperature is not None:
        if temperature <= 10:
            tags.append("temperature:cool")
        elif temperature >= 30:
            tags.append("temperature:warm")
        else:
            tags.append("temperature:mild")

    if pressure is not None:
        if pressure < 1000:
            tags.append("pressure:low")
        elif pressure > 1020:
            tags.append("pressure:high")
        else:
            tags.append("pressure:moderate")

    if cloud is not None:
        if cloud >= 70:
            tags.append("cloud:overcast")
        elif cloud <= 20:
            tags.append("cloud:clear")
        else:
            tags.append("cloud:partial")

    if precipitation is not None:
        tags.append(
            "precipitation:active" if precipitation > 0 else "precipitation:none"
        )

    if vegetation is not None:
        tags.append(
            "vegetation:strong" if vegetation >= 0.5 else "vegetation:moderate"
        )

    return tags


# ------------------------------------------------------------
# Lunar phase and Sun-Moon aspect
# ------------------------------------------------------------

_PHASE_BOUNDARIES = [
    (22.5, "new_moon"),
    (67.5, "waxing_crescent"),
    (112.5, "first_quarter"),
    (157.5, "waxing_gibbous"),
    (202.5, "full_moon"),
    (247.5, "waning_gibbous"),
    (292.5, "last_quarter"),
    (337.5, "waning_crescent"),
    (360.01, "new_moon"),
]

_ASPECTS = (
    (0.0, "conjunction"),
    (60.0, "sextile"),
    (90.0, "square"),
    (120.0, "trine"),
    (180.0, "opposition"),
)

_ASPECT_ORB = 6.0


def _moon_phase_name(phase_angle):
    if phase_angle is None:
        return None

    angle = phase_angle % 360

    for upper, name in _PHASE_BOUNDARIES:
        if angle < upper:
            return name

    return "new_moon"


def _sun_moon_aspect(separation):
    if separation is None:
        return None

    for angle, name in _ASPECTS:
        if abs(separation - angle) <= _ASPECT_ORB:
            return name

    return None


def _real_sun_moon_aspect(concepts):
    """
    Look up the real Sun-Moon aspect from astrology.aspects'
    computed aspect list (proper per-aspect orbs, includes
    quincunx), when the richer astrology engine populated it.

    Returns the raw aspect dict, or None if unavailable.
    """

    aspects_list = _single_value(concepts.get("astrological_aspects"))

    if not isinstance(aspects_list, list):
        return None

    for item in aspects_list:
        pair = {item.get("body_a"), item.get("body_b")}

        if pair == {"sun", "moon"}:
            return item

    return None


# ------------------------------------------------------------
# Elemental balance (chart-derived, not environmental)
# ------------------------------------------------------------
#
# `strength` here is the elemental_balance concept's value: a
# {"fire": n, "earth": n, "air": n, "water": n} count of how many
# chart planets fall in a sign of each element (see
# astrology.elemental_balance.chart_elemental_balance).

def dominant_domains(strength, top=2):
    populated = {domain: count for domain, count in strength.items() if count > 0}

    if not populated:
        return []

    ranked = sorted(populated.items(), key=lambda item: (-item[1], item[0]))

    if not ranked:
        return []

    top_count = ranked[0][1]

    leading = [domain for domain, count in ranked if count == top_count]

    if len(leading) >= top:
        return leading

    return [domain for domain, _ in ranked[:top]]


# ------------------------------------------------------------
# Public entry point
# ------------------------------------------------------------

def build_features(concepts: dict[str, Any]) -> FeatureBundle:
    tags = _signal_tags(concepts)

    season = _single_value(concepts.get("season"))

    if season:
        tags.append(f"season:{season}")

    sabbat_info = _single_value(concepts.get("wheel_of_the_year_sabbat"))
    sabbat = None
    sabbat_days_away = None

    if isinstance(sabbat_info, dict):
        sabbat = sabbat_info.get("sabbat")
        sabbat_days_away = sabbat_info.get("days_away")

        if sabbat:
            tags.append(f"sabbat:{sabbat.lower()}")

    sun_longitude = _longitude(concepts.get("sun"))
    moon_longitude = _longitude(concepts.get("moon"))

    sun_sign = None
    moon_sign = None
    planet_signs = {}
    retrograde_planets = []

    sun_house = None
    moon_house = None
    planet_houses = {}

    sun_value = _single_value(concepts.get("sun"))

    if isinstance(sun_value, dict) and sun_value.get("sign"):
        sun_sign = sun_value["sign"]
        tags.append(f"sign:sun:{sun_sign}")

        if sun_value.get("house") is not None:
            sun_house = sun_value["house"]
            tags.append(f"house:sun:{sun_house}")

    moon_value = _single_value(concepts.get("moon"))

    if isinstance(moon_value, dict) and moon_value.get("sign"):
        moon_sign = moon_value["sign"]
        tags.append(f"sign:moon:{moon_sign}")

        if moon_value.get("house") is not None:
            moon_house = moon_value["house"]
            tags.append(f"house:moon:{moon_house}")

    planetary_value = _single_value(concepts.get("planetary_positions"))

    if isinstance(planetary_value, dict):
        for planet_name, body in planetary_value.items():
            if not isinstance(body, dict):
                continue

            if body.get("sign"):
                planet_signs[planet_name] = body["sign"]
                tags.append(f"sign:{planet_name}:{body['sign']}")

            if body.get("house") is not None:
                planet_houses[planet_name] = body["house"]
                tags.append(f"house:{planet_name}:{body['house']}")

            if body.get("retrograde"):
                retrograde_planets.append(planet_name)
                tags.append(f"retrograde:{planet_name}")

    phase_angle = None
    phase_name = None
    aspect = None
    aspect_orb = None
    aspect_strength = None

    if sun_longitude is not None and moon_longitude is not None:
        phase_angle = (moon_longitude - sun_longitude) % 360
        phase_name = _moon_phase_name(phase_angle)

        tags.append(f"moon_phase:{phase_name}")

        # Prefer the real, orb-aware aspect from the astrology engine
        # (astrological_aspects) when it's available; otherwise fall
        # back to the flat-orb approximation so this still works with
        # a plain Sun/Moon-longitude-only concept set.
        real_aspect = _real_sun_moon_aspect(concepts)

        if real_aspect:
            aspect = real_aspect.get("aspect")
            aspect_orb = real_aspect.get("orb")
            aspect_strength = real_aspect.get("orb_strength")
        else:
            separation = min(phase_angle, 360 - phase_angle)
            aspect = _sun_moon_aspect(separation)

        if aspect:
            tags.append(f"aspect:{aspect}")

    # Minor aspects (semisquare/sesquiquadrate/septile/novile) — only
    # present when the chart was built with include_minor_aspects=True
    # (astrology.chart.build_chart); tagged generically (presence
    # anywhere in the chart) rather than per Sun-Moon only, since
    # minor aspects are read across any body pair, not just the
    # luminaries.
    minor_aspects_present = set()

    all_aspects_list = _single_value(concepts.get("astrological_aspects"))

    if isinstance(all_aspects_list, list):
        minor_names = {"semisquare", "sesquiquadrate", "septile", "novile"}

        for item in all_aspects_list:
            aspect_name = item.get("aspect")

            if aspect_name in minor_names:
                minor_aspects_present.add(aspect_name)
                tags.append(f"minor_aspect:{aspect_name}")
                tags.append(
                    f"minor_aspect_pair:{item.get('body_a')}:"
                    f"{aspect_name}:{item.get('body_b')}"
                )

    # Declination aspects (parallel/contraparallel) — only present
    # when the chart was built with include_declinations=True.
    declination_aspects_present = set()

    declination_aspects_value = _single_value(concepts.get("declination_aspects"))

    if isinstance(declination_aspects_value, list):
        for item in declination_aspects_value:
            aspect_name = item.get("aspect")

            if not aspect_name:
                continue

            declination_aspects_present.add(aspect_name)
            tags.append(f"declination_aspect:{aspect_name}")
            tags.append(
                f"declination_aspect_pair:{item.get('body_a')}:"
                f"{aspect_name}:{item.get('body_b')}"
            )

    # Antiscia / contra-antiscia (Sun, Moon) — only present when the
    # chart was built with include_antiscia=True.
    antiscion_sun_sign = None
    antiscion_moon_sign = None

    antiscia_value = _single_value(concepts.get("antiscia"))

    if isinstance(antiscia_value, dict):
        for body_name, points in antiscia_value.items():
            if not isinstance(points, dict):
                continue

            antiscion = points.get("antiscion")
            contra = points.get("contra_antiscion")

            if isinstance(antiscion, dict) and antiscion.get("sign"):
                tags.append(f"antiscion:{body_name}:{antiscion['sign']}")

                if body_name == "sun":
                    antiscion_sun_sign = antiscion["sign"]
                elif body_name == "moon":
                    antiscion_moon_sign = antiscion["sign"]

            if isinstance(contra, dict) and contra.get("sign"):
                tags.append(f"contra_antiscion:{body_name}:{contra['sign']}")

    # Harmonic charts (5H/7H/9H) — only present when the chart was
    # built with include_harmonics=True. Tagged for Sun/Moon/
    # Ascendant only (the three points most commonly read in a
    # harmonic chart), generic across harmonics rather than one
    # FeatureBundle field per harmonic.
    harmonic_sun_signs = {}

    harmonic_charts_value = _single_value(concepts.get("harmonic_charts"))

    if isinstance(harmonic_charts_value, dict):
        for harmonic_n, chart in harmonic_charts_value.items():
            if not isinstance(chart, dict):
                continue

            harmonic_n = int(harmonic_n)
            harmonic_bodies = chart.get("bodies", {})
            harmonic_ascendant = chart.get("ascendant", {})

            for point_name, point in (
                ("sun", harmonic_bodies.get("sun")),
                ("moon", harmonic_bodies.get("moon")),
                ("ascendant", harmonic_ascendant),
            ):
                if isinstance(point, dict) and point.get("sign"):
                    tags.append(f"harmonic:{harmonic_n}:{point_name}:{point['sign']}")

                    if point_name == "sun":
                        harmonic_sun_signs[harmonic_n] = point["sign"]

            tags.append(f"harmonic_present:{harmonic_n}")

    # Aspect patterns + chart shape
    aspect_patterns_present = set()
    chart_shape = None

    chart_shape_value = _single_value(concepts.get("chart_shape"))

    if isinstance(chart_shape_value, dict) and chart_shape_value.get("shape"):
        chart_shape = chart_shape_value["shape"]
        tags.append(f"chart_shape:{chart_shape}")

    aspect_patterns_value = _single_value(concepts.get("aspect_patterns"))

    if isinstance(aspect_patterns_value, dict):
        _pattern_list_keys = {
            "grand_trines": "grand_trine",
            "t_squares": "t_square",
            "grand_crosses": "grand_cross",
            "yods": "yod",
            "kites": "kite",
            "mystic_rectangles": "mystic_rectangle",
            "stelliums": "stellium",
        }

        for list_key, pattern_name in _pattern_list_keys.items():
            entries = aspect_patterns_value.get(list_key)

            if not entries:
                continue

            aspect_patterns_present.add(pattern_name)
            tags.append(f"aspect_pattern:{pattern_name}")

            if pattern_name == "stellium":
                for entry in entries:
                    if entry.get("sign"):
                        tags.append(f"stellium_sign:{entry['sign']}")

    # Chart ruler + dispositor chains
    chart_ruler = None
    chart_ruler_house = None
    final_dispositor = None

    rulership_value = _single_value(concepts.get("rulership"))

    if isinstance(rulership_value, dict) and rulership_value.get("chart_ruler"):
        chart_ruler = rulership_value["chart_ruler"]
        chart_ruler_house = rulership_value.get("chart_ruler_house")
        final_dispositor = rulership_value.get("final_dispositor")

        tags.append(f"chart_ruler:{chart_ruler}")

        if chart_ruler_house is not None:
            tags.append(f"chart_ruler_house:{chart_ruler_house}")

        if final_dispositor:
            tags.append(f"final_dispositor:{final_dispositor}")
        else:
            tags.append("final_dispositor:none")

    # Structural findings — house concentrations, aspect-pattern
    # empty-leg matches, and declination relationships (reinforces
    # vs. genuinely new information relative to the longitude
    # aspects already tagged above).
    structural_findings_value = _single_value(concepts.get("structural_findings"))

    if isinstance(structural_findings_value, dict):
        for finding in structural_findings_value.get("house_concentrations", []):
            house = finding.get("house")

            if house is not None:
                tags.append(f"house_concentration:{house}")

        for finding in structural_findings_value.get("pattern_empty_leg_matches", []):
            pattern = finding.get("pattern")

            if pattern:
                tags.append(f"pattern_empty_leg_match:{pattern}")

        for finding in structural_findings_value.get("declination_relationships", []):
            relationship = finding.get("relationship")

            if relationship == "new_information":
                tags.append("declination_relationship:new_information")
            elif relationship == "reinforces":
                tags.append("declination_relationship:reinforces")

    ascendant_longitude = _single_value(concepts.get("ascendant"))
    ascendant_sign = None

    if isinstance(ascendant_longitude, (int, float)):
        ascendant_sign = longitude_to_zodiac(ascendant_longitude)["sign"]
        tags.append(f"ascendant:{ascendant_sign}")

    # Vertex — a calculated point (ecliptic x prime vertical), not a
    # body; astrology/chart.py already resolves sign/house for it.
    vertex_sign = None
    vertex_house = None

    vertex_value = _single_value(concepts.get("vertex"))

    if isinstance(vertex_value, dict) and vertex_value.get("sign"):
        vertex_sign = vertex_value["sign"]
        vertex_house = vertex_value.get("house")
        tags.append(f"vertex:{vertex_sign}")

        if vertex_house is not None:
            tags.append(f"vertex_house:{vertex_house}")

    # Arabic Parts (Part of Fortune / Part of Spirit) — sect-aware
    # points, not new ephemeris bodies; see astrology/arabic_parts.py.
    day_chart = None
    fortune_sign = None
    fortune_house = None
    spirit_sign = None
    spirit_house = None

    fortune_value = _single_value(concepts.get("part_of_fortune"))

    if isinstance(fortune_value, dict) and fortune_value.get("sign"):
        day_chart = fortune_value.get("day_chart")
        fortune_sign = fortune_value["sign"]
        fortune_house = fortune_value.get("house")
        tags.append(f"sign:fortune:{fortune_sign}")

        if fortune_house is not None:
            tags.append(f"house:fortune:{fortune_house}")

        tags.append(f"sect:{'day' if day_chart else 'night'}")

    spirit_value = _single_value(concepts.get("part_of_spirit"))

    if isinstance(spirit_value, dict) and spirit_value.get("sign"):
        if day_chart is None:
            day_chart = spirit_value.get("day_chart")

        spirit_sign = spirit_value["sign"]
        spirit_house = spirit_value.get("house")
        tags.append(f"sign:spirit:{spirit_sign}")

        if spirit_house is not None:
            tags.append(f"house:spirit:{spirit_house}")

    # The five additional Hermetic (Panaretos) Lots — Eros, Necessity,
    # Courage, Victory, Nemesis. Sign/house tagged generically like
    # Fortune/Spirit; no dedicated FeatureBundle fields since these
    # are read individually via tags rather than combined narrative.
    for _lot_key in ("eros", "necessity", "courage", "victory", "nemesis"):
        _lot_value = _single_value(concepts.get(f"part_of_{_lot_key}"))

        if isinstance(_lot_value, dict) and _lot_value.get("sign"):
            tags.append(f"sign:{_lot_key}:{_lot_value['sign']}")

            if _lot_value.get("house") is not None:
                tags.append(f"house:{_lot_key}:{_lot_value['house']}")

    # Vedic (sidereal) placements — same sign:/house: tag shapes as
    # tropical, prefixed vedic_sign:/vedic_house:, plus nakshatra
    # tags that have no tropical equivalent.
    vedic_sun_sign = None
    vedic_moon_sign = None
    vedic_ascendant_sign = None
    vedic_planet_signs = {}

    vedic_sun_nakshatra = None
    vedic_moon_nakshatra = None
    vedic_ascendant_nakshatra = None
    vedic_planet_nakshatras = {}

    vedic_sun_house = None
    vedic_moon_house = None
    vedic_planet_houses = {}

    def _tag_vedic_point(body_name, point):
        tags.append(f"vedic_sign:{body_name}:{point['sign']}")
        tags.append(f"nakshatra:{body_name}:{point['nakshatra']}")
        tags.append(f"nakshatra_pada:{body_name}:{point['nakshatra_pada']}")

        if point.get("house") is not None:
            tags.append(f"vedic_house:{body_name}:{point['house']}")

    vedic_sun_value = _single_value(concepts.get("vedic_sun"))

    if isinstance(vedic_sun_value, dict) and vedic_sun_value.get("sign"):
        vedic_sun_sign = vedic_sun_value["sign"]
        vedic_sun_nakshatra = vedic_sun_value.get("nakshatra")
        vedic_sun_house = vedic_sun_value.get("house")
        _tag_vedic_point("sun", vedic_sun_value)

    vedic_moon_value = _single_value(concepts.get("vedic_moon"))

    if isinstance(vedic_moon_value, dict) and vedic_moon_value.get("sign"):
        vedic_moon_sign = vedic_moon_value["sign"]
        vedic_moon_nakshatra = vedic_moon_value.get("nakshatra")
        vedic_moon_house = vedic_moon_value.get("house")
        _tag_vedic_point("moon", vedic_moon_value)

    vedic_ascendant_value = _single_value(concepts.get("vedic_ascendant"))

    if isinstance(vedic_ascendant_value, dict) and vedic_ascendant_value.get("sign"):
        vedic_ascendant_sign = vedic_ascendant_value["sign"]
        vedic_ascendant_nakshatra = vedic_ascendant_value.get("nakshatra")
        _tag_vedic_point("ascendant", vedic_ascendant_value)

    vedic_planetary_value = _single_value(concepts.get("vedic_positions"))

    if isinstance(vedic_planetary_value, dict):
        for planet_name, body in vedic_planetary_value.items():
            if not isinstance(body, dict) or not body.get("sign"):
                continue

            vedic_planet_signs[planet_name] = body["sign"]
            vedic_planet_nakshatras[planet_name] = body.get("nakshatra")

            if body.get("house") is not None:
                vedic_planet_houses[planet_name] = body["house"]

            _tag_vedic_point(planet_name, body)

    # Navamsa (D9 divisional chart) — its own sign:/house: tag shapes,
    # prefixed navamsa_sign:/navamsa_house: since D9 has its own house
    # wheel counted from its own D9 Ascendant, distinct from the D1
    # sidereal houses above.
    navamsa_sun_sign = None
    navamsa_moon_sign = None
    navamsa_ascendant_sign = None
    navamsa_planet_signs = {}

    def _tag_navamsa_point(body_name, point):
        tags.append(f"navamsa_sign:{body_name}:{point['sign']}")

        if point.get("house") is not None:
            tags.append(f"navamsa_house:{body_name}:{point['house']}")

    navamsa_sun_value = _single_value(concepts.get("navamsa_sun"))

    if isinstance(navamsa_sun_value, dict) and navamsa_sun_value.get("sign"):
        navamsa_sun_sign = navamsa_sun_value["sign"]
        _tag_navamsa_point("sun", navamsa_sun_value)

    navamsa_moon_value = _single_value(concepts.get("navamsa_moon"))

    if isinstance(navamsa_moon_value, dict) and navamsa_moon_value.get("sign"):
        navamsa_moon_sign = navamsa_moon_value["sign"]
        _tag_navamsa_point("moon", navamsa_moon_value)

    navamsa_ascendant_value = _single_value(concepts.get("navamsa_ascendant"))

    if isinstance(navamsa_ascendant_value, dict) and navamsa_ascendant_value.get("sign"):
        navamsa_ascendant_sign = navamsa_ascendant_value["sign"]
        _tag_navamsa_point("ascendant", navamsa_ascendant_value)

    navamsa_planetary_value = _single_value(concepts.get("navamsa_positions"))

    if isinstance(navamsa_planetary_value, dict):
        for planet_name, body in navamsa_planetary_value.items():
            if not isinstance(body, dict) or not body.get("sign"):
                continue

            navamsa_planet_signs[planet_name] = body["sign"]
            _tag_navamsa_point(planet_name, body)

    # Remaining Shodasavarga divisional charts (D2, D3, D4, D7, D10,
    # D12, D16, D20, D24, D27, D30, D40, D45, D60) — one generic
    # concept (astrology.varga.build_all_vargas' output) rather than
    # per-chart concepts, same reasoning as the harmonic-chart block
    # above. Tagged for Sun/Moon/Ascendant only, same scope as
    # harmonics; varga:{n}:{body}:{sign} tags are matched by the
    # existing Vedic sign-meaning claims (extended to cover them),
    # reusing content the same way navamsa_sign: already does.
    varga_ascendant_signs = {}

    vedic_vargas_value = _single_value(concepts.get("vedic_vargas"))

    if isinstance(vedic_vargas_value, dict):
        for varga_n, chart in vedic_vargas_value.items():
            if not isinstance(chart, dict):
                continue

            varga_n = int(varga_n)
            varga_bodies = chart.get("bodies", {})
            varga_ascendant = chart.get("ascendant", {})

            for point_name, point in (
                ("sun", varga_bodies.get("sun")),
                ("moon", varga_bodies.get("moon")),
                ("ascendant", varga_ascendant),
            ):
                if isinstance(point, dict) and point.get("sign"):
                    tags.append(f"varga:{varga_n}:{point_name}:{point['sign']}")

                    if point_name == "ascendant":
                        varga_ascendant_signs[varga_n] = point["sign"]

            tags.append(f"varga_present:{varga_n}")

    # Vedic structural findings — bhava concentrations and Vargottama
    # (astrology.vedic_structural_findings' output), the sidereal
    # counterpart to the Western structural-findings tags above.
    vedic_structural_findings_value = _single_value(concepts.get("vedic_structural_findings"))

    if isinstance(vedic_structural_findings_value, dict):
        for finding in vedic_structural_findings_value.get("bhava_concentrations", []):
            house = finding.get("house")

            if house is not None:
                tags.append(f"bhava_concentration:{house}")

        for finding in vedic_structural_findings_value.get("vargottama", []):
            if finding.get("is_dusthana"):
                tags.append("vargottama:dusthana")
            else:
                tags.append("vargottama:favorable")

    # Vedic planetary dignity + Baladi Avastha (astrology.dignity's
    # output: {planet: {"dignity": ..., "avastha": ...}}). Body-
    # agnostic tags, matched the same way sign/nakshatra/bhava claims
    # already are. Exalted/debilitated planet lists are tracked
    # separately since they're the two narratively strongest states,
    # worth a direct structural note.
    exalted_planets = []
    debilitated_planets = []

    vedic_dignity_value = _single_value(concepts.get("vedic_dignity"))

    if isinstance(vedic_dignity_value, dict):
        for planet_name, info in vedic_dignity_value.items():
            if not isinstance(info, dict):
                continue

            dignity = info.get("dignity")
            avastha = info.get("avastha")

            if dignity:
                tags.append(f"dignity:{planet_name}:{dignity}")

                if dignity == "exalted":
                    exalted_planets.append(planet_name)
                elif dignity == "debilitated":
                    debilitated_planets.append(planet_name)

            if avastha:
                tags.append(f"avastha:{planet_name}:{avastha}")

    # Jaimini Chara Karakas (astrology.jaimini's output: {karaka_name:
    # {"planet": ..., "degree_in_sign": ...}}). Atmakaraka is tracked
    # separately as the single most consulted rank in Jaimini technique.
    atmakaraka_planet = None

    vedic_karakas_value = _single_value(concepts.get("vedic_karakas"))

    if isinstance(vedic_karakas_value, dict):
        for karaka_name, info in vedic_karakas_value.items():
            if not isinstance(info, dict) or not info.get("planet"):
                continue

            tags.append(f"karaka:{karaka_name}:{info['planet']}")

            if karaka_name == "Atmakaraka":
                atmakaraka_planet = info["planet"]

    # Marak (2nd/7th lord) planets — astrology.jaimini's output: a
    # flat list of planet names, can be empty (Dwi Marak Na Marak).
    marak_planets = []

    vedic_marak_value = _single_value(concepts.get("vedic_marak"))

    if isinstance(vedic_marak_value, list):
        for planet_name in vedic_marak_value:
            if not planet_name:
                continue

            marak_planets.append(planet_name)
            tags.append(f"marak:{planet_name}")

    # Ashtakavarga (astrology.ashtakavarga's output). Own-sign Bindu
    # strength (a planet's Bhinnashtakavarga score in the sign it
    # currently occupies) uses the standard classical threshold: 0-3
    # weak, 4 medium, 5-8 strong. Sarvashtakavarga strength (a sign's
    # combined score) uses the standard threshold: <25 weak, 25-28
    # medium, >28 strong. Scoped to Sun/Moon/Ascendant for
    # Sarvashtakavarga, same convention as harmonics/vargas above.
    ashtakavarga_own_sign_strength = {}
    sarvashtakavarga_strength = {}

    ashtakavarga_value = _single_value(concepts.get("vedic_ashtakavarga"))

    if isinstance(ashtakavarga_value, dict):
        bhinnashtakavarga = ashtakavarga_value.get("bhinnashtakavarga", {})
        sarvashtakavarga = ashtakavarga_value.get("sarvashtakavarga", {})

        _all_vedic_planet_signs = dict(vedic_planet_signs)
        if vedic_sun_sign:
            _all_vedic_planet_signs["sun"] = vedic_sun_sign
        if vedic_moon_sign:
            _all_vedic_planet_signs["moon"] = vedic_moon_sign

        for planet_name, own_sign in _all_vedic_planet_signs.items():
            scores = bhinnashtakavarga.get(planet_name)
            if not isinstance(scores, dict) or own_sign not in scores:
                continue

            bindus = scores[own_sign]
            if bindus <= 3:
                strength = "weak"
            elif bindus == 4:
                strength = "medium"
            else:
                strength = "strong"

            ashtakavarga_own_sign_strength[planet_name] = strength
            tags.append(f"ashtakavarga_own_sign:{planet_name}:{strength}")

        for point_name, sign in (
            ("sun", vedic_sun_sign),
            ("moon", vedic_moon_sign),
            ("ascendant", vedic_ascendant_sign),
        ):
            if not sign or sign not in sarvashtakavarga:
                continue

            bindus = sarvashtakavarga[sign]
            if bindus < 25:
                strength = "weak"
            elif bindus <= 28:
                strength = "medium"
            else:
                strength = "strong"

            sarvashtakavarga_strength[point_name] = strength
            tags.append(f"sarvashtakavarga:{point_name}:{strength}")

    # Shadbala (partial) — astrology.shadbala's output. Only the
    # relative strongest/weakest planet by the well-verified subset
    # of components is surfaced (see astrology/shadbala.py's module
    # docstring for what's excluded and why) -- deliberately not a
    # true Shadbala grand total or Rashmana-threshold comparison.
    shadbala_strongest_planet = None
    shadbala_weakest_planet = None

    shadbala_value = _single_value(concepts.get("vedic_shadbala"))

    if isinstance(shadbala_value, dict) and shadbala_value:
        _ranked = sorted(
            (
                (planet, scores["partial_total"])
                for planet, scores in shadbala_value.items()
                if isinstance(scores, dict) and "partial_total" in scores
            ),
            key=lambda item: item[1],
        )
        if _ranked:
            shadbala_weakest_planet = _ranked[0][0]
            shadbala_strongest_planet = _ranked[-1][0]
            tags.append(f"shadbala_strongest:{shadbala_strongest_planet}")
            tags.append(f"shadbala_weakest:{shadbala_weakest_planet}")

    # Vedic yogas (classical planetary combinations) — a flat list of
    # whichever yogas from the curated set (astrology/yogas.py) are
    # present in this chart; can be empty.
    vedic_yogas = []

    yogas_value = _single_value(concepts.get("vedic_yogas"))

    if isinstance(yogas_value, list):
        for yoga in yogas_value:
            if not isinstance(yoga, dict) or not yoga.get("id"):
                continue

            vedic_yogas.append(yoga["id"])
            tags.append(f"yoga:{yoga['id']}")

    # Vimshottari Dasha — optional, only present when the CLI was
    # given --as-of-date/--as-of-time.
    has_dasha = False
    dasha_mahadasha_lord = None
    dasha_antardasha_lord = None

    dasha_value = _single_value(concepts.get("vedic_dasha"))

    if isinstance(dasha_value, dict) and dasha_value.get("current_mahadasha"):
        has_dasha = True
        dasha_mahadasha_lord = dasha_value["current_mahadasha"].get("lord")
        tags.append(f"dasha_mahadasha:{dasha_mahadasha_lord}")

        current_antardasha = dasha_value.get("current_antardasha")
        if isinstance(current_antardasha, dict):
            dasha_antardasha_lord = current_antardasha.get("lord")
            tags.append(f"dasha_antardasha:{dasha_antardasha_lord}")

        current_pratyantardasha = dasha_value.get("current_pratyantardasha")
        if isinstance(current_pratyantardasha, dict) and current_pratyantardasha.get("lord"):
            tags.append(f"dasha_pratyantardasha:{current_pratyantardasha['lord']}")

        current_sookshma = dasha_value.get("current_sookshma_dasha")
        if isinstance(current_sookshma, dict) and current_sookshma.get("lord"):
            tags.append(f"dasha_sookshma:{current_sookshma['lord']}")

    # Yogini Dasha — a distinct 36-year timing cycle, also optional
    # and --as-of-dependent.
    has_yogini_dasha = False
    yogini_dasha_current = None

    yogini_dasha_value = _single_value(concepts.get("vedic_yogini_dasha"))

    if isinstance(yogini_dasha_value, dict) and yogini_dasha_value.get("current_yogini_dasha"):
        has_yogini_dasha = True
        yogini_dasha_current = yogini_dasha_value["current_yogini_dasha"].get("yogini")
        tags.append(f"yogini_dasha:{yogini_dasha_current}")

    # Chara Dasha (Jaimini) — sign-based, also optional and
    # --as-of-dependent.
    has_chara_dasha = False
    chara_dasha_current_sign = None

    chara_dasha_value = _single_value(concepts.get("vedic_chara_dasha"))

    if isinstance(chara_dasha_value, dict) and chara_dasha_value.get("current_sign_dasha"):
        has_chara_dasha = True
        chara_dasha_current_sign = chara_dasha_value["current_sign_dasha"].get("sign")
        tags.append(f"chara_dasha_sign:{chara_dasha_current_sign}")

    # Chinese (BaZi) Four Pillars. No sign/house tags — BaZi has
    # neither; see chinese/pillars.py's module docstring.
    chinese_day_master = None
    chinese_day_master_element = None
    chinese_year_animal = None
    chinese_pillar_names = {}

    chinese_value = _single_value(concepts.get("chinese_pillars"))

    if isinstance(chinese_value, dict) and chinese_value.get("day_master"):
        chinese_day_master = chinese_value["day_master"]
        chinese_day_master_element = chinese_value.get("day_master_element")

        tags.append(f"chinese_day_master:{chinese_day_master}")
        tags.append(f"chinese_day_master_element:{chinese_day_master_element}")

        for position in ("year", "month", "day", "hour"):
            pillar = chinese_value.get(position)

            if not isinstance(pillar, dict):
                continue

            chinese_pillar_names[position] = pillar.get("name")
            tags.append(f"chinese_pillar_position:{position}")
            tags.append(f"chinese_pillar:{position}:{pillar.get('name')}")
            tags.append(f"chinese_stem:{position}:{pillar.get('stem')}")
            tags.append(f"chinese_branch:{position}:{pillar.get('branch')}")
            tags.append(f"chinese_element:{pillar.get('stem_element')}")

            if position == "year":
                chinese_year_animal = pillar.get("branch_animal")
                tags.append(f"chinese_year_animal:{chinese_year_animal}")

    # Chinese Ten Gods (Shi Shen) — classification of every visible
    # (non-Day) and hidden stem relative to the Day Master.
    chinese_ten_gods = []

    def _slug(name):
        return name.lower().replace(" ", "_")

    ten_gods_value = _single_value(concepts.get("chinese_ten_gods"))

    if isinstance(ten_gods_value, dict):
        for position, info in ten_gods_value.get("stems", {}).items():
            ten_god = info.get("ten_god")

            if not ten_god:
                continue

            chinese_ten_gods.append(ten_god)
            tags.append(f"ten_god:{position}:{_slug(ten_god)}")

        for position, entries in ten_gods_value.get("hidden_stems", {}).items():
            for entry in entries:
                stem = entry.get("stem")
                ten_god = entry.get("ten_god")

                if stem:
                    tags.append(f"chinese_hidden_stem:{position}:{stem}")

                if ten_god:
                    chinese_ten_gods.append(ten_god)
                    tags.append(f"ten_god_hidden:{position}:{_slug(ten_god)}")

    # Chinese structural findings — repeated Ten Gods and Guan Sha
    # Hun Za (chinese.structural_findings' output).
    chinese_structural_findings_value = _single_value(concepts.get("chinese_structural_findings"))

    if isinstance(chinese_structural_findings_value, dict):
        for finding in chinese_structural_findings_value.get("repeated_ten_gods", []):
            ten_god = finding.get("ten_god")

            if ten_god:
                tags.append(f"repeated_ten_god:{_slug(ten_god)}")

        if chinese_structural_findings_value.get("guan_sha_hun_za"):
            tags.append("guan_sha_hun_za:present")

    # Da Yun (Luck Pillars) — optional, only present when the CLI was
    # given --as-of-date/--as-of-time AND --gender.
    has_dayun = False
    dayun_current_pillar = None

    dayun_value = _single_value(concepts.get("chinese_dayun"))

    if isinstance(dayun_value, dict) and dayun_value.get("current_pillar"):
        has_dayun = True
        current = dayun_value["current_pillar"]["pillar"]
        dayun_current_pillar = current.get("name")

        tags.append(f"chinese_dayun_stem:{current.get('stem')}")
        tags.append(f"chinese_dayun_branch:{current.get('branch')}")
        tags.append(f"dayun_direction:{dayun_value.get('direction')}")

    # Liu Nian (annual pillar) — optional, only present when the CLI
    # was given --as-of-date/--as-of-time.
    has_liu_nian = False
    liu_nian_pillar_name = None

    liu_nian_value = _single_value(concepts.get("chinese_liu_nian"))

    if isinstance(liu_nian_value, dict) and liu_nian_value.get("pillar"):
        has_liu_nian = True
        pillar = liu_nian_value["pillar"]
        liu_nian_pillar_name = pillar.get("name")

        tags.append(f"chinese_liu_nian_stem:{pillar.get('stem')}")
        tags.append(f"chinese_liu_nian_branch:{pillar.get('branch')}")

    # Shen Sha (symbolic stars) — chinese.shen_sha's output: a flat
    # list of star dicts, can be empty.
    chinese_shen_sha_present = []

    shen_sha_value = _single_value(concepts.get("chinese_shen_sha"))

    if isinstance(shen_sha_value, list):
        for star in shen_sha_value:
            if not isinstance(star, dict) or not star.get("id"):
                continue

            chinese_shen_sha_present.append(star["id"])
            tags.append(f"shen_sha:{star['id']}")

    # Na Yin — chinese.na_yin's output: {pillar_role: {name, gloss,
    # element}}. Day Pillar's Na Yin element is tracked separately as
    # the most commonly consulted single value (the Day Master's own
    # Na Yin, describing the person's core element through this
    # older, sound-derived lens rather than the stem's own element).
    chinese_na_yin_day_element = None

    na_yin_value = _single_value(concepts.get("chinese_na_yin"))

    if isinstance(na_yin_value, dict):
        for role, entry in na_yin_value.items():
            if not isinstance(entry, dict) or not entry.get("element"):
                continue

            tags.append(f"na_yin_element:{role}:{entry['element']}")

            if role == "day":
                chinese_na_yin_day_element = entry["element"]

    # Chinese stem/branch interactions (chinese.interactions' output)
    # — presence tags per interaction category, generic across which
    # specific pair/pillars are involved (the specific stems/branches
    # are already covered by the chinese_stem:/chinese_branch: tags
    # above).
    chinese_interactions_present = []

    interactions_value = _single_value(concepts.get("chinese_interactions"))

    if isinstance(interactions_value, dict):
        for category, items in interactions_value.items():
            if not items:
                continue

            if category == "punishments":
                for item in items:
                    punishment_id = item.get("id")
                    if punishment_id:
                        chinese_interactions_present.append(punishment_id)
                        tags.append(f"chinese_punishment:{punishment_id}")
                continue

            chinese_interactions_present.append(category)
            tags.append(f"chinese_interaction:{category}")

    # Chinese elemental balance (chinese.elemental_balance's output)
    # — missing/dominant/weakest-present elements, chart-relative.
    chinese_missing_elements = []
    chinese_dominant_elements = []

    elemental_balance_value = _single_value(concepts.get("chinese_elemental_balance"))

    if isinstance(elemental_balance_value, dict):
        chinese_missing_elements = list(elemental_balance_value.get("missing_elements", []))
        chinese_dominant_elements = list(elemental_balance_value.get("dominant_elements", []))

        for element in chinese_missing_elements:
            tags.append(f"chinese_element_missing:{element}")

        for element in chinese_dominant_elements:
            tags.append(f"chinese_element_dominant:{element}")

        for element in elemental_balance_value.get("weakest_present_elements", []):
            tags.append(f"chinese_element_weakest:{element}")

    # Transits and secondary progressions — both optional, only
    # present when the CLI was given --as-of-date/--as-of-time.
    has_transits = False
    transit_signs = {}
    transit_houses = {}
    transit_retrograde = []

    transits_value = _single_value(concepts.get("current_transits"))

    if isinstance(transits_value, dict) and transits_value.get("bodies"):
        has_transits = True

        for body_name, body in transits_value["bodies"].items():
            if not isinstance(body, dict) or not body.get("sign"):
                continue

            transit_signs[body_name] = body["sign"]
            tags.append(f"transit_sign:{body_name}:{body['sign']}")

            if body.get("natal_house") is not None:
                transit_houses[body_name] = body["natal_house"]
                tags.append(f"transit_house:{body_name}:{body['natal_house']}")

            if body.get("retrograde"):
                transit_retrograde.append(body_name)
                tags.append(f"transit_retrograde:{body_name}")

        for item in transits_value.get("aspects", []):
            aspect = item.get("aspect")

            if not aspect:
                continue

            tags.append(f"transit_aspect:{aspect}")
            tags.append(
                f"transit_aspect_pair:{item.get('transiting_body')}:"
                f"{aspect}:{item.get('natal_body')}"
            )

    has_progressions = False
    progressed_signs = {}
    progressed_houses = {}
    progressed_moon_sign = None

    progressions_value = _single_value(concepts.get("secondary_progressions"))

    if isinstance(progressions_value, dict) and progressions_value.get("bodies"):
        has_progressions = True

        for body_name, body in progressions_value["bodies"].items():
            if not isinstance(body, dict) or not body.get("sign"):
                continue

            progressed_signs[body_name] = body["sign"]
            tags.append(f"progressed_sign:{body_name}:{body['sign']}")

            if body_name == "moon":
                progressed_moon_sign = body["sign"]
                tags.append(f"progressed_moon_sign:{body['sign']}")

            if body.get("natal_house") is not None:
                progressed_houses[body_name] = body["natal_house"]
                tags.append(
                    f"progressed_house:{body_name}:{body['natal_house']}"
                )

        for item in progressions_value.get("aspects", []):
            aspect = item.get("aspect")

            if not aspect:
                continue

            tags.append(f"progression_aspect:{aspect}")
            tags.append(
                f"progression_aspect_pair:{item.get('progressed_body')}:"
                f"{aspect}:{item.get('natal_body')}"
            )

    has_tertiary = False
    tertiary_moon_sign = None

    tertiary_value = _single_value(concepts.get("tertiary_progressions"))

    if isinstance(tertiary_value, dict) and tertiary_value.get("bodies"):
        has_tertiary = True

        for body_name, body in tertiary_value["bodies"].items():
            if not isinstance(body, dict) or not body.get("sign"):
                continue

            tags.append(f"tertiary_sign:{body_name}:{body['sign']}")

            if body_name == "moon":
                tertiary_moon_sign = body["sign"]
                tags.append(f"tertiary_moon_sign:{body['sign']}")

            if body.get("natal_house") is not None:
                tags.append(f"tertiary_house:{body_name}:{body['natal_house']}")

        for item in tertiary_value.get("aspects", []):
            aspect = item.get("aspect")

            if not aspect:
                continue

            tags.append(f"tertiary_aspect:{aspect}")

    star_conjunction_body = None
    star_conjunction_star = None
    star_conjunction_orb = None
    star_conjunction_magnitude = None

    conjunctions = _single_value(concepts.get("fixed_star_conjunctions"))

    if isinstance(conjunctions, list) and conjunctions:
        # Already sorted tightest-first by find_star_conjunctions().
        tightest = conjunctions[0]
        star_conjunction_body = tightest.get("body")
        star_conjunction_star = tightest.get("star")
        star_conjunction_orb = tightest.get("orb")
        star_conjunction_magnitude = tightest.get("star_magnitude")

        # Tag EVERY conjunction, not just the single tightest overall —
        # a documented star (e.g. Regulus) should be able to match a
        # claim even when some other, undocumented star happens to be
        # marginally tighter for a different body.
        for item in conjunctions:
            body = item.get("body")
            star = item.get("star")

            if body and star:
                star_slug = star.lower().replace(" ", "_")
                tags.append(f"star_conjunction:{body}:{star_slug}")

    strength = _single_value(concepts.get("elemental_balance")) or {}
    dominant = dominant_domains(strength)

    for domain in dominant:
        tags.append(f"element_dominant:{domain}")

    return FeatureBundle(
        tags=tags,
        season=season,
        sabbat=sabbat,
        sabbat_days_away=sabbat_days_away,
        sun_longitude=sun_longitude,
        moon_longitude=moon_longitude,
        moon_phase_angle=phase_angle,
        moon_phase_name=phase_name,
        sun_moon_aspect=aspect,
        sun_moon_aspect_orb=aspect_orb,
        sun_moon_aspect_strength=aspect_strength,
        ascendant_longitude=ascendant_longitude,
        ascendant_sign=ascendant_sign,
        vertex_sign=vertex_sign,
        vertex_house=vertex_house,
        minor_aspects_present=minor_aspects_present,
        declination_aspects_present=declination_aspects_present,
        antiscion_sun_sign=antiscion_sun_sign,
        antiscion_moon_sign=antiscion_moon_sign,
        chart_ruler=chart_ruler,
        chart_ruler_house=chart_ruler_house,
        final_dispositor=final_dispositor,
        aspect_patterns_present=aspect_patterns_present,
        chart_shape=chart_shape,
        harmonic_sun_signs=harmonic_sun_signs,
        day_chart=day_chart,
        fortune_sign=fortune_sign,
        fortune_house=fortune_house,
        spirit_sign=spirit_sign,
        spirit_house=spirit_house,
        sun_sign=sun_sign,
        moon_sign=moon_sign,
        planet_signs=planet_signs,
        retrograde_planets=retrograde_planets,
        sun_house=sun_house,
        moon_house=moon_house,
        planet_houses=planet_houses,
        star_conjunction_body=star_conjunction_body,
        star_conjunction_star=star_conjunction_star,
        star_conjunction_orb=star_conjunction_orb,
        star_conjunction_magnitude=star_conjunction_magnitude,
        elemental_strength=strength,
        dominant_domains=dominant,
        vedic_sun_sign=vedic_sun_sign,
        vedic_moon_sign=vedic_moon_sign,
        vedic_ascendant_sign=vedic_ascendant_sign,
        vedic_planet_signs=vedic_planet_signs,
        vedic_sun_nakshatra=vedic_sun_nakshatra,
        vedic_moon_nakshatra=vedic_moon_nakshatra,
        vedic_ascendant_nakshatra=vedic_ascendant_nakshatra,
        vedic_planet_nakshatras=vedic_planet_nakshatras,
        vedic_sun_house=vedic_sun_house,
        vedic_moon_house=vedic_moon_house,
        vedic_planet_houses=vedic_planet_houses,
        navamsa_sun_sign=navamsa_sun_sign,
        navamsa_moon_sign=navamsa_moon_sign,
        navamsa_ascendant_sign=navamsa_ascendant_sign,
        navamsa_planet_signs=navamsa_planet_signs,
        varga_ascendant_signs=varga_ascendant_signs,
        exalted_planets=exalted_planets,
        debilitated_planets=debilitated_planets,
        atmakaraka_planet=atmakaraka_planet,
        marak_planets=marak_planets,
        ashtakavarga_own_sign_strength=ashtakavarga_own_sign_strength,
        sarvashtakavarga_strength=sarvashtakavarga_strength,
        shadbala_strongest_planet=shadbala_strongest_planet,
        shadbala_weakest_planet=shadbala_weakest_planet,
        vedic_yogas=vedic_yogas,
        has_dasha=has_dasha,
        dasha_mahadasha_lord=dasha_mahadasha_lord,
        dasha_antardasha_lord=dasha_antardasha_lord,
        has_yogini_dasha=has_yogini_dasha,
        yogini_dasha_current=yogini_dasha_current,
        has_chara_dasha=has_chara_dasha,
        chara_dasha_current_sign=chara_dasha_current_sign,
        chinese_day_master=chinese_day_master,
        chinese_day_master_element=chinese_day_master_element,
        chinese_year_animal=chinese_year_animal,
        chinese_pillar_names=chinese_pillar_names,
        chinese_ten_gods=chinese_ten_gods,
        has_liu_nian=has_liu_nian,
        liu_nian_pillar_name=liu_nian_pillar_name,
        chinese_shen_sha_present=chinese_shen_sha_present,
        chinese_na_yin_day_element=chinese_na_yin_day_element,
        chinese_interactions_present=chinese_interactions_present,
        chinese_missing_elements=chinese_missing_elements,
        chinese_dominant_elements=chinese_dominant_elements,
        has_dayun=has_dayun,
        dayun_current_pillar=dayun_current_pillar,
        has_transits=has_transits,
        transit_signs=transit_signs,
        transit_houses=transit_houses,
        transit_retrograde=transit_retrograde,
        has_progressions=has_progressions,
        progressed_signs=progressed_signs,
        progressed_houses=progressed_houses,
        progressed_moon_sign=progressed_moon_sign,
        has_tertiary=has_tertiary,
        tertiary_moon_sign=tertiary_moon_sign,
    )


if __name__ == "__main__":
    concepts = {
        "sun": {
            "observations": [
                {"value": {"longitude": 119.596}, "source": "astronomy"}
            ]
        },
        "moon": {
            "observations": [
                {"value": {"longitude": 209.6}, "source": "astronomy"}
            ]
        },
        "temperature": {
            "observations": [{"value": 8.0, "source": "atmosphere"}]
        },
        "elemental_balance": {
            "observations": [
                {
                    "value": {"fire": 3, "earth": 2, "air": 4, "water": 1},
                    "source": "astrology.elemental_balance",
                }
            ]
        },
    }

    features = build_features(concepts)

    print("Tags:", features.tags)
    print("Moon phase:", features.moon_phase_name)
    print("Aspect:", features.sun_moon_aspect)
    print("Dominant domains:", features.dominant_domains)

    assert features.moon_phase_name is not None
    assert "temperature:cool" in features.tags

    print("features.py: OK")
