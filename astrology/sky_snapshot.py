"""
Full sky snapshot: one composite object covering every tracked body/
point at once for a single date, per Key Events Engine brief 1b.

Promoted this session from a scratchpad prototype (built and verified
against the real 2026-04-16 Saturn-return date) into real, generalized
Celeste code -- self-contained, no scratchpad dependency. Reuses
astrology.daily's existing single-instant functions directly rather
than re-deriving them, and adds the one piece the prototype didn't
have: an eclipse flag, via astrology.eclipses (K3).

Composition is intentionally mostly aggregation, per the brief's own
"doesn't require new engine capability" framing -- the one genuinely
new piece here is moon-phase-vs-natal-point contact checking (is a
New/Full Moon itself conjunct/opposite a natal point right now).
"""

from datetime import datetime, timedelta

from astrology.daily import (
    compute_current_moon_phase,
    compute_transit_aspects_to_key_points,
    compute_transit_house_placements,
)
from astrology.eclipses import find_eclipses
from astrology.normaliser import longitude_in_house, longitude_to_zodiac
from astrology.scanning import signed_diff
from providers.astronomy import get_astronomy

MOON_PHASE_NATAL_ORB = 1.0

# Bodies compute_transit_house_placements() (astrology/daily.py)
# already covers -- everyone else needs a direct longitude_in_house()
# call against the natal cusps.
_HOUSE_PLACEMENT_COVERED = (
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
    "uranus", "neptune", "pluto",
)

# The full body set this snapshot reports on -- everything
# providers.astronomy.get_astronomy() tracks except the two derived
# south nodes (always exactly opposite their true/mean north
# counterpart, so reporting both is double-counting one real point,
# not two independent measurements).
BODY_ORDER = (
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
    "uranus", "neptune", "pluto", "north_node_true", "north_node_mean",
    "chiron", "lilith_mean", "lilith_true", "ceres", "pallas", "juno", "vesta",
)


def _natal_targets(natal_chart: dict) -> dict:
    targets = {name: data["longitude"] for name, data in natal_chart["bodies"].items()}
    targets["ascendant"] = natal_chart["houses"]["angles"]["ascendant"]
    targets["mc"] = natal_chart["houses"]["angles"]["mc"]
    return targets


def _direction(body_data: dict) -> str:
    speed = body_data.get("longitude_speed")
    if speed is None:
        return "n/a (derived point, no speed)"
    return "retrograde" if speed < 0 else "direct"


def _moon_phase_natal_contacts(sun_lon: float, moon_lon: float, phase_angle: float, natal_targets: dict) -> list[str]:
    """If today's Sun-Moon phase is near New (0) or Full (180),
    checks whether the Sun or Moon is itself conjunct/opposite a
    natal point at that same moment. Absent on ordinary days by
    design -- phase_angle rarely lands within MOON_PHASE_NATAL_ORB of
    0/180 on an arbitrary date."""

    near_new = abs(signed_diff(phase_angle, 0)) <= MOON_PHASE_NATAL_ORB
    near_full = abs(signed_diff(phase_angle, 180)) <= MOON_PHASE_NATAL_ORB

    if not (near_new or near_full):
        return []

    phase_label = "New Moon" if near_new else "Full Moon"
    contacts = []

    for moving_name, moving_lon in (("Sun", sun_lon), ("Moon", moon_lon)):
        for target_name, target_lon in natal_targets.items():
            conj_orb = abs(signed_diff(moving_lon, target_lon))
            opp_orb = abs(signed_diff(moving_lon, (target_lon + 180) % 360))

            if conj_orb <= MOON_PHASE_NATAL_ORB:
                contacts.append(
                    f"{phase_label}: transiting {moving_name} conjunct natal {target_name} (orb {conj_orb:.2f} deg)"
                )
            if opp_orb <= MOON_PHASE_NATAL_ORB:
                contacts.append(
                    f"{phase_label}: transiting {moving_name} opposite natal {target_name} (orb {opp_orb:.2f} deg)"
                )

    return contacts


