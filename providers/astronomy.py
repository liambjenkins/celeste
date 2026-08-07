import swisseph as swe


def get_astronomy(year, month, day, hour):

    julian_day = swe.julday(
        year,
        month,
        day,
        hour
    )

    bodies = {
        "sun": swe.SUN,
        "moon": swe.MOON,
        "mercury": swe.MERCURY,
        "venus": swe.VENUS,
        "mars": swe.MARS,
        "jupiter": swe.JUPITER,
        "saturn": swe.SATURN,
        "uranus": swe.URANUS,
        "neptune": swe.NEPTUNE,
        "pluto": swe.PLUTO
    }

    observations = {}

    for name, body in bodies.items():

        data = swe.calc_ut(
            julian_day,
            body
        )[0]

        observations[name] = {
            "longitude": data[0],
            "latitude": data[1],
            "distance_au": data[2],
            "longitude_speed": data[3],
            "latitude_speed": data[4],
            "distance_speed": data[5]
        }

    return {
        "julian_day": julian_day,
        "bodies": observations
    }