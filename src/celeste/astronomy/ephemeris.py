from datetime import datetime

import swisseph as swe

from celeste.models.sky import SkySnapshot


class AstronomyEngine:
    """Calculates the astronomical state of the sky."""

    @staticmethod
    def get_sky_snapshot(moment: datetime) -> SkySnapshot:
        """
        Calculate planetary positions for a given UTC datetime.
        """

        julian_day = swe.julday(
            moment.year,
            moment.month,
            moment.day,
            moment.hour
            + moment.minute / 60
            + moment.second / 3600,
        )

        def longitude(body: int) -> float:
            position, _ = swe.calc_ut(julian_day, body)
            return position[0]

        return SkySnapshot(
            sun=longitude(swe.SUN),
            moon=longitude(swe.MOON),
            mercury=longitude(swe.MERCURY),
            venus=longitude(swe.VENUS),
            mars=longitude(swe.MARS),
            jupiter=longitude(swe.JUPITER),
            saturn=longitude(swe.SATURN),
            uranus=longitude(swe.URANUS),
            neptune=longitude(swe.NEPTUNE),
            pluto=longitude(swe.PLUTO),
        )