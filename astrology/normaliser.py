ZODIAC_SIGNS = (
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
)


def longitude_to_zodiac(longitude: float):
    longitude = longitude % 360.0

    sign_index = int(longitude // 30)
    within_sign = longitude % 30

    degree = int(within_sign)
    minutes_float = (within_sign - degree) * 60
    minute = int(minutes_float)
    second = round((minutes_float - minute) * 60)

    if second == 60:
        second = 0
        minute += 1

    if minute == 60:
        minute = 0
        degree += 1

    return {
        "sign": ZODIAC_SIGNS[sign_index],
        "sign_index": sign_index,
        "degree": degree,
        "minute": minute,
        "second": second,
        "longitude": longitude,
    }


def longitude_in_house(
    longitude: float,
    cusps: dict,
):
    """Determine which Placidus house contains a longitude."""

    longitude = longitude % 360.0

    cusp_values = [
        cusps[str(index)]
        for index in range(1, 13)
    ]

    for index in range(12):
        start = cusp_values[index]
        end = cusp_values[(index + 1) % 12]

        if end <= start:
            end += 360

        test_longitude = longitude

        if test_longitude < start:
            test_longitude += 360

        if start <= test_longitude < end:
            return index + 1

    return 12


def normalise_body(
    name: str,
    data: dict,
    cusps: dict,
):
    """Normalise one astronomical object into a chart concept."""

    longitude = data["longitude"]

    zodiac = longitude_to_zodiac(longitude)

    house = longitude_in_house(
        longitude,
        cusps,
    )

    speed = data.get("longitude_speed")

    return {
        "name": name,
        "longitude": longitude,
        "sign": zodiac["sign"],
        "sign_index": zodiac["sign_index"],
        "degree": zodiac["degree"],
        "minute": zodiac["minute"],
        "second": zodiac["second"],
        "house": house,
        "longitude_speed": speed,
        "retrograde": (
            speed is not None and speed < 0
        ),
    }
