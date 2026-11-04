"""Build correct Home Assistant service parameters for each transport."""
from __future__ import annotations

import json
from .routing import valid_action


def create_payload(item):
    action = item.get("action") or "notify.send_message"
    if not valid_action(action):
        raise ValueError(f"unsupported action: {action}")
    extra = json.loads(item.get("payload_json") or "{}")
    if not isinstance(extra, dict):
        raise ValueError("saved payload is not an object")
    message = item["message"]
    title = item.get("title")
    if action == "telegram_bot.send_photo":
        if not any(k in extra for k in ("file", "url")):
            raise ValueError("send_photo requires file or url")
        payload = dict(extra)
        if message or title:
            payload.setdefault("caption", "\n".join(x for x in (title, message) if x))
    elif action == "telegram_bot.send_message":
        payload = {**extra, "message": "\n".join(x for x in (title, message) if x)}
    else:
        payload = {**extra, "message": message}
        if title is not None:
            payload["title"] = title
    return action.split(".", 1), payload