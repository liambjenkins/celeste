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

Visual language (confirmed with Liam against an earlier reference
mockup): dark field, glowing dots, monochrome -- no per-aspect-type
color coding. Dot size encodes each placement's own "signal" (how
tight/weighty the real contact touching it is); line weight/opacity
encodes that same real strength for the aspect itself. Natal placements
sit on an inner ring (dim, small), today's transiting placements on an
outer ring (bright, larger) -- both still positioned at each
placement's REAL zodiacal longitude (a deliberate choice for this
narrower, few-node headline-only case, not the freely-scattered
force-layout the denser standout/background prototype used).
"""

from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from astrology.event_significance import ASPECT_WEIGHTS, natal_targets  # noqa: E402
from astrology.normaliser import ZODIAC_SIGNS  # noqa: E402
from astrology.transits import TRANSIT_ORBS  # noqa: E402

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

_BG = "#040406"
_RING_COLOR = "#33364a"
_DOT_COLOR = "#f5f6fa"
_LINE_COLOR = "#c7cbe0"
_TEXT_COLOR = "#e7e9f5"
_DIM_TEXT_COLOR = "#8d92ab"


def _label(role: str) -> str:
    return BODY_LABELS.get(role, role.replace("_", " ").title())


def _longitude_from_display(display: dict) -> float | None:
    sign = display.get("sign")
    degree = display.get("degree")
    if sign is None or degree is None or sign not in ZODIAC_SIGNS:
        return None
    return ZODIAC_SIGNS.index(sign) * 30.0 + float(degree)


def _hit_strength(hit: dict) -> float:
    """0-1 real-signal strength for one hit -- the same weight *
    (1 - orb/max_orb) shape daily.py's own _score_threads uses for
    aspect-type thread scoring, extended to stations/returns (full
    aspect weight, scaled by the station/return's own orb against its
    own direct-hit orb boundary). Drives both this hit's line weight
    and (via the max over each point's incident hits) that point's dot
    size -- real computed tightness, not a stand-in for narrative
    importance."""

    orb = hit["resolution"]["orb_to_nearest"]
    if orb is None:
        return 0.6

    if hit["kind"] == "transit_aspect":
        aspect = hit["display"]["aspect"]
        weight = ASPECT_WEIGHTS.get(aspect, 0.5)
        max_orb = TRANSIT_ORBS.get(aspect, 2.0)
    else:
        weight = 1.0
        max_orb = hit["resolution"].get("direct_hit_orb_used") or 2.0

    if max_orb <= 0:
        return weight
    return weight * max(0.0, min(1.0, 1.0 - (orb / max_orb)))


def headline_placements(
    natal_chart: dict, hits: list[dict], headline_thread: dict | None
) -> tuple[dict[str, tuple[str, float, float]], list[tuple[str, str, str, float]]]:
    """The filtered point/edge set a headline-only constellation draws
    -- ONLY placements belonging to headline_thread['hit_ids'], never
    the full standout+background hit list. Returns (points, edges):

    points: {point_key: (display_label, longitude_degrees, signal)}.
    point_key is prefixed ("transit:"/"natal:") so the same body can
    appear twice (its natal degree and today's transiting degree)
    without colliding. signal is the max _hit_strength() of every hit
    touching that point.

    edges: [(from_point_key, to_point_key, aspect_or_kind, strength)],
    one per hit, connecting the transiting placement to the natal
    point it touches. A station/return with no resolvable nearest
    natal point (rare -- resolution['nearest_natal_point'] is None)
    contributes its point but no edge, since there's nothing real to
    connect it to.
    """

    if headline_thread is None:
        return {}, []

    winning_ids = set(headline_thread["hit_ids"])
    winning_hits = [h for h in hits if h["hit_id"] in winning_ids]
    if not winning_hits:
        return {}, []

    targets = natal_targets(natal_chart)
    raw_points: dict[str, tuple[str, float]] = {}
    signals: dict[str, float] = {}
    edges: list[tuple[str, str, str, float]] = []

    for hit in winning_hits:
        kind = hit["kind"]
        display = hit["display"]
        transiting_body = display.get("transiting_body")
        transit_lon = _longitude_from_display(display)
        strength = _hit_strength(hit)

        if kind == "transit_aspect":
            target_role = display["target_role"]
            aspect = display["aspect"]
        else:
            target_role = hit["resolution"].get("nearest_natal_point")
            aspect = kind  # "station" or "return"

        transit_key = f"transit:{transiting_body}"
        if transit_lon is not None and transiting_body is not None:
            raw_points[transit_key] = (_label(transiting_body), transit_lon)
            signals[transit_key] = max(signals.get(transit_key, 0.0), strength)

        if target_role is None:
            continue

        natal_lon = targets.get(target_role)
        if natal_lon is None:
            continue
        natal_key = f"natal:{target_role}"
        raw_points[natal_key] = (_label(target_role), natal_lon)
        signals[natal_key] = max(signals.get(natal_key, 0.0), strength)

        if transit_lon is not None and transiting_body is not None:
            edges.append((transit_key, natal_key, aspect, strength))

    points = {
        key: (label, lon, signals.get(key, 0.6))
        for key, (label, lon) in raw_points.items()
    }
    return points, edges


def _caption_for_thread(headline_thread: dict, hits: list[dict]) -> str:
    """One factual line describing the headline thread -- restates
    real computed data (label, hit count, kind) already on the hit
    dicts, same "computed fact, no interpretive claim" discipline
    daily.py's own _computed_hit_claim uses, never invented prose."""

    winning_ids = set(headline_thread["hit_ids"])
    winning_hits = [h for h in hits if h["hit_id"] in winning_ids]
    label = headline_thread.get("label", "")

    if headline_thread.get("score") == float("inf") and len(winning_hits) == 1:
        hit = winning_hits[0]
        d = hit["display"]
        role = hit["resolution"].get("nearest_natal_point")
        orb = hit["resolution"].get("orb_to_nearest")
        body = _label(d.get("transiting_body", ""))
        if hit["kind"] == "station":
            verb = f"stations {'retrograde' if d.get('retrograde') else 'direct'}"
        else:
            verb = "returns to its own natal degree"
        base = f"{body} {verb} at {d.get('sign')} {d.get('degree')}°"
        if role and orb is not None:
            return f"{base} -- {orb:.2f}° from natal {_label(role)}."
        return base + "."

    n = len(winning_hits)
    return f"{n} real aspect{'s' if n != 1 else ''} converge on today's headline: {label}."


def render_headline_constellation(
    natal_chart: dict,
    hits: list[dict],
    headline_thread: dict | None,
    output_path: str,
    date_label: str | None = None,
) -> str:
    """Render the headline-only constellation PNG to `output_path`.

    Positions every placement at its real zodiacal longitude around
    two concentric rings (natal inner, transiting-today outer) rather
    than a free force-layout -- with only a handful of points in a
    headline-only image, real angle stays legible instead of colliding
    the way it would across a full standout+background hit set.

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

    def _xy(longitude_deg: float, radius: float) -> tuple[float, float]:
        # 0 deg (Aries 0) at the top, increasing clockwise -- a plain
        # reading-friendly convention, not the traditional Ascendant-
        # at-9-o'clock house wheel (this chart carries no houses).
        math_angle = math.radians(90.0 - longitude_deg)
        return radius * math.cos(math_angle), radius * math.sin(math_angle)

    # Two concentric guide rings, no zodiac sign labels -- matches the
    # confirmed reference: dot size/line weight carry the real signal,
    # the rings only separate "natal (fixed)" from "transiting today".
    natal_r = 0.50
    transit_r = 0.92

    for guide_r in (natal_r, transit_r):
        ax.add_patch(
            plt.Circle((0, 0), guide_r, fill=False, color=_RING_COLOR,
                       linewidth=0.7, linestyle=(0, (1, 3)))
        )

    def _point_radius(key: str) -> float:
        return transit_r if key.startswith("transit:") else natal_r

    def _glow(x, y, base_size, color, alpha_scale=1.0, zorder=2):
        for mult, alpha in ((3.2, 0.05), (2.0, 0.10), (1.0, 1.0)):
            ax.scatter(
                [x], [y], s=base_size * mult, color=color,
                alpha=alpha * alpha_scale if mult != 1.0 else min(1.0, alpha_scale),
                linewidths=0, zorder=zorder,
            )

    # Aspect lines first, so dots/labels draw on top. Width and alpha
    # both scale with the edge's real strength (_hit_strength) --
    # never with anything about how the reading text used it.
    for from_key, to_key, _aspect, strength in edges:
        _, from_lon, _ = points[from_key]
        _, to_lon, _ = points[to_key]
        x0, y0 = _xy(from_lon, _point_radius(from_key))
        x1, y1 = _xy(to_lon, _point_radius(to_key))
        ax.plot(
            [x0, x1], [y0, y1], color=_LINE_COLOR, solid_capstyle="round",
            linewidth=0.6 + 2.4 * strength, alpha=0.25 + 0.55 * strength, zorder=1,
        )

    for key, (label, lon, signal) in points.items():
        is_transit = key.startswith("transit:")
        r = _point_radius(key)
        x, y = _xy(lon, r)
        base_size = (55 if is_transit else 30) + (140 if is_transit else 80) * signal
        alpha_scale = 0.65 + 0.35 * signal
        _glow(x, y, base_size, _DOT_COLOR, alpha_scale=alpha_scale, zorder=3)

        label_r = r - 0.13 if not is_transit else r + 0.13
        lx, ly = _xy(lon, label_r)
        ax.text(
            lx, ly, label, color=_TEXT_COLOR if is_transit else _DIM_TEXT_COLOR,
            fontsize=9.5 if is_transit else 8, ha="center", va="center", zorder=4,
        )

    title = date_label or ""
    ax.text(
        0, 1.30, title, color=_TEXT_COLOR, fontsize=15, ha="center", va="center",
        fontweight="bold", fontfamily="serif",
    )

    if headline_thread is not None:
        caption = _caption_for_thread(headline_thread, hits)
    else:
        caption = "No headline thread today."
    ax.text(
        0, -1.30, caption, color=_DIM_TEXT_COLOR, fontsize=9.5, ha="center",
        va="center", fontstyle="italic", wrap=True,
    )

    legend_y = -1.20
    ax.scatter([-0.55], [legend_y], s=40, color=_DOT_COLOR, alpha=0.55, linewidths=0)
    ax.text(-0.49, legend_y, "natal (inner ring, fixed)", color=_DIM_TEXT_COLOR,
            fontsize=8, ha="left", va="center")
    ax.scatter([0.55], [legend_y], s=110, color=_DOT_COLOR, linewidths=0)
    ax.text(0.61, legend_y, "transiting today (outer ring)", color=_DIM_TEXT_COLOR,
            fontsize=8, ha="left", va="center")

    fig.tight_layout()
    fig.savefig(output_path, facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path
