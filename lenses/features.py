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

    sun_longitude: Optional[float] = None
    moon_longitude: Optional[float] = None
    moon_phase_angle: Optional[float] = None
    moon_phase_name: Optional[str] = None
    sun_moon_aspect: Optional[str] = None
    sun_moon_aspect_orb: Optional[float] = None
    sun_moon_aspect_strength: Optional[str] = None

    ascendant_longitude: Optional[float] = None
    ascendant_sign: Optional[str] = None

    star_conjunction_body: Optional[str] = None
    star_conjunction_star: Optional[str] = None
    star_conjunction_orb: Optional[float] = None
    star_conjunction_magnitude: Optional[float] = None

    elemental_strength: dict[str, int] = field(default_factory=dict)
    dominant_domains: list[str] = field(default_factory=list)


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

    sun_longitude = _longitude(concepts.get("sun"))
    moon_longitude = _longitude(concepts.get("moon"))

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

        if star_conjunction_body and star_conjunction_star:
            star_slug = star_conjunction_star.lower().replace(" ", "_")
            tags.append(
                f"star_conjunction:{star_conjunction_body}:{star_slug}"
            )

    strength = _single_value(concepts.get("elemental_balance")) or {}
    dominant = dominant_domains(strength)

    for domain in dominant:
        tags.append(f"element_dominant:{domain}")

    return FeatureBundle(
        tags=tags,
        season=season,
        sun_longitude=sun_longitude,
        moon_longitude=moon_longitude,
        moon_phase_angle=phase_angle,
        moon_phase_name=phase_name,
        sun_moon_aspect=aspect,
        sun_moon_aspect_orb=aspect_orb,
        sun_moon_aspect_strength=aspect_strength,
        ascendant_longitude=ascendant_longitude,
        ascendant_sign=ascendant_sign,
        star_conjunction_body=star_conjunction_body,
        star_conjunction_star=star_conjunction_star,
        star_conjunction_orb=star_conjunction_orb,
        star_conjunction_magnitude=star_conjunction_magnitude,
        elemental_strength=strength,
        dominant_domains=dominant,
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
