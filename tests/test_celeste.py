from celeste.app import Celeste
from celeste.profiles.liam import LIAM


def test_celeste_birth_sky():

    celeste = Celeste(LIAM)

    sky = celeste.birth_sky()

    assert sky.sun > 0