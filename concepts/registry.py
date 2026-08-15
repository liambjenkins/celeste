CONCEPTS = {

"atmospheric_moisture": {
    "label": "Atmospheric moisture",
    "domain": "air",
    "description": (
        "Water present in the atmosphere, represented primarily "
        "by humidity and related atmospheric conditions."
    ),
    "synonyms": [
        "humidity",
        "moisture",
        "dampness",
        "wet air",
        "water vapour",
        "water vapor"
    ],
    "related": [
        "cloud",
        "dew",
        "precipitation"
    ],
    "distinct_from": [
        "soil_moisture",
        "surface_water"
    ]
},
"soil_moisture": {
    "label": "Soil moisture",
    "domain": "earth",
    "description": (
        "Water stored within the soil."
    ),
    "synonyms": [
        "soil water",
        "ground moisture",
        "groundwater in soil"
    ],
    "related": [
        "precipitation",
        "vegetation",
        "evapotranspiration"
    ],
    "distinct_from": [
        "atmospheric_moisture",
        "surface_water"
    ]
},
"temperature": {
    "label": "Temperature",
    "domain": "air",
    "description": (
        "Measured thermal condition of the local environment."
    ),
    "synonyms": [
        "heat",
        "cold",
        "warmth",
        "thermal condition"
    ],
    "related": [
        "season",
        "solar_energy"
    ]
},
"precipitation": {
    "label": "Precipitation",
    "domain": "water",
    "description": (
        "Water falling from the atmosphere, including rain "
        "and other forms of precipitation."
    ),
    "synonyms": [
        "rain",
        "rainfall",
        "snow",
        "precipitation"
    ],
    "related": [
        "atmospheric_moisture",
        "soil_moisture",
        "cloud"
    ]
},
"cloud": {
    "label": "Cloud cover",
    "domain": "air",
    "description": (
        "The fraction of the sky obscured by clouds."
    ),
    "synonyms": [
        "cloud",
        "cloudiness",
        "cloud cover",
        "overcast"
    ],
    "related": [
        "atmospheric_moisture",
        "precipitation",
        "sunlight"
    ]
},
"pressure": {
    "label": "Atmospheric pressure",
    "domain": "air",
    "description": (
        "Pressure exerted by the atmosphere at the observation location."
    ),
    "synonyms": [
        "air pressure",
        "barometric pressure",
        "atmospheric pressure"
    ],
    "related": [
        "weather",
        "wind"
    ]
},
"wind": {
    "label": "Wind",
    "domain": "air",
    "description": (
        "Movement of air through the local environment."
    ),
    "synonyms": [
        "air movement",
        "airflow",
        "wind"
    ],
    "related": [
        "pressure",
        "weather"
    ]
},
"tide": {
    "label": "Tidal state",
    "domain": "water",
    "description": (
        "The observed state and height of the local tide."
    ),
    "synonyms": [
        "tide",
        "tidal state",
        "tidal height",
        "high tide",
        "low tide"
    ],
    "related": [
        "moon",
        "sea",
        "water"
    ]
},
"marine_conditions": {
    "label": "Marine conditions",
    "domain": "water",
    "description": (
        "Observed conditions of the nearby marine environment, "
        "including waves, sea temperature and currents."
    ),
    "synonyms": [
        "ocean conditions",
        "sea conditions",
        "marine state",
        "waves",
        "ocean currents"
    ],
    "related": [
        "tide",
        "water",
        "wind"
    ]
},
"soil_temperature": {
    "label": "Soil temperature",
    "domain": "earth",
    "description": (
        "Thermal condition of the soil at measured depths."
    ),
    "synonyms": [
        "ground temperature",
        "soil heat"
    ],
    "related": [
        "temperature",
        "soil_moisture"
    ]
},
"vegetation": {
    "label": "Vegetation",
    "domain": "earth",
    "description": (
        "Observed state or greenness of vegetation."
    ),
    "synonyms": [
        "plants",
        "vegetation",
        "greenness",
        "plant activity",
        "NDVI"
    ],
    "related": [
        "soil_moisture",
        "precipitation",
        "season"
    ]
},
"geology": {
    "label": "Geology",
    "domain": "earth",
    "description": (
        "Underlying geological and tectonic character of the location."
    ),
    "synonyms": [
        "geology",
        "geological province",
        "tectonic zone",
        "rock"
    ],
    "related": [
        "earthquake",
        "elevation"
    ]
},
"earthquake": {
    "label": "Seismic activity",
    "domain": "earth",
    "description": (
        "Recorded earthquake activity within the defined search window."
    ),
    "synonyms": [
        "earthquake",
        "earthquakes",
        "seismic activity",
        "earth tremor"
    ],
    "related": [
        "geology",
        "tectonics"
    ]
},
"elevation": {
    "label": "Elevation",
    "domain": "earth",
    "description": (
        "Height of the observation location above sea level."
    ),
    "synonyms": [
        "altitude",
        "elevation",
        "height above sea level"
    ],
    "related": [
        "terrain",
        "topography"
    ]
},
"solar_activity": {
    "label": "Solar activity",
    "domain": "fire",
    "description": (
        "Observed or reconstructed activity of the Sun, "
        "including sunspot activity and solar radio measurements."
    ),
    "synonyms": [
        "solar activity",
        "sunspots",
        "sunspot number",
        "solar cycle"
    ],
    "related": [
        "sun",
        "sunlight",
        "heat"
    ]
},
"sun": {
    "label": "Sun",
    "domain": "space",
    "description": (
        "Astronomical position and state of the Sun."
    ),
    "synonyms": [
        "sun",
        "solar position",
        "solar body"
    ],
    "related": [
        "solar_activity",
        "sunlight",
        "season"
    ]
},
"moon": {
    "label": "Moon",
    "domain": "space",
    "description": (
        "Astronomical position and state of the Moon."
    ),
    "synonyms": [
        "moon",
        "lunar state",
        "lunar position"
    ],
    "related": [
        "tide",
        "lunar_phase"
    ]
},
"planetary_positions": {
    "label": "Planetary positions",
    "domain": "space",
    "description": (
        "Observed astronomical positions and motions of the planets."
    ),
    "synonyms": [
        "planetary positions",
        "planets",
        "planetary configuration",
        "planetary alignment"
    ],
    "related": [
        "astronomy",
        "zodiac"
    ]
},
"ascendant": {
    "label": "Ascendant",
    "domain": "space",
    "description": (
        "The zodiac degree rising on the eastern horizon at the "
        "observation moment and location — the chart's rising sign."
    ),
    "synonyms": [
        "ascendant",
        "rising sign",
        "lagna"
    ],
    "related": [
        "astrological_houses",
        "sun",
        "moon"
    ]
},
"midheaven": {
    "label": "Midheaven",
    "domain": "space",
    "description": (
        "The zodiac degree at the chart's upper meridian (MC) at the "
        "observation moment and location."
    ),
    "synonyms": [
        "midheaven",
        "mc",
        "medium coeli"
    ],
    "related": [
        "astrological_houses",
        "ascendant"
    ]
},
"astrological_houses": {
    "label": "Astrological houses",
    "domain": "space",
    "description": (
        "The twelve house cusps computed for the observation moment "
        "and location under a given house system."
    ),
    "synonyms": [
        "houses",
        "house cusps",
        "chart houses"
    ],
    "related": [
        "ascendant",
        "midheaven",
        "astrological_house_system"
    ]
},
"astrological_aspects": {
    "label": "Astrological aspects",
    "domain": "space",
    "description": (
        "Computed angular relationships (conjunction, sextile, square, "
        "trine, quincunx, opposition) between chart bodies at the "
        "observation moment."
    ),
    "synonyms": [
        "aspects",
        "planetary aspects",
        "chart aspects"
    ],
    "related": [
        "sun",
        "moon",
        "planetary_positions"
    ]
},
"elemental_balance": {
    "label": "Chart elemental balance",
    "domain": "space",
    "description": (
        "Count of chart planets falling in fire/earth/air/water "
        "signs via classical triplicities — a property of the "
        "chart's geometry, independent of environmental data."
    ),
    "synonyms": [
        "elemental balance",
        "triplicity balance"
    ],
    "related": [
        "sun",
        "moon",
        "planetary_positions"
    ]
},
"fixed_stars": {
    "label": "Fixed stars",
    "domain": "space",
    "description": (
        "Positions of named fixed stars from the Swiss Ephemeris "
        "catalog at the observation moment."
    ),
    "synonyms": [
        "fixed stars",
        "stars",
        "star catalog"
    ],
    "related": [
        "fixed_star_conjunctions",
        "planetary_positions"
    ]
},
"fixed_star_conjunctions": {
    "label": "Fixed star conjunctions",
    "domain": "space",
    "description": (
        "Chart bodies found in tight conjunction (within a small "
        "orb) with a named fixed star — the traditional threshold "
        "for a fixed star being considered meaningful."
    ),
    "synonyms": [
        "star conjunctions",
        "fixed star aspects"
    ],
    "related": [
        "fixed_stars",
        "astrological_aspects"
    ]
},
"astrological_house_system": {
    "label": "Astrological house system",
    "domain": "space",
    "description": (
        "The house-division method used to compute the chart's "
        "houses (e.g. Placidus, whole sign, equal, Koch)."
    ),
    "synonyms": [
        "house system"
    ],
    "related": [
        "astrological_houses"
    ]
},
"astronomical_time": {
    "label": "Astronomical time",
    "domain": "space",
    "description": (
        "The Julian Day of the observation moment — provenance/"
        "timing context rather than an interpretive concept itself."
    ),
    "synonyms": [
        "julian day"
    ],
    "related": [
        "sun",
        "moon"
    ]
},
"night": {
    "label": "Nighttime",
    "domain": "space",
    "description": (
        "The observation occurring during local nighttime."
    ),
    "synonyms": [
        "night",
        "nighttime",
        "darkness",
        "nocturnal"
    ],
    "related": [
        "moon",
        "sun",
        "darkness"
    ]
},
"season": {
    "label": "Season",
    "domain": "space",
    "description": (
        "Seasonal position of the observation within the annual cycle."
    ),
    "synonyms": [
        "season",
        "seasonal state",
        "winter",
        "summer",
        "spring",
        "autumn",
        "fall"
    ],
    "related": [
        "temperature",
        "sun",
        "vegetation"
    ]
},
"wheel_of_the_year_sabbat": {
    "label": "Wheel of the Year sabbat",
    "domain": "space",
    "description": (
        "The nearest of the eight Pagan/Wiccan sabbats to the "
        "observation date, adjusted for hemisphere so the sabbat's "
        "seasonal meaning (e.g. Yule at the winter solstice) matches "
        "the season actually experienced at that latitude."
    ),
    "synonyms": [
        "sabbat",
        "wheel of the year",
        "Samhain",
        "Yule",
        "Imbolc",
        "Ostara",
        "Beltane",
        "Litha",
        "Lughnasadh",
        "Mabon"
    ],
    "related": [
        "season",
        "sun"
    ]
},
"vedic_sun": {
    "label": "Vedic Sun placement",
    "domain": "space",
    "description": (
        "Sun's sidereal (Lahiri ayanamsa) sign, nakshatra, and "
        "whole-sign house, as used in Vedic/Jyotish astrology — "
        "distinct from the tropical Sun used elsewhere in this chart."
    ),
    "synonyms": [
        "sidereal sun",
        "vedic sun",
        "jyotish sun"
    ],
    "related": [
        "sun",
        "vedic_moon",
        "vedic_ascendant"
    ]
},
"vedic_moon": {
    "label": "Vedic Moon placement",
    "domain": "space",
    "description": (
        "Moon's sidereal (Lahiri ayanamsa) sign, nakshatra, and "
        "whole-sign house."
    ),
    "synonyms": [
        "sidereal moon",
        "vedic moon",
        "jyotish moon"
    ],
    "related": [
        "moon",
        "vedic_sun",
        "vedic_ascendant"
    ]
},
"vedic_ascendant": {
    "label": "Vedic Ascendant (Lagna)",
    "domain": "space",
    "description": (
        "Sidereal Ascendant sign and nakshatra — the Lagna, the "
        "reference point whole-sign houses are counted from."
    ),
    "synonyms": [
        "lagna",
        "sidereal ascendant",
        "vedic ascendant"
    ],
    "related": [
        "ascendant",
        "vedic_sun",
        "vedic_moon"
    ]
},
"vedic_positions": {
    "label": "Vedic planetary positions",
    "domain": "space",
    "description": (
        "Sidereal (Lahiri ayanamsa) sign, nakshatra, and whole-sign "
        "house for chart bodies other than the Sun, Moon, and "
        "Ascendant."
    ),
    "synonyms": [
        "sidereal positions",
        "jyotish positions",
        "vedic planets"
    ],
    "related": [
        "vedic_sun",
        "vedic_moon",
        "vedic_ascendant",
        "planetary_positions"
    ]
},
"chinese_pillars": {
    "label": "Chinese Four Pillars (BaZi)",
    "domain": "space",
    "description": (
        "Year, Month, Day, and Hour pillars (each a Heavenly Stem + "
        "Earthly Branch) and the Day Master — BaZi's own chart "
        "structure, built from a lunisolar/sexagenary calendar "
        "rather than planets-in-signs. Has no native Sun/Moon/"
        "Ascendant or Western/Vedic-style house system."
    ),
    "synonyms": [
        "bazi",
        "four pillars",
        "chinese zodiac",
        "day master",
        "sexagenary pillars"
    ],
    "related": []
},
"chart_shape": {
    "label": "Chart shape",
    "domain": "space",
    "description": (
        "Marc Edmund Jones' chart-shape classification (Bundle, "
        "Bowl, Locomotive, Splash, ...) based on how the chart's "
        "bodies are distributed around the 360-degree wheel — the "
        "size of the largest empty gap between them."
    ),
    "synonyms": [
        "bundle",
        "bowl",
        "bucket",
        "locomotive",
        "splash",
        "splay",
        "planetary pattern"
    ],
    "related": ["aspect_patterns"]
},
"harmonic_charts": {
    "label": "Harmonic charts",
    "domain": "space",
    "description": (
        "5th, 7th, and 9th harmonic charts (John Addey's harmonic "
        "theory) — every body's longitude multiplied by the harmonic "
        "number and wrapped to 360 degrees, with Equal House "
        "placements from the harmonic Ascendant. A different lens on "
        "the same birth moment, corresponding to the quintile "
        "(5th), septile (7th), and novile (9th) aspect families."
    ),
    "synonyms": [
        "harmonic chart",
        "H5", "H7", "H9",
        "quintile chart", "septile chart", "novile chart"
    ],
    "related": ["astrological_aspects"]
},
"aspect_patterns": {
    "label": "Aspect patterns",
    "domain": "space",
    "description": (
        "Recurring geometric configurations formed by three or more "
        "aspects linking chart points (Grand Trine, T-Square, Grand "
        "Cross, Yod, Kite, Mystic Rectangle), plus sign-based "
        "Stelliums and the overall chart shape (how bodies are "
        "distributed around the wheel) — distinct from any single "
        "aspect on its own."
    ),
    "synonyms": [
        "grand trine",
        "t-square",
        "yod",
        "grand cross",
        "kite",
        "mystic rectangle",
        "stellium",
        "chart shape"
    ],
    "related": ["astrological_aspects"]
},
"rulership": {
    "label": "Chart ruler and dispositor chains",
    "domain": "space",
    "description": (
        "The chart ruler (traditional ruler of the Ascendant sign), "
        "its own sign and house, and every classical planet's "
        "dispositor chain — which planet's sign each is placed in, "
        "followed until it reaches a planet in its own sign (final "
        "dispositor) or a mutual-reception loop."
    ),
    "synonyms": [
        "chart ruler",
        "ruling planet",
        "dispositor",
        "final dispositor",
        "rulership chain"
    ],
    "related": ["ascendant"]
},
"antiscia": {
    "label": "Antiscia and contra-antiscia",
    "domain": "space",
    "description": (
        "Mirror points across the zodiac's two symmetry axes: "
        "antiscion (mirrored across the solstice axis, 0 Cancer/0 "
        "Capricorn — a 'hidden harmony' point) and contra-antiscion "
        "(mirrored across the equinox axis, 0 Aries/0 Libra — a "
        "'hidden tension' point), computed for the Sun and Moon."
    ),
    "synonyms": [
        "antiscia",
        "antiscion",
        "contra-antiscia",
        "contrantiscia",
        "shadow point"
    ],
    "related": [
        "sun",
        "moon"
    ]
},
"declination_aspects": {
    "label": "Declination aspects (parallels)",
    "domain": "space",
    "description": (
        "Parallel and contraparallel aspects — a body pair sharing "
        "the same declination (angular distance from the celestial "
        "equator), either in the same hemisphere (parallel, read "
        "like a strong conjunction) or opposite hemispheres "
        "(contraparallel, read like a weaker opposition). A "
        "different coordinate axis from the longitude-based aspects "
        "above, computed only when opted in."
    ),
    "synonyms": [
        "parallel",
        "contraparallel",
        "declination aspect"
    ],
    "related": [
        "astrological_aspects"
    ]
},
"structural_findings": {
    "label": "Structural findings",
    "domain": "space",
    "description": (
        "Chart-wide observations that describe how several "
        "independently-computed placements relate as a system rather "
        "than attaching to one body or aspect: multiple significant "
        "points clustering in one house, an aspect pattern's "
        "structurally 'empty' point coinciding with an unrelated "
        "placement, or a declination contact that carries no matching "
        "longitude aspect at all (genuinely new information rather "
        "than a second, reinforcing measurement of an aspect already "
        "visible)."
    ),
    "synonyms": [
        "house concentration",
        "empty leg",
        "declination relationship",
        "structural finding"
    ],
    "related": [
        "astrological_houses",
        "aspect_patterns",
        "declination_aspects"
    ]
},
"vertex": {
    "label": "Vertex",
    "domain": "space",
    "description": (
        "A mathematically calculated point — the intersection of the "
        "ecliptic and the prime vertical — traditionally read as an "
        "'auxiliary Descendant' marking fated or karmic encounters. "
        "Falls in the Vertex's own sign and house; the Anti-Vertex is "
        "the exact opposite point."
    ),
    "synonyms": [
        "vertex",
        "anti-vertex",
        "antivertex",
        "third angle"
    ],
    "related": [
        "ascendant",
        "midheaven"
    ]
},
"part_of_fortune": {
    "label": "Part of Fortune",
    "domain": "space",
    "description": (
        "Classical Hellenistic Lot of Fortune: a sect-aware (day/"
        "night) point derived from the Ascendant, Sun, and Moon "
        "longitudes, placed by sign and house."
    ),
    "synonyms": [
        "part of fortune",
        "lot of fortune",
        "pars fortunae"
    ],
    "related": [
        "part_of_spirit",
        "ascendant",
        "sun",
        "moon"
    ]
},
"part_of_spirit": {
    "label": "Part of Spirit",
    "domain": "space",
    "description": (
        "Classical Hellenistic Lot of Spirit: a sect-aware (day/"
        "night) point derived from the Ascendant, Sun, and Moon "
        "longitudes — the exact reverse formula of the Part of "
        "Fortune at the same sect — placed by sign and house."
    ),
    "synonyms": [
        "part of spirit",
        "lot of spirit",
        "pars spiritus"
    ],
    "related": [
        "part_of_fortune",
        "ascendant",
        "sun",
        "moon"
    ]
},
"chinese_ten_gods": {
    "label": "Chinese Ten Gods",
    "domain": "space",
    "description": (
        "Classification of the Year/Month/Hour visible stems and "
        "every hidden stem within all four branches, relative to the "
        "Day Master, by the Five Element generating/controlling "
        "cycle and stem polarity — a BaZi-native structural role "
        "(Wealth, Officer, Resource, Output, Companion) each stem "
        "plays relative to the person's own core element."
    ),
    "synonyms": [
        "ten gods",
        "shi shen",
        "wealth star",
        "officer star",
        "resource star",
        "output star",
        "companion star"
    ],
    "related": [
        "chinese_pillars"
    ]
},
"chinese_dayun": {
    "label": "Chinese Da Yun (Luck Pillars)",
    "domain": "space",
    "description": (
        "The 10-year Luck Pillar sequence overlaid on the Four "
        "Pillars, continuing the sexagenary cycle from the Month "
        "Pillar in a direction determined by Year Stem polarity and "
        "gender — which pillar is active as of a specified 'as of' "
        "date."
    ),
    "synonyms": [
        "da yun",
        "luck pillars",
        "great luck",
        "10-year cycle"
    ],
    "related": [
        "chinese_pillars",
        "current_transits",
        "secondary_progressions",
        "vedic_dasha"
    ]
},
"vedic_dasha": {
    "label": "Vimshottari Dasha",
    "domain": "space",
    "description": (
        "The classical Vedic planetary-period timing system: which "
        "Mahadasha (major period) and Antardasha (sub-period) lord "
        "is active as of a specified 'as of' date, plus the full "
        "birth-to-120-year Mahadasha sequence."
    ),
    "synonyms": [
        "dasha",
        "vimshottari dasha",
        "mahadasha",
        "antardasha",
        "planetary period"
    ],
    "related": [
        "vedic_moon",
        "current_transits",
        "secondary_progressions"
    ]
},
"vedic_yogas": {
    "label": "Vedic yogas",
    "domain": "space",
    "description": (
        "Classical planetary combinations (Gajakesari, Budhaditya, "
        "and the five Pancha Mahapurusha yogas) present in the "
        "sidereal chart — specific, named configurations distinct "
        "from any single planet's sign or house on its own."
    ),
    "synonyms": [
        "yogas",
        "yoga",
        "planetary combinations",
        "gajakesari",
        "budhaditya",
        "pancha mahapurusha"
    ],
    "related": [
        "vedic_positions",
        "vedic_sun",
        "vedic_moon"
    ]
},
"navamsa_sun": {
    "label": "Navamsa (D9) Sun placement",
    "domain": "space",
    "description": (
        "Sun's sign and whole-sign house in the Navamsa (D9) "
        "divisional chart — the ninth-harmonic subdivision of the "
        "sidereal chart, read as a subtler confirmation of the D1 "
        "chart's strength."
    ),
    "synonyms": [
        "D9 sun",
        "navamsa sun"
    ],
    "related": [
        "vedic_sun",
        "navamsa_moon",
        "navamsa_ascendant"
    ]
},
"navamsa_moon": {
    "label": "Navamsa (D9) Moon placement",
    "domain": "space",
    "description": (
        "Moon's sign and whole-sign house in the Navamsa (D9) "
        "divisional chart."
    ),
    "synonyms": [
        "D9 moon",
        "navamsa moon"
    ],
    "related": [
        "vedic_moon",
        "navamsa_sun",
        "navamsa_ascendant"
    ]
},
"navamsa_ascendant": {
    "label": "Navamsa (D9) Ascendant",
    "domain": "space",
    "description": (
        "The D9 chart's own Ascendant sign — the reference point its "
        "whole-sign houses are counted from, distinct from the D1 "
        "(Rasi) Ascendant."
    ),
    "synonyms": [
        "D9 ascendant",
        "navamsa lagna"
    ],
    "related": [
        "vedic_ascendant",
        "navamsa_sun",
        "navamsa_moon"
    ]
},
"navamsa_positions": {
    "label": "Navamsa (D9) planetary positions",
    "domain": "space",
    "description": (
        "Sign and whole-sign house in the Navamsa (D9) divisional "
        "chart for bodies other than the Sun, Moon, and Ascendant."
    ),
    "synonyms": [
        "D9 positions",
        "navamsa planets"
    ],
    "related": [
        "navamsa_sun",
        "navamsa_moon",
        "navamsa_ascendant",
        "vedic_positions"
    ]
},
"vedic_vargas": {
    "label": "Vedic divisional charts (Shodasavarga)",
    "domain": "space",
    "description": (
        "The remaining Shodasavarga divisional charts beyond D1 "
        "(Rasi) and D9 (Navamsa, its own dedicated concept) — D2 "
        "(Hora, wealth), D3 (Drekkana, siblings/courage), D4 "
        "(Chaturthamsa, property), D7 (Saptamsa, children), D10 "
        "(Dasamsa, career), D12 (Dwadasamsa, parents), D16 "
        "(Shodasamsa, vehicles/comforts), D20 (Vimshamsa, spiritual "
        "practice), D24 (Chaturvimshamsa, learning), D27 "
        "(Saptavimshamsa, inherent strength), D30 (Trimshamsa, "
        "misfortune), D40 (Khavedamsa, auspicious/inauspicious "
        "effects), D45 (Akshavedamsa, general life conduct), and D60 "
        "(Shashtyamsa, past-life karma). Each divides the sidereal "
        "chart's signs by its own classical rule, per Brihat "
        "Parashara Hora Shastra ch. 6."
    ),
    "synonyms": [
        "divisional charts", "varga charts", "amsha charts",
        "Shodasavarga", "D2", "D3", "D4", "D7", "D10", "D12", "D16",
        "D20", "D24", "D27", "D30", "D40", "D45", "D60"
    ],
    "related": ["navamsa_ascendant", "vedic_positions"]
},
"vedic_dignity": {
    "label": "Vedic planetary dignity",
    "domain": "space",
    "description": (
        "Classical dignity (exalted, moolatrikona, own sign, "
        "friendly sign, neutral sign, enemy sign, or debilitated) "
        "and Baladi Avastha (degree-based Bala/Kumara/Yuva/Vriddha/ "
        "Mrita 'age' state) for each of the 7 classical planets, per "
        "Brihat Parashara Hora Shastra."
    ),
    "synonyms": [
        "planetary dignity", "exaltation", "debilitation",
        "moolatrikona", "own sign", "avastha", "baladi avastha"
    ],
    "related": ["vedic_positions"]
},
"vedic_karakas": {
    "label": "Jaimini Chara Karakas",
    "domain": "space",
    "description": (
        "The classical 7-karaka Jaimini scheme: the 7 planets ranked "
        "by degree within their sign, from Atmakaraka (soul "
        "significator, highest degree) to Darakaraka (spouse "
        "significator, lowest degree)."
    ),
    "synonyms": [
        "chara karaka", "atmakaraka", "amatyakaraka", "darakaraka",
        "jaimini karaka"
    ],
    "related": ["vedic_positions"]
},
"vedic_marak": {
    "label": "Marak (killer) planets",
    "domain": "space",
    "description": (
        "The lords of the 2nd and 7th houses from the Ascendant, "
        "traditionally consulted as timing significators for periods "
        "of vulnerability via Dasha — unless a single planet rules "
        "both houses, in which case it loses maraka status (Dwi "
        "Marak Na Marak)."
    ),
    "synonyms": ["maraka", "killer planets", "marak planets"],
    "related": ["vedic_positions", "vedic_dasha"]
},
"vedic_yogini_dasha": {
    "label": "Yogini Dasha",
    "domain": "space",
    "description": (
        "A distinct, compact 36-year Vedic timing cycle (8 Yoginis "
        "ruling 1-8 years each in fixed sequence), entered via the "
        "Moon's birth nakshatra — read alongside, not instead of, "
        "Vimshottari Dasha."
    ),
    "synonyms": ["yogini dasha", "36 year cycle", "yogini period"],
    "related": ["vedic_dasha"]
},
"vedic_chara_dasha": {
    "label": "Chara Dasha (Jaimini)",
    "domain": "space",
    "description": (
        "The Jaimini school's sign-based (not planet-based) timing "
        "system — each of the 12 signs rules a period of 1-12 years, "
        "determined by counting from the sign to wherever its lord "
        "sits."
    ),
    "synonyms": ["chara dasha", "char dasha", "jaimini dasha", "rashi dasha"],
    "related": ["vedic_dasha", "vedic_karakas"]
},
"vedic_ashtakavarga": {
    "label": "Ashtakavarga",
    "domain": "space",
    "description": (
        "The classical Vedic point-scoring system mapping relative "
        "strength across all 12 signs — each of 8 reference points "
        "(the 7 classical planets plus the Ascendant) contributes a "
        "tabulated set of Bindus (points) toward each planet's "
        "individual Bhinnashtakavarga scorecard, and summing all 7 "
        "gives the combined Sarvashtakavarga (337 points total)."
    ),
    "synonyms": [
        "ashtakavarga", "bindu", "bhinnashtakavarga", "sarvashtakavarga",
        "eight-fold strength"
    ],
    "related": ["vedic_dignity", "vedic_positions"]
},
"vedic_shadbala": {
    "label": "Shadbala (partial)",
    "domain": "space",
    "description": (
        "A deliberately partial computation of the classical Vedic "
        "six-fold planetary strength system — Uchcha, Ojayugma, "
        "Kendradi, and Drekkana Bala (four of Sthana Bala's five "
        "sub-parts), Dig Bala, and Naisargika Bala, each with a "
        "single well-verified classical formula. Explicitly does "
        "NOT include Saptavargaja Bala, Kala Bala, Chesta Bala, or "
        "Drik Bala — components research found genuinely contested "
        "or under-sourced — so this does not represent a true "
        "Shadbala grand total or a comparison against classical "
        "minimum-strength thresholds, only a relative comparison "
        "among the 7 classical planets on the well-verified factors."
    ),
    "synonyms": ["shadbala", "planetary strength", "sthana bala", "dig bala"],
    "related": ["vedic_dignity", "vedic_positions"]
},
"chinese_interactions": {
    "label": "Chinese stem/branch interactions",
    "domain": "space",
    "description": (
        "Classical BaZi interactions among the Four Pillars' stems "
        "and branches: He (stem combinations), Chong (branch "
        "clashes), He (branch combinations), Hai (branch harms), Po "
        "(branch destructions), and Xing (branch punishments) — "
        "structural relationships between pillars, distinct from any "
        "single pillar's own meaning."
    ),
    "synonyms": [
        "chong", "he", "xing", "po", "hai", "clash", "combination",
        "punishment", "harm", "destruction"
    ],
    "related": ["chinese_pillars"]
},
"chinese_elemental_balance": {
    "label": "Chinese elemental balance",
    "domain": "space",
    "description": (
        "A count of the 5 Chinese elements (Wood, Fire, Earth, "
        "Metal, Water) across all 8 stem positions a Four Pillars "
        "chart carries — the 4 visible pillar stems plus every "
        "hidden stem within the 4 pillar branches — reported "
        "chart-relatively as missing, dominant, and weakest-present "
        "elements."
    ),
    "synonyms": [
        "five elements", "wu xing", "elemental balance",
        "over-represented element", "missing element"
    ],
    "related": ["chinese_pillars"]
},
"chinese_liu_nian": {
    "label": "Chinese Liu Nian (Flowing Year)",
    "domain": "space",
    "description": (
        "The annual pillar overlaid on the Four Pillars as of a "
        "specified 'as of' date — the same sexagenary Year Pillar "
        "construction as the natal Year Pillar, applied to the "
        "current year. Read alongside Da Yun as the finer, "
        "year-by-year layer of BaZi timing technique."
    ),
    "synonyms": ["liu nian", "flowing year", "annual pillar"],
    "related": ["chinese_pillars", "chinese_dayun"]
},
"chinese_shen_sha": {
    "label": "Chinese Shen Sha (symbolic stars)",
    "domain": "space",
    "description": (
        "A curated set of 18 classical BaZi lookup-table stars — "
        "Tian Yi Gui Ren, Wen Chang Gui Ren, Jin Yu, Yang Ren, Tao "
        "Hua, Yi Ma, Hua Gai, Jiang Xing, Jie Sha, Zai Sha, Wang "
        "Shen, Gu Chen, Gua Su, Tian De Gui Ren, Yue De Gui Ren, "
        "Kong Wang, Sui Po, and Yuan Chen — each a specific "
        "stem/branch pattern across the Four Pillars, distinct from "
        "the Ten Gods classification."
    ),
    "synonyms": [
        "shen sha", "symbolic stars", "noble star", "nobleman",
        "peach blossom", "tao hua", "travel horse", "void", "kong wang"
    ],
    "related": ["chinese_pillars", "chinese_interactions"]
},
"chinese_na_yin": {
    "label": "Chinese Na Yin",
    "domain": "space",
    "description": (
        "The classical 60-Jiazi elemental-phase table — each pillar's "
        "Stem-Branch pair maps to one of 30 fixed Na Yin names and "
        "an associated element, distinct from (and older than) the "
        "stem's own element."
    ),
    "synonyms": ["na yin", "納音", "elemental sound", "sixty jiazi"],
    "related": ["chinese_pillars"]
},
"part_of_eros": {
    "label": "Lot of Eros",
    "domain": "space",
    "description": (
        "One of the seven classical Hermetic (Panaretos) Lots, built "
        "from Venus and the Lot of Spirit — desire, attraction, and "
        "what draws the soul toward union."
    ),
    "synonyms": ["lot of eros", "part of eros"],
    "related": ["part_of_fortune", "part_of_spirit"]
},
"part_of_necessity": {
    "label": "Lot of Necessity",
    "domain": "space",
    "description": (
        "One of the seven classical Hermetic (Panaretos) Lots, built "
        "from Mercury and the Lot of Fortune — obligation, "
        "constraint, and where fate imposes its demands."
    ),
    "synonyms": ["lot of necessity", "part of necessity"],
    "related": ["part_of_fortune"]
},
"part_of_courage": {
    "label": "Lot of Courage",
    "domain": "space",
    "description": (
        "One of the seven classical Hermetic (Panaretos) Lots, built "
        "from Mars and the Lot of Fortune — boldness, physical "
        "energy, and assertive action."
    ),
    "synonyms": ["lot of courage", "part of courage"],
    "related": ["part_of_fortune"]
},
"part_of_victory": {
    "label": "Lot of Victory",
    "domain": "space",
    "description": (
        "One of the seven classical Hermetic (Panaretos) Lots, built "
        "from Jupiter and the Lot of Spirit — success, achievement, "
        "and the expansion of influence through effort."
    ),
    "synonyms": ["lot of victory", "part of victory"],
    "related": ["part_of_spirit"]
},
"part_of_nemesis": {
    "label": "Lot of Nemesis",
    "domain": "space",
    "description": (
        "One of the seven classical Hermetic (Panaretos) Lots, built "
        "from Saturn and the Lot of Fortune — fate, karmic debts, "
        "and the weight of limitation and consequence."
    ),
    "synonyms": ["lot of nemesis", "part of nemesis"],
    "related": ["part_of_fortune"]
},
"current_transits": {
    "label": "Current transits",
    "domain": "space",
    "description": (
        "Present-moment planetary positions (Sun through Pluto) at a "
        "specified 'as of' date, placed in the natal house wheel and "
        "checked for aspects to natal planetary positions — the "
        "classical technique for reading a specific span of time "
        "against a birth chart."
    ),
    "synonyms": [
        "transits",
        "transiting planets",
        "current planetary positions"
    ],
    "related": [
        "planetary_positions",
        "astrological_aspects",
        "secondary_progressions"
    ]
},
"secondary_progressions": {
    "label": "Secondary progressions",
    "domain": "space",
    "description": (
        "The 'day for a year' progressed chart at a specified 'as "
        "of' date — personal/social planetary positions recomputed "
        "at natal Julian day plus elapsed years, placed in the natal "
        "house wheel and checked for aspects to natal planetary "
        "positions."
    ),
    "synonyms": [
        "progressions",
        "progressed chart",
        "progressed planets",
        "progressed moon"
    ],
    "related": [
        "planetary_positions",
        "astrological_aspects",
        "current_transits"
    ]
},
"tertiary_progressions": {
    "label": "Tertiary progressions",
    "domain": "space",
    "description": (
        "The 'day for a sidereal month' progressed chart at a "
        "specified 'as of' date — a faster, month-by-month symbolic "
        "timing technique than secondary progressions, personal/"
        "social planetary positions recomputed at natal Julian day "
        "plus elapsed sidereal months, checked for aspects to natal "
        "planetary positions."
    ),
    "synonyms": [
        "tertiary progressions",
        "tertiary progressed chart",
        "T I progressions"
    ],
    "related": [
        "planetary_positions",
        "astrological_aspects",
        "secondary_progressions"
    ]
}

}