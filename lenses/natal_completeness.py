"""
Natal chart completeness check (brief 2a): before answering any
query, confirm the chart actually has what's needed -- all planets,
Ascendant, MC, nodes, house cusps. If something's missing, the honest
answer is "I don't have enough of your chart to check this," never a
guess dressed as an answer.

astrology.chart.build_chart() always produces every field checked
here for an in-process chart built the normal way -- so this passes
trivially in the common case, by design. Its real job is guarding a
chart dict that arrived some other way (a cache, a future partial-
data path, a malformed/truncated input) and might genuinely be
missing pieces; every field access here is defensive (.get(), never
a bare [] that would raise) so a missing chart can't crash the query
layer, only degrade its answer honestly.
"""

from dataclasses import dataclass

REQUIRED_BODIES = (
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
    "uranus", "neptune", "pluto", "north_node_true",
)


@dataclass(frozen=True)
class CompletenessResult:
    complete: bool
    missing: tuple[str, ...]
    can_answer_house_questions: bool
    can_answer_point_questions: bool
    can_answer_node_questions: bool
    message: str


def check_natal_completeness(natal_chart: dict) -> CompletenessResult:
    missing: list[str] = []

    bodies = natal_chart.get("bodies") or {}
    for name in REQUIRED_BODIES:
        body = bodies.get(name)
        if not body or body.get("longitude") is None:
            missing.append(f"bodies.{name}")

    houses = natal_chart.get("houses") or {}
    angles = houses.get("angles") or {}
    if angles.get("ascendant") is None:
        missing.append("houses.angles.ascendant")
    if angles.get("mc") is None:
        missing.append("houses.angles.mc")

    cusps = houses.get("cusps") or {}
    for i in range(1, 13):
        if cusps.get(str(i)) is None:
            missing.append(f"houses.cusps.{i}")

    rulership = natal_chart.get("rulership") or {}
    if rulership.get("chart_ruler") is None:
        missing.append("rulership.chart_ruler")

    can_answer_point_questions = not any(m.startswith("bodies.") for m in missing)
    can_answer_house_questions = not any(
        m.startswith("houses.cusps") or m in ("houses.angles.ascendant", "houses.angles.mc")
        for m in missing
    )
    can_answer_node_questions = "bodies.north_node_true" not in missing

    complete = len(missing) == 0

    if complete:
        message = "Full chart loaded -- all placements, angles, and house cusps present."
    else:
        message = (
            "I don't have enough of your chart to check this -- missing: " + ", ".join(missing) + "."
        )

    return CompletenessResult(
        complete=complete,
        missing=tuple(missing),
        can_answer_house_questions=can_answer_house_questions,
        can_answer_point_questions=can_answer_point_questions,
        can_answer_node_questions=can_answer_node_questions,
        message=message,
    )


if __name__ == "__main__":
    from datetime import datetime, timezone

    from astrology.chart import build_chart
    from astrology.time import local_to_utc

    local_time = datetime(1996, 7, 22, 3, 10)
    aware_utc = local_to_utc(local_time, "Australia/Melbourne")
    birth_utc = aware_utc.replace(tzinfo=timezone.utc) if aware_utc.tzinfo is None else aware_utc
    natal = build_chart(birth_utc, -37.7392, 144.7967, house_system="placidus")

    result = check_natal_completeness(natal)
    print(f"A real, fully-built chart: complete={result.complete}")
    print(f"  {result.message}")

    broken = {"bodies": {name: data for name, data in natal["bodies"].items() if name != "saturn"}}
    result2 = check_natal_completeness(broken)
    print(f"\nA chart missing Saturn and all house data: complete={result2.complete}")
    print(f"  missing: {result2.missing}")
    print(f"  {result2.message}")
    print(f"  can_answer_point_questions={result2.can_answer_point_questions} "
          f"can_answer_house_questions={result2.can_answer_house_questions} "
          f"can_answer_node_questions={result2.can_answer_node_questions}")

    empty = {}
    result3 = check_natal_completeness(empty)
    print(f"\nAn empty chart dict: complete={result3.complete}, {len(result3.missing)} fields missing, no crash")
