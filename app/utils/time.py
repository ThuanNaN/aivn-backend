"""
All datetime in database is created in UTC timezone (aware datetime)
All datetime in response is converted to Asia/Ho_Chi_Minh timezone (aware datetime)

Example:

- Native to Aware
aware_dt = timezone.localize(naive_dt)


- Aware to Aware
aware_dt = timezone.localize(datetime(2024, 11, 15, 12, 30))
utc_dt = aware_dt.astimezone(pytz.UTC)

- Aware to Native
naive_dt = aware_dt.replace(tzinfo=None)
"""

from datetime import datetime, UTC, timedelta
import pytz
from pytz import timezone


utc_tz = pytz.utc
hcm_timezone = timezone(zone="Asia/Ho_Chi_Minh")


def utc_to_local(utc_time: datetime | str, 
                 return_isoformat: bool = True
                 ) -> datetime | str:
    if isinstance(utc_time, str):
        utc_time = datetime.fromisoformat(utc_time)

    if utc_time.tzinfo is None:
        utc_time = utc_time.replace(tzinfo=pytz.utc)

    hcm_time = utc_time.astimezone(hcm_timezone)

    if return_isoformat:
        return hcm_time.isoformat()
    return hcm_time


def local_to_utc(local_dt: str | datetime,
                 return_isoformat: bool = True
                 ) -> datetime | str:
    
    if isinstance(local_dt, str):
        local_dt = datetime.fromisoformat(local_dt)

    if local_dt.tzinfo is None:
        local_dt = hcm_timezone.localize(local_dt)
    else:
        local_dt = local_dt.astimezone(hcm_timezone)
        
    utc_dt = local_dt.astimezone(utc_tz)

    if return_isoformat:
        return utc_dt.isoformat()
    return utc_dt


def is_past(datetime_input: str | datetime, tz: str = "utc") -> bool:
    """
    Check if datetime_input is in the past. Using UTC time
    :param datetime_input: datetime
    :return: bool
    """
    if isinstance(datetime_input, str):
        datetime_input = datetime.fromisoformat(datetime_input)

    if tz == "utc":
        if datetime_input.tzinfo is None:
            datetime_input = datetime_input.replace(tzinfo=pytz.utc)
        return datetime_input < datetime.now(UTC)
    elif tz == "hcm":
        if datetime_input.tzinfo is None:
            datetime_input = hcm_timezone.localize(datetime_input)
        return datetime_input < datetime.now(hcm_timezone)

