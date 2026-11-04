"""Named notification profiles with deterministic override precedence."""
from __future__ import annotations
import re

IDENT=re.compile(r"^[a-z][a-z0-9_]{0,63}$")
FIELDS={"priority","recipients","message_type","archive","archive_days",
        "ttl","strategy","only_if","test_mode","acknowledgement"}
DEFAULT={
  "standard":{"priority":"info"},
  "important":{"priority":"warning"},
  "critical":{"priority":"critical"},
  "temporary":{"priority":"info","archive":"delete_after_send"},
  "digest":{"priority":"info","strategy":"digest"},
}


def validate_profiles(raw):
    if not isinstance(raw,dict) or len(raw)>100:
        raise ValueError("profiles must be a mapping of at most 100 entries")
    result={}
    for name,profile in raw.items():
        if not isinstance(name,str) or not IDENT.fullmatch(name):
            raise ValueError("invalid profile name")
        if not isinstance(profile,dict) or not profile or set(profile)-FIELDS:
            raise ValueError("unsupported profile fields")
        if profile.get("priority","info") not in ("info","warning","critical"):
            raise ValueError("invalid priority")
        if profile.get("archive","keep") not in ("keep","delete_after_send"):
            raise ValueError("invalid archive policy")
        if profile.get("strategy","always") not in ("always","replace","digest"):
            raise ValueError("invalid strategy")
        if "archive_days" in profile and (type(profile["archive_days"]) is not int
            or not 0<=profile["archive_days"]<=365):
            raise ValueError("invalid archive days")
        if "ttl" in profile and (type(profile["ttl"]) is not int or
            not 0<=profile["ttl"]<=31*86400):
            raise ValueError("invalid TTL")
        if "recipients" in profile:
            names=profile["recipients"]
            if isinstance(names,str):names=[names]
            if not isinstance(names,list) or not names or len(names)>50 or not all(
                isinstance(x,str) and IDENT.fullmatch(x) for x in names
            ):
                raise ValueError("invalid profile recipients")
        if "only_if" in profile:
            cond=profile["only_if"]
            if not isinstance(cond,dict) or set(cond)!={"entity_id","state"} or not all(
                isinstance(x,str) and x for x in cond.values()
            ):
                raise ValueError("invalid condition")
        if "test_mode" in profile and profile["test_mode"] not in ("off","stage"):
            raise ValueError("invalid test mode")
        result[name]=dict(profile)
    return result


def resolve_profile(message,profiles):
    """Profile defaults < explicit enqueue fields. No mutation of caller data."""
    name=message.get("profile")
    if not name:
        return dict(message)
    if not isinstance(name,str) or not IDENT.fullmatch(name):
        raise ValueError("invalid profile")
    effective=validate_profiles(profiles)
    if name not in effective:
        raise ValueError("unknown notification profile: "+name)
    return {**effective[name],**message}
