"""Validated, opt-in address book and fan-out configuration.

Routes never contain credentials; external mail transports use existing HA notify.
"""
from __future__ import annotations

import re
NATIVE_ACTIONS = frozenset(("reliable_notify.ntfy","reliable_notify.gotify","reliable_notify.webhook"))
ALLOWED = {"notify.send_message", "telegram_bot.send_message", "telegram_bot.send_photo", "smtp.send_message"}
LEGACY_NOTIFY = re.compile(r"^notify\.[a-z][a-z0-9_]*$")
REST_COMMAND = re.compile(r"^rest_command\.[a-z][a-z0-9_]*$")
ROUTE_KINDS = ("recipients", "groups", "persons")
MAX_LABEL = 100


def valid_label(value):
    """Display names are free text, but bounded and without control characters."""
    return (isinstance(value, str) and 0 < len(value.strip()) <= MAX_LABEL
            and not any(ord(char) < 32 or ord(char) == 127 for char in value))


# Extra call data (``reliable_notify.enqueue`` -> ``data``) each transport can accept.
# Unsupported keys would make HA reject the call, i.e. a guaranteed dead letter.
_EXTRA_ALLOW = {
    "notify.send_message": frozenset(),   # entity action: message/title only
    # Same sets as native_transport.NATIVE_EXTRAS (kept here so routing has no imports).
    "reliable_notify.ntfy": frozenset(("click", "attach", "icon", "tags", "actions", "filename")),
    "reliable_notify.gotify": frozenset(("click", "image")),
}
_EXTRA_DENY = {
    "telegram_bot.send_message": frozenset(("file", "url", "caption", "data")),
    "telegram_bot.send_photo": frozenset(("data",)),
}
_LEGACY_NOTIFY_KEYS = frozenset(("data", "target"))


def filter_extras(action, extra):
    """Split call data into (kept, dropped key names) for one transport."""
    extra = dict(extra or {})
    if action in _EXTRA_ALLOW:
        allowed = _EXTRA_ALLOW[action]
        kept = {k: v for k, v in extra.items() if k in allowed}
    elif action in _EXTRA_DENY:
        kept = {k: v for k, v in extra.items() if k not in _EXTRA_DENY[action]}
    elif action.startswith("notify."):
        # Classic notify services (Companion app, e-mail, ...): message, title, target, data.
        kept = {k: v for k, v in extra.items() if k in _LEGACY_NOTIFY_KEYS}
    else:
        # smtp, rest_command and native transports define their own fields.
        kept = extra
    return kept, sorted(set(extra) - set(kept))


def is_classic_notify(action):
    """Classic notify service (Companion app, e-mail, YAML groups): message/title/target/data."""
    return (isinstance(action, str) and action.startswith("notify.")
            and action not in _EXTRA_ALLOW and action not in _EXTRA_DENY)


def transport_extra(action, extra, notify_data=None):
    """Extra data for one transport (3.9.0).

    ``notify_data`` is the ``data`` of a classic ``notify.reliable_<route>`` call.
    For classic notify transports it means the service's own ``data`` (Companion
    fields such as tag, channel, actions); for Telegram and others its keys stay
    top-level, as before. Explicit ``extra`` keys win.
    """
    extra = dict(extra or {})
    if not notify_data:
        return extra
    if is_classic_notify(action):
        inner = extra.get("data") if isinstance(extra.get("data"), dict) else {}
        return {**extra, "data": {**notify_data, **inner}}
    # Never let call data replace the routed chat (entity_id) of other transports.
    return {**{k: v for k, v in notify_data.items() if k != "entity_id"}, **extra}


def merge_transport_payload(action, defaults, kept):
    """Route defaults plus per-message data; the classic ``data`` field is merged one level deep."""
    payload = {**(defaults or {}), **kept}
    base = (defaults or {}).get("data")
    if is_classic_notify(action) and isinstance(base, dict) and isinstance(kept.get("data"), dict):
        payload["data"] = {**base, **kept["data"]}
    return payload


def telegram_entity_route(rec):
    """Send to a Telegram notify entity through telegram_bot.send_message (3.8.1).

    notify.send_message only accepts message/title, so parse_mode, keyboards,
    message tags and acknowledgement buttons would be rejected or lost.
    telegram_bot.send_message addresses the same chat via ``entity_id``.
    """
    target = rec.get("target_entity")
    data = dict(rec.get("data") or {})
    data["entity_id"] = target
    return {**rec, "action": "telegram_bot.send_message", "data": data, "target_entity": target}


