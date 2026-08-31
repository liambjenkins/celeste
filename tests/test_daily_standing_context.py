"""
Tests for daily.py's Synthesis Repair Brief Part 2.5 ("invented
timeliness") fix: real, natal-only/standing content (Big-3 sign+house,
Vedic Dasha, Vedic sidereal Big-3+bhava, Chinese Ten-God-in-position)
now reaches the synthesis prompt in its own labeled "# Standing
identity & context" section instead of the flat claims loop, so
synthesis has an explicit signal that these aren't today's news --
unless the same point is ALSO genuinely touched by a real hit today,
in which case it's legitimately hit-paired and stays in the flat
section instead.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.daily_hits import compute_daily_hits
from astrology.time import local_to_utc
from chinese.pillars import build_four_pillars
import daily
from daily import _render_daily_narrative_input, build_daily_reading

print("=== DAILY STANDING CONTEXT ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
MELBOURNE_PILLARS = build_four_pillars(MELBOURNE, datetime(1996, 7, 22, 3, 10))

# 2026-08-31: confirmed real date where Moon is hit-touched today
# (uranus trine moon) but Sun is not -- lets the same run exercise
# both the "hit-touched, stays out of standing" and "untouched,
# genuinely standing" branches against real data.
TEST_DAY = datetime(2026, 8, 31, tzinfo=timezone.utc)

hits_today = compute_daily_hits(MELBOURNE, TEST_DAY)
touched_roles = {h["resolution"].get("nearest_natal_point") for h in hits_today if h["resolution"].get("nearest_natal_point")}
assert "moon" in touched_roles, "test date must have a real hit touching natal Moon (confirmed earlier)"
assert "sun" not in touched_roles, "test date must have natal Sun untouched by any real hit today"
print("check test date's real hit-touch data: moon touched, sun untouched (as expected)")


captured = {}
real_render = daily._render_daily_narrative_input


def _spy(narrative_claims, hits=None, headline_thread=None, western_arc_standing=None, daily_mode_depth=None, standing_claim_ids=None):
    captured["standing_claim_ids"] = standing_claim_ids
    captured["narrative_claims"] = narrative_claims
    return real_render(narrative_claims, hits, headline_thread, western_arc_standing, daily_mode_depth, standing_claim_ids)


with patch("daily._render_daily_narrative_input", side_effect=_spy):
    result = build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, TEST_DAY, use_synthesis=True)

standing_ids = captured["standing_claim_ids"]
assert standing_ids, "expected real standing content on a normal date"

# Sun sign/house genuinely untouched today -- must be in the standing set.
sun_sign_ids = {c.claim_id for c in captured["narrative_claims"] if c.claim_id.startswith("astrology_sun_sign_")}
sun_house_ids = {c.claim_id for c in captured["narrative_claims"] if c.claim_id.startswith("astrology_sun_house_")}
assert sun_sign_ids and sun_sign_ids.issubset(standing_ids)
assert sun_house_ids and sun_house_ids.issubset(standing_ids)
print("check untouched natal Sun sign/house claims are in the standing set")

# Moon sign/house genuinely touched today by a real hit -- must NOT be
# in the standing set (legitimately paired to today's real activity).
moon_sign_ids = {c.claim_id for c in captured["narrative_claims"] if c.claim_id.startswith("astrology_moon_sign_")}
assert moon_sign_ids and not (moon_sign_ids & standing_ids)
print("check hit-touched natal Moon sign claim is EXCLUDED from the standing set (legitimately paired to today)")

# Vedic Dasha / sidereal Big-3 / Chinese Ten-God claims are always
# unconditionally standing -- no hit-pairing equivalent exists for them.
dasha_ids = {c.claim_id for c in captured["narrative_claims"] if c.claim_id.startswith("vedic_astrology_dasha_general_")}
ten_god_ids = {c.claim_id for c in captured["narrative_claims"] if "ten_god" in c.claim_id}
assert dasha_ids and dasha_ids.issubset(standing_ids)
assert ten_god_ids and ten_god_ids.issubset(standing_ids), f"ten god ids not fully standing: {ten_god_ids - standing_ids}"
print("check Vedic Dasha and Chinese Ten-God claims are always unconditionally standing")

# The rendered prompt text: every standing claim_id appears exactly
# once total (never duplicated between the standing section and the
# flat section below it).
rendered = real_render(
    captured["narrative_claims"], hits_today, None, None, "full", standing_ids
)
assert "# Standing identity & context" in rendered
claim_lines = [l for l in rendered.splitlines() if l.strip().startswith("- CLAIM_ID:")]
seen_ids = [l.split("CLAIM_ID: ")[1] for l in claim_lines]
assert len(seen_ids) == len(set(seen_ids)), "a claim_id appears more than once in the rendered prompt"
print(f"check rendered prompt: {len(seen_ids)} claim lines total, zero duplicates, standing header present")

# A day with no standing content at all (empty narrative_claims list,
# no standing_claim_ids) must not print the header or crash.
empty_render = real_render([], [], None, None, None, None)
assert "# Standing identity & context" not in empty_render
print("check no standing header is printed when there's nothing standing to show")

print()
print("DAILY STANDING CONTEXT: OK")
