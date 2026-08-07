from datetime import datetime

from celeste.astronomy.ephemeris import AstronomyEngine


def test_astronomy_engine():
    moment = datetime(1996, 7, 22, 3, 10)

    sky = AstronomyEngine.get_sky_snapshot(moment)

    print(sky)

    assert sky.sun > 0
    assert sky.moon > 0