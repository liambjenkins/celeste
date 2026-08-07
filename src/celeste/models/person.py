from dataclasses import dataclass

from celeste.models.birth import BirthData


@dataclass(frozen=True)
class Person:
    """A person using Celeste."""

    name: str
    birth: BirthData