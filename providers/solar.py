from datetime import datetime
import json
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
NOAA_SOLAR_CYCLE_URL = (
    "https://services.swpc.noaa.gov/"
    "json/solar-cycle/observed-solar-cycle-indices.json"
)
def _load_json(url):
    """
    Load JSON from a public NOAA endpoint.
    Returns None if the request fails.
    """
    try:
        with urlopen(url, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except (URLError, HTTPError, TimeoutError, OSError, ValueError):
        return None
def _find_month(data, requested_time):
    """
    Find the monthly solar-cycle record matching requested_time.
    NOAA's observed solar-cycle dataset uses a yyyy-mm time tag.
    """
    if not data:
        return None
    target = requested_time.strftime("%Y-%m")
    for record in data:
        if not isinstance(record, dict):
            continue
        time_tag = str(record.get("time-tag", ""))
        if time_tag.startswith(target):
            return record
    return None
def get_solar(requested_time):
    """
    Reconstruct historical solar / space-weather context.
    Current implementation uses NOAA SWPC's long-term observed
    solar-cycle dataset, which provides monthly solar activity
    indices such as sunspot number and 10.7 cm radio flux.
    This deliberately returns None for unavailable fields rather
    than inventing values.
    """
    data = _load_json(NOAA_SOLAR_CYCLE_URL)
    if data is None:
        return {
            "source": "NOAA Space Weather Prediction Center",
            "available": False,
            "reason": "Unable to retrieve NOAA solar-cycle data"
        }
    record = _find_month(
        data,
        requested_time
    )
    if record is None:
        return {
            "source": "NOAA Space Weather Prediction Center",
            "available": False,
            "requested_time": requested_time.isoformat(),
            "reason": "No NOAA solar-cycle record found for this period"
        }
    def number(key):
        value = record.get(key)

        if value in (None, "", "*", "-1", -1, -1.0):
            return None

        try:
            number_value = float(value)

            if number_value < 0:
                return None

            return number_value

        except (TypeError, ValueError):
            return None
    return {
        "source": "NOAA Space Weather Prediction Center",
        "available": True,
        "requested_time":
            requested_time.isoformat(),
        "observed_period":
            record.get("time-tag"),
        "observations": {
            "solar_activity": {
                "sunspot_number": number(
                    "ssn"
                ),
                "smoothed_sunspot_number": number(
                    "smoothed_ssn"
                ),
                "swpc_sunspot_number": number(
                    "observed_swpc_ssn"
                ),
                "smoothed_swpc_sunspot_number": number(
                    "smoothed_swpc_ssn"
                )
            },
            "radio_flux": {
                "f10_7_sfu": number(
                    "f10.7"
                ),
                "smoothed_f10_7_sfu": number(
                    "smoothed_f10.7"
                )
            }
        }
    }