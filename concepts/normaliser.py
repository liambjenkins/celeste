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