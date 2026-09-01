"""
Tests for daily.py's Exhibit A fix (2026-09-01 live incident): a real
reading built its entire "partnership under real pressure right now"
narrative on a single 0.3-weight minor aspect (Mars sesquiquadrate
Descendant) while a genuine 4-hit, 2.70-score convergence on natal
Juno sat unused in the same prompt. Root cause: every standout hit got
the SAME full grounding block (sign/house/aspect meaning) regardless
of whether it was the primary thread, so a wall of equally-detailed
evidence made the weak hit look just as headline-worthy as the real
one.

Fix (Option A from "Celeste — Exhibit A Fix Options"): only the
PRIMARY THREAD's own hit(s) get full _render_hit_block grounding;
every other hit is still shown (real, available as supporting
texture) but compressed to _render_hit_core_line's bare fact only, no
meaning-notes. Paired with a hard-constraint instruction line naming
the primary thread as the ONLY permitted headline source.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astrology.chart import build_chart
from astrology.time import local_to_utc
from chinese.pillars import build_four_pillars
import daily
from daily import _render_hit_block, _render_hit_core_line, build_daily_reading

print("=== DAILY HEADLINE SCOPE ===")


def build_natal(local_dt, tz, lat, lon):
    aware = local_to_utc(local_dt, tz)
    utc = aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware
    return build_chart(utc, lat, lon, house_system="placidus")


MELBOURNE = build_natal(datetime(1996, 7, 22, 3, 10), "Australia/Melbourne", -37.7392, 144.7967)
MELBOURNE_PILLARS = build_four_pillars(MELBOURNE, datetime(1996, 7, 22, 3, 10))

# 2026-09-01: the real, locked Exhibit A date -- confirmed directly to
# produce a real 4-hit primary thread (natal juno: Saturn conjunction,
# Mars square, Jupiter trine, Mercury quincunx) plus 9 other real
# standout hits, including the Mars/Descendant minor aspect the actual
# incident's reading was built around.
EXHIBIT_A_DAY = datetime(2026, 9, 1, 3, 9, 44, tzinfo=timezone.utc)


# Captured via the same spy pattern this session's other daily tests
# use (test_daily_house_claims.py etc): build_daily_reading mutates
# its OWN internal hit dicts in place (setting natal_sign_note,
# aspect_meaning_note, ...) -- a fresh compute_daily_hits() call has
# none of that, so the real internal hits + the real headline_thread +
# the real rendered prompt text all need to come from this same call.
captured = {}
real_render = daily._render_daily_narrative_input


def _spy(narrative_claims, hits=None, headline_thread=None, western_arc_standing=None, daily_mode_depth=None, standing_claim_ids=None):
    rendered = real_render(narrative_claims, hits, headline_thread, western_arc_standing, daily_mode_depth, standing_claim_ids)
    captured["hits"] = hits
    captured["headline_thread"] = headline_thread
    captured["rendered"] = rendered
    return rendered


with patch("daily._render_daily_narrative_input", side_effect=_spy):
    build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, EXHIBIT_A_DAY, use_synthesis=True)

hits = captured["hits"]
headline_thread = captured["headline_thread"]
rendered = captured["rendered"]

assert headline_thread is not None and headline_thread["label"] == "natal juno", (
    f"test assumption broken -- expected the locked natal-juno convergence as today's headline, got {headline_thread}"
)
primary_hit_ids = set(headline_thread["hit_ids"])
assert len(primary_hit_ids) == 4, f"expected the real 4-hit juno convergence, got {primary_hit_ids}"
print(f"check the locked Exhibit A date reproduces the real natal-juno primary thread ({headline_thread['score']:.2f})")

descendant_hit = next(
    (h for h in hits if h["kind"] == "transit_aspect" and h["resolution"]["nearest_natal_point"] == "descendant"),
    None,
)
assert descendant_hit is not None, "test assumption broken -- expected the real Mars/Descendant hit from the incident"
assert descendant_hit["hit_id"] not in primary_hit_ids, "the Descendant hit must NOT be part of the primary thread"


# --- _render_hit_core_line / _render_hit_block: the split itself ---

core_line = _render_hit_core_line(descendant_hit)
full_block = _render_hit_block(descendant_hit)
assert full_block.startswith(core_line), "the full block must still start with the exact same core line"
assert len(full_block) > len(core_line), "the full block must carry more (meaning-note) content than the core line"
assert "sign meaning:" not in core_line and "aspect means:" not in core_line and "OWN birth house:" not in core_line, (
    "the core (compressed) line must carry NO interpretive meaning-notes"
)
assert "sign meaning:" in full_block or "aspect means:" in full_block or "OWN birth house:" in full_block, (
    "the full block must still carry real meaning-note content for this hit"
)
print("check _render_hit_core_line is the bare fact only; _render_hit_block adds real meaning-notes on top")


# --- The rendered prompt: primary thread gets full detail, every
# other hit is compressed, the hard-rule instruction is present ---

assert "HARD RULE" in rendered and "PRIMARY THREAD" in rendered
assert "Other real hits today (supporting texture only" in rendered
print("check the rendered prompt carries the PRIMARY THREAD anchor, the HARD RULE instruction, and the compressed-section header")

hits_section = rendered[rendered.find("# Today's active astrological hits"):]
primary_section = hits_section[:hits_section.find("# Other real hits today")]
other_section = hits_section[hits_section.find("# Other real hits today"):]

for hit_id in primary_hit_ids:
    hit = next(h for h in hits if h["hit_id"] == hit_id)
    assert _render_hit_block(hit) in primary_section, f"primary-thread hit {hit_id} must render with full grounding detail"
print("check every primary-thread hit renders with its full grounding block in the PRIMARY THREAD section")

assert core_line in other_section
assert full_block not in other_section, "a non-primary hit must NOT carry its full grounding block in the compressed section"
for hit in hits:
    if hit["hit_id"] not in primary_hit_ids:
        assert _render_hit_block(hit) not in rendered, (
            f"non-primary hit {hit['hit_id']} must never appear with full grounding detail anywhere in the prompt"
        )
print("check every non-primary hit (including the real Mars/Descendant hit from the incident) renders compressed only, everywhere in the prompt")


# --- No headline_thread at all (e.g. a day with no transit_aspect
# hits): every hit keeps full detail -- no primary/secondary split to
# draw, matching pre-fix behavior for this edge case ---

no_thread_rendered = real_render([], hits[:2], None, None, "full", set())
assert "HARD RULE" not in no_thread_rendered and "PRIMARY THREAD" not in no_thread_rendered
for hit in hits[:2]:
    assert _render_hit_block(hit) in no_thread_rendered, "every hit must keep full detail when there's no headline_thread at all"
print("check with no headline_thread at all, every hit keeps full grounding detail (no primary/secondary split)")


# --- End to end through build_daily_reading: no crash, same
# attribution/claims behavior as before (this fix only changes what's
# SENT to the model, never result['claims']) ---

result = build_daily_reading(MELBOURNE, MELBOURNE_PILLARS, EXHIBIT_A_DAY, use_synthesis=False)
assert result["claims"], "result['claims'] must still be populated -- this fix doesn't touch attribution"
print("check build_daily_reading still runs end to end without crashing on the locked Exhibit A date")

print()
print("DAILY HEADLINE SCOPE: OK")
