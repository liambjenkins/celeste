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

    chinese_day_master: Optional[str] = None
    chinese_day_master_element: Optional[str] = None
    chinese_year_animal: Optional[str] = None
    chinese_pillar_names: dict[str, str] = field(default_factory=dict)


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

    ascendant_longitude = _single_value(concepts.get("ascendant"))
    ascendant_sign = None

    if isinstance(ascendant_longitude, (int, float)):
        ascendant_sign = longitude_to_zodiac(ascendant_longitude)["sign"]
        tags.append(f"ascendant:{ascendant_sign}")

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
        chinese_day_master=chinese_day_master,
        chinese_day_master_element=chinese_day_master_element,
        chinese_year_animal=chinese_year_animal,
        chinese_pillar_names=chinese_pillar_names,
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
