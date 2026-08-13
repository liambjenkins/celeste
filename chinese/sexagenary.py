"""
Sexagenary cycle primitives: the 10 Heavenly Stems and 12 Earthly
Branches that combine into the 60-cycle underlying all Four Pillars.
Pure data + the Pillar construction helper — no calendar logic here
(see chinese/pillars.py for Year/Month/Day/Hour derivation).
"""

from dataclasses import dataclass

STEMS = (
    ("Jia", "Wood", "Yang"), ("Yi", "Wood", "Yin"),
    ("Bing", "Fire", "Yang"), ("Ding", "Fire", "Yin"),
    ("Wu", "Earth", "Yang"), ("Ji", "Earth", "Yin"),
    ("Geng", "Metal", "Yang"), ("Xin", "Metal", "Yin"),
    ("Ren", "Water", "Yang"), ("Gui", "Water", "Yin"),
)

BRANCHES = (
    ("Zi", "Rat"), ("Chou", "Ox"), ("Yin", "Tiger"), ("Mao", "Rabbit"),
    ("Chen", "Dragon"), ("Si", "Snake"), ("Wu", "Horse"), ("Wei", "Goat"),
    ("Shen", "Monkey"), ("You", "Rooster"), ("Xu", "Dog"), ("Hai", "Pig"),
)

STEM_INDEX = {name: index for index, (name, _, _) in enumerate(STEMS)}
BRANCH_INDEX = {name: index for index, (name, _) in enumerate(BRANCHES)}


@dataclass(frozen=True)
class Pillar:
    stem: str
    stem_element: str
    stem_polarity: str
    branch: str
    branch_animal: str

    @property
    def name(self) -> str:
        return f"{self.stem}-{self.branch}"

    def to_dict(self) -> dict:
        return {
            "stem": self.stem,
            "stem_element": self.stem_element,
            "stem_polarity": self.stem_polarity,
            "branch": self.branch,
            "branch_animal": self.branch_animal,
            "name": self.name,
        }


def pillar_from_indices(stem_index: int, branch_index: int) -> Pillar:
    stem_index %= 10
    branch_index %= 12
    stem_name, stem_element, stem_polarity = STEMS[stem_index]
    branch_name, branch_animal = BRANCHES[branch_index]
    return Pillar(
        stem=stem_name,
        stem_element=stem_element,
        stem_polarity=stem_polarity,
        branch=branch_name,
        branch_animal=branch_animal,
    )
