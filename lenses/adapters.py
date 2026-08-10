from .model import LensInterpretation

from .catalog import get_catalog
from .context import LensContext
from .registry import LensDefinition, LensRegistry


def _placeholder_interpretation(
    lens,
    context: LensContext,
):
    """
    Structured placeholder interpretation.

    The adapter may derive descriptive astrological themes from
    canonical planetary observations, while keeping those themes
    distinct from source-backed knowledge claims.
    """

    themes = []
    features = {}

    planetary = context.concepts.get(
        "planetary_positions"
    )

    if planetary:
        observations = planetary.get(
            "observations",
            [],
        )

        if observations:
            themes.append(
                "planetary_positions_present"
            )

    sun = context.concepts.get("sun")
    moon = context.concepts.get("moon")

    if sun:
        themes.append(
            "solar_position_present"
        )

    if moon:
        themes.append(
            "lunar_position_present"
        )

    # Extract astronomical longitudes when available.
    sun_longitude = None
    moon_longitude = None

    if sun:
        for observation in sun.get(
            "observations",
            [],
        ):
            value = observation.get(
                "value"
            )

            if isinstance(value, dict):
                sun_longitude = value.get(
                    "longitude"
                )

    if moon:
        for observation in moon.get(
            "observations",
            [],
        ):
            value = observation.get(
                "value"
            )

            if isinstance(value, dict):
                moon_longitude = value.get(
                    "longitude"
                )

    # Derive the angular separation between Sun and Moon.
    if (
        isinstance(sun_longitude, (int, float))
        and isinstance(moon_longitude, (int, float))
    ):
        separation = abs(
            sun_longitude - moon_longitude
        )

        if separation > 180:
            separation = 360 - separation

        features["sun_moon_angular_separation"] = separation

        if separation < 10:
            phase = "close_alignment"
            themes.append(
                "sun_moon_close_alignment"
            )
        elif separation < 100:
            phase = "growing_separation"
            themes.append(
                "sun_moon_growing_separation"
            )
        elif separation < 170:
            phase = "wide_separation"
            themes.append(
                "sun_moon_wide_separation"
            )
        else:
            phase = "opposition_range"
            themes.append(
                "sun_moon_opposition_range"
            )

        features["sun_moon_relationship"] = phase

    relevant_claims = list(
        context.knowledge_claims
    )

    sources = [
        source_id
        for item in relevant_claims
        if hasattr(item, "claim")
        for source_id in getattr(
            item.claim,
            "source_ids",
            (),
        )
    ]

    # Build interpretation only from approved,
    # resolver-selected knowledge.
    claim_statements = [
        item.claim.statement
        for item in relevant_claims
        if hasattr(item, "claim")
        and getattr(
            item.claim,
            "statement",
            None,
        )
    ]

    if claim_statements:
        interpretation = (
            f"{lens['name']} interpretation is informed "
            "by the following source-backed traditional "
            "claims:\n\n"
            + "\n".join(
                f"- {statement}"
                for statement in claim_statements
            )
        )
    else:
        interpretation = (
            f"{lens['name']} received "
            f"{len(context.concepts)} canonical concept(s) "
            "but no approved knowledge claims matched "
            "the supplied observations or features."
        )

    return LensInterpretation(
        lens_id=lens["lens_id"],
        name=lens["name"],
        tradition=lens["tradition"],
        relevant_claims=relevant_claims,
        observations=list(
            context.concepts.values()
        ),
        themes=themes,
        features=features,
        interpretation=interpretation,
        evidence_status=(
            "source_backed"
            if relevant_claims
            else "observation_only"
        ),
        caveats=[
            "Themes describe how the astrology lens "
            "organises supplied observations; they are "
            "not scientific claims about causation."
        ],
        sources=sources,
    )


def build_registry():
    """
    Build the complete Celeste lens registry.
    """

    registry = LensRegistry()

    for lens in get_catalog():

        def interpret(
            context,
            lens=lens,
        ):
            return _placeholder_interpretation(
                lens,
                context,
            )

        registry.register(
            LensDefinition(
                lens_id=lens["lens_id"],
                name=lens["name"],
                tradition=lens["tradition"],
                description=lens["description"],
                interpret=interpret,
            )
        )

    return registry


if __name__ == "__main__":
    registry = build_registry()

    print("=== CELESTE LENS ADAPTERS ===")
    print(
        f"Registered lenses: {len(registry)}"
    )

    for lens_id in registry.list():
        print(
            f"- {lens_id}"
        )

    print()
    print("Lens adapters: OK")
