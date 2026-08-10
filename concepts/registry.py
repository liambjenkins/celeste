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
}

}