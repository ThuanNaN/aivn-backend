import datetime

hcm_difference = datetime.timedelta(hours=7)

def utc_to_local_default(utc_time: datetime.datetime) -> datetime.datetime:
    local_time = utc_time + hcm_difference
    return local_time


def utc_to_local(utc_time: datetime.datetime) -> str:
    local_time = utc_time + hcm_difference
    return local_time.isoformat()

def local_to_utc(local_time: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(local_time) - hcm_difference

def str_to_datetime(str_datetime: str) -> datetime.datetime:
    return datetime.datetime.strptime(str_datetime, '%Y-%m-%dT%H:%M:%S.%f')


def created_before(datetime1: str, datetime2: str) -> bool:
    return str_to_datetime(datetime1) < str_to_datetime(datetime2)