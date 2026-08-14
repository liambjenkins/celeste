"""
Celeste interpretive lens catalogue.

Important:
These are distinct interpretive traditions, not interchangeable
"spirituality" categories.

The catalogue defines scope only.
Actual interpretation belongs in each lens implementation.
"""


LENS_CATALOG = [
    {
        "lens_id": "astrology",
        "name": "Astrology",
        "tradition": "Astrological traditions",
        "description": (
            "Symbolic interpretation of celestial positions, cycles, "
            "placements, and relationships."
        ),
    },
    {
        "lens_id": "islamic_cosmology",
        "name": "Islamic Cosmology",
        "tradition": "Islamic intellectual and cosmological traditions",
        "description": (
            "Cosmological perspectives grounded in Islamic thought, "
            "including creation, celestial order, signs, time, and the "
            "relationship between the created world and the Creator."
        ),
    },
    {
        "lens_id": "islamic_mysticism",
        "name": "Islamic Mysticism",
        "tradition": "Sufi and Islamic mystical traditions",
        "description": (
            "Mystical reflection on inner transformation, remembrance, "
            "the heart, signs, presence, and relationship with God."
        ),
    },
    {
        "lens_id": "christian_mysticism",
        "name": "Christian Mysticism",
        "tradition": "Christian mystical traditions",
        "description": (
            "Contemplative and mystical approaches to creation, "
            "divine presence, spiritual transformation, and the inner life."
        ),
    },
    {
        "lens_id": "jewish_mysticism",
        "name": "Jewish Mysticism",
        "tradition": "Jewish mystical traditions",
        "description": (
            "Mystical Jewish approaches to creation, divine emanation, "
            "sacred symbolism, the soul, and the structure of reality."
        ),
    },
    {
        "lens_id": "hindu_cosmology",
        "name": "Hindu Cosmology",
        "tradition": "Hindu philosophical and cosmological traditions",
        "description": (
            "Perspectives on cosmic cycles, time, nature, consciousness, "
            "dharma, and the relationship between individual and cosmos."
        ),
    },
    {
        "lens_id": "buddhist_cosmology",
        "name": "Buddhist Cosmology",
        "tradition": "Buddhist philosophical and cosmological traditions",
        "description": (
            "Buddhist perspectives on impermanence, dependent arising, "
            "cyclical existence, consciousness, and the nature of experience."
        ),
    },
    {
        "lens_id": "taoist_cosmology",
        "name": "Taoist Cosmology",
        "tradition": "Taoist philosophical traditions",
        "description": (
            "Perspectives on harmony, natural process, yin and yang, "
            "cyclicality, balance, and alignment with the Tao."
        ),
    },
    {
        "lens_id": "pagan_wiccan",
        "name": "Pagan & Wiccan",
        "tradition": "Modern Pagan and Wiccan traditions",
        "description": (
            "Nature-centred symbolic traditions engaging with seasonal "
            "cycles, lunar symbolism, elemental imagery, ritual, and "
            "relationship with the natural world."
        ),
    },
    {
        "lens_id": "greco_roman",
        "name": "Greco-Roman Cosmology",
        "tradition": "Ancient Greek and Roman religious traditions",
        "description": (
            "Ancient Mediterranean perspectives involving gods, celestial "
            "bodies, natural phenomena, fate, ritual, and cosmic order."
        ),
    },
    {
        "lens_id": "egyptian_cosmology",
        "name": "Ancient Egyptian Cosmology",
        "tradition": "Ancient Egyptian religious traditions",
        "description": (
            "Ancient Egyptian perspectives on cosmic order, sacred nature, "
            "death and renewal, celestial symbolism, and Ma'at."
        ),
    },
    {
        "lens_id": "depth_psychology",
        "name": "Depth Psychology",
        "tradition": "Jungian and symbolic psychological traditions",
        "description": (
            "Psychological interpretation of symbols, archetypes, dreams, "
            "patterns, inner states, and meaning-making."
        ),
    },
    {
        "lens_id": "vedic_astrology",
        "name": "Vedic Astrology",
        "tradition": "Jyotish (Vedic astrological traditions)",
        "description": (
            "Technical, predictive astrology using the sidereal "
            "zodiac (Lahiri ayanamsa) and nakshatras — distinct from "
            "the Hindu Cosmology lens, which covers cosmological and "
            "philosophical perspectives rather than chart technique."
        ),
    },
    {
        "lens_id": "chinese_zodiac",
        "name": "Chinese Astrology (BaZi)",
        "tradition": "Chinese Four Pillars of Destiny traditions",
        "description": (
            "Technical astrology built from the lunisolar sexagenary "
            "calendar — Year, Month, Day, and Hour pillars, and the "
            "Day Master as the reading's central reference point. "
            "Has no native Sun/Moon/Ascendant or Western/Vedic-style "
            "house system — read on its own terms, not forced into "
            "an equivalence this tradition doesn't make."
        ),
    },
    {
        "lens_id": "philosophy",
        "name": "Philosophy",
        "tradition": "Classical Western philosophical traditions",
        "description": (
            "Ethical and metaphysical perspectives grounded in classical "
            "philosophy — virtue, character, reason, fate, impermanence, "
            "and how to live well — drawn from Stoic and Aristotelian "
            "thought in particular."
        ),
    },
]


def get_catalog():
    """Return the complete lens catalogue."""
    return list(LENS_CATALOG)


def get_lens(lens_id):
    """Return one lens definition by ID."""
    for lens in LENS_CATALOG:
        if lens["lens_id"] == lens_id:
            return lens

    raise KeyError(f"Unknown lens: {lens_id}")