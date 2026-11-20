"""Quiet hours and smart-notification policy validation."""
from datetime import datetime, timedelta, time as clock_time
from zoneinfo import ZoneInfo

DEFAULT_QUIET_HOURS = {
    "enabled": False,
    "start": "22:00",
    "end": "07:00",
    "allow_priorities": ["critical"],
}

def _parse_clock(value):
    if not isinstance(value,str) or len(value)!=5 or value[2]!=":":
        raise ValueError("time must use HH:MM")
    try:
        hour, minute=map(int,value.split(":"))
        return clock_time(hour,minute)
    except (ValueError,TypeError) as exc:
        raise ValueError("invalid HH:MM") from exc


def parse_clock(value):
    """Public HH:MM check (raises ValueError)."""
    return _parse_clock(value)


def validate_quiet_hours(raw):
    if not isinstance(raw,dict) or set(raw)-set(DEFAULT_QUIET_HOURS):
        raise ValueError("quiet_hours must be a mapping with known keys")
    policy={**DEFAULT_QUIET_HOURS,**raw}
    if type(policy["enabled"]) is not bool:
        raise ValueError("quiet_hours.enabled must be boolean")
    start=_parse_clock(policy["start"])
    end=_parse_clock(policy["end"])
    if start==end:
        raise ValueError("quiet hours start and end must differ")
    allow=policy["allow_priorities"]
    if not isinstance(allow,list) or any(x not in ("info","warning","critical") for x in allow):
        raise ValueError("invalid allow_priorities")
    return policy


def validate_route_quiet_hours(routes):
    """Check optional quiet_hours of recipients and persons (raises ValueError)."""
    for kind in ("recipients", "persons"):
        for name, spec in (routes.get(kind) or {}).items():
            if isinstance(spec, dict) and "quiet_hours" in spec:
                try:
                    validate_quiet_hours(spec["quiet_hours"])
                except ValueError as err:
                    raise ValueError(f"{name}: quiet_hours: {err}") from err
    return routes


MAX_SCHEDULE_SECONDS = 31 * 86400


def scheduled_timestamp(now, send_at=None, delay=None, timezone="UTC"):
    """Earliest send time requested by the caller (``send_at`` and/or ``delay``).

    ``send_at`` may be a datetime or ISO string; without a time zone it is read
    in the HA time zone. Times in the past mean "now". At most 31 days ahead.
    """
    target = now
    if delay is not None:
        if isinstance(delay, bool) or not isinstance(delay, (int, float)) or not 0 <= delay <= MAX_SCHEDULE_SECONDS:
            raise ValueError("delay must be 0..2678400 seconds")
        target = max(target, now + float(delay))
    if isinstance(send_at, str) and not send_at.strip():
        send_at = None  # empty form field
    if send_at is not None:
        if isinstance(send_at, str):
            try:
                send_at = datetime.fromisoformat(send_at.strip().replace("Z", "+00:00"))
            except ValueError as err:
                raise ValueError("send_at must be an ISO date/time") from err
        if not isinstance(send_at, datetime):
            raise ValueError("send_at must be a date/time")
        if send_at.tzinfo is None:
            send_at = send_at.replace(tzinfo=ZoneInfo(timezone))
        target = max(target, send_at.timestamp())
    if target - now > MAX_SCHEDULE_SECONDS:
        raise ValueError("notifications can be scheduled at most 31 days ahead")
    return target


def next_allowed_timestamp(now, priority, policy, timezone):
    """Return earliest allowed UNIX timestamp (DST-aware local civil clock)."""
    policy=validate_quiet_hours(policy)
    if not policy["enabled"] or priority in policy["allow_priorities"]:
        return now
    zone=ZoneInfo(timezone)
    local=datetime.fromtimestamp(now,zone)
    start=_parse_clock(policy["start"])
    end=_parse_clock(policy["end"])
    t=local.time().replace(tzinfo=None)
    if start < end:
        if not start<=t<end:
            return now
        end_date=local.date()
    else:
        if t>=start:
            end_date=local.date()+timedelta(days=1)
        elif t<end:
            end_date=local.date()
        else:
            return now
    target=datetime.combine(end_date,end,tzinfo=zone)
    return max(now,target.timestamp())
