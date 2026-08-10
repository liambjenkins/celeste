def _make_lens(name, tradition, lens_type):
    def lens(inputs):
        return {
            "name": name,
            "tradition": tradition,
            "type": lens_type,
            "interpretation": None,
        }

    return lens


LENSES = {
    "astrology": _make_lens(
        "Astrology",
        "Western astrological tradition",
        "symbolic",
    ),
    "islamic_cosmology": _make_lens(
        "Islamic Cosmology",
        "Islamic cosmological thought",
        "religious",
    ),
    "islamic_mysticism": _make_lens(
        "Islamic Mysticism",
        "Islamic mystical traditions",
        "mystical",
    ),
    "christian_mysticism": _make_lens(
        "Christian Mysticism",
        "Christian mystical traditions",
        "religious_mystical",
    ),
    "jewish_mysticism": _make_lens(
        "Jewish Mysticism",
        "Jewish mystical traditions",
        "religious_mystical",
    ),
    "hindu_cosmology": _make_lens(
        "Hindu Cosmology",
        "Hindu philosophical and cosmological traditions",
        "religious",
    ),
    "buddhist_cosmology": _make_lens(
        "Buddhist Cosmology",
        "Buddhist philosophical and cosmological traditions",
        "religious",
    ),
    "taoist_cosmology": _make_lens(
        "Taoist Cosmology",
        "Taoist philosophical traditions",
        "philosophical",
    ),
    "pagan_wiccan": _make_lens(
        "Pagan / Wiccan",
        "Pagan and Wiccan traditions",
        "earth_spiritual",
    ),
    "philosophy": _make_lens(
        "Philosophy",
        "Philosophical traditions",
        "philosophical",
    ),
    "psychology": _make_lens(
        "Psychology",
        "Modern psychological frameworks",
        "psychological",
    ),
    "esotericism": _make_lens(
        "Western Esotericism",
        "Western esoteric traditions",
        "esoteric",
    ),
}