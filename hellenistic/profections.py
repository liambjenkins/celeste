"""
Annual profections: age-based whole-sign house activation.

Age is computed as elapsed tropical years (days elapsed / 365.25)
rather than a calendar-birthday difference -- profections are
traditionally keyed to the Sun's actual return to its natal degree
(the solar return), and elapsed-tropical-years tracks that far more
closely than a calendar-date comparison would (a calendar-birthday
check can be off by up to a day around leap years and doesn't account
for the birth time-of-day at all).
"""

from datetime import datetime

from hellenistic.constants import DOMICILE_LORDS

TROPICAL_YEAR_DAYS = 365.242190


def age_in_years(birth_utc_time: datetime, as_of_utc_time: datetime) -> float:
    elapsed_days = (as_of_utc_time - birth_utc_time).total_seconds() / 86400.0
    return elapsed_days / TROPICAL_YEAR_DAYS


def build_profection(birth_utc_time: datetime, as_of_utc_time: datetime, house_signs: dict) -> dict:
    age = age_in_years(birth_utc_time, as_of_utc_time)
    activated_house = 1 + (int(age) % 12)
    activated_sign = house_signs[str(activated_house)]

    return {
        "age_years": age,
        "activated_house": activated_house,
        "activated_sign": activated_sign,
        "year_lord": DOMICILE_LORDS[activated_sign],
    }
