from hellenistic.lunar_phase import is_void_of_course, moon_phase


def test_moon_phase_new():
    assert moon_phase(sun_longitude=100.0, moon_longitude=105.0) == "new"


def test_moon_phase_full():
    assert moon_phase(sun_longitude=100.0, moon_longitude=280.0) == "full"


def test_voc_true_when_no_completing_aspect_before_sign_exit():
    # Moon at 29 degrees of its sign (1 degree from exit, moving ~13
    # deg/day so it exits in a couple of hours) with no other planet
    # anywhere near a whole-sign aspect relationship -- aversion only.
    moon_longitude = 29.0  # late Aries
    moon_speed = 13.0
    other_bodies = {
        "sun": {"longitude": 45.0, "longitude_speed": 1.0},  # Taurus -- aversion (1 sign apart)
    }
    assert is_void_of_course(moon_longitude, moon_speed, other_bodies) is True


def test_voc_false_when_an_applying_aspect_will_complete_in_time():
    # Moon at 0 degrees Aries (30 degrees / ~13deg/day ~= 2.3 days
    # until sign exit), applying to a sextile with a planet at 61
    # degrees (Gemini, sign-sextile to Aries) that will perfect well
    # within that window.
    moon_longitude = 0.5
    moon_speed = 13.0
    other_bodies = {
        "venus": {"longitude": 61.0, "longitude_speed": 0.0},
    }
    assert is_void_of_course(moon_longitude, moon_speed, other_bodies) is False
