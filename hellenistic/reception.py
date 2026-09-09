"""
Reception: is a planet welcomed by the planet that rules its sign?

Two fields, matching the variable spec:

- `mutual_reception_with`: strict, unambiguous case -- planet A sits
  in a sign domicile-ruled by planet B, and B sits in a sign domicile-
  ruled by A. Deliberately domicile-only (not extended to mutual
  reception by exaltation/triplicity/bound/decan, which is a real but
  looser classical extension) -- domicile-only is the standard,
  unambiguous base case and avoids picking among competing looser
  conventions for MVP.

- `received_by_dispositor`: whether this planet's dispositor (the
  domicile lord of the sign it occupies) is ITSELF dignified where it
  sits -- i.e. is this planet in the hands of a ruler who is
  well-placed, rather than a peregrine/afflicted one. A planet that
  IS its own dispositor (already in its own domicile) is trivially
  counted as received.
"""

from hellenistic.constants import CLASSICAL_PLANETS, DOMICILE_LORDS

_WEAK_STATUSES = {"peregrine", "detriment", "fall"}


def build_reception(bodies: dict, dignity_by_planet: dict) -> dict:
    dispositor_of = {
        planet: DOMICILE_LORDS[bodies[planet]["sign"]]
        for planet in CLASSICAL_PLANETS
        if planet in bodies
    }

    result = {}

    for planet, dispositor in dispositor_of.items():
        if dispositor == planet:
            received_by_dispositor = True
        else:
            dispositor_dignity = dignity_by_planet.get(dispositor, {})
            received_by_dispositor = dispositor_dignity.get("status") not in _WEAK_STATUSES

        mutual_with = None
        if dispositor != planet and dispositor_of.get(dispositor) == planet:
            mutual_with = dispositor

        result[planet] = {
            "dispositor": dispositor,
            "received_by_dispositor": received_by_dispositor,
            "mutual_reception_with": mutual_with,
        }

    return result
