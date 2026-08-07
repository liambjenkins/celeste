from celeste.formatter.sky_formatter import SkyFormatter
from celeste.profiles.liam import LIAM
from celeste.astronomy.ephemeris import AstronomyEngine


def test_sky_formatter():

    sky = AstronomyEngine.get_sky_snapshot(
        LIAM.birth.moment
    )

    output = SkyFormatter.format(sky)

    print(output)

    assert "Sun:" in output
    assert "Moon:" in output