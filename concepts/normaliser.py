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

        harmonic_charts_value = astronomy.get("harmonic_charts")

        if harmonic_charts_value:
            add_concept(
                "harmonic_charts",
                harmonic_charts_value,
                "astrology.harmonic_charts"
            )

        aspect_patterns_value = astronomy.get("aspect_patterns")

        if isinstance(aspect_patterns_value, dict) and aspect_patterns_value.get("chart_shape", {}).get("shape"):
            add_concept(
                "chart_shape",
                aspect_patterns_value["chart_shape"],
                "astrology.aspect_patterns.chart_shape"
            )

        if isinstance(aspect_patterns_value, dict) and any(
            aspect_patterns_value.get(key)
            for key in (
                "grand_trines", "t_squares", "grand_crosses", "yods",
                "kites", "mystic_rectangles", "stelliums",
            )
        ):
            add_concept(
                "aspect_patterns",
                aspect_patterns_value,
                "astrology.aspect_patterns"
            )

        rulership_value = astronomy.get("rulership")

        if isinstance(rulership_value, dict) and rulership_value.get("chart_ruler"):
            add_concept(
                "rulership",
                rulership_value,
                "astrology.rulership"
            )

        antiscia_value = astronomy.get("antiscia")

        if antiscia_value:
            add_concept(
                "antiscia",
                antiscia_value,
                "astrology.antiscia"
            )

        declination_aspects = astronomy.get("declination_aspects")

        if declination_aspects:
            add_concept(
                "declination_aspects",
                declination_aspects,
                "astrology.declination_aspects"
            )

        vertex_point = astronomy.get("vertex")

        if isinstance(vertex_point, dict) and vertex_point.get("sign"):
            add_concept(
                "vertex",
                vertex_point,
                "astrology.vertex"
            )

        arabic_parts = astronomy.get(
            "arabic_parts"
        )

        if isinstance(arabic_parts, dict):

            if arabic_parts.get("fortune"):
                add_concept(
                    "part_of_fortune",
                    {
                        **arabic_parts["fortune"],
                        "day_chart": arabic_parts.get("day_chart"),
                    },
                    "astrology.arabic_parts.fortune"
                )

            if arabic_parts.get("spirit"):
                add_concept(
                    "part_of_spirit",
                    {
                        **arabic_parts["spirit"],
                        "day_chart": arabic_parts.get("day_chart"),
                    },
                    "astrology.arabic_parts.spirit"
                )

            for _lot_key in ("eros", "necessity", "courage", "victory", "nemesis"):
                if arabic_parts.get(_lot_key):
                    add_concept(
                        f"part_of_{_lot_key}",
                        {
                            **arabic_parts[_lot_key],
                            "day_chart": arabic_parts.get("day_chart"),
                        },
                        f"astrology.arabic_parts.{_lot_key}"
                    )

    # --------------------------------------------------------
    # VEDIC ASTROLOGY (sidereal)
    # --------------------------------------------------------
    #
    # "vedic_astrology" is the output of
    # astrology.sidereal.build_sidereal_chart(): sidereal body
    # positions (sign, nakshatra, whole-sign house) plus the
    # sidereal Ascendant. Same split as tropical astrology above —
    # Sun and Moon get their own concepts, everything else is
    # bundled into vedic_positions.
    #
    vedic = observations.get(
        "vedic_astrology",
        {}
    )

    if isinstance(vedic, dict):

        vedic_bodies = vedic.get(
            "bodies",
            {}
        )

        if isinstance(vedic_bodies, dict):

            if "sun" in vedic_bodies:
                add_concept(
                    "vedic_sun",
                    vedic_bodies["sun"],
                    "vedic_astrology.bodies.sun"
                )

            if "moon" in vedic_bodies:
                add_concept(
                    "vedic_moon",
                    vedic_bodies["moon"],
                    "vedic_astrology.bodies.moon"
                )

            vedic_planetary = {
                name: data
                for name, data in vedic_bodies.items()
                if name not in ("sun", "moon")
            }

            if vedic_planetary:
                add_concept(
                    "vedic_positions",
                    vedic_planetary,
                    "vedic_astrology.bodies"
                )

        if vedic.get("ascendant"):
            add_concept(
                "vedic_ascendant",
                vedic["ascendant"],
                "vedic_astrology.ascendant"
            )

    # --------------------------------------------------------
    # VEDIC YOGAS (classical planetary combinations)
    # --------------------------------------------------------
    #
    # "vedic_yogas" is the output of astrology.yogas.find_yogas(): a
    # list of yoga dicts, one per yoga found in the sidereal chart.
    # One bundled concept — a specific list, not a per-yoga concept,
    # since which yogas exist varies chart to chart.
    #
    yogas = observations.get(
        "vedic_yogas",
        []
    )

    if isinstance(yogas, list) and yogas:
        add_concept(
            "vedic_yogas",
            yogas,
            "vedic_yogas"
        )

    # --------------------------------------------------------
    # VIMSHOTTARI DASHA (optional — only present when
    # --as-of-date/--as-of-time were supplied)
    # --------------------------------------------------------
    #
    # "vedic_dasha" is the output of
    # astrology.dasha.build_vimshottari_dasha(): the Mahadasha/
    # Antardasha active as of a specified moment, plus the full
    # birth-to-120-year Mahadasha sequence.
    #
    dasha = observations.get(
        "vedic_dasha",
        {}
    )

    if isinstance(dasha, dict) and dasha:
        add_concept(
            "vedic_dasha",
            dasha,
            "vedic_dasha"
        )

    # --------------------------------------------------------
    # YOGINI DASHA, CHARA DASHA (Jaimini)
    # --------------------------------------------------------
    #
    # Outputs of astrology.yogini_dasha.build_yogini_dasha() and
    # astrology.chara_dasha.build_chara_dasha() respectively — both
    # optional and --as-of-dependent, same as vedic_dasha above.
    #
    yogini_dasha = observations.get(
        "vedic_yogini_dasha",
        {}
    )

    if isinstance(yogini_dasha, dict) and yogini_dasha:
        add_concept(
            "vedic_yogini_dasha",
            yogini_dasha,
            "vedic_yogini_dasha"
        )

    chara_dasha = observations.get(
        "vedic_chara_dasha",
        {}
    )

    if isinstance(chara_dasha, dict) and chara_dasha:
        add_concept(
            "vedic_chara_dasha",
            chara_dasha,
            "vedic_chara_dasha"
        )

    # --------------------------------------------------------
    # NAVAMSA (D9 divisional chart)
    # --------------------------------------------------------
    #
    # "navamsa" is the output of astrology.navamsa.build_navamsa_chart():
    # each body's sign and D9-house in the ninth-harmonic divisional
    # chart. Same sun/moon/ascendant-split pattern as the sidereal
    # chart above.
    #
    navamsa = observations.get(
        "navamsa",
        {}
    )

    if isinstance(navamsa, dict):

        navamsa_bodies = navamsa.get(
            "bodies",
            {}
        )

        if isinstance(navamsa_bodies, dict):

            if "sun" in navamsa_bodies:
                add_concept(
                    "navamsa_sun",
                    navamsa_bodies["sun"],
                    "navamsa.bodies.sun"
                )

            if "moon" in navamsa_bodies:
                add_concept(
                    "navamsa_moon",
                    navamsa_bodies["moon"],
                    "navamsa.bodies.moon"
                )

            navamsa_planetary = {
                name: data
                for name, data in navamsa_bodies.items()
                if name not in ("sun", "moon")
            }

            if navamsa_planetary:
                add_concept(
                    "navamsa_positions",
                    navamsa_planetary,
                    "navamsa.bodies"
                )

        if navamsa.get("ascendant"):
            add_concept(
                "navamsa_ascendant",
                navamsa["ascendant"],
                "navamsa.ascendant"
            )

    # --------------------------------------------------------
    # VEDIC DIVISIONAL CHARTS (Shodasavarga, beyond D1/D9)
    # --------------------------------------------------------
    #
    # "vedic_vargas" is the output of astrology.varga.build_all_vargas():
    # {n: {"bodies": {...}, "ascendant": {...}}} for D2, D3, D4, D7,
    # D10, D12, D16, D20, D24, D27, D30, D40, D45, D60. Kept as one
    # generic concept (mirroring astrology.harmonic_charts' pattern)
    # rather than per-chart concepts — 14 charts would otherwise mean
    # 14x the per-body concept sprawl D9 already has its own dedicated
    # concepts for.
    #
    vedic_vargas = observations.get(
        "vedic_vargas",
        {}
    )

    if isinstance(vedic_vargas, dict) and vedic_vargas:
        add_concept(
            "vedic_vargas",
            vedic_vargas,
            "vedic_vargas"
        )

    # --------------------------------------------------------
    # VEDIC DIGNITY, JAIMINI KARAKAS, MARAK PLANETS
    # --------------------------------------------------------
    #
    # Outputs of astrology.dignity.build_dignity(),
    # astrology.jaimini.build_chara_karakas(), and
    # astrology.jaimini.build_marak_planets() respectively.
    #
    vedic_dignity = observations.get(
        "vedic_dignity",
        {}
    )

    if isinstance(vedic_dignity, dict) and vedic_dignity:
        add_concept(
            "vedic_dignity",
            vedic_dignity,
            "vedic_dignity"
        )

    vedic_karakas = observations.get(
        "vedic_karakas",
        {}
    )

    if isinstance(vedic_karakas, dict) and vedic_karakas:
        add_concept(
            "vedic_karakas",
            vedic_karakas,
            "vedic_karakas"
        )

    vedic_marak = observations.get(
        "vedic_marak",
        []
    )

    if isinstance(vedic_marak, list) and vedic_marak:
        add_concept(
            "vedic_marak",
            vedic_marak,
            "vedic_marak"
        )

    vedic_ashtakavarga = observations.get(
        "vedic_ashtakavarga",
        {}
    )

    if isinstance(vedic_ashtakavarga, dict) and vedic_ashtakavarga:
        add_concept(
            "vedic_ashtakavarga",
            vedic_ashtakavarga,
            "vedic_ashtakavarga"
        )

    vedic_shadbala = observations.get(
        "vedic_shadbala",
        {}
    )

    if isinstance(vedic_shadbala, dict) and vedic_shadbala:
        add_concept(
            "vedic_shadbala",
            vedic_shadbala,
            "vedic_shadbala"
        )

    # --------------------------------------------------------
    # CHINESE ASTROLOGY (BaZi Four Pillars)
    # --------------------------------------------------------
    #
    # "chinese_pillars" is the output of
    # chinese.pillars.build_four_pillars(): Year/Month/Day/Hour
    # pillars and the Day Master. One bundled concept, not split per
    # pillar — a BaZi reading isn't coherent with only one pillar,
    # so there's no reason to let claim matching see them separately.
    #
    chinese = observations.get(
        "chinese_pillars",
        {}
    )

    if isinstance(chinese, dict) and chinese:
        add_concept(
            "chinese_pillars",
            chinese,
            "chinese_pillars"
        )

    ten_gods = observations.get(
        "chinese_ten_gods",
        {}
    )

    if isinstance(ten_gods, dict) and ten_gods:
        add_concept(
            "chinese_ten_gods",
            ten_gods,
            "chinese_ten_gods"
        )

    dayun = observations.get(
        "chinese_dayun",
        {}
    )

    if isinstance(dayun, dict) and dayun:
        add_concept(
            "chinese_dayun",
            dayun,
            "chinese_dayun"
        )

    shen_sha = observations.get(
        "chinese_shen_sha",
        []
    )

    if isinstance(shen_sha, list) and shen_sha:
        add_concept(
            "chinese_shen_sha",
            shen_sha,
            "chinese_shen_sha"
        )

    na_yin = observations.get(
        "chinese_na_yin",
        {}
    )

    if isinstance(na_yin, dict) and na_yin:
        add_concept(
            "chinese_na_yin",
            na_yin,
            "chinese_na_yin"
        )

    liu_nian = observations.get(
        "chinese_liu_nian",
        {}
    )

    if isinstance(liu_nian, dict) and liu_nian:
        add_concept(
            "chinese_liu_nian",
            liu_nian,
            "chinese_liu_nian"
        )

    chinese_interactions = observations.get(
        "chinese_interactions",
        {}
    )

    if isinstance(chinese_interactions, dict) and chinese_interactions:
        add_concept(
            "chinese_interactions",
            chinese_interactions,
            "chinese_interactions"
        )

    chinese_elemental_balance = observations.get(
        "chinese_elemental_balance",
        {}
    )

    if isinstance(chinese_elemental_balance, dict) and chinese_elemental_balance:
        add_concept(
            "chinese_elemental_balance",
            chinese_elemental_balance,
            "chinese_elemental_balance"
        )

    # --------------------------------------------------------
    # TRANSITS AND SECONDARY PROGRESSIONS (both optional — only
    # present when --as-of-date/--as-of-time were supplied)
    # --------------------------------------------------------
    #
    # "transits" is the output of astrology.transits.build_transits();
    # "secondary_progressions" is the output of
    # astrology.progressions.build_secondary_progressions(). Both are
    # bundled concepts (all bodies + aspects together) rather than
    # split per body, matching the chinese_pillars pattern — a
    # transit or progression reading isn't coherent from one isolated
    # body, so there's no reason to let claim matching see them
    # separately.
    #
    transits = observations.get(
        "transits",
        {}
    )

    if isinstance(transits, dict) and transits:
        add_concept(
            "current_transits",
            transits,
            "transits"
        )

    secondary_progressions = observations.get(
        "secondary_progressions",
        {}
    )

    if isinstance(secondary_progressions, dict) and secondary_progressions:
        add_concept(
            "secondary_progressions",
            secondary_progressions,
            "secondary_progressions"
        )

    tertiary_progressions = observations.get(
        "tertiary_progressions",
        {}
    )

    if isinstance(tertiary_progressions, dict) and tertiary_progressions:
        add_concept(
            "tertiary_progressions",
            tertiary_progressions,
            "tertiary_progressions"
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