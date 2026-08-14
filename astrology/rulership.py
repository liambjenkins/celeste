"""
Chart ruler and dispositor chains: traditional (7-planet) sign
rulerships, verified via search during curation, consistent with the
project's other traditional-technique sourcing (Lilly, Ptolemy).
Modern rulers (Uranus/Aquarius, Neptune/Pisces, Pluto/Scorpio) are a
real alternate convention but not used here, for the same reason
traditional rulership is used elsewhere in this codebase: it gives
every sign exactly one ruler, which is what a deterministic dispositor
chain needs — dual rulership (as under the modern system) doesn't
resolve to a single chain cleanly.

The chart ruler is the ruler of the Ascendant sign. A dispositor is
the ruler of the sign a planet occupies; walking a planet's
dispositor repeatedly either reaches a planet in its own sign (which
disposes itself — the chain's "final dispositor", not every chart has
one) or a mutual-reception loop (two or more planets disposing each
other in a cycle, with no single terminus).
"""

TRADITIONAL_RULERS = {
    "Aries": "mars",
    "Taurus": "venus",
    "Gemini": "mercury",
    "Cancer": "moon",
    "Leo": "sun",
    "Virgo": "mercury",
    "Libra": "venus",
    "Scorpio": "mars",
    "Sagittarius": "jupiter",
    "Capricorn": "saturn",
    "Aquarius": "saturn",
    "Pisces": "jupiter",
}

_CLASSICAL_PLANETS = (
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
)


def dispositor_of(sign: str) -> str:
    return TRADITIONAL_RULERS[sign]


def _dispositor_chain(planet_name: str, planet_signs: dict, max_steps: int = 10) -> dict:
    """
    Walk a planet's dispositor chain until it reaches a planet in its
    own sign (self-disposing, chain terminates) or repeats a planet
    already seen (a mutual-reception loop).
    """

    chain = [planet_name]
    seen = {planet_name}
    current = planet_name

    for _ in range(max_steps):
        sign = planet_signs.get(current)

        if sign is None:
            return {"chain": chain, "terminus": None, "loop": False}

        next_planet = dispositor_of(sign)

        if next_planet == current:
            # Self-disposing: in its own sign.
            return {"chain": chain, "terminus": current, "loop": False}

        if next_planet in seen:
            chain.append(next_planet)
            return {"chain": chain, "terminus": None, "loop": True}

        chain.append(next_planet)
        seen.add(next_planet)
        current = next_planet

    return {"chain": chain, "terminus": None, "loop": False}


def build_rulership(tropical_chart: dict) -> dict:
    """
    Chart ruler (ruler of the Ascendant), every classical planet's
    dispositor chain, and the final dispositor if the chart has one.
    """

    ascendant_longitude = tropical_chart["houses"]["angles"]["ascendant"]
    from astrology.normaliser import longitude_to_zodiac

    ascendant_sign = longitude_to_zodiac(ascendant_longitude)["sign"]
    chart_ruler = dispositor_of(ascendant_sign)

    bodies = tropical_chart["bodies"]
    planet_signs = {
        name: bodies[name]["sign"]
        for name in _CLASSICAL_PLANETS
        if name in bodies
    }

    chains = {
        name: _dispositor_chain(name, planet_signs)
        for name in planet_signs
    }

    # A final dispositor is a single planet in its own sign that
    # every OTHER planet's chain eventually reaches. Most charts
    # don't have one.
    self_disposing = {
        name for name, chain in chains.items()
        if chain["terminus"] == name
    }

    final_dispositor = None

    if len(self_disposing) == 1:
        candidate = next(iter(self_disposing))

        if all(
            chain["terminus"] == candidate
            for chain in chains.values()
        ):
            final_dispositor = candidate

    return {
        "ascendant_sign": ascendant_sign,
        "chart_ruler": chart_ruler,
        "chart_ruler_sign": planet_signs.get(chart_ruler),
        "chart_ruler_house": bodies.get(chart_ruler, {}).get("house"),
        "dispositor_chains": chains,
        "final_dispositor": final_dispositor,
    }


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    utc_aware = (
        aware_utc.replace(tzinfo=timezone.utc)
        if aware_utc.tzinfo is None
        else aware_utc
    )

    tropical = build_chart(utc_aware, -37.7392, 144.7967, house_system="placidus")
    rulership = build_rulership(tropical)

    print(f"Ascendant: {rulership['ascendant_sign']}")
    print(
        f"Chart ruler: {rulership['chart_ruler']} "
        f"({rulership['chart_ruler_sign']}, house {rulership['chart_ruler_house']})"
    )
    print(f"Final dispositor: {rulership['final_dispositor']}")
    print()
    for name, chain in rulership["dispositor_chains"].items():
        marker = " (loop)" if chain["loop"] else f" -> self-disposing: {chain['terminus']}" if chain["terminus"] else ""
        print(f"  {name:8s} {' -> '.join(chain['chain'])}{marker}")
