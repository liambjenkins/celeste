import swisseph as swe


print("✨ Celeste")
print("Astronomical Reconstruction")
print()


# Birth moment
year = 1996
month = 7
day = 22
hour = 3.1667  # 3:10 AM in decimal hours


# Convert to Julian Day
julian_day = swe.julday(
    year,
    month,
    day,
    hour
)


print("Julian Day:")
print(julian_day)
print()


# Celestial bodies to capture
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


# Calculate observations
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


# Output
print("Celeste Astronomy Observation:")
print()

for body, data in observations.items():
    print(body.upper())
    print(data)
    print()