"""
Celeste fixed star positions and conjunctions.

Fixed stars are only traditionally considered meaningful when a chart
body sits in TIGHT conjunction with one — unlike the wide, multi-
aspect orbs used for planet-to-planet relationships in
astrology.aspects. This module:

    - parses the full sefstars.txt catalog (~770 named stars) rather
      than a hand-curated subset, since there's no principled way to
      decide in advance which stars might turn out to be relevant —
      the tight-orb conjunction filter is what actually determines
      relevance for any given chart.
    - computes every resolvable star's position for one moment
    - finds which chart bodies are in tight conjunction with which
      stars, sorted tightest (most traditionally significant) first
"""

from pathlib import Path

import swisseph as swe

from astrology.aspects import angular_distance

EPHEMERIS_PATH = Path(__file__).resolve().parent.parent / "ephe"
SEFSTARS_PATH = EPHEMERIS_PATH / "sefstars.txt"

# Idempotent — providers/astronomy.py also sets this, but this module
# must not depend on import order to find the star catalog.
swe.set_ephe_path(str(EPHEMERIS_PATH))

DEFAULT_CONJUNCTION_ORB = 1.0

_CATALOG_NAMES = None


def _parse_catalog_names():
    """
    Parse star names (and catalog magnitude) out of sefstars.txt.

    A name is the first comma-delimited field of each non-comment,
    non-blank line. Magnitude is field 14 (index 13) where present.
    """

    names = {}

    with open(SEFSTARS_PATH, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            fields = line.split(",")

            name = fields[0].strip()

            if not name:
                continue

            magnitude = None

            if len(fields) > 13:
                try:
                    magnitude = float(fields[13])
                except ValueError:
                    magnitude = None

            names[name] = magnitude

    return names


def catalog_names():
    """Lazily parsed, cached {star_name: magnitude_or_None} dict."""

    global _CATALOG_NAMES

    if _CATALOG_NAMES is None:
        _CATALOG_NAMES = _parse_catalog_names()

    return _CATALOG_NAMES


def get_star_positions(julian_day):
    """
    Compute positions for every resolvable star in the catalog.

    A handful of catalog rows are non-star objects (galaxies,
    clusters) or otherwise fail to resolve — skipped defensively
    rather than pre-filtered, since swe.fixstar2_ut() is the ground
    truth for what's actually resolvable.
    """

    positions = {}

    for name, magnitude in catalog_names().items():
        try:
            data, _resolved_name, _return_flag = swe.fixstar2_ut(
                name, julian_day
            )
        except swe.Error:
            continue

        positions[name] = {
            "longitude": data[0],
            "latitude": data[1],
            "distance_au": data[2],
            "longitude_speed": data[3],
            "latitude_speed": data[4],
            "distance_speed": data[5],
            "magnitude": magnitude,
        }

    return positions


def find_star_conjunctions(bodies, stars, orb=DEFAULT_CONJUNCTION_ORB):
    """
    Find every chart-body/star pair within `orb` degrees of exact
    conjunction, sorted tightest (most significant) first.
    """

    conjunctions = []

    for body_name, body in bodies.items():
        body_longitude = body.get("longitude")

        if body_longitude is None:
            continue

        for star_name, star in stars.items():
            separation = angular_distance(
                body_longitude, star["longitude"]
            )

            if separation <= orb:
                conjunctions.append(
                    {
                        "body": body_name,
                        "star": star_name,
                        "orb": separation,
                        "star_longitude": star["longitude"],
                        "star_magnitude": star.get("magnitude"),
                    }
                )

    conjunctions.sort(key=lambda item: item["orb"])

    return conjunctions


if __name__ == "__main__":
    import time

    names = catalog_names()
    print(f"Catalog names parsed: {len(names)}")
    assert len(names) > 700

    julian_day = 2450000.5

    start = time.perf_counter()
    positions = get_star_positions(julian_day)
    elapsed = time.perf_counter() - start

    print(f"Resolved {len(positions)}/{len(names)} stars in {elapsed:.3f}s")
    print(f"({elapsed / max(len(names), 1) * 1000:.2f} ms/call average)")

    assert "Regulus" in positions
    assert "Aldebaran" in positions
    assert "Sirius" in positions

    bodies = {
        "sun": {"longitude": positions["Regulus"]["longitude"] + 0.3},
    }

    conjunctions = find_star_conjunctions(bodies, positions, orb=1.0)
    print(f"Test conjunctions found: {len(conjunctions)}")
    assert conjunctions
    assert conjunctions[0]["star"] == "Regulus"

    print("stars.py: OK")
