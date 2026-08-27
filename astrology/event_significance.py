"""
Significance tiering: classifies every event type K2/K3/K4 can
produce into standout / background / appendix, and collapses a
multi-pass retrograde return (K1's group_passes output) into one
extended event rather than separate entries.

Speed classes deliberately split into THREE, not two -- Jupiter is
neither a fast personal-planet transit nor a Saturn-grade "chapter
marker" on every contact. It's standout-eligible for its own return
and for entering a new natal house (both real, ~once-in-however-long
chapter markers), but background for ordinary aspects, since it
contacts roughly 10 natal points a year and treating it as fully
"slow" would flood the standout tier with routine Jupiter transits.
Confirmed with Liam before building this.

Angle direct-hit orb (6 degrees) is wider than the 3-degree orb used
for planet-to-planet contacts -- also confirmed with Liam, sized so
the locked eclipse worked example (5.69 degrees from natal MC) reads
as a genuine contact rather than "thematically adjacent."
"""

from datetime import datetime

from astrology.eclipses import NODAL_AXIS_ORB, check_eclipse_nodal_relationship
from astrology.scanning import signed_diff

FAST_BODIES = ("sun", "moon", "mercury", "venus", "mars")
SOCIAL_BODIES = ("jupiter",)
SLOW_BODIES = ("saturn", "uranus", "neptune", "pluto")

# 10 traditional bodies + Ascendant + MC + chart ruler + true nodes --
# the points that can raise a tier to standout. Everything else
# (Chiron, Liliths, asteroids, mean nodes) is still reported on any
# event that touches it, but never raises the tier on its own.
PRIMARY_NATAL_ROLES = (
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
    "uranus", "neptune", "pluto", "ascendant", "mc", "chart_ruler", "north_node_true",
)

STANDOUT_SLOW_EXACT_ORB = 1.0       # slow-body exact crossing to a primary planet point
STANDOUT_STATION_ORB = 1.0          # slow-body station within this of a primary natal point
DIRECT_HIT_ORB = 3.0                # planet-to-planet "direct hit" boundary
ANGLE_DIRECT_HIT_ORB = 6.0          # Ascendant/MC direct-hit boundary -- confirmed wider with Liam
LUNATION_CONTACT_ORB = 1.0          # New/Full Moon degree to a primary natal point

TIERS = ("standout", "background", "appendix")


def direct_hit_orb(role: str) -> float:
    """The direct-hit orb boundary for a given natal role -- wider
    for the angles (Ascendant/MC) than for planet-to-planet contacts,
    per the locked decision this module documents above. Public: also
    reused by astrology/event_resolution.py (K7)."""

    return ANGLE_DIRECT_HIT_ORB if role in ("ascendant", "mc") else DIRECT_HIT_ORB


def natal_targets(natal_chart: dict, roles=PRIMARY_NATAL_ROLES) -> dict:
    chart_ruler = natal_chart["rulership"]["chart_ruler"]
    targets = {}
    for role in roles:
        if role == "ascendant":
            targets[role] = natal_chart["houses"]["angles"]["ascendant"]
        elif role == "mc":
            targets[role] = natal_chart["houses"]["angles"]["mc"]
        elif role == "chart_ruler":
            targets[role] = natal_chart["bodies"][chart_ruler]["longitude"]
        else:
            targets[role] = natal_chart["bodies"][role]["longitude"]
    return targets


def nearest_primary_natal_point(longitude: float, natal_chart: dict) -> tuple[str, float]:
    """The closest PRIMARY natal point to `longitude` and its orb
    (0-180 degrees, conjunction-style distance -- suitable for
    stations/ingresses/lunations, which aren't aspect-typed)."""

    targets = natal_targets(natal_chart)
    best_role, best_orb = None, 181.0
    for role, target_lon in targets.items():
        orb = abs(signed_diff(longitude, target_lon))
        if orb < best_orb:
            best_role, best_orb = role, orb
    return best_role, best_orb


def _build_recurrence_note(group: list[dict]) -> str | None:
    if len(group) <= 1:
        return None

    parts = []
    for p in group:
        date_str = p["utc_time"].strftime("%d %b %Y")
        if p["kind"] == "exact_crossing":
            parts.append(f"exact on {date_str}")
        else:
            motion = "stationing retrograde" if p["retrograde"] else "stationing direct"
            parts.append(f"again at {p['orb']:.2f} deg on {date_str} while {motion}")

    body = group[0]["transiting_body"]
    verb = "Crosses this degree" if len(group) == 2 else f"Crosses this degree {len(group)} times"
    return f"{verb}: {', then '.join(parts)}."


def collapse_repeat_passes(group: list[dict]) -> dict:
    """Collapses one group of TransitPass records (from
    astrology.transit_passes.group_passes, all sharing the same
    transiting body/target/aspect) into ONE extended KeyEvent -- the
    "one row, never two" requirement. The event's peak orb/date is
    the TIGHTEST pass, not necessarily the first or last."""

    peak = min(group, key=lambda p: p["orb"])
    is_return = peak["target_role"] == peak["transiting_body"]
    ordered = sorted(group, key=lambda p: p["utc_time"])

    return {
        "kind": "return" if is_return else "transit_aspect",
        "transiting_body": peak["transiting_body"],
        "aspect": peak["aspect"],
        "target_role": peak["target_role"],
        "peak_utc_time": peak["utc_time"],
        "peak_orb": peak["orb"],
        "start_date": ordered[0]["utc_time"],
        "end_date": ordered[-1]["utc_time"],
        "natal_house": peak["natal_house"],
        "is_repeating": len(group) > 1,
        "pass_count": len(group),
        "passes": ordered,
        "recurrence_note": _build_recurrence_note(ordered),
    }


