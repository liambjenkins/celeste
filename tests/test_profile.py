from celeste.profiles.liam import LIAM


def test_liam_profile():

    assert LIAM.name == "Liam"
    assert LIAM.birth.location.name == "Sunshine Hospital, St Albans"