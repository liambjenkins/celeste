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
from hellenistic.solar_phase import build_solar_phase
from hellenistic.stations import build_stations
from hellenistic.transits import build_transits
from hellenistic.zr import build_zr_track
from providers.astronomy import get_astronomy


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

    # Today's LIVE solar phase per planet (oriental/occidental,
    # combustion, motion) -- distinct from the natal chart's solar_
    # phase, which is a fixed birth-moment fact. Added per an
    # engineering note from content development: Venus's oriental/
    # occidental fragment content and the Moon's phase-based content
    # both need this checked against TODAY's sky, not just birth.
    today_astronomy = get_astronomy(as_of_utc_time)
    solar_phase_today = build_solar_phase(today_astronomy["bodies"])

    return {
        "as_of_utc_time": as_of_utc_time.isoformat(),
        "profection": profection,
        "zr_fortune": zr_fortune,
        "zr_spirit": zr_spirit,
        "transits": transits,
        "solar_phase_today": solar_phase_today,
        "lunar_phase_today": lunar_phase["phase"],
        "lunar_phase_today_three_way": lunar_phase["phase_three_way"],
        "void_of_course": lunar_phase["void_of_course"],
        "stations_today": stations,
        "eclipses": eclipses,
    }