def companion_group(payload, group):
    """Group Companion app notifications per message type (Android group, iOS thread-id).

    Values the caller already set are kept.
    """
    phone = payload.get("data")
    if phone is None:
        phone = {}
    if not isinstance(phone, dict):
        return payload
    phone = dict(phone)
    phone.setdefault("group", str(group))
    push = phone.get("push")
    if push is None or isinstance(push, dict):
        push = dict(push or {})
        push.setdefault("thread-id", str(group))
        phone["push"] = push
    return {**payload, "data": phone}


def route_quiet_hours(config, names, priority="info", presence=None):
    """Quiet-hour policy per resolved recipient: its own, else that of the person
    it was reached through. Recipients without one use the global policy.
    """
    persons = config.get("persons", {})
    recipients = config.get("recipients", {})
    groups = config.get("groups", {})
    result = {}
    pending, seen = list(names), set()
    while pending:  # persons may be addressed directly or inside (nested) groups
        name = pending.pop(0)
        if name in seen:
            continue
        seen.add(name)
        if name in groups:
            pending.extend(groups[name])
            continue
        spec = persons.get(name)
        if spec and isinstance(spec.get("quiet_hours"), dict):
            for recipient, _ in resolve(config, [name], priority=priority, presence=presence):
                result.setdefault(recipient, spec["quiet_hours"])
    for name, rec in recipients.items():
        if isinstance(rec.get("quiet_hours"), dict):
            result[name] = rec["quiet_hours"]  # the recipient's own setting wins
    return result


OWN_ENTITY_PREFIX = "notify.reliable_"


def is_own_entity(entity_id, own=()):
    """True for notify entities created by Reliable Notify itself.

    Sending to them would enqueue the message again (endless loop). ``own``
    holds registry entity IDs, so renamed entities are recognised as well.
    """
    return isinstance(entity_id, str) and (entity_id.startswith(OWN_ENTITY_PREFIX) or entity_id in own)


def merge_routes(file_routes, ui_routes):
    """UI-defined routes and display names override YAML; labels only for existing routes."""
    merged = {kind: {**(file_routes.get(kind) or {}), **(ui_routes.get(kind) or {})}
              for kind in ROUTE_KINDS}
    names = set().union(*(merged[kind] for kind in ROUTE_KINDS))
    labels = {**(file_routes.get("labels") or {}), **(ui_routes.get("labels") or {})}
    merged["labels"] = {name: label for name, label in labels.items() if name in names}
    return merged


def display_name(routes, name):
    """Human-readable name of a route; the internal alias stays the routing key."""
    label = (routes.get("labels") or {}).get(name)
    return label.strip() if valid_label(label) else name


def valid_action(action):
    if action.startswith('notify.reliable_'):
        return False
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
    labels = config.get("labels", {})
    if not isinstance(labels, dict) or any(
            not isinstance(name, str) or not valid_label(label) for name, label in labels.items()):
        raise ValueError(f"labels must map route names to display names (1-{MAX_LABEL} characters, no control characters)")
    for name, rec in recipients.items():
        if not isinstance(name, str) or not isinstance(rec, dict):
            raise ValueError("recipient must be named mapping")
        action = rec.get("action", "notify.send_message")
        if not valid_action(action):
            raise ValueError(f"invalid action for {name}: {action}")
        if not isinstance(rec.get("data", {}), dict):
            raise ValueError(f"invalid data for {name}")
        if action in NATIVE_ACTIONS:
            from .native_transport import validate_native_route
            validate_native_route(action,rec.get("data",{}))
        if action in ("notify.send_message", "smtp.send_message") and not str(rec.get("target_entity", "")).startswith("notify."):
            raise ValueError(f"{name} requires a notify entity")
        if action.startswith("telegram_bot.") and not any(k in rec.get("data", {}) for k in ("chat_id", "entity_id", "config_entry_id")):
            raise ValueError(f"{name} requires Telegram chat_id, entity_id or config_entry_id")
    for name, rec in recipients.items():
        fallback = rec.get("fallback")
        if fallback in (None, ""):
            continue
        if not isinstance(fallback, str) or fallback == name or not (
                fallback in recipients or fallback in groups or fallback in persons):
            raise ValueError(f"{name}: fallback must name another existing recipient, group or person")
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