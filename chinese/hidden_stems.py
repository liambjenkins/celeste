"""
Hidden Stems (藏干, Cang Gan): each Earthly Branch conceals one to
three Heavenly Stems, representing the qi of other elements present
within it. Needed for a correct BaZi reading, not an optional
refinement — a chart read only from its four visible (stem) positions
misses most of the elemental balance actually present, since every
branch carries this additional hidden layer.

Classical table (Main/Middle/Residual qi), verified via search during
curation against a real reference (the three branches at the peak of
each season — Zi, Mao, You — carry only their single main qi stem;
every other branch carries two or three).
"""

from chinese.sexagenary import STEM_INDEX, STEMS

# branch name -> tuple of (stem_name, qi_type), main qi first.
# qi_type is one of "main", "middle", "residual".
HIDDEN_STEMS = {
    "Zi": (("Gui", "main"),),
    "Chou": (("Ji", "main"), ("Gui", "middle"), ("Xin", "residual")),
    "Yin": (("Jia", "main"), ("Bing", "middle"), ("Wu", "residual")),
    "Mao": (("Yi", "main"),),
    "Chen": (("Wu", "main"), ("Yi", "middle"), ("Gui", "residual")),
    "Si": (("Bing", "main"), ("Geng", "middle"), ("Wu", "residual")),
    "Wu": (("Ding", "main"), ("Ji", "middle")),
    "Wei": (("Ji", "main"), ("Ding", "middle"), ("Yi", "residual")),
    "Shen": (("Geng", "main"), ("Ren", "middle"), ("Wu", "residual")),
    "You": (("Xin", "main"),),
    "Xu": (("Wu", "main"), ("Xin", "middle"), ("Ding", "residual")),
    "Hai": (("Ren", "main"), ("Jia", "middle")),
}


def hidden_stems_for(branch_name: str) -> list[dict]:
    """Every hidden stem within a branch, main qi first."""

    entries = []

    for stem_name, qi_type in HIDDEN_STEMS[branch_name]:
        _, element, polarity = STEMS[STEM_INDEX[stem_name]]
        entries.append(
            {
                "stem": stem_name,
                "element": element,
                "polarity": polarity,
                "qi_type": qi_type,
            }
        )

    return entries


if __name__ == "__main__":
    for branch in ("Zi", "Chou", "Yin", "Xu", "Hai"):
        stems = hidden_stems_for(branch)
        summary = ", ".join(f"{s['stem']} ({s['qi_type']})" for s in stems)
        print(f"{branch:6s} {summary}")
