"""Read-only proposal engine for Home Assistant notify automation migration.

No automation files are ever modified. Proposals are intentionally conservative:
only unambiguous routes and static destination selectors are considered safe.
"""
from __future__ import annotations

from copy import deepcopy
import re

import yaml

TEMPLATE = re.compile(r"\{[{%]|[%}]\}")

# Stable reason codes (translated in the panel); English text kept for JSON exports.
REASONS = {
    "templated": "Templated service/data action",
    "non_object_data": "Non-object data",
    "complex_target": "Non-static or complex target",
    "advanced_fields": "Advanced action fields",
    "entity_in_data": "notify entity in data instead of target",
    "telegram_ambiguous": "Telegram destination is ambiguous",
    "telegram_target": "Unexpected separate Telegram target",
    "legacy_target": "Legacy notify action has extra target",
    "no_static_destination": "No unique static notify destination",
    "dynamic_destination": "Dynamic or multi-recipient destination",
    "no_route": "No configured matching route",
    "multiple_routes": "Multiple routes match destination",
    "transport_data": "Transport-specific data must be reviewed",
    "missing_message": "Missing message",
    "yaml_tags": "Uses YAML tags such as !secret or !include; review manually",
    "unambiguous": "Unambiguous static destination",
}


class Tagged:
    """Placeholder for HA YAML tags (!secret, !include, !input, ...).

    The analyzer never resolves them: secrets must not reach the UI and
    includes are scanned as their own files where supported.
    """
    __slots__ = ("tag", "value")

    def __init__(self, tag, value):
        self.tag, self.value = tag, value

    def __repr__(self):
        return f"{self.tag} {self.value!r}" if self.value is not None else self.tag


class AutomationLoader(yaml.SafeLoader):
    """Safe loader returning plain Python values (no HA node classes)."""


def _construct_tagged(loader, suffix, node):
    value = loader.construct_scalar(node) if isinstance(node, yaml.ScalarNode) else None
    return Tagged("!" + suffix, value)


AutomationLoader.add_multi_constructor("!", _construct_tagged)


def load_automation_yaml(path):
    """Parse an automation/script/package file for read-only analysis."""
    with open(path, encoding="utf-8") as file:
        return yaml.load(file, Loader=AutomationLoader)  # noqa: S506 - SafeLoader subclass


def _plain(value):
    """True for YAML values that can be copied into a suggestion verbatim."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return True
    if isinstance(value, list):
        return all(_plain(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _plain(item) for key, item in value.items())
    return False


def _manual(code, action, **extra):
    return {"status": "manual", "reason_code": code, "reason": REASONS[code], "source": action, **extra}


def route_targets(routes):
    """Canonicalize configured destinations for static source lookup."""
    index={}
    for name,spec in routes.get("recipients",{}).items():
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}",name):
            continue  # This alias is not exportable as a notify service.
        action=spec.get("action","notify.send_message")
        data=spec.get("data",{})
        key=None
        if action=="notify.send_message":
            target=spec.get("target_entity")
            if target:
                key=(action,str(target))
        elif action.startswith("telegram_bot."):
            selector=next((k for k in ("chat_id","entity_id","config_entry_id")
                           if k in data),None)
            if selector and not isinstance(data[selector],(dict,list)):
                key=(action,str(data[selector]))
        elif action.startswith("notify.") or action.startswith("rest_command."):
            key=(action,"")
        if key:
            index.setdefault(key,[]).append(name)
    return index


def inspect_action(node,index):
    """Return safe migration metadata or reason it requires manual review."""
    action=node.get("action",node.get("service"))
    if not isinstance(action,str) or TEMPLATE.search(action):
        return None
    if not (action.startswith("notify.") or action.startswith("telegram_bot.")
            or action.startswith("smtp.")):
        return None
    if action.startswith("notify.reliable_"):
        return None
    if "service_template" in node or "data_template" in node:
        return _manual("templated",action)
    body=node.get("data",{})
    if not isinstance(body,dict):
        return _manual("yaml_tags" if isinstance(body,Tagged) else "non_object_data",action)
    target=node.get("target",{})
    if target is None:
        target={}
    if not isinstance(target,dict) or set(target)-{"entity_id"}:
        return _manual("complex_target",action)
    keys=set(node)-{"action","service","data","target","alias","continue_on_error","enabled"}
    if keys:
        return _manual("advanced_fields",action)
    destination=""
    if action=="notify.send_message":
        if "entity_id" in body:
            return _manual("entity_in_data",action)
        destination=target.get("entity_id","")
        if isinstance(destination,list) and len(destination)==1:
            destination=destination[0]
    elif action.startswith("telegram_bot."):
        found=[key for key in ("chat_id","entity_id","config_entry_id") if key in body]
        if len(found)!=1:
            return _manual("telegram_ambiguous",action)
        destination=body[found[0]]
        if any(key in target for key in ("entity_id",)):
            return _manual("telegram_target",action)
    elif action.startswith("notify.") and action!="notify.notify":
        if target:
            return _manual("legacy_target",action)
    else:
        return _manual("no_static_destination",action)
    if isinstance(destination,Tagged):
        return _manual("yaml_tags",action)
    if not isinstance(destination,(str,int)) or TEMPLATE.search(str(destination)):
        return _manual("dynamic_destination",action)
    matches=index.get((action,str(destination)),[])
    if len(matches)!=1:
        return _manual("no_route" if not matches else "multiple_routes",action)
    route=matches[0]
    extra=set(body)-{"title","message"}
    if action.startswith("telegram_bot."):
        extra-={"chat_id","entity_id","config_entry_id"}
    if extra:
        return _manual("transport_data",action,suggested_route=route)
    if "message" not in body:
        return _manual("missing_message",action)
    copied={key:node[key] for key in ("alias","continue_on_error","enabled") if key in node}
    if not _plain(body.get("message")) or not _plain(body.get("title")) or not _plain(copied):
        # Never copy unresolved !secret/!include values into a suggestion.
        return _manual("yaml_tags",action,suggested_route=route)
    replacement={
        "action":"notify.reliable_"+route,
        "data":{"message":deepcopy(body["message"])}
    }
    if "title" in body:
        replacement["data"]["title"]=deepcopy(body["title"])
    replacement.update(deepcopy(copied))
    return {"status":"proposed","source":action,"route":route,"replacement":replacement,
            "reason_code":"unambiguous","reason":REASONS["unambiguous"]}


def analyze(root,routes,limit=300):
    """Inspect nested sequences/choose/repeat/parallel without mutating YAML."""
    if not isinstance(root,(dict,list)) or not 1<=limit<=2000:
        raise ValueError("invalid automation document or suggestion limit")
    index=route_targets(routes)
    results=[]
    visited=set()
    def walk(obj,path,automation="",depth=0):
        if len(results)>=limit or depth>32:
            return
        if isinstance(obj,(dict,list)):
            identity=id(obj)
            if identity in visited:
                return
            visited.add(identity)
        if isinstance(obj,list):
            for idx,item in enumerate(obj):
                walk(item,f"{path}[{idx}]",automation,depth+1)
        elif isinstance(obj,dict):
            label=str(obj.get("alias") or obj.get("id") or automation)
            inspection=inspect_action(obj,index)
            if inspection:
                results.append({"path":path,"automation":label,**inspection})
            for key,value in obj.items():
                if isinstance(value,(dict,list)):
                    walk(value,f"{path}.{key}",label,depth+1)
    walk(root,"root")
    return results
