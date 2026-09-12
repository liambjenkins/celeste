"""
End-to-end smoke test against the same real chart used elsewhere in
this codebase's astrology/*.py __main__ blocks (1996-07-22 03:10,
Melbourne, -37.7392/144.7967) -- not a hand-verified traditional
reading, but a fixed regression point: if these structural facts ever
change, something in the pipeline changed, not the sky.
"""

from datetime import datetime, timezone

from astrology.time import local_to_utc
from hellenistic.daily import build_daily_layer
from hellenistic.natal import build_natal_chart

LOCAL_TIME = datetime(1996, 7, 22, 3, 10)
LATITUDE, LONGITUDE = -37.7392, 144.7967


def _birth_utc():
    aware = local_to_utc(LOCAL_TIME, "Australia/Melbourne")
    return aware.replace(tzinfo=timezone.utc) if aware.tzinfo is None else aware


def test_natal_chart_structure_and_known_values():
    chart = build_natal_chart(_birth_utc(), LATITUDE, LONGITUDE)

    assert chart["sect"] == "night"
    assert chart["ascendant"]["sign"] == "Taurus"
    assert set(chart["planets"].keys()) == {
        "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
    }

    for planet, entry in chart["planets"].items():
        assert entry["sect_status"] in ("of_sect", "contrary_to_sect")
        assert entry["angularity"] in ("angular", "succedent", "cadent")
        assert entry["dignity"]["status"] in (
            "domicile", "exalted", "triplicity", "bound", "decan",
            "peregrine", "detriment", "fall",
        )
        assert entry["gender"] in ("masculine", "feminine")
        assert isinstance(entry["house_rulerships"], list)

    assert "bonding" in chart["planets"]["moon"]
    assert chart["prenatal_lunation"]["type"] in ("new", "full")


def test_reception_is_internally_consistent():
    chart = build_natal_chart(_birth_utc(), LATITUDE, LONGITUDE)

    for planet, entry in chart["planets"].items():
        mutual = entry["reception"]["mutual_reception_with"]
        if mutual is not None:
            # Mutual reception must be symmetric.
            other = chart["planets"][mutual]
            assert other["reception"]["mutual_reception_with"] == planet


def test_daily_layer_runs_against_natal_chart():
    birth_utc = _birth_utc()
    chart = build_natal_chart(birth_utc, LATITUDE, LONGITUDE)
    as_of = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)

    daily = build_daily_layer(chart, birth_utc, as_of)

    assert daily["profection"]["activated_house"] in range(1, 13)
    assert daily["zr_fortune"]["L1"]["current_period_lord"] in chart["planets"]
    assert daily["zr_spirit"]["L1"]["current_period_lord"] in chart["planets"]
    assert daily["lunar_phase_today"] in ("new", "waxing", "full", "waning", "balsamic")
    assert daily["lunar_phase_today_hellenistic"] in ("new", "full", "dark")
    assert isinstance(daily["void_of_course"], bool)

    # Today's LIVE solar phase (distinct from the natal chart's fixed
    # birth-moment solar_phase) -- added per an engineering note: Venus
    # oriental/occidental and Moon phase content both need this
    # checked against today's sky, not just birth.
    assert "venus" in daily["solar_phase_today"]
    assert daily["solar_phase_today"]["venus"]["visibility"] in ("oriental", "occidental")
    assert "bonding" in daily["solar_phase_today"]["moon"]
    assert len(daily["transits"]) == 7


def test_next_applying_aspect_is_a_real_whole_sign_aspect():
    chart = build_natal_chart(_birth_utc(), LATITUDE, LONGITUDE)

    for planet, entry in chart["planets"].items():
        next_aspect = entry["next_applying_aspect"]
        if next_aspect is None:
            continue
        assert next_aspect["phase"] == "applying"
        assert next_aspect in entry["aspects"]


def test_planet_conditions_are_built_for_every_planet():
    chart = build_natal_chart(_birth_utc(), LATITUDE, LONGITUDE)

    assert set(chart["planet_conditions"].keys()) == set(chart["planets"].keys())

    for planet, condition in chart["planet_conditions"].items():
        assert condition["nature"] in ("luminary", "benefic", "malefic", "common")
        assert condition["essential_dignity"]["status"] == chart["planets"][planet]["dignity"]["status"]
        assert condition["condition_of_domicile_lord"]["counteraction"] in ("helps", "hinders", "neutral")
        assert "judgment_grade" not in condition  # explicitly the assembly layer's job, not this engine's

    # The Moon has no self-referential lunar_aspects; every other
    # planet's lunar_aspects (if present) must actually be one of the
    # Moon's own recorded aspects to that planet.
    assert chart["planet_conditions"]["moon"]["lunar_aspects"] is None
    for planet, condition in chart["planet_conditions"].items():
        if planet == "moon":
            continue
        if condition["lunar_aspects"] is not None:
            assert condition["lunar_aspects"]["to_planet"] == planet
            assert condition["lunar_aspects"] in chart["planets"]["moon"]["aspects"]
