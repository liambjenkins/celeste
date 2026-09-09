"""
Natal computation orchestrator: combines every module in this package
into the single structured-data shape described by
celeste-variable-spec-for-code.md's "Per-planet fixed facts" and
"Chart-level fixed facts" sections. Pure data out -- no prose, no
interpretation; this is the assembly layer's input, not its output.

Run once per user and cache the result (per the spec) -- nothing here
depends on "today", only on birth moment + location.
"""

from datetime import datetime

from hellenistic.angularity import angularity
from hellenistic.aspects import build_aspects
from hellenistic.constants import CLASSICAL_PLANETS, FIXED_GENDER
from hellenistic.dignity import build_all_dignity
from hellenistic.houses import build_house_rulerships, build_joy
from hellenistic.lots import build_lots
from hellenistic.lunation import find_prenatal_lunation
from hellenistic.positions import build_positions
from hellenistic.reception import build_reception
from hellenistic.sect import chart_sect, sect_status
from hellenistic.solar_phase import build_solar_phase, mercury_gender


def _dispositor_condition(planet: str, positions: dict, dignity: dict, sect_statuses: dict) -> dict:
    from hellenistic.constants import DOMICILE_LORDS

    dispositor = DOMICILE_LORDS[positions["bodies"][planet]["sign"]]
    dispositor_body = positions["bodies"].get(dispositor)

    if dispositor_body is None:
        return {"dispositor": dispositor, "dignity_status": None, "sect_status": None, "angularity": None}

    return {
        "dispositor": dispositor,
        "dignity_status": dignity.get(dispositor, {}).get("status"),
        "sect_status": sect_statuses.get(dispositor),
        "angularity": angularity(dispositor_body["house"]),
    }


def build_natal_chart(utc_time: datetime, latitude: float, longitude: float) -> dict:
    positions = build_positions(utc_time, latitude, longitude)
    bodies = positions["bodies"]
    ascendant_longitude = positions["ascendant"]["longitude"]

    sect = chart_sect(bodies["sun"]["longitude"], ascendant_longitude)

    solar_phase = build_solar_phase(bodies)
    mercury_oriental = solar_phase["mercury"]["oriental"]

    sect_statuses = {
        planet: sect_status(planet, sect, mercury_oriental)
        for planet in CLASSICAL_PLANETS
        if planet in bodies
    }

    dignity = build_all_dignity(bodies, sect)
    reception = build_reception(bodies, dignity)
    aspects = build_aspects(bodies, sect_statuses)
    house_rulerships = build_house_rulerships(positions["house_signs"])
    joy = build_joy(bodies, ascendant_longitude, sect)
    lots = build_lots(
        ascendant_longitude, bodies["sun"]["longitude"], bodies["moon"]["longitude"], sect, positions["asc_sign_index"]
    )
    prenatal_lunation = find_prenatal_lunation(utc_time)

    genders = dict(FIXED_GENDER)
    genders["mercury"] = mercury_gender(mercury_oriental)

    planets = {}
    for planet in CLASSICAL_PLANETS:
        if planet not in bodies:
            continue

        body = bodies[planet]
        entry = {
            "sign": body["sign"],
            "degree": body["degree"],
            "minute": body["minute"],
            "longitude": body["longitude"],
            "house": body["house"],
            "dignity": dignity[planet],
            "sect_status": sect_statuses[planet],
            "angularity": angularity(body["house"]),
            "gender": genders[planet],
            "solar_phase": solar_phase[planet],
            "aspects": aspects.get(planet, []),
            "reception": {
                "received_by_dispositor": reception[planet]["received_by_dispositor"],
                "mutual_reception_with": reception[planet]["mutual_reception_with"],
            },
            "dispositor_condition": _dispositor_condition(planet, positions, dignity, sect_statuses),
            "house_rulerships": house_rulerships[planet],
            "doruphoria": None,  # stub -- explicitly deferred per the brief
            "joy": joy[planet]["joy"],
        }

        if planet == "moon":
            entry["bonding"] = solar_phase["moon"]["bonding"]

        planets[planet] = entry

    return {
        "utc_time": positions["utc_time"],
        "julian_day": positions["julian_day"],
        "location": positions["location"],
        "sect": sect,
        "ascendant": positions["ascendant"],
        "house_signs": positions["house_signs"],
        "nodes": positions["nodes"],
        "lot_of_fortune": lots["fortune"],
        "lot_of_spirit": lots["spirit"],
        "other_lots": [],  # stub -- explicitly deferred per the brief
        "prenatal_lunation": prenatal_lunation,
        "planets": planets,
    }
