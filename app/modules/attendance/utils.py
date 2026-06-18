from datetime import datetime, timedelta, timezone

INDIA_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


def get_india_now():
    return datetime.now(INDIA_TIMEZONE)


def get_india_today():
    return get_india_now().date()


def to_india_datetime(value):
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(INDIA_TIMEZONE)
