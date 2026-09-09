"""
Daily/activation layer orchestrator: everything in
celeste-variable-spec-for-code.md's "Daily/activation layer" section,
computed against an already-built natal chart (hellenistic.natal.
build_natal_chart's output) for one requested date.
"""

from datetime import datetime

from hellenistic.eclipses import build_eclipse_activation
from hellenistic.lunar_phase import build_lunar_phase
from hellenistic.profections import build_profection
from hellenistic.stations import build_stations
from hellenistic.transits import build_transits
from hellenistic.zr import build_zr_track


def build_daily_layer(natal_chart: dict, birth_utc_time: datetime, as_of_utc_time: datetime) -> dict:
    profection = build_profection(birth_utc_time, as_of_utc_time, natal_chart["house_signs"])

    zr_fortune = build_zr_track(
        natal_chart["lot_of_fortune"]["sign_index"], birth_utc_time, as_of_utc_time
    )
    zr_spirit = build_zr_track(
        natal_chart["lot_of_spirit"]["sign_index"], birth_utc_time, as_of_utc_time
    )

    transits = build_transits(natal_chart, as_of_utc_time)
    lunar_phase = build_lunar_phase(as_of_utc_time)
    stations = build_stations(as_of_utc_time)
    eclipses = build_eclipse_activation(as_of_utc_time)

    return {
        "as_of_utc_time": as_of_utc_time.isoformat(),
        "profection": profection,
        "zr_fortune": zr_fortune,
        "zr_spirit": zr_spirit,
        "transits": transits,
        "lunar_phase_today": lunar_phase["phase"],
        "void_of_course": lunar_phase["void_of_course"],
        "stations_today": stations,
        "eclipses": eclipses,
    }
