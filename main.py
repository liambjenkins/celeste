from dotenv import load_dotenv
load_dotenv()

from datetime import datetime
import json
import warnings

# Silence noisy dependency warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from providers.astronomy import get_astronomy
from providers.atmosphere import get_atmosphere
from providers.marine import get_marine
from providers.hydrology import get_hydrology
from providers.tides import get_tides
from providers.elevation import get_elevation
from providers.earthquakes import get_earthquakes
from providers.geology import get_geology
from providers.land import get_land
from providers.biosphere import get_biosphere
from providers.solar import get_solar

from concepts.normaliser import normalise_observations
from concepts.summary import build_summary
from elements import classify_observations


# ============================================================
# CELESTE
# Environmental Reconstruction
# ============================================================

latitude = -37.8136
longitude = 144.9631

requested_time = datetime(
    1996,
    7,
    22,
    3,
    10
)


# ============================================================
# COLLECT RAW ENVIRONMENTAL OBSERVATIONS
# ============================================================

observations = {

    "astronomy": get_astronomy(
        1996,
        7,
        22,
        3.1667
    ),

    "atmosphere": get_atmosphere(
        latitude,
        longitude,
        requested_time
    ),

    "marine": get_marine(
        latitude,
        longitude,
        requested_time
    ),

    "hydrology": get_hydrology(
        latitude,
        longitude,
        requested_time
    ),

    "tides": get_tides(
        latitude,
        longitude,
        requested_time
    ),

    "earth": {
        "elevation": get_elevation(
            latitude,
            longitude
        ),

        "earthquakes": get_earthquakes(
            latitude,
            longitude,
            requested_time
        ),

        "geology": get_geology(
            latitude,
            longitude
        )
    },

    "land": get_land(
        latitude,
        longitude,
        requested_time
    ),

    "biosphere": get_biosphere(
        latitude,
        longitude,
        requested_time
    ),

    "space_weather": get_solar(
        requested_time
    )
}


# ============================================================
# NORMALISE + SUMMARISE
# ============================================================

concepts = normalise_observations(observations)

summary = build_summary(concepts)

elements = classify_observations(observations)


# ============================================================
# OUTPUT — SUMMARY ONLY
# ============================================================

output = {
    "requested_time": requested_time.isoformat(),

    "location": {
        "latitude": latitude,
        "longitude": longitude
    },

    "summary": summary,

    "elements": elements
}

print("✨ Celeste")
print("Environmental Reconstruction")
print()
print(json.dumps(output, indent=2, default=str))