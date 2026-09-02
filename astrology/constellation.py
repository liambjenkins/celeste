"""
Headline-only constellation image renderer.

Earlier sessions prototyped a constellation-style chart image in
scratch files that were never committed to this repo (lost between
sessions), and that prototype always drew the full standout+background
hit set together -- every real placement active that day, regardless
of whether it was part of the day's actual headline. That's real data,
but it's not what a reader asked "what's my day about" wants: a
14-point tangle doesn't read as a story the way daily.py's own
headline_thread (_score_threads() in daily.py) already picked out.

This module draws ONLY the placements that belong to a given day's
headline_thread -- the same hit_ids daily.py itself treats as "the
day's real headline" when scoping the synthesis prompt (see daily.py's
_render_daily_narrative_input PRIMARY THREAD section). A named-occasion
thread (a return/station at its own peak, score == inf) draws just that
one body and, when the station/return lands near a real natal point,
the natal point it's nearest to. A point-convergence or house-
convergence thread draws every transiting body/natal point pair that
won the day's scoring.
"""

from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from astrology.event_significance import natal_targets  # noqa: E402
from astrology.normaliser import ZODIAC_SIGNS  # noqa: E402

# Short display labels for every role that can appear in a hit's
# display/resolution dicts -- deliberately covers the full
# PRIMARY_NATAL_ROLES set (astrology/event_significance.py) plus the
# 10 transiting bodies, not just whatever happens to show up in any
# one sampled day, so this renderer doesn't silently mislabel a role
# it hasn't been run against yet.
BODY_LABELS = {
    "sun": "Sun", "moon": "Moon", "mercury": "Mercury", "venus": "Venus",
    "mars": "Mars", "jupiter": "Jupiter", "saturn": "Saturn",
    "uranus": "Uranus", "neptune": "Neptune", "pluto": "Pluto",
    "chart_ruler": "Chart Ruler", "ascendant": "Ascendant", "mc": "MC",
    "descendant": "Descendant", "ic": "IC",
    "north_node_true": "N. Node", "north_node_mean": "N. Node (mean)",
    "south_node_true": "S. Node", "south_node_mean": "S. Node (mean)",
    "chiron": "Chiron", "lilith_mean": "Lilith", "lilith_true": "Lilith (osc.)",
    "ceres": "Ceres", "pallas": "Pallas", "juno": "Juno", "vesta": "Vesta",
}

# Aspect-type render style -- color/dash groups roughly by classical
# harmony (soft aspects green, hard aspects red, the unifying
# conjunction gold), matching this project's own ASPECT_WEIGHTS
# grouping (astrology/event_significance.py) rather than inventing a
# new taxonomy.
_HARD = dict(color="#e0555d", linewidth=1.6)
_SOFT = dict(color="#5fd3a6", linewidth=1.4)
_MINOR = dict(color="#8a93b3", linewidth=0.9, linestyle=(0, (1, 2)))
ASPECT_STYLES = {
    "conjunction": dict(color="#f2c14e", linewidth=1.8),
    "opposition": {**_HARD, "linestyle": "--"},
    "square": {**_HARD, "linestyle": "-"},
    "trine": {**_SOFT, "linestyle": "-"},
    "sextile": {**_SOFT, "linestyle": "--"},
    "quincunx": _MINOR,
    "semisquare": _MINOR,
    "sesquiquadrate": _MINOR,
    "semisextile": _MINOR,
    "station": dict(color="#f2c14e", linewidth=2.2, linestyle=":"),
    "return": dict(color="#f2c14e", linewidth=1.8),
}
_DEFAULT_STYLE = dict(color="#8a93b3", linewidth=1.0, linestyle="-")

_BG = "#0b1026"
_RING_COLOR = "#2a3363"
_TRANSIT_COLOR = "#f2c14e"
_NATAL_COLOR = "#eef1fb"
_TEXT_COLOR = "#c9cfe8"