def _eclipse_flag(as_of_utc_time: datetime, window: timedelta = timedelta(hours=24)) -> dict | None:
    """Whether as_of_utc_time itself falls on (or within `window` of)
    an eclipse -- eclipses are rare enough that most snapshots will
    correctly return None, not a fabricated near-miss."""

    nearby = find_eclipses(as_of_utc_time - window, as_of_utc_time + window)
    if not nearby:
        return None

    closest = min(nearby, key=lambda e: abs((e["utc_time"] - as_of_utc_time).total_seconds()))
    return {
        "kind": closest["kind"],
        "type": closest["type"],
        "utc_time": closest["utc_time"].isoformat(),
        "sign": closest["sign"],
        "degree": closest["degree"],
    }


def build_sky_snapshot(natal_chart: dict, as_of_utc_time: datetime) -> dict:
    """Composite sky state for one moment -- generic over any date
    and any natal chart, not specific to any single event."""

    astronomy = get_astronomy(as_of_utc_time)
    bodies_raw = astronomy["bodies"]
    natal_targets = _natal_targets(natal_chart)

    bodies = {}
    for name in BODY_ORDER:
        data = bodies_raw[name]
        longitude = data["longitude"]
        zodiac = longitude_to_zodiac(longitude)
        if name in _HOUSE_PLACEMENT_COVERED:
            house = None  # filled in below from compute_transit_house_placements
        else:
            house = longitude_in_house(longitude, natal_chart["houses"]["cusps"])
        bodies[name] = {
            "longitude": longitude,
            "sign": zodiac["sign"],
            "degree": zodiac["degree"],
            "minute": zodiac["minute"],
            "direction": _direction(data),
            "natal_house": house,
        }

    for placement in compute_transit_house_placements(natal_chart, as_of_utc_time):
        bodies[placement["transiting_body"]]["natal_house"] = placement["natal_house"]

    moon_phase = compute_current_moon_phase(as_of_utc_time)
    moon_phase_natal_contacts = _moon_phase_natal_contacts(
        moon_phase["sun_longitude"], moon_phase["moon_longitude"], moon_phase["phase_angle"], natal_targets
    )

    aspects_active = compute_transit_aspects_to_key_points(natal_chart, as_of_utc_time)

    return {
        "as_of_utc_time": as_of_utc_time.isoformat(),
        "bodies": bodies,
        "moon_phase": moon_phase,
        "moon_phase_natal_contacts": moon_phase_natal_contacts,
        "eclipse": _eclipse_flag(as_of_utc_time),
        "aspects_active": aspects_active,
    }


if __name__ == "__main__":
    from datetime import timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    birth_utc = aware_utc.replace(tzinfo=timezone.utc) if aware_utc.tzinfo is None else aware_utc
    natal = build_chart(birth_utc, -37.7392, 144.7967, house_system="placidus")

    # The exact locked Saturn-return date from K1.
    saturn_return_utc = datetime(2026, 4, 16, 0, 32, tzinfo=timezone.utc)
    snap = build_sky_snapshot(natal, saturn_return_utc)
    print(f"Snapshot for {snap['as_of_utc_time']}:")
    print(f"  Moon phase: {snap['moon_phase']['phase_name']} (elongation {snap['moon_phase']['phase_angle']:.2f})")
    print(f"  Eclipse: {snap['eclipse']}")
    sat = snap["bodies"]["saturn"]
    print(f"  Saturn: {sat['sign']} {sat['degree']}deg{sat['minute']:02d}' house {sat['natal_house']} [{sat['direction']}]")
    print(f"  Exact aspects active: {len(snap['aspects_active'])}")

    # And the locked eclipse date from K3.
    print()
    eclipse_date = datetime(2026, 8, 28, 4, 12, tzinfo=timezone.utc)
    snap2 = build_sky_snapshot(natal, eclipse_date)
    print(f"Snapshot for {snap2['as_of_utc_time']}:")
    print(f"  Eclipse: {snap2['eclipse']}")
