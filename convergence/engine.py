from copy import deepcopy
from .registry import LENSES


def build_convergence(concepts):
    convergence = {}

    for key, lens in LENSES.items():
        lens_inputs = {}

        for concept_id, concept in concepts.items():
            observations = deepcopy(
                concept.get("observations", [])
            )

            lens_inputs[concept_id] = {
                "label": concept.get("label"),
                "domain": concept.get("domain"),
                "observations": observations,
            }

        result = lens(deepcopy(lens_inputs))

        convergence[key] = {
            "name": result.get("name"),
            "tradition": result.get("tradition"),
            "type": result.get("type"),
            "inputs": lens_inputs,
            "interpretation": result.get("interpretation"),
        }

    return convergence