def _label(role: str) -> str:
    return BODY_LABELS.get(role, role.replace("_", " ").title())


def _longitude_from_display(display: dict) -> float | None:
    sign = display.get("sign")
    degree = display.get("degree")
    if sign is None or degree is None or sign not in ZODIAC_SIGNS:
        return None
    return ZODIAC_SIGNS.index(sign) * 30.0 + float(degree)


def headline_placements(
    natal_chart: dict, hits: list[dict], headline_thread: dict | None
) -> tuple[dict[str, tuple[str, float]], list[tuple[str, str, str]]]:
    """The filtered point/edge set a headline-only constellation draws
    -- ONLY placements belonging to headline_thread['hit_ids'], never
    the full standout+background hit list. Returns (points, edges):

    points: {point_key: (display_label, longitude_degrees)}, one entry
    per distinct natal or transiting placement actually involved.
    point_key is prefixed ("transit:"/"natal:") so the same body can
    appear twice (its natal degree and today's transiting degree)
    without colliding.

    edges: [(from_point_key, to_point_key, aspect_or_kind), ...], one
    per hit, connecting the transiting placement to the natal point it
    touches. A station/return with no resolvable nearest natal point
    (rare -- resolution['nearest_natal_point'] is None) contributes its
    point but no edge, since there's nothing real to connect it to.
    """

    if headline_thread is None:
        return {}, []

    winning_ids = set(headline_thread["hit_ids"])
    winning_hits = [h for h in hits if h["hit_id"] in winning_ids]
    if not winning_hits:
        return {}, []

    targets = natal_targets(natal_chart)
    points: dict[str, tuple[str, float]] = {}
    edges: list[tuple[str, str, str]] = []

    for hit in winning_hits:
        kind = hit["kind"]
        display = hit["display"]
        transiting_body = display.get("transiting_body")
        transit_lon = _longitude_from_display(display)

        if kind == "transit_aspect":
            target_role = display["target_role"]
            aspect = display["aspect"]
        else:
            target_role = hit["resolution"].get("nearest_natal_point")
            aspect = kind  # "station" or "return"

        transit_key = f"transit:{transiting_body}"
        if transit_lon is not None and transiting_body is not None:
            points[transit_key] = (_label(transiting_body), transit_lon)

        if target_role is None:
            continue

        natal_lon = targets.get(target_role)
        if natal_lon is None:
            continue
        natal_key = f"natal:{target_role}"
        points[natal_key] = (_label(target_role), natal_lon)

        if transit_lon is not None and transiting_body is not None:
            edges.append((transit_key, natal_key, aspect))

    return points, edges


