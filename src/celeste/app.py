from celeste.models.person import Person
from celeste.astronomy.ephemeris import AstronomyEngine


class Celeste:
    """Main Celeste interface."""

    def __init__(self, person: Person):
        self.person = person

    def birth_sky(self):
        return AstronomyEngine.get_sky_snapshot(
            self.person.birth.moment
        )