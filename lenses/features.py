"""
Celeste shared feature extraction.

Turns canonical concepts (and the elemental classification derived
from them) into a small set of derived, machine-readable feature
tags that any lens can draw on:

    - environmental signal tags (temperature, humidity, pressure, ...)
    - the actual lunar phase, derived from Sun/Moon ecliptic longitude
    - a Sun-Moon aspect tag, for claim resolution (e.g. "aspect:square")
    - which classical elemental domains (fire/water/earth/air/space)
    carry the most observational weight for this moment

This module does not interpret. It only derives structured,
tradition-neutral features that lens-specific code (structural.py,
the knowledge claim resolver) can consume.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FeatureBundle:
    tags: list[str] = field(default_factory=list)

    season: Optional[str] = None

    sun_longitude: Optional[float] = None
    moon_longitude: Optional[float] = None
    moon_phase_angle: Optional[float] = None
    moon_phase_name: Optional[str] = None
    sun_moon_aspect: Optional[str] = None

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


# ------------------------------------------------------------
# Elemental strength
# ------------------------------------------------------------
#
# `elements` is the output of elements.classify_observations(): a
# nested fire/water/earth/air/space dict whose leaves are either
# None or a canonical concept dict. Strength is simply how many
# leaves under a domain carry an actual observation.

def _iter_leaves(node):
    if node is None:
        yield None
        return

    if isinstance(node, dict) and "observations" in node:
        yield node
        return

    if isinstance(node, dict):
        for value in node.values():
            yield from _iter_leaves(value)
        return

    yield node


def elemental_strength(elements):
    strength = {}

    for domain, fields in elements.items():
        count = sum(1 for leaf in _iter_leaves(fields) if leaf is not None)
        strength[domain] = count

    return strength


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

def build_features(concepts: dict[str, Any], elements: dict[str, Any]) -> FeatureBundle:
    tags = _signal_tags(concepts)

    season = _single_value(concepts.get("season"))

    if season:
        tags.append(f"season:{season}")

    sun_longitude = _longitude(concepts.get("sun"))
    moon_longitude = _longitude(concepts.get("moon"))

    phase_angle = None
    phase_name = None
    aspect = None

    if sun_longitude is not None and moon_longitude is not None:
        phase_angle = (moon_longitude - sun_longitude) % 360
        phase_name = _moon_phase_name(phase_angle)

        separation = min(phase_angle, 360 - phase_angle)
        aspect = _sun_moon_aspect(separation)

        tags.append(f"moon_phase:{phase_name}")

        if aspect:
            tags.append(f"aspect:{aspect}")

    strength = elemental_strength(elements)
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
    }

    elements = {
        "fire": {"solar_activity": None, "thermal": concepts["temperature"]},
        "water": {"tides": None, "hydrology": None, "marine": None},
        "earth": {
            "geology": None,
            "earthquakes": None,
            "elevation": None,
            "land": None,
            "biosphere": None,
            "soil_temperature": None,
        },
        "air": {
            "atmosphere": {
                "moisture": None,
                "pressure": None,
                "cloud": None,
                "temperature": concepts["temperature"],
            }
        },
        "space": {"astronomy": concepts["sun"], "space_weather": None},
    }

    features = build_features(concepts, elements)

    print("Tags:", features.tags)
    print("Moon phase:", features.moon_phase_name)
    print("Aspect:", features.sun_moon_aspect)
    print("Dominant domains:", features.dominant_domains)

    assert features.moon_phase_name is not None
    assert "temperature:cool" in features.tags

    print("features.py: OK")
