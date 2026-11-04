"""Validated, opt-in address book and fan-out configuration.

Routes never contain credentials; external mail transports use existing HA notify.
"""
from __future__ import annotations

import re

ALLOWED = {"notify.send_message", "telegram_bot.send_message", "telegram_bot.send_photo", "smtp.send_message"}
LEGACY_NOTIFY = re.compile(r"^notify\.[a-z][a-z0-9_]*$")


def valid_action(action):
    return action in ALLOWED or (bool(LEGACY_NOTIFY.fullmatch(action)) and action not in {"notify.send_message"})


def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError("routes file must contain a mapping")
    recipients = config.get("recipients", {})
    groups = config.get("groups", {})
    if not isinstance(recipients, dict) or not isinstance(groups, dict):
        raise ValueError("recipients and groups must be mappings")
    for name, rec in recipients.items():
        if not isinstance(name, str) or not isinstance(rec, dict):
            raise ValueError("recipient must be named mapping")
        action = rec.get("action", "notify.send_message")
        if not valid_action(action):
            raise ValueError(f"invalid action for {name}: {action}")
        if not isinstance(rec.get("data", {}), dict):
            raise ValueError(f"invalid data for {name}")
        if action in ("notify.send_message", "smtp.send_message") and not str(rec.get("target_entity", "")).startswith("notify."):
            raise ValueError(f"{name} requires a notify entity")
        if action.startswith("telegram_bot.") and not any(k in rec.get("data", {}) for k in ("chat_id", "entity_id", "config_entry_id")):
            raise ValueError(f"{name} requires Telegram chat_id, entity_id or config_entry_id")
    for group, members in groups.items():
        if not isinstance(group, str) or not isinstance(members, list) or any(not isinstance(x, str) for x in members):
            raise ValueError(f"invalid group: {group}")
    for name in groups:
        if name in recipients:
            raise ValueError(f"ambiguous route name: {name}")
        resolve(config, [name])  # validate groups and detect cycles
    return config


def resolve(config, names):
    recipients = config.get("recipients", {})
    groups = config.get("groups", {})
    output = []
    seen = set()

    def expand(name, stack):
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