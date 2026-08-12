def _values(inputs):
    return {
        key: [
            observation.get("value")
            for observation in item.get("observations", [])
            if observation.get("value") is not None
        ]
        for key, item in inputs.items()
    }


def _mean(values):
    numbers = [
        value for value in values
        if isinstance(value, (int, float))
        and not isinstance(value, bool)
    ]
    return sum(numbers) / len(numbers) if numbers else None


def _base_interpretation(inputs):
    values = _values(inputs)
    signals = []

    humidity = _mean(values.get("atmospheric_moisture", []))
    temperature = _mean(values.get("temperature", []))
    pressure = _mean(values.get("pressure", []))
    cloud = _mean(values.get("cloud", []))
    precipitation = _mean(values.get("precipitation", []))

    if humidity is not None:
        if humidity >= 80:
            signals.append("high atmospheric moisture")
        elif humidity <= 30:
            signals.append("low atmospheric moisture")

    if temperature is not None:
        if temperature <= 10:
            signals.append("cool thermal conditions")
        elif temperature >= 30:
            signals.append("warm thermal conditions")

    if pressure is not None:
        if pressure < 1000:
            signals.append("relatively low atmospheric pressure")
        elif pressure > 1020:
            signals.append("relatively high atmospheric pressure")

    if cloud is not None:
        if cloud >= 70:
            signals.append("substantial cloud cover")
        elif cloud <= 20:
            signals.append("limited cloud cover")

    if precipitation is not None:
        signals.append(
            "active precipitation"
            if precipitation > 0
            else "no recorded precipitation"
        )

    return (
        "No interpretable environmental signals were available."
        if not signals
        else "; ".join(signals) + "."
    )


def _astronomy_interpretation(inputs):
    values = _values(inputs)
    signals = []

    if values.get("sun"):
        signals.append("solar position available")

    if values.get("moon"):
        signals.append("lunar position available")

    if values.get("planetary_positions"):
        signals.append("planetary configuration available")

    if values.get("season"):
        signals.append(
            f"seasonal context: {values['season'][0]}"
        )

    return (
        "No astronomical signals were available."
        if not signals
        else "; ".join(signals) + "."
    )


def _seasonal_interpretation(inputs):
    values = _values(inputs)
    season = values.get("season", [])

    if not season:
        return "No seasonal context was available."

    return f"seasonal context recorded as {season[0]}."


def _mystical_interpretation(inputs, tradition):
    values = _values(inputs)
    signals = []

    if values.get("season"):
        signals.append(
            f"seasonal symbolism may be considered within {tradition}"
        )

    if values.get("moon"):
        signals.append("lunar observation available as symbolic context")

    if values.get("sun"):
        signals.append("solar observation available as symbolic context")

    return (
        "No symbolic astronomical context was available."
        if not signals
        else "; ".join(signals) + "."
    )


def _philosophical_interpretation(inputs):
    values = _values(inputs)
    signals = []

    if values.get("season"):
        signals.append(
            f"the observation is situated in {values['season'][0]}"
        )

    if values.get("temperature"):
        signals.append("thermal conditions are part of the observed environment")

    if values.get("cloud"):
        signals.append("sky conditions are part of the observed environment")

    return (
        "No environmental context was available for philosophical reflection."
        if not signals
        else "; ".join(signals) + "."
    )


def _psychological_interpretation(inputs):
    values = _values(inputs)
    signals = []

    if values.get("temperature"):
        signals.append("cool environmental conditions")

    if values.get("atmospheric_moisture"):
        signals.append("high-resolution atmospheric context available")

    if values.get("season"):
        signals.append(
            f"seasonal context: {values['season'][0]}"
        )

    return (
        "No environmental context was available."
        if not signals
        else "; ".join(signals) + "."
    )


def _make_lens(name, tradition, lens_type, interpreter):
    def lens(inputs):
        return {
            "name": name,
            "tradition": tradition,
            "type": lens_type,
            "interpretation": interpreter(inputs),
        }

    return lens


LENSES = {
    "astrology": _make_lens(
        "Astrology",
        "Western astrological tradition",
        "symbolic",
        _astronomy_interpretation,
    ),

    "islamic_cosmology": _make_lens(
        "Islamic Cosmology",
        "Islamic cosmological thought",
        "religious",
        _seasonal_interpretation,
    ),

    "islamic_mysticism": _make_lens(
        "Islamic Mysticism",
        "Islamic mystical traditions",
        "mystical",
        lambda inputs: _mystical_interpretation(
            inputs,
            "Islamic mystical traditions",
        ),
    ),

    "christian_mysticism": _make_lens(
        "Christian Mysticism",
        "Christian mystical traditions",
        "religious_mystical",
        lambda inputs: _mystical_interpretation(
            inputs,
            "Christian mystical traditions",
        ),
    ),

    "jewish_mysticism": _make_lens(
        "Jewish Mysticism",
        "Jewish mystical traditions",
        "religious_mystical",
        lambda inputs: _mystical_interpretation(
            inputs,
            "Jewish mystical traditions",
        ),
    ),

    "hindu_cosmology": _make_lens(
        "Hindu Cosmology",
        "Hindu philosophical and cosmological traditions",
        "religious",
        _seasonal_interpretation,
    ),

    "buddhist_cosmology": _make_lens(
        "Buddhist Cosmology",
        "Buddhist philosophical and cosmological traditions",
        "religious",
        _seasonal_interpretation,
    ),

    "taoist_cosmology": _make_lens(
        "Taoist Cosmology",
        "Taoist philosophical traditions",
        "philosophical",
        _philosophical_interpretation,
    ),

    "pagan_wiccan": _make_lens(
        "Pagan / Wiccan",
        "Pagan and Wiccan traditions",
        "earth_spiritual",
        lambda inputs: _mystical_interpretation(
            inputs,
            "Pagan and Wiccan traditions",
        ),
    ),

    "philosophy": _make_lens(
        "Philosophy",
        "Philosophical traditions",
        "philosophical",
        _philosophical_interpretation,
    ),

    "psychology": _make_lens(
        "Psychology",
        "Modern psychological frameworks",
        "psychological",
        _psychological_interpretation,
    ),

    "esotericism": _make_lens(
        "Western Esotericism",
        "Western esoteric traditions",
        "esoteric",
        lambda inputs: _mystical_interpretation(
            inputs,
            "Western esoteric traditions",
        ),
    ),
}