def render_headline_constellation(
    natal_chart: dict,
    hits: list[dict],
    headline_thread: dict | None,
    output_path: str,
    date_label: str | None = None,
) -> str:
    """Render the headline-only constellation PNG to `output_path`.
    Draws a zodiac ring (sign boundaries only -- this is a longitude
    wheel, not a house wheel, since headline placements are about
    which sign/degree is active, not the natal house wheel daily.py's
    own text output already covers) plus one star-marker per placement
    in headline_placements() above, connected by aspect-styled lines.

    Raises ValueError if the headline thread resolves to no placements
    at all (nothing to draw) -- callers should treat that as "no
    headline-only image for today", not silently emit a blank canvas.
    """

    points, edges = headline_placements(natal_chart, hits, headline_thread)
    if not points:
        raise ValueError(
            "No headline placements to render -- headline_thread is "
            "None, or none of its hit_ids resolved to a drawable point."
        )

    fig, ax = plt.subplots(figsize=(8, 8), dpi=150)
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)
    ax.set_aspect("equal")
    ax.axis("off")

    ring_r = 1.15

    def _xy(longitude_deg: float, radius: float) -> tuple[float, float]:
        # 0 deg (Aries 0) at the top, increasing clockwise -- a plain
        # reading-friendly convention, not the traditional Ascendant-
        # at-9-o'clock house wheel (this chart carries no houses).
        math_angle = math.radians(90.0 - longitude_deg)
        return radius * math.cos(math_angle), radius * math.sin(math_angle)

    # Zodiac ring: 12 boundary spokes + sign name at each wedge's midpoint.
    circle = plt.Circle((0, 0), ring_r, fill=False, color=_RING_COLOR, linewidth=1.2)
    ax.add_patch(circle)
    for i, sign in enumerate(ZODIAC_SIGNS):
        boundary_deg = i * 30.0
        x0, y0 = _xy(boundary_deg, ring_r - 0.03)
        x1, y1 = _xy(boundary_deg, ring_r + 0.03)
        ax.plot([x0, x1], [y0, y1], color=_RING_COLOR, linewidth=1.0)

        mid_deg = boundary_deg + 15.0
        lx, ly = _xy(mid_deg, ring_r + 0.09)
        ax.text(
            lx, ly, sign, color=_TEXT_COLOR, fontsize=8, ha="center", va="center",
            fontfamily="serif",
        )

    # Two concentric point-rings, not one shared radius -- a
    # conjunction (the most common real case: a station or an exact
    # aspect landing near-exactly on its target) puts a transiting and
    # a natal placement at nearly the SAME longitude, which collided
    # into unreadable overlapping stars/labels when both were plotted
    # at one radius. Natal placements sit on the inner ring, today's
    # transiting placements on the outer ring (still inside the zodiac
    # ring), so a conjunction reads as a short near-radial connector
    # instead of two markers stacked on top of each other.
    natal_r = 0.52
    transit_r = 0.84

    for guide_r in (natal_r, transit_r):
        ax.add_patch(
            plt.Circle((0, 0), guide_r, fill=False, color=_RING_COLOR,
                       linewidth=0.6, linestyle=(0, (1, 3)))
        )

    def _point_radius(key: str) -> float:
        return transit_r if key.startswith("transit:") else natal_r

    # Aspect lines first, so star markers/labels draw on top.
    for from_key, to_key, aspect in edges:
        style = ASPECT_STYLES.get(aspect, _DEFAULT_STYLE)
        _, from_lon = points[from_key]
        _, to_lon = points[to_key]
        x0, y0 = _xy(from_lon, _point_radius(from_key))
        x1, y1 = _xy(to_lon, _point_radius(to_key))
        ax.plot([x0, x1], [y0, y1], alpha=0.85, solid_capstyle="round", **style)

    for key, (label, lon) in points.items():
        is_transit = key.startswith("transit:")
        color = _TRANSIT_COLOR if is_transit else _NATAL_COLOR
        r = _point_radius(key)
        x, y = _xy(lon, r)
        ax.scatter(
            [x], [y], s=170 if is_transit else 130,
            marker="*", color=color, edgecolors=_BG, linewidths=0.6, zorder=3,
        )
        # Natal labels sit just inside their ring (toward center);
        # transiting labels sit just outside theirs (toward the zodiac
        # ring) -- opposite directions, so the two rings' labels never
        # compete for the same band even when longitudes are close.
        label_r = r - 0.13 if not is_transit else r + 0.13
        lx, ly = _xy(lon, label_r)
        tag = "transiting" if is_transit else "natal"
        ax.text(
            lx, ly, f"{label}\n({tag})", color=color, fontsize=8.5,
            ha="center", va="center", zorder=4,
        )

    if headline_thread is not None:
        headline_label = headline_thread.get("label", "")
        subtitle = f"headline: {headline_label}"
    else:
        subtitle = "no headline thread"

    title = date_label or ""
    ax.text(
        0, 1.32, title, color=_NATAL_COLOR, fontsize=14, ha="center", va="center",
        fontweight="bold", fontfamily="serif",
    )
    ax.text(
        0, 1.23, subtitle, color=_TEXT_COLOR, fontsize=10.5, ha="center", va="center",
        fontstyle="italic",
    )

    fig.tight_layout()
    fig.savefig(output_path, facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path
