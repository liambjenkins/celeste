from hellenistic.lunar_phase import is_void_of_course, moon_phase, moon_phase_three_way


def test_moon_phase_new():
    assert moon_phase(sun_longitude=100.0, moon_longitude=105.0) == "new"


def test_moon_phase_full():
    assert moon_phase(sun_longitude=100.0, moon_longitude=280.0) == "full"


def test_moon_phase_three_way_collapses_waxing_and_full():
    assert moon_phase_three_way("new") == "new"
    assert moon_phase_three_way("waxing") == "waxing_to_full"
    assert moon_phase_three_way("full") == "waxing_to_full"
    assert moon_phase_three_way("waning") == "waning"
    assert moon_phase_three_way("balsamic") == "waning"


def test_voc_true_when_no_aspect_completes_within_the_window():
    # Moon at 10 degrees Cancer (longitude 100), speed 13/day. Sun sits
    # in Gemini (longitude 80) -- in aversion to the Moon's current
    # sign (Cancer), and in a genuine sextile relationship to the
    # Moon's NEXT sign (Leo), but the exact sextile point (Sun + 60 =
    # 140) is 40 degrees of Moon-travel away -- past the 30-degree
    # window, so it does not count as completing.
    moon_longitude = 100.0
    moon_speed = 13.0
    other_bodies = {
        "sun": {"longitude": 80.0, "longitude_speed": 0.0},
    }
    assert is_void_of_course(moon_longitude, moon_speed, other_bodies) is True


def test_voc_false_when_completion_falls_just_past_a_sign_boundary():
    # This is the specific case the fixed-window rewrite exists for
    # (per an engineering note citing Demetra George, "Ancient
    # Astrology in Theory and Practice" Vol. 1, Ch. 28): Moon at 29
    # degrees Aries, 1 degree from leaving the sign. The OLD sign-
    # boundary-cutoff implementation would call this void (nothing
    # completes in the 1 degree left in Aries). The Sun sits at 45
    # degrees (Taurus) -- in aversion to Aries, but the Moon conjoins
    # it (same sign, Taurus) about 17 degrees of travel later, well
    # inside the 30-degree window and just past the sign cusp -- so
    # the corrected Hellenistic method (unlike the popular modern one)
    # correctly calls this NOT void.
    moon_longitude = 29.0
    moon_speed = 13.0
    other_bodies = {
        "sun": {"longitude": 45.0, "longitude_speed": 1.0},
    }
    assert is_void_of_course(moon_longitude, moon_speed, other_bodies) is False


def test_voc_false_when_an_applying_aspect_completes_within_current_sign():
    # Ordinary case, unaffected by the fixed-window change: Moon early
    # in Aries, applying to a sextile with Venus in Gemini (a valid
    # whole-sign relationship to the Moon's CURRENT sign) that
    # completes almost immediately.
    moon_longitude = 0.5
    moon_speed = 13.0
    other_bodies = {
        "venus": {"longitude": 61.0, "longitude_speed": 0.0},
    }
    assert is_void_of_course(moon_longitude, moon_speed, other_bodies) is False
