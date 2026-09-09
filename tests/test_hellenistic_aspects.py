from hellenistic.aspects import applying_or_separating, sign_distance, whole_sign_aspect


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
