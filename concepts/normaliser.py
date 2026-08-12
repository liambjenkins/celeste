from .registry import CONCEPTS
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
    # ASTRONOMY
    # --------------------------------------------------------
    #
    # Astronomy remains observational data here.
    # Astrological or religious meaning belongs downstream.
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
                    "astronomy.bodies.sun"
                )

            if "moon" in bodies:
                add_concept(
                    "moon",
                    bodies["moon"],
                    "astronomy.bodies.moon"
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
                    "astronomy.bodies"
                )

        # Julian day is useful provenance/context,
        # but is not itself an interpretive concept.
        if "julian_day" in astronomy:
            add_concept(
                "astronomical_time",
                astronomy["julian_day"],
                "astronomy.julian_day"
            )

    # --------------------------------------------------------
    # ASTROLOGY
    # --------------------------------------------------------
    #
    # Astrology is derived from the astronomical state of the
    # requested birth moment. Keep the structured chart intact
    # while exposing useful concepts to downstream lenses.
    #
    astrology = observations.get(
        "astrology",
        {}
    )

    if isinstance(astrology, dict):

        bodies = astrology.get(
            "bodies",
            {}
        )

        if isinstance(bodies, dict):

            if "sun" in bodies:
                add_concept(
                    "astrological_sun",
                    bodies["sun"],
                    "astrology.bodies.sun"
                )

            if "moon" in bodies:
                add_concept(
                    "astrological_moon",
                    bodies["moon"],
                    "astrology.bodies.moon"
                )

            if "ascendant" in astrology.get("houses", {}).get("angles", {}):
                add_concept(
                    "ascendant",
                    astrology["houses"]["angles"]["ascendant"],
                    "astrology.houses.angles.ascendant"
                )

            if "mc" in astrology.get("houses", {}).get("angles", {}):
                add_concept(
                    "midheaven",
                    astrology["houses"]["angles"]["mc"],
                    "astrology.houses.angles.mc"
                )

            add_concept(
                "astrological_positions",
                bodies,
                "astrology.bodies"
            )

        houses = astrology.get(
            "houses",
            {}
        )

        if isinstance(houses, dict):
            cusps = houses.get(
                "cusps",
                {}
            )

            if cusps:
                add_concept(
                    "astrological_houses",
                    cusps,
                    "astrology.houses.cusps"
                )

        aspects = astrology.get(
            "aspects",
            []
        )

        if isinstance(aspects, list):
            add_concept(
                "astrological_aspects",
                aspects,
                "astrology.aspects"
            )

        if "house_system" in astrology:
            add_concept(
                "astrological_house_system",
                astrology["house_system"],
                "astrology.house_system"
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

    if requested_time is None:
        requested_time = observations.get(
            "requested_time"
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

        add_concept(
            "season",
            season,
            "derived.season"
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
    earth = observations.get(
        "earth",
        {}
    )
    if isinstance(earth, dict):
        if earth.get("elevation"):
            elevation = earth[
                "elevation"
            ]
            if elevation.get(
                "available"
            ) is True:
                add_concept(
                    "elevation",
                    elevation.get(
                        "elevation_m"
                    ),
                    "earth.elevation.elevation_m"
                )
        if earth.get("geology"):
            add_concept(
                "geology",
                earth[
                    "geology"
                ],
                "earth.geology"
            )
        if earth.get("earthquakes"):
            add_concept(
                "earthquake",
                earth[
                    "earthquakes"
                ],
                "earth.earthquakes"
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
        "space_weather",
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
        if "sunspot_number" in solar_activity:
            add_concept(
                "solar_activity",
                solar_activity[
                    "sunspot_number"
                ],
                "space_weather.observations.solar_activity.sunspot_number"
            )
    return concepts