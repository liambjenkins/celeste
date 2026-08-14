from dotenv import load_dotenv
load_dotenv()
import argparse
from datetime import datetime, timedelta, timezone
import json
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
from astrology.chart import build_chart
from astrology.dasha import build_vimshottari_dasha
from astrology.dignity import build_dignity
from astrology.jaimini import build_chara_karakas, build_marak_planets
from astrology.yogini_dasha import build_yogini_dasha
from astrology.chara_dasha import build_chara_dasha
from astrology.ashtakavarga import build_ashtakavarga
from astrology.shadbala import build_shadbala_partial
from astrology.houses import HOUSE_SYSTEMS
from astrology.navamsa import build_navamsa_chart
from astrology.progressions import build_secondary_progressions
from astrology.tertiary_progressions import build_tertiary_progressions
from astrology.varga import build_all_vargas
from astrology.sidereal import build_sidereal_chart
from astrology.time import local_to_utc
from astrology.transits import build_transits
from astrology.yogas import find_yogas
from chinese.dayun import build_da_yun
from chinese.liu_nian import build_liu_nian
from chinese.interactions import find_all_interactions
from chinese.elemental_balance import build_elemental_balance
from chinese.pillars import build_four_pillars
from chinese.sexagenary import STEM_INDEX, STEMS
from chinese.ten_gods import build_ten_gods
from providers.atmosphere import get_atmosphere
from providers.marine import get_marine
from providers.earthquakes import get_earthquakes
from providers.geology import get_geology
from providers.elevation import get_elevation
from providers.tides import get_tides
from providers.hydrology import get_hydrology
from providers.land import get_land
from providers.biosphere import get_biosphere
from providers.solar import get_solar
from concepts.normaliser import normalise_observations
from concepts.summary import build_summary
from elements import classify_observations
from lenses.cross_system import build_cross_system_convergence
from lenses.editor import build_editorial_payload
from lenses.pipeline import run_lenses
from lenses.synthesis import build_synthesis
# ------------------------------------------------------------
# CELESTE — Environmental Reconstruction
# ------------------------------------------------------------


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Celeste — reconstruct the environmental and celestial "
            "state of a specific moment and place."
        )
    )

    parser.add_argument(
        "--date",
        required=True,
        help="Birth date, in YYYY-MM-DD format.",
    )

    parser.add_argument(
        "--time",
        required=True,
        help="Birth time, in HH:MM or HH:MM:SS (24-hour) format.",
    )

    parser.add_argument(
        "--timezone",
        default=None,
        help=(
            "IANA timezone name for --date/--time (e.g. "
            "'Australia/Melbourne'). Recommended over --utc-offset: "
            "it accounts for historical DST rules automatically. "
            "Takes precedence over --utc-offset if both are given."
        ),
    )

    parser.add_argument(
        "--utc-offset",
        type=float,
        default=0.0,
        help=(
            "Hours the supplied date/time is ahead of UTC "
            "(e.g. 10 for Melbourne AEST). Used only if --timezone "
            "is not given. --date/--time are treated as local time "
            "and converted to UTC using this fixed offset — it does "
            "NOT account for historical DST. Defaults to 0 (i.e. "
            "--date/--time are already UTC)."
        ),
    )

    parser.add_argument(
        "--lat",
        type=float,
        required=True,
        help="Latitude in decimal degrees (-90 to 90).",
    )

    parser.add_argument(
        "--lon",
        type=float,
        required=True,
        help="Longitude in decimal degrees (-180 to 180).",
    )

    parser.add_argument(
        "--location",
        default=None,
        help="Optional human-readable label for the location.",
    )

    parser.add_argument(
        "--house-system",
        default="placidus",
        choices=sorted(HOUSE_SYSTEMS),
        help="Astrological house system to use. Defaults to placidus.",
    )

    parser.add_argument(
        "--as-of-date",
        default=None,
        help=(
            "Optional date (YYYY-MM-DD) to evaluate transits, "
            "secondary progressions, Vimshottari Dasha, and Da Yun "
            "against the birth chart. Must be given together with "
            "--as-of-time. Interpreted in the same "
            "--timezone/--utc-offset as --date/--time. Omit to skip "
            "all of these timing techniques entirely."
        ),
    )

    parser.add_argument(
        "--as-of-time",
        default=None,
        help=(
            "Optional time (HH:MM or HH:MM:SS) paired with "
            "--as-of-date."
        ),
    )

    parser.add_argument(
        "--gender",
        default=None,
        choices=("male", "female"),
        help=(
            "Required alongside --as-of-date/--as-of-time to compute "
            "Da Yun (Chinese Luck Pillars) — its direction through "
            "the sexagenary cycle depends on gender and there is no "
            "astronomical way to derive it. Da Yun is skipped "
            "(without error) if --gender is omitted even when "
            "--as-of is given; other --as-of-dependent techniques "
            "are unaffected."
        ),
    )

    args = parser.parse_args()

    if not (-90 <= args.lat <= 90):
        parser.error("--lat must be between -90 and 90.")

    if not (-180 <= args.lon <= 180):
        parser.error("--lon must be between -180 and 180.")

    for time_format in ("%H:%M:%S", "%H:%M"):
        try:
            local_time = datetime.strptime(
                f"{args.date} {args.time}",
                f"%Y-%m-%d {time_format}",
            )
            break
        except ValueError:
            local_time = None

    if local_time is None:
        parser.error(
            "--date/--time could not be parsed. "
            "Use --date YYYY-MM-DD --time HH:MM[:SS]."
        )

    if args.timezone:
        try:
            aware_utc = local_to_utc(local_time, args.timezone)
        except Exception as error:
            parser.error(
                f"--timezone {args.timezone!r} could not be used: "
                f"{error}"
            )
        args.requested_time_utc = aware_utc.replace(tzinfo=None)
    else:
        args.requested_time_utc = local_time - timedelta(
            hours=args.utc_offset
        )

    # Kept alongside the UTC conversion (not just discarded) because
    # the Chinese Four Pillars' Day/Hour boundaries are local-civil-
    # clock-based, not UTC-instant-based like Year/Month.
    args.requested_time_local = local_time

    if bool(args.as_of_date) != bool(args.as_of_time):
        parser.error(
            "--as-of-date and --as-of-time must be given together."
        )

    args.as_of_time_utc = None

    if args.as_of_date and args.as_of_time:
        for time_format in ("%H:%M:%S", "%H:%M"):
            try:
                as_of_local = datetime.strptime(
                    f"{args.as_of_date} {args.as_of_time}",
                    f"%Y-%m-%d {time_format}",
                )
                break
            except ValueError:
                as_of_local = None

        if as_of_local is None:
            parser.error(
                "--as-of-date/--as-of-time could not be parsed. "
                "Use --as-of-date YYYY-MM-DD --as-of-time HH:MM[:SS]."
            )

        if args.timezone:
            as_of_aware_utc = local_to_utc(as_of_local, args.timezone)
            args.as_of_time_utc = as_of_aware_utc.replace(tzinfo=None)
        else:
            args.as_of_time_utc = as_of_local - timedelta(
                hours=args.utc_offset
            )

    return args


