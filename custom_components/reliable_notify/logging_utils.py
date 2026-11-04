"""Sanitized per-transport debug configuration (never log credentials)."""
from __future__ import annotations

LEVELS=("off","error","warning","info","debug")
TRANSPORTS=("telegram","smtp","companion","notify","webhook")


def validate_transport_logging(settings):
    if not isinstance(settings,dict) or set(settings)-set(TRANSPORTS):
        raise ValueError("logging must be a map of supported transports")
    for channel,level in settings.items():
        if level not in LEVELS:
            raise ValueError("invalid log level")
    return {channel:settings.get(channel,"warning") for channel in TRANSPORTS}


def transport_for(action):
    if action.startswith("telegram_bot."):return "telegram"
    if action.startswith("notify.mobile_app_"):return "companion"
    if action.startswith("rest_command."):return "webhook"
    if action.startswith("smtp."):return "smtp"
    return "notify"
