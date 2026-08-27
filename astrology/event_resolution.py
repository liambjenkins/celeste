"""
Event-to-natal resolution (brief 2b): given any event's degree and a
natal chart, computes which natal house it falls in and how close it
is to the nearest natal point -- classified as a "direct hit" (exact
conjunction/opposition, tight orb) or "thematically adjacent" (same
house as an occupied natal point, but no exact contact), never
silently blurring the two.

Built on astrology.event_significance's already-established
nearest_primary_natal_point / direct_hit_orb / natal_targets (K5) --
this module doesn't recompute that geometry, it adds the house-
occupancy classification K5 didn't need but the query-answering layer
does.
"""

from astrology.event_significance import direct_hit_orb, natal_targets, nearest_primary_natal_point
from astrology.normaliser import longitude_in_house


def resolve_event_to_natal(longitude: float, natal_chart: dict) -> dict:
    """Resolves one degree (an eclipse's degree, a station's
    longitude, a transit pass's peak longitude, ...) against a natal
    chart. `contact` is one of:
      - "direct_hit": within the direct-hit orb of the nearest
        primary point (6 deg for Ascendant/MC, 3 deg otherwise).
      - "thematically_adjacent": not a direct hit, but shares a house
        with at least one primary natal point.
      - "no_contact": neither -- an ordinary house with nothing in it.
    """

    cusps = natal_chart["houses"]["cusps"]
    house = longitude_in_house(longitude, cusps)

    role, orb = nearest_primary_natal_point(longitude, natal_chart)
    hit_orb = direct_hit_orb(role)

    targets = natal_targets(natal_chart)
    house_occupants = [
        target_role for target_role, target_lon in targets.items()
        if target_role not in ("ascendant", "mc")  # angles define their own house cusp, not "in" a house
        and longitude_in_house(target_lon, cusps) == house
    ]

    if orb <= hit_orb:
        contact = "direct_hit"
    elif house_occupants:
        contact = "thematically_adjacent"
    else:
        contact = "no_contact"

    return {
        "natal_house": house,
        "house_occupants": house_occupants,
        "nearest_natal_point": role,
        "orb_to_nearest": orb,
        "direct_hit_orb_used": hit_orb,
        "contact": contact,
    }


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    birth_utc = aware_utc.replace(tzinfo=timezone.utc) if aware_utc.tzinfo is None else aware_utc
    natal = build_chart(birth_utc, -37.7392, 144.7967, house_system="placidus")

    # The locked eclipse worked example: 2026-08-28 partial lunar
    # eclipse, Pisces 4.85 deg (334.85 deg), expected: house 9,
    # nearest = MC at 5.69 deg -- a direct hit under the 6-deg angle
    # threshold, thematically_adjacent under a flat 3-deg one.
    resolution = resolve_event_to_natal(334.85, natal)
    print("Locked eclipse example:")
    for k, v in resolution.items():
        print(f"  {k}: {v}")

    # The locked Saturn-return example: exact conjunction to natal
    # Saturn itself -- must be a direct hit with ~0 orb.
    natal_saturn = natal["bodies"]["saturn"]["longitude"]
    resolution2 = resolve_event_to_natal(natal_saturn, natal)
    print("\nLocked Saturn-return example:")
    for k, v in resolution2.items():
        print(f"  {k}: {v}")
