"""
Celeste daily-mode knowledge seed (Western): today's real moon phase,
and a first tranche of transit-to-natal-key-point fragments.

Distinct from knowledge/claims/seeds/astrology_timing.py's existing
"transit_technique_core" claim (what a transit IS, in general) and
from the generic per-aspect-type claims (astrology_aspect_trine.json
etc., already extended to match transit_aspect:<type> tags) — those
stay as the baseline fallback for any transiting-body/target combo
that doesn't have its own daily-mode fragment yet (lenses/features.py
pushes both the specific daily_transit_aspect:<body>:<aspect>:<role>
tag and the generic transit_aspect:<aspect> tag for exactly this
reason). This seed adds real, Celeste-voice, PAIR-specific content
for a first tranche, not the full combinatorial space.

Scope of this tranche, matching the daily-mode brief's own scoping:
one ease-flavored and one tension-flavored fragment per natal target
role (Sun, Moon, Ascendant, chart ruler) — 8 fragments total, picked
from among the 5 in-scope transiting bodies (Sun, Mercury, Venus,
Mars, Moon) for real variety rather than repeating the same
transiting body every time. The remaining transiting-body/aspect/
target combinations are real, cheap-to-extend follow-up work using
the exact same process — not written now to avoid producing 100+
claims of declining quality/verification rigor in one pass.

Sourcing: transit-astrology's compositional convention (a transiting
body's own significance, meeting a natal point's own significance,
through an aspect's own classical mechanism) is cross-source
consistent and well documented across mainstream modern astrological
literature -- verified via web search during curation (spot-checked
transiting Mars square natal Moon specifically against 9 independent
sources, all converging on the same "urgency/action vs. emotional-
safety" reading used below). Both halves of each composition (the
body's core signification, the aspect's tension/ease mechanism) are
already independently source-backed elsewhere in this exact codebase
(Lilly 1647 for aspects; Tompkins/standard convention for planetary
significations) -- this seed composes them at the daily timescale,
it doesn't invent either half.

Moon phase meanings (new/waxing crescent/first quarter/waxing
gibbous/full/waning gibbous/last quarter/waning crescent as
beginning/building/deciding/refining/culminating/integrating/
releasing/resting) are standard, cross-source-consistent modern
astrological convention, not a single-author claim -- same sourcing
tier as this project's existing "modern_convention" claims (chart
shape, minor aspects, aspect patterns).

Run as a script to write ApprovedClaim JSON into
knowledge/claims/approved/.
"""

import json
from dataclasses import asdict
from pathlib import Path

from knowledge.claims.model import ApprovedClaim

APPROVED_DIR = Path(__file__).resolve().parent.parent / "approved"

claims: list[ApprovedClaim] = []


def _add(
    claim_id,
    statement,
    concept_ids=(),
    feature_ids=(),
    theme_tags=(),
    life_domain=None,
    source_id="",
    notes="",
):
    claims.append(
        ApprovedClaim(
            claim_id=f"astrology_{claim_id}",
            lens_id="astrology",
            statement=statement,
            concept_ids=tuple(concept_ids),
            feature_ids=tuple(feature_ids),
            source_ids=(source_id,),
            theme_tags=tuple(theme_tags),
            life_domain=life_domain,
            editorial_note=notes,
        )
    )


# ------------------------------------------------------------------
# Moon phase (today's real Sun-Moon phase, not the natal lunation
# feature)
# ------------------------------------------------------------------

_add(
    "daily_moon_phase_new",
    "Today's the kind of blank page you don't get very often. "
    "Whatever you start now gets to be genuinely new, not a patch "
    "on something old.",
    concept_ids=["daily_moon_phase"],
    feature_ids=["daily_moon_phase:new_moon"],
    theme_tags=["daily_mode"],
    life_domain="cyclicality",
    source_id="moon_phases_modern_convention",
)

_add(
    "daily_moon_phase_waxing_crescent",
    "Whatever you set in motion recently still needs tending, not "
    "results yet. This is a building day, not a proving day.",
    concept_ids=["daily_moon_phase"],
    feature_ids=["daily_moon_phase:waxing_crescent"],
    theme_tags=["daily_mode"],
    life_domain="cyclicality",
    source_id="moon_phases_modern_convention",
)

_add(
    "daily_moon_phase_first_quarter",
    "Something's asking for an actual decision today, not more "
    "thinking about it. This phase doesn't reward hesitation.",
    concept_ids=["daily_moon_phase"],
    feature_ids=["daily_moon_phase:first_quarter"],
    theme_tags=["daily_mode"],
    life_domain="cyclicality",
    source_id="moon_phases_modern_convention",
)

_add(
    "daily_moon_phase_waxing_gibbous",
    "You're close enough to something finishing that the temptation "
    "is to rush it. Today's for the last real adjustments, not for "
    "stopping early.",
    concept_ids=["daily_moon_phase"],
    feature_ids=["daily_moon_phase:waxing_gibbous"],
    theme_tags=["daily_mode"],
    life_domain="cyclicality",
    source_id="moon_phases_modern_convention",
)

_add(
    "daily_moon_phase_full",
    "Whatever's been building finally shows itself today, one way "
    "or another. This isn't a day that stays quiet.",
    concept_ids=["daily_moon_phase"],
    feature_ids=["daily_moon_phase:full_moon"],
    theme_tags=["daily_mode"],
    life_domain="cyclicality",
    source_id="moon_phases_modern_convention",
)

