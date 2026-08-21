ASPECTS = {
    "conjunction": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "quincunx": 150.0,
    "opposition": 180.0,
}


DEFAULT_ORBS = {
    "conjunction": 8.0,
    "sextile": 6.0,
    "square": 7.0,
    "trine": 7.0,
    "quincunx": 3.0,
    "opposition": 8.0,
}


# Minor aspects — opt-in (see calculate_aspects's include_minor param),
# not part of the default core reading. Angles and orbs verified via
# search during curation against standard modern astrological
# convention (most astrologers cap minor-aspect orbs at 2-3 degrees,
# tighter than major aspects, since these are subtler harmonics).
MINOR_ASPECTS = {
    "semisquare": 45.0,
    "sesquiquadrate": 135.0,
    "septile": 360.0 / 7.0,
    "novile": 40.0,
}

MINOR_ORBS = {
    "semisquare": 2.0,
    "sesquiquadrate": 2.0,
    "septile": 1.0,
    "novile": 1.0,
}


OBJECT_GROUPS = {
    "luminary": {
        "sun",
        "moon",
    },
    "planet": {
        "mercury",
        "venus",
        "mars",
        "jupiter",
        "saturn",
        "uranus",
        "neptune",
        "pluto",
    },
    "node": {
        "north_node_true",
        "north_node_mean",
        "south_node_true",
        "south_node_mean",
    },
    "point": {
        "lilith_mean",
        "lilith_true",
        "chiron",
    },
    "asteroid": {
        "ceres",
        "pallas",
        "juno",
        "vesta",
    },
}


# Which categories are allowed to form aspects in each profile.
#
# "core" is deliberately conservative.
# "all" preserves the complete mathematical relationship layer.

ASPECT_PROFILES = {
    "core": {
        ("luminary", "luminary"),
        ("luminary", "planet"),
        ("planet", "planet"),
    },

    "extended": {
        ("luminary", "luminary"),
        ("luminary", "planet"),
        ("luminary", "node"),
        ("luminary", "point"),
        ("luminary", "asteroid"),
        ("planet", "planet"),
        ("planet", "node"),
        ("planet", "point"),
        ("planet", "asteroid"),
    },

    "all": {
        ("luminary", "luminary"),
        ("luminary", "planet"),
        ("luminary", "node"),
        ("luminary", "point"),
        ("luminary", "asteroid"),
        ("planet", "planet"),
        ("planet", "node"),
        ("planet", "point"),
        ("planet", "asteroid"),
        ("node", "node"),
        ("node", "point"),
        ("node", "asteroid"),
        ("point", "point"),
        ("point", "asteroid"),
        ("asteroid", "asteroid"),
    },
}


def object_group(name):
    """Return the conceptual group for a chart object."""

    for group, names in OBJECT_GROUPS.items():
        if name in names:
            return group

    return "unknown"


def pair_allowed(name_a, name_b, profile="core"):
    """Return whether two objects may form an aspect."""

    group_a = object_group(name_a)
    group_b = object_group(name_b)

    if group_a == "unknown" or group_b == "unknown":
        return False

    pair = (group_a, group_b)
    reverse_pair = (group_b, group_a)

    allowed = ASPECT_PROFILES[profile]

    return (
        pair in allowed
        or reverse_pair in allowed
    )


def angular_distance(longitude_a, longitude_b):
    """Return the smallest angular distance between two longitudes."""

    difference = abs(
        (longitude_a - longitude_b) % 360.0
    )

    return min(
        difference,
        360.0 - difference,
    )


def find_aspect(
    longitude_a,
    longitude_b,
    orbs=None,
    angles=None,
):
    """Determine the closest configured aspect."""

    if orbs is None:
        orbs = DEFAULT_ORBS

    if angles is None:
        angles = ASPECTS

    distance = angular_distance(
        longitude_a,
        longitude_b,
    )

    matches = []

    for name, exact_angle in angles.items():

        orb = abs(
            distance - exact_angle
        )

        if orb <= orbs.get(name, 0):
            matches.append(
                {
                    "aspect": name,
                    "angle": exact_angle,
                    "orb": orb,
                }
            )

    if not matches:
        return None

    return min(
        matches,
        key=lambda item: item["orb"],
    )


def evaluate_all_aspects(
    longitude_a,
    longitude_b,
    orbs=None,
    angles=None,
):
    """
    Diagnostic sibling to find_aspect(): returns every configured
    aspect angle's computed orb, not just the ones that cleared
    threshold. find_aspect() itself is intentionally left untouched
    (it's used throughout the codebase as "return the best match or
    None") -- this exists purely so a verbose/debug mode can show what
    was actually evaluated, including near-misses, rather than only
    what resolved into a claim.
    """

    if orbs is None:
        orbs = DEFAULT_ORBS

    if angles is None:
        angles = ASPECTS

    distance = angular_distance(longitude_a, longitude_b)

    return [
        {
            "aspect": name,
            "angle": exact_angle,
            "orb": abs(distance - exact_angle),
            "max_orb": orbs.get(name, 0),
            "cleared": abs(distance - exact_angle) <= orbs.get(name, 0),
        }
        for name, exact_angle in angles.items()
    ]


def aspect_strength(orb, max_orb):
    """
    Classify an aspect by how close it is to exact.

    Returns a qualitative label while preserving
    the underlying numeric orb.
    """

    ratio = orb / max_orb

    if ratio <= 0.20:
        return "exact"

    if ratio <= 0.50:
        return "tight"

    if ratio <= 0.80:
        return "moderate"

    return "wide"

def calculate_aspects(
    bodies,
    orbs=None,
    profile="core",
    include_minor=False,
):
    """
    Calculate pairwise aspects between chart objects.

    Each pair is evaluated only once.

    The profile controls which conceptual categories
    are allowed to form relationships. include_minor additionally
    checks the minor aspects (semisquare, sesquiquadrate, septile,
    novile) — off by default, since these are a subtler, opt-in
    layer, not part of the core reading.
    """

    if profile not in ASPECT_PROFILES:
        raise ValueError(
            f"Unknown aspect profile: {profile}"
        )

    if orbs is None:
        orbs = DEFAULT_ORBS

    angles = ASPECTS
    active_orbs = orbs

    if include_minor:
        angles = {**ASPECTS, **MINOR_ASPECTS}
        active_orbs = {**orbs, **MINOR_ORBS}

    names = list(bodies.keys())
    aspects = []

    for index, name_a in enumerate(names):

        for name_b in names[index + 1:]:

            if not pair_allowed(
                name_a,
                name_b,
                profile,
            ):
                continue

            body_a = bodies[name_a]
            body_b = bodies[name_b]

            result = find_aspect(
                body_a["longitude"],
                body_b["longitude"],
                active_orbs,
                angles,
            )

            if result is None:
                continue

            aspects.append(
                {
                    "body_a": name_a,
                    "body_b": name_b,
                    "aspect": result["aspect"],
                    "angle": result["angle"],
                    "orb": result["orb"],
                    "orb_strength": aspect_strength(
                        result["orb"],
                        active_orbs[result["aspect"]],
                    ),
                    "profile": profile,
                }
            )

    return aspects
