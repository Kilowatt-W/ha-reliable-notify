"""German/English texts the backend sends to people (buttons, callback answers).

The HA system language selects German for ``de`` and regional variants; any other
language falls back to English. Stored messages, aliases and IDs are never translated.
"""
from __future__ import annotations

TEXTS = {
    "ack": {"de": "Bestätigen", "en": "Acknowledge"},
    "snooze": {"de": "15 Min. später", "en": "Snooze 15 min"},
    "escalate": {"de": "Eskalieren", "en": "Escalate"},
    "action_applied": {"de": "Aktion übernommen", "en": "Action applied"},
    "action_rejected": {"de": "Bereits bearbeitet oder ungültig", "en": "Already handled or invalid"},
    "test_title": {"de": "Reliable Notify · Test", "en": "Reliable Notify · Test"},
    "test_message": {"de": "Testnachricht von Reliable Notify an {name}.",
                     "en": "Test notification from Reliable Notify to {name}."},
}


def language(value) -> str:
    """Normalise an HA language code (``de-AT``, ``de_DE``, ``en``) to ``de`` or ``en``."""
    code = str(value or "en").lower().replace("_", "-").split("-")[0]
    return "de" if code == "de" else "en"


def text(lang, key: str, **values) -> str:
    return TEXTS[key][language(lang)].format(**values)


def ha_text(hass, key: str, **values) -> str:
    """Text in the HA system language (used where no user profile language exists)."""
    return text(getattr(getattr(hass, "config", None), "language", None), key, **values)
