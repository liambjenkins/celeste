"""
Celeste canonical moment.

A Moment is the shared, normalised representation of one
reconstructed point in time and space.

All lenses consume the same moment.
Lenses do not fetch or reinterpret raw provider data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Moment:
    """
    Canonical reconstructed moment.
    """

    requested_time: datetime

    latitude: float
    longitude: float

    observations: dict[str, Any] = field(
        default_factory=dict
    )

    concepts: dict[str, Any] = field(
        default_factory=dict
    )


def build_moment(
    requested_time: datetime,
    latitude: float,
    longitude: float,
    observations: dict[str, Any],
    concepts: dict[str, Any],
) -> Moment:
    """
    Construct the canonical moment consumed by lenses.
    """

    return Moment(
        requested_time=requested_time,
        latitude=latitude,
        longitude=longitude,
        observations=observations,
        concepts=concepts,
    )


if __name__ == "__main__":
    moment = build_moment(
        requested_time=datetime(
            1996,
            7,
            22,
            3,
            10,
        ),
        latitude=-37.8136,
        longitude=144.9631,
        observations={},
        concepts={},
    )

    print("=== CELESTE MOMENT ===")
    print(
        "Time:",
        moment.requested_time,
    )
    print(
        "Location:",
        moment.latitude,
        moment.longitude,
    )
    print("Moment model: OK")
