from dotenv import load_dotenv
load_dotenv()
from datetime import datetime
import json
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
from providers.astronomy import get_astronomy
from providers.atmosphere import get_atmosphere
from providers.marine import get_marine
from providers.earthquakes import get_earthquakes
from providers.geology import get_geology
from providers.land import get_land
from providers.biosphere import get_biosphere
from providers.solar import get_solar
from concepts.normaliser import normalise_observations
from concepts.summary import build_summary
from elements import classify_observations
from convergence.engine import build_convergence
# ------------------------------------------------------------
# CELESTE — Environmental Reconstruction
# ------------------------------------------------------------
LATITUDE = -37.8136
LONGITUDE = 144.9631
REQUESTED_TIME = datetime(1996, 7, 22, 3, 10)
# ------------------------------------------------------------
# COLLECT
# ------------------------------------------------------------
observations = {
    "astronomy": get_astronomy(1996, 7, 22, 3.1667),
    "atmosphere": get_atmosphere(
        LATITUDE, LONGITUDE, REQUESTED_TIME
    ),
    "marine": get_marine(
        LATITUDE, LONGITUDE, REQUESTED_TIME
    ),
    "geology": get_geology(
        LATITUDE, LONGITUDE
    ),
    "earthquake": get_earthquakes(
        LATITUDE, LONGITUDE, REQUESTED_TIME
    ),
    "land": get_land(
        LATITUDE, LONGITUDE, REQUESTED_TIME
    ),
    "biosphere": get_biosphere(
        LATITUDE, LONGITUDE, REQUESTED_TIME
    ),
    "solar_activity": get_solar(
        REQUESTED_TIME
    ),
}
# ------------------------------------------------------------
# PROCESS
# ------------------------------------------------------------
normalised = normalise_observations(observations)
summary = build_summary(normalised)
elements = classify_observations(normalised)
convergence = build_convergence(normalised)
# ------------------------------------------------------------
# OUTPUT
# ------------------------------------------------------------
result = {
    "requested_time": REQUESTED_TIME.isoformat(),
    "location": {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
    },
    "summary": summary,
    "elements": elements,
    "convergence": convergence,
}
print("✨ Celeste")
print("Environmental Reconstruction")
print()
print(
    json.dumps(
        result,
        indent=2,
        default=str,
    )
)