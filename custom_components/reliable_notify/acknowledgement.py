"""Validate acknowledgement/escalation plans before durable queuing."""


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
