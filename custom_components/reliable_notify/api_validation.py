"""Strict, side-effect-free validation for the optional external API."""
from __future__ import annotations
import re

IDENT=re.compile(r"^[a-z][a-z0-9_]{0,63}$")
FIELDS=frozenset(("message","title","recipients","priority","message_type",
                  "dedup_key","profile","archive","archive_days","ttl"))


def validate_api_message(value,routes,allowed_routes):
    if not isinstance(value,dict) or set(value)-FIELDS:
        raise ValueError("unsupported API fields")
    if not isinstance(value.get("message"),str) or not 1<=len(value["message"])<=8192:
        raise ValueError("message required, max 8192 characters")
    if "title" in value and (not isinstance(value["title"],str) or len(value["title"])>256):
        raise ValueError("invalid title")
    names=value.get("recipients")
    if isinstance(names,str):names=[names]
    if not isinstance(names,list) or not 1<=len(names)<=20 or any(
        not isinstance(x,str) for x in names
    ):
        raise ValueError("explicit recipient aliases required")
    configured=set(routes.get("recipients",{}))|set(routes.get("persons",{}))|set(routes.get("groups",{}))
    if any(name not in configured for name in names):
        raise ValueError("unconfigured recipient")
    if any(name not in allowed_routes for name in names):
        raise ValueError("recipient not allowed through external API")
    if value.get("priority","info") not in ("info","warning"):
        raise ValueError("external API restricted to info and warning")
    if value.get("archive","keep") not in ("keep","delete_after_send"):
        raise ValueError("invalid archive policy")
    for key in ("message_type","profile"):
        if key in value and (not isinstance(value[key],str) or not IDENT.fullmatch(value[key])):
            raise ValueError("invalid "+key)
    if "dedup_key" in value and (not isinstance(value["dedup_key"],str)
        or not 1<=len(value["dedup_key"])<=128):
        raise ValueError("invalid dedup key")
    if "archive_days" in value and (type(value["archive_days"]) is not int or not 0<=value["archive_days"]<=365):
        raise ValueError("invalid archive days")
    if "ttl" in value and (type(value["ttl"]) is not int or not 0<=value["ttl"]<=86400):
        raise ValueError("invalid TTL")
    return {**value,"recipients":names}
