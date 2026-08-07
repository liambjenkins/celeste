from dataclasses import dataclass
from datetime import datetime

from celeste.models.location import Location


@dataclass(frozen=True)
class BirthData:
    """A person's exact birth information."""

    moment: datetime
    location: Location