"""Validate acknowledgement/escalation plans before durable queuing."""
import re

INCIDENT_KEYS = ("display_text", "area", "escalate_while_resolved", "source_entity", "problem_state",
                 "problem_states", "resolve_after", "auto_close_after")
AREA = re.compile(r"[a-z0-9_]{1,64}")
ENTITY_ID = re.compile(r"[a-z0-9_]+\.[a-z0-9_]+")
MAX_RESOLVE_AFTER = 86400
MAX_AUTO_CLOSE = 30 * 86400


def _seconds(value, name, maximum):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise ValueError(f"incident.{name} must be whole seconds between 0 and {maximum}")
    return value


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
    # Phase 2 (3.7.0): Reliable Notify watches the cause itself.
    source = raw.get("source_entity")
    if source is not None and (not isinstance(source, str) or not ENTITY_ID.fullmatch(source)):
        raise ValueError("incident.source_entity must be an entity ID such as binary_sensor.burner_fault")
    if "problem_state" in raw and "problem_states" in raw:
        raise ValueError("use either incident.problem_state or incident.problem_states")
    states = raw.get("problem_states", [raw["problem_state"]] if "problem_state" in raw else None)
    if states is not None:
        if source is None:
            raise ValueError("incident.problem_state(s) requires incident.source_entity")
        if isinstance(states, str):
            states = [states]
        if not isinstance(states, list) or not 1 <= len(states) <= 10 or any(
                not isinstance(s, str) or not s or len(s) > 64 or s in ("unavailable", "unknown") for s in states):
            raise ValueError("incident.problem_states must be 1 to 10 states (not unavailable/unknown)")
    elif source is not None:
        states = ["on"]
    resolve_after = _seconds(raw.get("resolve_after", 0), "resolve_after", MAX_RESOLVE_AFTER)
    if resolve_after and source is None:
        raise ValueError("incident.resolve_after requires incident.source_entity")
    auto_close = _seconds(raw.get("auto_close_after", 0), "auto_close_after", MAX_AUTO_CLOSE)
    return {"display_text": text, "area": area, "escalate_while_resolved": remind,
            "source_entity": source, "problem_states": states, "resolve_after": resolve_after,
            "auto_close_after": auto_close}


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
