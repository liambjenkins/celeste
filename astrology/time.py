from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def local_to_utc(local_time: datetime, timezone_name: str) -> datetime:
    if local_time.tzinfo is not None:
        raise ValueError("local_time must be timezone-naive")

    localised = local_time.replace(
        tzinfo=ZoneInfo(timezone_name)
    )

    return localised.astimezone(timezone.utc)
