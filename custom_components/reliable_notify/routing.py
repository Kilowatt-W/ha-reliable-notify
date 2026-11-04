"""Validated, opt-in address book and fan-out configuration.

Routes never contain credentials; external mail transports use existing HA notify.
"""
from __future__ import annotations

import re
from .native_transport import NATIVE_ACTIONS,validate_native_route
ALLOWED = {"notify.send_message", "telegram_bot.send_message", "telegram_bot.send_photo", "smtp.send_message"}
LEGACY_NOTIFY = re.compile(r"^notify\.[a-z][a-z0-9_]*$")
REST_COMMAND = re.compile(r"^rest_command\.[a-z][a-z0-9_]*$")


def valid_action(action):
    return (action in ALLOWED or action in NATIVE_ACTIONS or bool(REST_COMMAND.fullmatch(action))
            or (bool(LEGACY_NOTIFY.fullmatch(action)) and action != "notify.send_message"))


def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError("routes file must contain a mapping")
    recipients = config.get("recipients", {})
    groups = config.get("groups", {})
    persons = config.get("persons", {})
    if not isinstance(recipients, dict) or not isinstance(groups, dict) or not isinstance(persons, dict):
        raise ValueError("recipients and groups must be mappings")
    for name, rec in recipients.items():
        if not isinstance(name, str) or not isinstance(rec, dict):
            raise ValueError("recipient must be named mapping")
        action = rec.get("action", "notify.send_message")
        if not valid_action(action):
            raise ValueError(f"invalid action for {name}: {action}")
        if not isinstance(rec.get("data", {}), dict):
            raise ValueError(f"invalid data for {name}")
        if action in NATIVE_ACTIONS:
            validate_native_route(action,rec.get("data",{}))
        if action in ("notify.send_message", "smtp.send_message") and not str(rec.get("target_entity", "")).startswith("notify."):
            raise ValueError(f"{name} requires a notify entity")
        if action.startswith("telegram_bot.") and not any(k in rec.get("data", {}) for k in ("chat_id", "entity_id", "config_entry_id")):
            raise ValueError(f"{name} requires Telegram chat_id, entity_id or config_entry_id")
    for group, members in groups.items():
        if not isinstance(group, str) or not isinstance(members, list) or any(not isinstance(x, str) for x in members):
            raise ValueError(f"invalid group: {group}")
    for name, spec in persons.items():
        if not isinstance(name,str) or not isinstance(spec,dict) or not isinstance(spec.get("channels"),dict):
            raise ValueError("person must define channels")
        if spec.get("entity") and not str(spec["entity"]).startswith("person."):
            raise ValueError("person entity must start with person.")
        if not spec["channels"] or any(not isinstance(k,str) or v not in recipients for k,v in spec["channels"].items()):
            raise ValueError("person channels must refer to existing recipients")
        prefs=spec.get("preferred",{})
        if not isinstance(prefs,dict) or any(k not in ("info","warning","critical") or not isinstance(v,(str,list)) for k,v in prefs.items()):
            raise ValueError("invalid preferred channels")
        zone_rules=spec.get("preferred_by_zone",{})
        if not isinstance(zone_rules,dict):
            raise ValueError("invalid preferred_by_zone")
        for zone,zone_policy in zone_rules.items():
            if not isinstance(zone,str) or not isinstance(zone_policy,dict):
                raise ValueError("zone policy must be a mapping")
            if set(zone_policy)-{"info","warning","critical"}:
                raise ValueError("unsupported zone priority")
            prefs={**prefs,**zone_policy}
        for pref in prefs.values():
            selected=[pref] if isinstance(pref,str) else pref
            if not selected or any(v not in spec["channels"] for v in selected):
                raise ValueError("unknown preferred channel")
    for name in groups:
        if name in recipients or name in persons:
            raise ValueError(f"ambiguous route name: {name}")
        resolve(config, [name])  # validate groups and detect cycles
    for name in persons:
        if name in recipients or name in groups:
            raise ValueError("duplicate recipient/person name")
        for prio in ("info","warning","critical"):
            resolve(config,[name],priority=prio)
    return config


def resolve(config, names, priority="info", presence=None):
    recipients = config.get("recipients", {})
    groups = config.get("groups", {})
    persons = config.get("persons", {})
    output = []
    seen = set()

    def expand(name, stack):
        if name in persons:
            if name in stack:
                raise ValueError("cyclic person route")
            spec=persons[name]
            person_entity=spec.get("entity")
            state=(presence or {}).get(person_entity,"unknown")
            zone_policy=spec.get("preferred_by_zone",{}).get(state,{})
            preference=zone_policy.get(priority,spec.get("preferred",{}).get(priority))
            choices=([preference] if isinstance(preference,str) else preference) if preference else list(spec["channels"])
            for channel in choices:
                expand(spec["channels"][channel],[*stack,name])
            return
        if name in recipients:
            if name not in seen:
                seen.add(name)
                output.append((name, recipients[name]))
            return
        if name not in groups:
            raise ValueError(f"unknown recipient or group: {name}")
        if name in stack:
            raise ValueError("cyclic group: " + " -> ".join([*stack, name]))
        for child in groups[name]:
            expand(child, [*stack, name])

    for name in names:
        expand(name, [])
    if not output:
        raise ValueError("recipient resolution resulted in empty group")
    return output