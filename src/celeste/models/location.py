from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    """A physical place on Earth."""

    latitude: float
    longitude: float
    timezone: str
    name: str | None = None