args = parse_args()

LATITUDE = args.lat
LONGITUDE = args.lon
REQUESTED_TIME = args.requested_time_utc
REQUESTED_TIME_AWARE = REQUESTED_TIME.replace(tzinfo=timezone.utc)

# ------------------------------------------------------------
# COLLECT
# ------------------------------------------------------------
_tropical_chart = build_chart(
    REQUESTED_TIME_AWARE,
    LATITUDE,
    LONGITUDE,
    house_system=args.house_system,
)

_sidereal_chart = build_sidereal_chart(_tropical_chart)
_four_pillars = build_four_pillars(_tropical_chart, args.requested_time_local)

observations = {
    "astrology": _tropical_chart,
    "vedic_astrology": _sidereal_chart,
    "vedic_yogas": find_yogas(_sidereal_chart),
    "navamsa": build_navamsa_chart(_sidereal_chart),
    "vedic_vargas": build_all_vargas(_sidereal_chart),
    "vedic_dignity": build_dignity(_sidereal_chart),
    "vedic_karakas": build_chara_karakas(_sidereal_chart),
    "vedic_marak": build_marak_planets(_sidereal_chart),
    "vedic_ashtakavarga": build_ashtakavarga(_sidereal_chart),
    "vedic_shadbala": build_shadbala_partial(_sidereal_chart),
    "chinese_pillars": _four_pillars.to_dict(),
    "chinese_ten_gods": build_ten_gods(
        _four_pillars, _four_pillars.day_master_element, _four_pillars.day_master_polarity
    ),
    "chinese_interactions": find_all_interactions(_four_pillars),
    "chinese_elemental_balance": build_elemental_balance(_four_pillars),
    "atmosphere": get_atmosphere(
        LATITUDE, LONGITUDE, REQUESTED_TIME
    ),
    "marine": get_marine(
        LATITUDE, LONGITUDE, REQUESTED_TIME
    ),
    "geology": get_geology(
        LATITUDE, LONGITUDE
    ),
    "elevation": get_elevation(
        LATITUDE, LONGITUDE
    ),
    "tides": get_tides(
        LATITUDE, LONGITUDE, REQUESTED_TIME
    ),
    "hydrology": get_hydrology(
        LATITUDE, LONGITUDE, REQUESTED_TIME
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
    "_requested_time": REQUESTED_TIME,
    "_latitude": LATITUDE,
}

if args.as_of_time_utc is not None:
    AS_OF_TIME_AWARE = args.as_of_time_utc.replace(tzinfo=timezone.utc)
    observations["transits"] = build_transits(
        _tropical_chart, AS_OF_TIME_AWARE
    )
    observations["secondary_progressions"] = build_secondary_progressions(
        _tropical_chart, REQUESTED_TIME_AWARE, AS_OF_TIME_AWARE
    )
    observations["tertiary_progressions"] = build_tertiary_progressions(
        _tropical_chart, REQUESTED_TIME_AWARE, AS_OF_TIME_AWARE
    )
    observations["vedic_dasha"] = build_vimshottari_dasha(
        _sidereal_chart, REQUESTED_TIME_AWARE, AS_OF_TIME_AWARE
    )
    observations["vedic_yogini_dasha"] = build_yogini_dasha(
        _sidereal_chart, REQUESTED_TIME_AWARE, AS_OF_TIME_AWARE
    )
    observations["vedic_chara_dasha"] = build_chara_dasha(
        _sidereal_chart, REQUESTED_TIME_AWARE, AS_OF_TIME_AWARE
    )
    observations["chinese_liu_nian"] = build_liu_nian(AS_OF_TIME_AWARE)

    if args.gender is not None:
        year_stem_polarity = STEMS[STEM_INDEX[_four_pillars.year.stem]][2]
        observations["chinese_dayun"] = build_da_yun(
            _tropical_chart,
            year_stem_polarity,
            _four_pillars.month.stem,
            _four_pillars.month.branch,
            args.gender,
            REQUESTED_TIME_AWARE,
            AS_OF_TIME_AWARE,
        )
# ------------------------------------------------------------
# PROCESS
# ------------------------------------------------------------
normalised = normalise_observations(observations)
summary = build_summary(normalised)
elements = classify_observations(normalised)

features, interpretations = run_lenses(normalised)

lenses_output = {
    lens_id: build_editorial_payload(interpretation)
    for lens_id, interpretation in interpretations.items()
}

synthesis = build_synthesis(interpretations)
cross_system = build_cross_system_convergence(interpretations)
# ------------------------------------------------------------
# OUTPUT
# ------------------------------------------------------------
result = {
    "requested_time_utc": REQUESTED_TIME.isoformat(),
    "location": {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "label": args.location,
    },
    "summary": summary,
    "elements": elements,
    "features": {
        "tags": features.tags,
        "season": features.season,
        "moon_phase": features.moon_phase_name,
        "sun_moon_aspect": features.sun_moon_aspect,
        "dominant_elemental_domains": features.dominant_domains,
    },
    "lenses": lenses_output,
    "synthesis": synthesis,
    "cross_system_convergence": {
        "claims_pooled": len(cross_system.points),
        "narrative": cross_system.narrative,
    },
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
