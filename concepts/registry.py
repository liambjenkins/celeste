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
}

}