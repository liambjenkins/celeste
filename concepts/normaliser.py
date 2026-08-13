from datetime import date

from .registry import CONCEPTS


# --------------------------------------------------------
# Wheel of the Year (Pagan/Wiccan)
# --------------------------------------------------------
#
# The eight sabbats are historically Northern-Hemisphere-dated
# (Wicca originated in England). Southern Hemisphere practitioners
# commonly keep each sabbat's SEASONAL MEANING (Yule = the winter
# solstice sabbat) rather than its calendar date, which means
# swapping each sabbat for its opposite on the wheel rather than
# shifting the calendar date itself.
#
# Deliberately not hardcoded to one hemisphere: this only supplies
# the reference dates; which name comes out depends on latitude.

_SABBAT_DATES = (
    ((10, 31), "Samhain"),
    ((12, 21), "Yule"),
    ((2, 1), "Imbolc"),
    ((3, 20), "Ostara"),
    ((5, 1), "Beltane"),
    ((6, 21), "Litha"),
    ((8, 1), "Lughnasadh"),
    ((9, 22), "Mabon"),
)

_SABBAT_OPPOSITE = {
    "Samhain": "Beltane",
    "Beltane": "Samhain",
    "Yule": "Litha",
    "Litha": "Yule",
    "Imbolc": "Lughnasadh",
    "Lughnasadh": "Imbolc",
    "Ostara": "Mabon",
    "Mabon": "Ostara",
}

# A fixed non-leap reference year, used only to compare (month, day)
# pairs as day-of-year distances.
_REFERENCE_YEAR = 2001


def _day_of_year(month, day):
    return (
        date(_REFERENCE_YEAR, month, day)
        - date(_REFERENCE_YEAR, 1, 1)
    ).days


def nearest_sabbat(month, day, latitude):
    """
    Return (sabbat_name, days_away) for the nearest point on the
    Wheel of the Year to the given (month, day), adjusted for
    hemisphere by latitude sign.
    """

    target = _day_of_year(month, day)

    best_name = None
    best_diff = None

    for (ref_month, ref_day), name in _SABBAT_DATES:
        point = _day_of_year(ref_month, ref_day)
        diff = min(abs(target - point), 365 - abs(target - point))

        if best_diff is None or diff < best_diff:
            best_diff = diff
            best_name = name

    if latitude is not None and latitude < 0:
        best_name = _SABBAT_OPPOSITE[best_name]

    return best_name, best_diff


