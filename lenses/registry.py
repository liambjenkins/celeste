"""
Celeste lens registry.

Defines the application-level registry used by the lens
adapter layer.

Knowledge is kept separate from lens registration.
"""

from dataclasses import dataclass
from typing import Callable, Any


@dataclass(frozen=True)
class LensDefinition:
    """
    Application-level definition of an interpretive lens.
    """

    lens_id: str
    name: str
    tradition: str
    description: str
    interpret: Callable[[Any], Any]


class LensRegistry:
    """
    Registry of available interpretive lenses.
    """

    def __init__(self):
        self._lenses = {}

    def register(self, lens):
        """
        Register one lens definition.
        """

        if lens.lens_id in self._lenses:
            raise ValueError(
                f"Lens already registered: "
                f"{lens.lens_id}"
            )

        self._lenses[lens.lens_id] = lens

    def get(self, lens_id):
        """
        Retrieve one registered lens.
        """

        try:
            return self._lenses[lens_id]
        except KeyError:
            raise KeyError(
                f"Lens not registered: {lens_id}"
            )

    def list(self):
        """
        Return registered lens IDs.
        """

        return sorted(
            self._lenses.keys()
        )

    def __len__(self):
        return len(self._lenses)
