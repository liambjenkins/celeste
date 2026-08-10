from copy import deepcopy
from .registry import LENSES
def build_convergence(summary):
    convergence = {}
    for key, lens in LENSES.items():
        inputs = {}
        for input_name, item in summary.items():
            values = item.get("values", [])
            observations = []
            for value in values:
                observations.append(
                    {
                        "value": value,
                        "source": None,
                    }
                )
            inputs[input_name] = {
                "label": item.get("label"),
                "domain": item.get("domain"),
                "observations": observations,
            }
        # Give each lens its own copy so a lens cannot mutate
        # the canonical convergence input data.
        lens_inputs = deepcopy(inputs)
        result = lens(lens_inputs)
        convergence[key] = {
            "name": result.get("name"),
            "tradition": result.get("tradition"),
            "type": result.get("type"),
            "inputs": inputs,
            "interpretation": result.get("interpretation"),
        }
    return convergence