_add(
    "daily_moon_phase_waning_gibbous",
    "Today's better spent digesting what just happened than chasing "
    "what's next. There's real information in what you just lived "
    "through.",
    concept_ids=["daily_moon_phase"],
    feature_ids=["daily_moon_phase:waning_gibbous"],
    theme_tags=["daily_mode"],
    life_domain="cyclicality",
    source_id="moon_phases_modern_convention",
)

_add(
    "daily_moon_phase_last_quarter",
    "Something's overdue to be let go of, and today makes that "
    "harder to keep avoiding. Holding on costs more than releasing "
    "does right now.",
    concept_ids=["daily_moon_phase"],
    feature_ids=["daily_moon_phase:last_quarter"],
    theme_tags=["daily_mode"],
    life_domain="cyclicality",
    source_id="moon_phases_modern_convention",
)

_add(
    "daily_moon_phase_waning_crescent",
    "This is a rest day whether you take it or not. Push through it "
    "and you'll just be starting the next cycle already depleted.",
    concept_ids=["daily_moon_phase"],
    feature_ids=["daily_moon_phase:waning_crescent"],
    theme_tags=["daily_mode"],
    life_domain="cyclicality",
    source_id="moon_phases_modern_convention",
)

# ------------------------------------------------------------------
# Transit-to-natal-key-point fragments -- first tranche (8 of the
# larger combinatorial space; see module docstring)
# ------------------------------------------------------------------

_add(
    "daily_transit_venus_trine_sun",
    "Today, being liked doesn't take effort. Whatever you already "
    "are lands well, without you having to dress it up.",
    concept_ids=["daily_transit_aspects"],
    feature_ids=["daily_transit_aspect:venus:trine:sun"],
    theme_tags=["daily_mode"],
    life_domain="identity",
    source_id="transit_astrology_modern_convention",
)

_add(
    "daily_transit_mars_square_sun",
    "Just being yourself takes more defending than usual today. "
    "Something's pushing on you, and staying steady about who you "
    "are takes real effort.",
    concept_ids=["daily_transit_aspects"],
    feature_ids=["daily_transit_aspect:mars:square:sun"],
    theme_tags=["daily_mode"],
    life_domain="identity",
    source_id="transit_astrology_modern_convention",
)

_add(
    "daily_transit_venus_trine_moon",
    "Comfort finds you today without you chasing it. Whatever you "
    "actually need emotionally is easier to get than usual.",
    concept_ids=["daily_transit_aspects"],
    feature_ids=["daily_transit_aspect:venus:trine:moon"],
    theme_tags=["daily_mode"],
    life_domain="emotion",
    source_id="transit_astrology_modern_convention",
)

_add(
    "daily_transit_mars_square_moon",
    "Today, what you need to do and what you need to feel are "
    "pulling in different directions. Expect some real friction if "
    "you try to ignore either one.",
    concept_ids=["daily_transit_aspects"],
    feature_ids=["daily_transit_aspect:mars:square:moon"],
    theme_tags=["daily_mode"],
    life_domain="emotion",
    source_id="transit_astrology_modern_convention",
    notes=(
        "Spot-verified via web search during curation across 9 "
        "independent sources (Medium/Hermes Astrology, AstroLibrary, "
        "Astrology.com, AstroMatrix, Astro-Seek, Astrolis, MyAstro, "
        "Astrology King, Hiroki Niizato Astrology), all converging on "
        "the same core mechanism: Mars' urgency/action colliding with "
        "the Moon's need for emotional safety and rest."
    ),
)

_add(
    "daily_transit_sun_trine_ascendant",
    "You don't have to work to be noticed today. However you show "
    "up, it reads clearly, and it reads well.",
    concept_ids=["daily_transit_aspects"],
    feature_ids=["daily_transit_aspect:sun:trine:ascendant"],
    theme_tags=["daily_mode"],
    life_domain="persona",
    source_id="transit_astrology_modern_convention",
)

_add(
    "daily_transit_mars_opposition_ascendant",
    "Today, other people aren't just going along with you. Whatever "
    "you're pushing for, expect some real pushback, not just quiet "
    "agreement.",
    concept_ids=["daily_transit_aspects"],
    feature_ids=["daily_transit_aspect:mars:opposition:ascendant"],
    theme_tags=["daily_mode"],
    life_domain="persona",
    source_id="transit_astrology_modern_convention",
)

_add(
    "daily_transit_mercury_sextile_chart_ruler",
    "Saying what you actually mean is easier than usual today. The "
    "opening's there. You just have to actually use it.",
    concept_ids=["daily_transit_aspects"],
    feature_ids=["daily_transit_aspect:mercury:sextile:chart_ruler"],
    theme_tags=["daily_mode"],
    life_domain="communication",
    source_id="transit_astrology_modern_convention",
)

_add(
    "daily_transit_mars_square_chart_ruler",
    "Today, your usual way of getting things done doesn't just work "
    "on its own. Something's making you push harder than you'd like "
    "to.",
    concept_ids=["daily_transit_aspects"],
    feature_ids=["daily_transit_aspect:mars:square:chart_ruler"],
    theme_tags=["daily_mode"],
    life_domain="drive_and_ambition",
    source_id="transit_astrology_modern_convention",
)


if __name__ == "__main__":
    for claim in claims:
        path = APPROVED_DIR / f"{claim.claim_id}.json"
        data = asdict(claim)
        data["status"] = "approved"

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    print(f"Wrote {len(claims)} claims to {APPROVED_DIR}")
