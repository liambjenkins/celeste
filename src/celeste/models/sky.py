from dataclasses import dataclass


@dataclass(frozen=True)
class SkySnapshot:
    """The astronomical state of the sky at a given moment."""

    sun: float
    moon: float
    mercury: float
    venus: float
    mars: float
    jupiter: float
    saturn: float
    uranus: float
    neptune: float
    pluto: float