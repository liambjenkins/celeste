from datetime import datetime, timedelta, timezone

from hellenistic.zr import LEVEL_UNIT_DAYS, SIGN_YEARS, _raw_period_sequence, locate_period


def test_sign_years_sum_to_211():
    # The "full lap" total the loosing-of-the-bond rule is anchored to.
    assert sum(SIGN_YEARS.values()) == 211


def test_raw_sequence_starts_at_given_sign_and_advances_forward():
    sequence = _raw_period_sequence(start_sign_index=0)
    first_five = [next(sequence) for _ in range(5)]
    signs = [s for s, _ in first_five]
    assert signs == [0, 1, 2, 3, 4]
    assert all(is_loosing is False for _, is_loosing in first_five)


def test_loosing_of_the_bond_fires_after_a_full_lap():
    sequence = _raw_period_sequence(start_sign_index=0)
    twelve = [next(sequence) for _ in range(12)]
    thirteenth_sign, thirteenth_is_loosing = next(sequence)

    # The 13th period (right after a full 12-sign lap) must NOT repeat
    # the start sign (index 0) -- it must jump to the opposite sign
    # (index 6) instead, and be flagged as the loosing event.
    assert thirteenth_sign == 6
    assert thirteenth_is_loosing is True
    assert all(is_loosing is False for _, is_loosing in twelve)


def test_locate_period_within_first_period():
    birth = datetime(2000, 1, 1, tzinfo=timezone.utc)
    target = birth + timedelta(days=10)
    period = locate_period(start_sign_index=0, level=3, level_start_time=birth, target_time=target)
    # Level 3 (days): Aries = 15 raw units = 15 days at this level.
    assert period["sign_index"] == 0
    assert period["is_loosing_of_bond"] is False


def test_locate_period_crosses_into_next_period():
    birth = datetime(2000, 1, 1, tzinfo=timezone.utc)
    # Aries at level 3 (days) lasts 15 days; 20 days in should be Taurus.
    target = birth + timedelta(days=20)
    period = locate_period(start_sign_index=0, level=3, level_start_time=birth, target_time=target)
    assert period["sign_index"] == 1


def test_level_unit_days_nest_consistently():
    # 12 months of 30 days each must equal exactly one 360-day year --
    # the whole point of using a fixed 360-day ZR year instead of the
    # real 365.242-day tropical year (see zr.py's module docstring).
    assert LEVEL_UNIT_DAYS[1] == 12 * LEVEL_UNIT_DAYS[2]
    assert LEVEL_UNIT_DAYS[2] == 30 * LEVEL_UNIT_DAYS[3]
