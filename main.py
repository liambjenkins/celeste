from datetime import datetime
import json

from providers.astronomy import get_astronomy
from providers.atmosphere import get_atmosphere
from providers.marine import get_marine
from providers.hydrology import get_hydrology
from providers.tides import get_tides


print("✨ Celeste")
print("Environmental Reconstruction")
print()


year = 1996
month = 7
day = 22
hour = 3.1667


latitude = -37.8136
longitude = 144.9631


moment = datetime(
    year,
    month,
    day,
    3,
    10
)


celeste = {

    "astronomy": get_astronomy(
        year,
        month,
        day,
        hour
    ),

    "atmosphere": get_atmosphere(
        latitude,
        longitude,
        moment
    ),

    "marine": get_marine(
        latitude,
        longitude,
        moment
    ),

    "hydrology": get_hydrology(
        latitude,
        longitude,
        moment
    ),

    "tides": get_tides(
        latitude,
        longitude,
        moment
    )

}


print("Celeste Snapshot:")
print()


print(
    json.dumps(
        celeste,
        indent=2
    )
)