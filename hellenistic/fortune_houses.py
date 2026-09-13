"""
A second whole-sign house wheel, anchored at the Lot of Fortune's
sign instead of the Ascendant's -- per an engineering note (source:
George Vol. 2 Ch. 88): Fortune's own house position generates a
derived house system used specifically to weight the intensity of
timing techniques (zodiacal releasing in particular). A period is
traditionally more dramatic/eventful when it lands on the house
containing Fortune itself, or a house angular to it (1st/4th/7th/10th
counting from Fortune, not from the Ascendant); non-angular periods
are comparatively quiet.

Purely a relabeling of the same 12 signs around a different starting
point -- no new ephemeris data, same mechanism as
hellenistic.positions.whole_sign_house.
"""

from hellenistic.constants import ZODIAC_SIGNS

ANGULAR_TO_FORTUNE_HOUSES = {1, 4, 7, 10}


def house_from_fortune(sign_index: int, fortune_sign_index: int) -> int:
    return 1 + ((sign_index - fortune_sign_index) % 12)


def is_angular_to_fortune(sign_index: int, fortune_sign_index: int) -> bool:
    return house_from_fortune(sign_index, fortune_sign_index) in ANGULAR_TO_FORTUNE_HOUSES


def build_fortune_houses(fortune_sign_index: int) -> dict:
    """{house_number (relative to Fortune): sign}, parallel in shape
    to hellenistic.positions.build_positions' house_signs (which is
    relative to the Ascendant)."""

    return {
        str(house_num): ZODIAC_SIGNS[(fortune_sign_index + house_num - 1) % 12]
        for house_num in range(1, 13)
    }