def normalise_observations(observations):
    concepts = {}
    def add_concept(
        concept_id,
        value=None,
        source=None
    ):
        if concept_id not in CONCEPTS:
            return
        if concept_id not in concepts:
            concepts[concept_id] = {
                "label":
                    CONCEPTS[concept_id]["label"],
                "domain":
                    CONCEPTS[concept_id]["domain"],
                "observations": []
            }
        if value is not None:
            concepts[concept_id][
                "observations"
            ].append({
                "value":
                    value,
                "source":
                    source
            })
    # --------------------------------------------------------
    # ASTRONOMY / ASTROLOGY
    # --------------------------------------------------------
    #
    # Astronomy remains observational data here.
    # Astrological or religious meaning belongs downstream.
    #
    # "astrology" is the output of astrology.chart.build_chart():
    # raw body positions already enriched with sign/house/retrograde,
    # plus house cusps, chart angles, and computed aspects.
    #
    astronomy = observations.get(
        "astrology",
        {}
    )

    if isinstance(astronomy, dict):

        bodies = astronomy.get(
            "bodies",
            {}
        )

        if isinstance(bodies, dict):

            if "sun" in bodies:
                add_concept(
                    "sun",
                    bodies["sun"],
                    "astrology.bodies.sun"
                )

            if "moon" in bodies:
                add_concept(
                    "moon",
                    bodies["moon"],
                    "astrology.bodies.moon"
                )

            planetary = {}

            for body_name, body_data in bodies.items():

                if body_name in (
                    "sun",
                    "moon",
                ):
                    continue

                planetary[body_name] = body_data

            if planetary:
                add_concept(
                    "planetary_positions",
                    planetary,
                    "astrology.bodies"
                )

        # Julian day is useful provenance/context,
        # but is not itself an interpretive concept.
        if "julian_day" in astronomy:
            add_concept(
                "astronomical_time",
                astronomy["julian_day"],
                "astrology.julian_day"
            )

        houses = astronomy.get(
            "houses",
            {}
        )

        if isinstance(houses, dict):

            angles = houses.get(
                "angles",
                {}
            )

            if "ascendant" in angles:
                add_concept(
                    "ascendant",
                    angles["ascendant"],
                    "astrology.houses.angles.ascendant"
                )

            if "mc" in angles:
                add_concept(
                    "midheaven",
                    angles["mc"],
                    "astrology.houses.angles.mc"
                )

            if houses.get("cusps"):
                add_concept(
                    "astrological_houses",
                    houses,
                    "astrology.houses"
                )

            if "system" in houses:
                add_concept(
                    "astrological_house_system",
                    houses["system"],
                    "astrology.houses.system"
                )

        aspects = astronomy.get(
            "aspects"
        )

        if aspects:
            add_concept(
                "astrological_aspects",
                aspects,
                "astrology.aspects"
            )

        elemental_balance = astronomy.get(
            "elemental_balance"
        )

        if elemental_balance:
            add_concept(
                "elemental_balance",
                elemental_balance,
                "astrology.elemental_balance"
            )

        stars = astronomy.get(
            "stars"
        )

        if stars:
            add_concept(
                "fixed_stars",
                stars,
                "astrology.stars"
            )

        star_conjunctions = astronomy.get(
            "star_conjunctions"
        )

        if star_conjunctions:
            add_concept(
                "fixed_star_conjunctions",
                star_conjunctions,
                "astrology.star_conjunctions"
            )

    # --------------------------------------------------------
    # SEASON
    # --------------------------------------------------------
    #
    # The requested moment is also located within the annual
    # solar cycle. This is descriptive, not interpretive.
    #
    requested_time = observations.get(
        "_requested_time"
    )

    latitude = observations.get(
        "_latitude"
    )

    if requested_time is not None:

        month = requested_time.month

        if month in (12, 1, 2):
            season = "summer"
        elif month in (3, 4, 5):
            season = "autumn"
        elif month in (6, 7, 8):
            season = "winter"
        else:
            season = "spring"

        # The above mapping is Southern Hemisphere. Flip it for
        # latitudes at or north of the equator.
        if latitude is not None and latitude >= 0:
            season = {
                "summer": "winter",
                "winter": "summer",
                "autumn": "spring",
                "spring": "autumn",
            }[season]

        add_concept(
            "season",
            season,
            "derived.season"
        )

        sabbat_name, sabbat_days_away = nearest_sabbat(
            requested_time.month,
            requested_time.day,
            latitude,
        )

        add_concept(
            "wheel_of_the_year_sabbat",
            {
                "sabbat": sabbat_name,
                "days_away": sabbat_days_away,
            },
            "derived.wheel_of_the_year_sabbat"
        )

    # --------------------------------------------------------
    # ATMOSPHERE
    # --------------------------------------------------------
    atmosphere = observations.get(
        "atmosphere",
        {}
    )
    if isinstance(atmosphere, dict):
        if "humidity_percent" in atmosphere:
            add_concept(
                "atmospheric_moisture",
                atmosphere[
                    "humidity_percent"
                ],
                "atmosphere.humidity_percent"
            )
        if "temperature_c" in atmosphere:
            add_concept(
                "temperature",
                atmosphere[
                    "temperature_c"
                ],
                "atmosphere.temperature_c"
            )
        if "pressure_hpa" in atmosphere:
            add_concept(
                "pressure",
                atmosphere[
                    "pressure_hpa"
                ],
                "atmosphere.pressure_hpa"
            )
        if "cloud_cover_percent" in atmosphere:
            add_concept(
                "cloud",
                atmosphere[
                    "cloud_cover_percent"
                ],
                "atmosphere.cloud_cover_percent"
            )
        if "precipitation_mm" in atmosphere:
            add_concept(
                "precipitation",
                atmosphere[
                    "precipitation_mm"
                ],
                "atmosphere.precipitation_mm"
            )
    # --------------------------------------------------------
    # HYDROLOGY
    # --------------------------------------------------------
    hydrology = observations.get(
        "hydrology",
        {}
    )
    if isinstance(hydrology, dict):
        hydro = hydrology.get(
            "observations",
            {}
        )
        for name, concept in [
            (
                "precipitation_mm",
                "precipitation"
            ),
            (
                "soil_moisture_0_7cm_m3m3",
                "soil_moisture"
            )
        ]:
            item = hydro.get(name)
            if isinstance(item, dict):
                if item.get(
                    "available"
                ) is True:
                    add_concept(
                        concept,
                        item.get("value"),
                        f"hydrology.observations.{name}"
                    )
    # --------------------------------------------------------
    # TIDES
    # --------------------------------------------------------
    tides = observations.get(
        "tides",
        {}
    )
    if isinstance(tides, dict):
        observation = tides.get(
            "observation",
            {}
        )
        if observation:
            add_concept(
                "tide",
                observation,
                "tides.observation"
            )
    # --------------------------------------------------------
    # MARINE
    # --------------------------------------------------------
    marine = observations.get(
        "marine",
        {}
    )
    if isinstance(marine, dict):
        marine_observations = marine.get(
            "observations",
            {}
        )
        for name, concept in [
            (
                "wave_height_m",
                "marine_conditions"
            ),
            (
                "wave_direction_deg",
                "marine_conditions"
            ),
            (
                "wave_period_seconds",
                "marine_conditions"
            ),
            (
                "sea_surface_temperature_c",
                "marine_conditions"
            ),
            (
                "ocean_current_velocity_kmh",
                "marine_conditions"
            ),
            (
                "ocean_current_direction_deg",
                "marine_conditions"
            )
        ]:
            item = marine_observations.get(
                name
            )
            if isinstance(item, dict):
                if item.get(
                    "available"
                ) is True:
                    add_concept(
                        concept,
                        item.get("value"),
                        f"marine.observations.{name}"
                    )
    # --------------------------------------------------------
    # EARTH
    # --------------------------------------------------------
    #
    # These come from separate top-level provider results
    # (elevation, geology, earthquake), not a nested "earth" key.
    #
    elevation = observations.get(
        "elevation",
        {}
    )
    if isinstance(elevation, dict):
        if elevation.get(
            "available"
        ) is True:
            add_concept(
                "elevation",
                elevation.get(
                    "elevation_m"
                ),
                "elevation.elevation_m"
            )

    geology = observations.get(
        "geology",
        {}
    )
    if isinstance(geology, dict):
        if geology.get(
            "available"
        ) is True:
            add_concept(
                "geology",
                geology,
                "geology"
            )

    earthquake = observations.get(
        "earthquake",
        {}
    )
    if isinstance(earthquake, dict):
        # The earthquake provider has no "available" flag; it
        # always returns a result (possibly with zero events).
        if earthquake.get(
            "events_found"
        ) is not None:
            add_concept(
                "earthquake",
                earthquake,
                "earthquake"
            )
    # --------------------------------------------------------
    # LAND
    # --------------------------------------------------------
    land = observations.get(
        "land",
        {}
    )
    if isinstance(land, dict):
        soil = land.get(
            "observations",
            {}
        ).get(
            "soil",
            {}
        )
        moisture = soil.get(
            "moisture",
            {}
        )
        for name, value in moisture.items():
            add_concept(
                "soil_moisture",
                value,
                f"land.observations.soil.moisture.{name}"
            )
        temperature = soil.get(
            "temperature",
            {}
        )
        for name, value in temperature.items():
            add_concept(
                "soil_temperature",
                value,
                f"land.observations.soil.temperature.{name}"
            )
    # --------------------------------------------------------
    # BIOSPHERE
    # --------------------------------------------------------
    biosphere = observations.get(
        "biosphere",
        {}
    )
    if isinstance(biosphere, dict):
        vegetation = biosphere.get(
            "observations",
            {}
        ).get(
            "vegetation",
            {}
        )
        if "ndvi" in vegetation:
            add_concept(
                "vegetation",
                vegetation[
                    "ndvi"
                ],
                "biosphere.observations.vegetation.ndvi"
            )
    # --------------------------------------------------------
    # SPACE WEATHER
    # --------------------------------------------------------
    space_weather = observations.get(
        "solar_activity",
        {}
    )
    if isinstance(space_weather, dict):
        solar_activity = space_weather.get(
            "observations",
            {}
        ).get(
            "solar_activity",
            {}
        )
        if solar_activity.get("sunspot_number") is not None:
            add_concept(
                "solar_activity",
                solar_activity[
                    "sunspot_number"
                ],
                "solar_activity.observations.solar_activity.sunspot_number"
            )
    return concepts