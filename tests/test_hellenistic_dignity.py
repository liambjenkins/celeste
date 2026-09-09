from hellenistic.constants import bound_lord, decan_lord
from hellenistic.dignity import resolve_dignity


def test_egyptian_bounds_aries():
    assert bound_lord("Aries", 0) == "jupiter"
    assert bound_lord("Aries", 5.9) == "jupiter"
    assert bound_lord("Aries", 6) == "venus"
    assert bound_lord("Aries", 29.9) == "saturn"


def test_egyptian_bounds_virgo_corrected():
    # Virgo's Venus segment is 7-17 (verified against two independent
    # sources during this build; an earlier recollection of 7-13 was
    # wrong -- this pins the corrected value down as a regression guard.
    assert bound_lord("Virgo", 7) == "venus"
    assert bound_lord("Virgo", 16.9) == "venus"
    assert bound_lord("Virgo", 17) == "jupiter"


def test_chaldean_decans_generative_rule():
    # Aries decan 1 = Mars (the anchor of the whole generative rule).
    assert decan_lord("Aries", 0) == "mars"
    assert decan_lord("Aries", 9.9) == "mars"
    assert decan_lord("Aries", 10) == "sun"
    assert decan_lord("Aries", 20) == "venus"
    # Cancer's decans: Venus, Mercury, Moon (a commonly-cited check).
    assert decan_lord("Cancer", 0) == "venus"
    assert decan_lord("Cancer", 10) == "mercury"
    assert decan_lord("Cancer", 20) == "moon"


def test_domicile_beats_everything():
    dignity = resolve_dignity("sun", "Leo", 15.0, chart_sect="day")
    assert dignity["status"] == "domicile"
    assert dignity["in_own_domicile"] is True


def test_detriment_when_no_positive_dignity():
    # Saturn in Cancer at 10 degrees: Cancer's bound at 10 is Venus's
    # (7-13) and its decan is Mercury's, so Saturn holds no positive
    # dignity here -- and Cancer is Saturn's detriment (opposite its
    # domicile pair, Capricorn/Aquarius). At 26-30 Saturn would hold
    # Cancer's OWN bound instead, which correctly outranks detriment
    # (see test_bound_outranks_detriment below) -- 10 degrees avoids
    # that overlap deliberately.
    dignity = resolve_dignity("saturn", "Cancer", 10.0, chart_sect="night")
    assert dignity["in_detriment"] is True
    assert dignity["status"] == "detriment"


def test_bound_outranks_detriment():
    # Same placement, but at 27 degrees -- inside Saturn's own Cancer
    # bound (26-30) -- demonstrates the deliberate resolution order:
    # a positive dignity (bound) reported ahead of detriment even
    # though the sign placement is still technically detriment
    # (in_detriment stays True; `status` reports the stronger fact).
    dignity = resolve_dignity("saturn", "Cancer", 27.0, chart_sect="night")
    assert dignity["in_detriment"] is True
    assert dignity["status"] == "bound"


def test_fall_sign():
    # Mars falls in Cancer (opposite its exaltation, Capricorn). By
    # DAY, Cancer's water triplicity is Venus's (not Mars's night
    # rulership), and 29 degrees is Jupiter's decan / Saturn's bound,
    # so Mars holds no positive dignity here at all.
    dignity = resolve_dignity("mars", "Cancer", 29.0, chart_sect="day")
    assert dignity["in_fall"] is True
    assert dignity["status"] == "fall"


def test_triplicity_day_vs_night():
    # Fire triplicity: Sun rules by day, Jupiter by night (Dorothean
    # scheme). Sagittarius (fire, but Jupiter's own domicile) at 20
    # degrees holds no Sun dignity at all except the day-triplicity
    # rulership -- and at night, Sun gets nothing there (peregrine),
    # since night-fire belongs to Jupiter, not Sun.
    day_dignity = resolve_dignity("sun", "Sagittarius", 20.0, chart_sect="day")
    night_dignity_sun = resolve_dignity("sun", "Sagittarius", 20.0, chart_sect="night")
    assert day_dignity["status"] == "triplicity"
    assert night_dignity_sun["status"] == "peregrine"

    # Leo (fire, but Sun's own domicile) at 20 degrees holds no
    # Jupiter dignity except night-triplicity rulership.
    night_dignity_jupiter = resolve_dignity("jupiter", "Leo", 20.0, chart_sect="night")
    assert night_dignity_jupiter["status"] == "triplicity"
