from hellenistic.fortune_houses import build_fortune_houses, house_from_fortune, is_angular_to_fortune
from hellenistic.houses import build_house_occupancy


def test_house_occupancy_flags_empty_houses_and_points_to_ruler():
    # Sun in Cancer (sign_index 3, house 3 if Cancer sits in house 3);
    # simplified two-body fixture: Sun in the house-3 sign, Moon
    # (Cancer's domicile ruler) elsewhere, so house 3 is occupied but
    # house 1 (empty) must point to whichever house ITS ruler sits in.
    house_signs = {
        "1": "Taurus", "2": "Gemini", "3": "Cancer", "4": "Leo", "5": "Virgo", "6": "Libra",
        "7": "Scorpio", "8": "Sagittarius", "9": "Capricorn", "10": "Aquarius", "11": "Pisces", "12": "Aries",
    }
    bodies = {
        "sun": {"house": 3},
        "venus": {"house": 2},  # Venus rules house 1 (Taurus) but sits in house 2
    }

    occupancy = build_house_occupancy(bodies, house_signs)

    assert occupancy["3"]["is_empty"] is False
    assert occupancy["3"]["occupants"] == ["sun"]

    # House 1 (Taurus, ruled by Venus) has no occupant -- must be
    # flagged empty AND point to where Venus (its ruler) actually is.
    assert occupancy["1"]["ruler"] == "venus"
    assert occupancy["1"]["is_empty"] is True
    assert occupancy["1"]["ruler_house"] == 2


def test_house_occupancy_multiple_occupants():
    house_signs = {str(i): sign for i, sign in enumerate(
        ["Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
         "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries"], start=1
    )}
    bodies = {"venus": {"house": 2}, "mars": {"house": 2}}

    occupancy = build_house_occupancy(bodies, house_signs)
    assert set(occupancy["2"]["occupants"]) == {"venus", "mars"}
    assert occupancy["2"]["is_empty"] is False


def test_house_from_fortune_anchors_at_fortune_not_ascendant():
    # Fortune in sign index 5 (Virgo) -> Fortune's own sign is house 1
    # from Fortune, regardless of where the Ascendant is.
    assert house_from_fortune(sign_index=5, fortune_sign_index=5) == 1
    assert house_from_fortune(sign_index=8, fortune_sign_index=5) == 4  # 3 signs forward -> 4th house


def test_is_angular_to_fortune():
    fortune_sign_index = 5
    assert is_angular_to_fortune(5, fortune_sign_index) is True   # Fortune's own sign: 1st
    assert is_angular_to_fortune(8, fortune_sign_index) is True   # 4th
    assert is_angular_to_fortune(11, fortune_sign_index) is True  # 7th
    assert is_angular_to_fortune(2, fortune_sign_index) is True   # 10th
    assert is_angular_to_fortune(6, fortune_sign_index) is False  # 2nd -- succedent, not angular


def test_build_fortune_houses_parallels_ascendant_house_signs_shape():
    houses = build_fortune_houses(fortune_sign_index=0)
    assert houses["1"] == "Aries"
    assert houses["4"] == "Cancer"
    assert len(houses) == 12
