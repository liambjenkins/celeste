from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConvergenceContext:
    """
    Shared interpretive context derived from the reconstructed moment.

    This is deliberately tradition-neutral.
    Lenses receive the same physical/celestial context and interpret it
    according to their own worldview.
    """

    requested_time: str
    location: dict[str, float]

    physical: dict[str, Any] = field(default_factory=dict)
    celestial: dict[str, Any] = field(default_factory=dict)
    terrestrial: dict[str, Any] = field(default_factory=dict)
    environmental: dict[str, Any] = field(default_factory=dict)

    signals: list[str] = field(default_factory=list)


@dataclass
class LensInterpretation:
    """
    Interpretation of a shared ConvergenceContext through one lens.

    A lens should describe what its own tradition notices or considers
    meaningful. It should not claim that another tradition agrees.
    """

    lens_id: str
    name: str
    tradition: str

    observations: list[str] = field(default_factory=list)
    themes: list[str] = field(default_factory=list)
    interpretation: str = ""

    confidence: str = "interpretive"

    sources: list[str] = field(default_factory=list)


@dataclass
class ConvergenceResult:
    """
    The result of passing one reconstructed moment through multiple lenses.
    """

    context: ConvergenceContext
    interpretations: list[LensInterpretation] = field(default_factory=list)

    shared_themes: list[str] = field(default_factory=list)

    synthesis: str = ""