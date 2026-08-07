from datetime import datetime

from celeste.models.person import Person
from celeste.models.birth import BirthData
from celeste.models.location import Location


LIAM = Person(
    name="Liam",
    birth=BirthData(
        moment=datetime(1996, 7, 22, 3, 10),
        location=Location(
            latitude=-37.760007,
            longitude=144.816422,
            timezone="Australia/Melbourne",
            name="Sunshine Hospital, St Albans",
        ),
    ),
)