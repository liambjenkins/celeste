from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CelestialEvent:
    """A meaningful celestial event."""

    name: str
    datetime: datetime
    category: str
    importance: float
    description: str