from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BirthData:
    """A person's birth information."""

    datetime: datetime
    latitude: float
    longitude: float
    timezone: str