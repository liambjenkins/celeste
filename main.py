from dotenv import load_dotenv
load_dotenv()
import argparse
from datetime import datetime, timedelta, timezone
import json
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
from astrology.chart import build_chart
from astrology.houses import HOUSE_SYSTEMS
from astrology.navamsa import build_navamsa_chart
from astrology.progressions import build_secondary_progressions
from astrology.sidereal import build_sidereal_chart
from astrology.time import local_to_utc
from astrology.transits import build_transits
from chinese.pillars import build_four_pillars
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
            "Optional date (YYYY-MM-DD) to evaluate transits and "
            "secondary progressions against the birth chart. Must be "
            "given together with --as-of-time. Interpreted in the "
            "same --timezone/--utc-offset as --date/--time. Omit to "
            "skip transits and progressions entirely."
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

observations = {
    "astrology": _tropical_chart,
    "vedic_astrology": _sidereal_chart,
    "navamsa": build_navamsa_chart(_sidereal_chart),
    "chinese_pillars": build_four_pillars(
        _tropical_chart, args.requested_time_local
    ).to_dict(),
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
