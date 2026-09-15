import pytest

from hellenistic.aspects import applying_or_separating, degrees_to_exact, next_applying_aspect, sign_distance, whole_sign_aspect


def test_whole_sign_conjunction():
    assert whole_sign_aspect(0, 0) == ("conjunction", 0.0)


def test_whole_sign_sextile_and_trine():
    assert whole_sign_aspect(0, 2) == ("sextile", 60.0)
    assert whole_sign_aspect(0, 4) == ("trine", 120.0)


def test_whole_sign_opposition():
    assert whole_sign_aspect(0, 6) == ("opposition", 180.0)


def test_aversion_signs_have_no_aspect():
    # 1 sign apart (adjacent) and 5 signs apart are both aversion.
    assert whole_sign_aspect(0, 1) is None
    assert whole_sign_aspect(0, 5) is None
    assert whole_sign_aspect(0, 7) is None
    assert whole_sign_aspect(0, 11) is None


def test_sign_distance_wraps_correctly():
    assert sign_distance(0, 11) == 1
    assert sign_distance(1, 11) == 2


def test_applying_when_closing_the_gap():
    # Two bodies 58 degrees apart approaching an exact 60-degree
    # sextile: body_a moving away from body_b (increasing separation
    # would be separating); here body_a is behind and catching up.
    phase = applying_or_separating(
        longitude_a=10.0, speed_a=1.0, longitude_b=70.0, speed_b=0.0, exact_angle=60.0
    )
    assert phase == "applying"


def test_separating_when_past_exact():
    phase = applying_or_separating(
        longitude_a=15.0, speed_a=1.0, longitude_b=70.0, speed_b=0.0, exact_angle=60.0
    )
    assert phase == "separating"


def test_degrees_to_exact_is_never_negative_for_a_retrograde_body():
    # Regression guard: an earlier version returned speed_a *
    # time_to_exact unabsoluted, which went negative whenever body A
    # was retrograde (speed_a < 0) -- caught on a real chart where
    # Jupiter and Saturn (both retrograde) produced negative "degrees
    # to exact" values. Body A here is retrograde (speed -0.1) and 91
    # degrees from body B, applying toward an exact 90-degree square
    # (i.e. only 1 more degree of its own backward travel needed).
    result = degrees_to_exact(
        longitude_a=100.0, speed_a=-0.1, longitude_b=9.0, speed_b=0.0, exact_angle=90.0
    )
    assert result is not None
    assert result == pytest.approx(1.0)


def test_next_applying_aspect_picks_the_truly_closest_one_not_the_most_negative():
    # Regression guard for the same bug's downstream effect: with
    # negative degrees_to_exact values in play, a naive min() would
    # have favored the most-negative (least imminent) entry instead of
    # the one nearest to perfecting.
    aspects = [
        {"to_planet": "a", "phase": "applying", "degrees_to_exact": 5.0},
        {"to_planet": "b", "phase": "applying", "degrees_to_exact": 0.5},
        {"to_planet": "c", "phase": "separating", "degrees_to_exact": None},
    ]
    assert next_applying_aspect(aspects)["to_planet"] == "b"
