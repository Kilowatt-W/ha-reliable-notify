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
