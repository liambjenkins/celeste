from celeste.app import Celeste
from celeste.profiles.liam import LIAM


def test_celeste_birth_sky_text():

    celeste = Celeste(LIAM)

    output = celeste.birth_sky_text()

    print(output)

    assert "Sun:" in output
    assert "Moon:" in output