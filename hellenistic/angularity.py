"""Whole-sign angularity: purely a function of house number."""

ANGULAR_HOUSES = {1, 4, 7, 10}
SUCCEDENT_HOUSES = {2, 5, 8, 11}
CADENT_HOUSES = {3, 6, 9, 12}


def angularity(house: int) -> str:
    if house in ANGULAR_HOUSES:
        return "angular"
    if house in SUCCEDENT_HOUSES:
        return "succedent"
    return "cadent"
