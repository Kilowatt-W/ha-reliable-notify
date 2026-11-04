"""Archive retention rules for Reliable Notify."""
import re

DEFAULT_RETENTION = {"info": 1, "warning": 7, "critical": 30}
_TYPE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


def validate_retention(value):
    if not isinstance(value, dict):
        raise ValueError("archive_retention must be an object")
    merged = dict(DEFAULT_RETENTION)
    for key, days in value.items():
        if not isinstance(key, str) or not _TYPE.fullmatch(key):
            raise ValueError("invalid archive message type")
        if type(days) is not int or not 0 <= days <= 365:
            raise ValueError("archive retention days must be integer 0..365")
        merged[key] = days
    return merged


def retention_for_message(data, policies):
    """Resolve per-message deletion, override, category and priority."""
    if data.get("archive") == "delete_after_send":
        return 0
    if data.get("archive_days") is not None:
        days = data["archive_days"]
        if type(days) is not int or not 0 <= days <= 365:
            raise ValueError("archive_days must be an integer 0..365")
        return days
    key = data.get("message_type") or data.get("priority", "info")
    return validate_retention(policies).get(key, DEFAULT_RETENTION.get(data.get("priority","info"), 1))
