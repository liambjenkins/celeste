"""
Solar phase per planet: motion (direct/retrograde/stationary),
combustion state, and oriental/occidental visibility.

Orb thresholds (cazimi 0d17', combustion 8d, under the beams 15d) are
the commonly-cited classical/Lilly-tradition figures -- sources vary
slightly (some give combustion as 8.5d, under-the-beams as wide as
17d); these are a defensible, documented standard choice rather than
an attempt to reconcile every variant.

Orientality: a planet is oriental of the Sun (rises before it, morning
star) when it trails the Sun by less than 180d in zodiacal order;
occidental (evening star) when it leads the Sun by less than 180d.
This is the standard convention applied to all five non-luminary
planets alike (not just Mercury/Venus) -- verified against how the
tradition ties Mercury's own sect/gender to this same orientality
split (hellenistic.sect.mercury_own_sect, hellenistic.constants'
FIXED_GENDER note).
"""

from hellenistic.constants import CLASSICAL_PLANETS

CAZIMI_ORB = 17.0 / 60.0
COMBUST_ORB = 8.0
UNDER_BEAMS_ORB = 15.0

# Typical daily motion per planet (degrees/day) used only to scale a
# "near enough to zero to call it stationary" threshold -- Jupiter and
# Saturn's ordinary motion is already so slow that a fixed cutoff would
# either miss their real stations or falsely flag their normal motion.
_AVERAGE_DAILY_MOTION = {
    "mercury": 1.383,
    "venus": 1.2,
    "mars": 0.524,
    "jupiter": 0.083,
    "saturn": 0.034,
}
_STATIONARY_FRACTION = 0.05


def _angular_separation(longitude_a: float, longitude_b: float) -> float:
    diff = abs((longitude_a - longitude_b) % 360.0)
    return min(diff, 360.0 - diff)


def is_oriental(planet_longitude: float, sun_longitude: float) -> bool:
    """True if the planet trails the Sun by < 180deg (rises before it)."""
    return ((sun_longitude - planet_longitude) % 360.0) < 180.0


def combustion_state(separation: float) -> str:
    if separation <= CAZIMI_ORB:
        return "cazimi"
    if separation <= COMBUST_ORB:
        return "combust"
    if separation <= UNDER_BEAMS_ORB:
        return "under_beams"
    return "free"


def motion_state(planet: str, speed: float) -> str:
    if planet in ("sun", "moon"):
        return "direct"
    if speed < 0:
        return "retrograde"
    threshold = _AVERAGE_DAILY_MOTION[planet] * _STATIONARY_FRACTION
    if abs(speed) <= threshold:
        return "stationary"
    return "direct"


def mercury_gender(mercury_oriental: bool) -> str:
    """Resolves Mercury's binary gender from its oriental/occidental
    status, per hellenistic.constants.FIXED_GENDER's note: oriental ->
    masculine, occidental -> feminine."""
    return "masculine" if mercury_oriental else "feminine"


def build_solar_phase(bodies: dict) -> dict:
    sun = bodies["sun"]
    sun_longitude = sun["longitude"]

    result = {}

    for planet in CLASSICAL_PLANETS:
        if planet not in bodies:
            continue

        body = bodies[planet]

        if planet == "sun":
            result[planet] = {
                "motion": "direct",
                "combustion": "free",
                "visibility": None,
            }
            continue

        separation = _angular_separation(body["longitude"], sun_longitude)
        oriental = is_oriental(body["longitude"], sun_longitude)

        result[planet] = {
            "motion": motion_state(planet, body["longitude_speed"] or 0.0),
            "combustion": combustion_state(separation),
            "visibility": "oriental" if oriental else "occidental",
            "oriental": oriental,
            "separation_from_sun": separation,
        }

        if planet == "moon":
            result[planet]["bonding"] = moon_bonding(separation)

    return result


def moon_bonding(solar_phase_moon_separation: float) -> str:
    """Moon-specific `bonding` field: under_beams if within the same
    combustion-family orb as any other planet (cazimi/combust/under_
    beams all collapse to under_beams for this simpler field), else
    free. Reuses the standard orb thresholds above rather than a
    separate lunar-specific figure."""
    return "under_beams" if solar_phase_moon_separation <= UNDER_BEAMS_ORB else "free"
