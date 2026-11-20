"""Validate acknowledgement/escalation plans before durable queuing."""
import re

INCIDENT_KEYS = ("display_text", "area", "escalate_while_resolved")
AREA = re.compile(r"[a-z0-9_]{1,64}")


def validate_incident(raw):
    """Optional alarm-window data of an acknowledged notification (3.6.0)."""
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("incident must be a mapping")
    unknown = set(raw) - set(INCIDENT_KEYS)
    if unknown:
        raise ValueError("unsupported incident fields: " + ", ".join(sorted(map(str, unknown)))
                         + " (supported: " + ", ".join(INCIDENT_KEYS) + ")")
    text = raw.get("display_text")
    if text is not None and (not isinstance(text, str) or len(text) > 500):
        raise ValueError("incident.display_text must be text up to 500 characters")
    area = raw.get("area")
    if area is not None and (not isinstance(area, str) or not AREA.fullmatch(area)):
        raise ValueError("incident.area must use a-z, 0-9 and _ (max 64)")
    remind = raw.get("escalate_while_resolved", True)
    if not isinstance(remind, bool):
        raise ValueError("incident.escalate_while_resolved must be true or false")
    return {"display_text": text, "area": area, "escalate_while_resolved": remind}


def validate_acknowledgement(raw, dedup_key):
    if raw is None:
        return None
    if not isinstance(raw, dict) or raw.get("required") is not True:
        raise ValueError("acknowledgement.required must be true")
    if not dedup_key or not isinstance(dedup_key,str) or len(dedup_key)>128:
        raise ValueError("acknowledged notifications require dedup_key (max 128 characters)")
    steps=raw.get("escalation", [])
    if not isinstance(steps,list) or len(steps)>5:
        raise ValueError("maximum five escalation stages")
    normalized=[]
    prior=0
    for step in steps:
        if not isinstance(step,dict) or set(step)!={"after","recipients"}:
            raise ValueError("escalation requires after and recipients")
        delay=step["after"]
        names=step["recipients"]
        if type(delay) is not int or not prior < delay <= 7*86400:
            raise ValueError("escalation after values must strictly increase")
        if isinstance(names,str):
            names=[names]
        if not isinstance(names,list) or not names or len(names)>20 or not all(
            isinstance(x,str) and x and len(x)<=100 for x in names
        ):
            raise ValueError("invalid escalation recipients")
        prior=delay
        normalized.append({"after":delay,"recipients":names})
    return {"key":dedup_key,"steps":normalized}