def assign_tier(event: dict, natal_chart: dict) -> tuple[str, list[str]]:
    """Classifies any event dict produced by collapse_repeat_passes,
    find_stations, find_sign_ingresses, find_natal_house_ingresses,
    find_eclipses, find_lunations, or a Dasha-change dict (see K6),
    into (tier, reasons) -- reasons accumulate every rule that
    matched, not just the first, so the caller can see the full
    justification, not just the verdict."""

    kind = event["kind"]
    reasons = []

    if kind == "eclipse":
        # Every eclipse is standout regardless of natal contact --
        # 2e's honesty principle is better served by "there's an
        # eclipse, and it doesn't touch your chart" than by hiding it.
        reasons.append("eclipse")
        return "standout", reasons

    if kind == "return":
        body = event["transiting_body"]
        if body in SLOW_BODIES or body in SOCIAL_BODIES or body == "sun":
            reasons.append("return")
            return "standout", reasons
        reasons.append("return_fast_body")
        return "background", reasons

    if kind == "transit_aspect":
        body = event["transiting_body"]
        role = event["target_role"]
        orb = event["peak_orb"]
        if body in SLOW_BODIES and role in PRIMARY_NATAL_ROLES and orb <= STANDOUT_SLOW_EXACT_ORB:
            reasons.append("slow_body_exact_within_1deg")
            return "standout", reasons
        reasons.append("ordinary_transit_aspect")
        return "background", reasons

    if kind == "station":
        body = event["body"]
        role, orb = nearest_primary_natal_point(event["longitude"], natal_chart)
        if body in SLOW_BODIES and orb <= STANDOUT_STATION_ORB:
            reasons.append(f"slow_body_station_within_1deg_of_{role}")
            return "standout", reasons
        reasons.append("routine_station")
        return "background", reasons

    if kind == "sign_ingress":
        if event["body"] == "moon":
            reasons.append("moon_sign_ingress")
            return "appendix", reasons
        reasons.append("sign_ingress")
        return "background", reasons

    if kind == "natal_house_ingress":
        body = event["body"]
        if body == "moon":
            reasons.append("moon_house_ingress")
            return "appendix", reasons
        if body in SLOW_BODIES or body in SOCIAL_BODIES:
            reasons.append("slow_or_social_body_house_ingress")
            return "standout", reasons
        reasons.append("fast_body_house_ingress")
        return "background", reasons

    if kind in ("new_moon", "full_moon"):
        targets = natal_targets(natal_chart)
        moon_lon = event["moon_longitude"]
        # Full Moon: Sun is opposite the Moon; New Moon: Sun ~ Moon.
        sun_lon = (moon_lon + 180) % 360 if kind == "full_moon" else moon_lon
        for label, lon in (("moon", moon_lon), ("sun", sun_lon)):
            for role, target_lon in targets.items():
                conj = abs(signed_diff(lon, target_lon))
                opp = abs(signed_diff(lon, (target_lon + 180) % 360))
                if min(conj, opp) <= LUNATION_CONTACT_ORB:
                    reasons.append(f"{label}_contacts_natal_{role}")
                    return "standout", reasons
        reasons.append("routine_lunation")
        return "background", reasons

    if kind == "dasha_change":
        level = event["level"]
        if level in ("mahadasha", "antardasha"):
            reasons.append(f"dasha_{level}_change")
            return "background", reasons
        reasons.append(f"dasha_{level}_change")
        return "appendix", reasons

    raise ValueError(f"assign_tier: unrecognized event kind {kind!r}")


if __name__ == "__main__":
    from datetime import timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc
    from astrology.transit_passes import find_transit_passes, group_passes

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    birth_utc = aware_utc.replace(tzinfo=timezone.utc) if aware_utc.tzinfo is None else aware_utc
    natal = build_chart(birth_utc, -37.7392, 144.7967, house_system="placidus")
    natal_saturn_lon = natal["bodies"]["saturn"]["longitude"]

    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end = datetime(2028, 1, 1, tzinfo=timezone.utc)

    passes = find_transit_passes(natal, "saturn", "saturn", natal_saturn_lon, "conjunction", start, end)
    groups = group_passes(passes, "saturn")
    for g in groups:
        event = collapse_repeat_passes(g)
        tier, reasons = assign_tier(event, natal)
        print(f"Saturn return: tier={tier} reasons={reasons}")
        print(f"  peak: {event['peak_utc_time'].date()} orb={event['peak_orb']:.4f} "
              f"repeating={event['is_repeating']} passes={event['pass_count']}")
        print(f"  {event['recurrence_note']}")

    # Locked eclipse example.
    eclipse_event = {
        "kind": "eclipse", "utc_time": datetime(2026, 8, 28, 4, 12, tzinfo=timezone.utc),
        "longitude": 334.85, "sign": "Pisces", "degree": 4, "type": "partial",
    }
    tier, reasons = assign_tier(eclipse_event, natal)
    print(f"\nEclipse: tier={tier} reasons={reasons}")
