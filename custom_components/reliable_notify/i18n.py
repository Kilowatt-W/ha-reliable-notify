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
    "report_title": {"de": "Reliable Notify · Fehlerbericht", "en": "Reliable Notify · Failure report"},
    "report_intro": {"de": "Letzte 24 Stunden: {dead} fehlgeschlagen, {expired} abgelaufen, {retrying} in Wiederholung.",
                     "en": "Last 24 hours: {dead} failed, {expired} expired, {retrying} retrying."},
    "report_more": {"de": "… und {count} weitere. Details: Reliable Notify → Statistik → Fehleranalyse.",
                    "en": "… and {count} more. Details: Reliable Notify → Statistics → Failure analysis."},
    "report_hint": {"de": "Details: Reliable Notify → Statistik → Fehleranalyse.",
                    "en": "Details: Reliable Notify → Statistics → Failure analysis."},
    "mirror_resolved": {"de": "Behoben um {time} – bitte quittieren.", "en": "Resolved at {time} – please acknowledge."},
    "mirror_hint": {"de": "Wegklicken quittiert den Vorfall.", "en": "Dismissing acknowledges the incident."},
    "test_title": {"de": "Reliable Notify · Test", "en": "Reliable Notify · Test"},
    "test_message": {"de": "Testnachricht von Reliable Notify an {name}.",
                     "en": "Test notification from Reliable Notify to {name}."},
}


CATEGORIES = {
    "network": {"de": "Netzwerk", "en": "network"},
    "provider_unavailable": {"de": "Anbieter gestört", "en": "provider unavailable"},
    "rate_limit": {"de": "Drosselung", "en": "rate limited"},
    "authentication": {"de": "Zugang abgelehnt", "en": "access denied"},
    "invalid_payload": {"de": "ungültiger Aufruf", "en": "invalid call"},
    "invalid_recipient": {"de": "Empfänger ungültig", "en": "invalid recipient"},
    "tls_certificate": {"de": "TLS-Zertifikat", "en": "TLS certificate"},
    "unexpected_redirect": {"de": "Weiterleitung", "en": "redirect"},
    "unknown": {"de": "unbekannt", "en": "unknown"},
    "service_not_loaded": {"de": "HA-Aktion nicht geladen", "en": "HA action not loaded"},
    "target_unavailable": {"de": "Entität nicht verfügbar", "en": "entity unavailable"},
    "ttl_expired": {"de": "Gültigkeit abgelaufen", "en": "validity expired"},
}


def failure_report(lang, failures, labels=None, limit=5):
    """Plain-text daily summary of failure-analysis rows (no message texts)."""
    code = language(lang)
    totals = {"dead": 0, "expired": 0, "retrying": 0}
    for row in failures:
        totals[row["status"]] = totals.get(row["status"], 0) + row["count"]
    lines = [text(code, "report_intro", **totals)]
    for row in failures[:limit]:
        target = (labels or {}).get(row["target"]) or row["target"]
        category = CATEGORIES.get(row["category"], {}).get(code, row["category"])
        lines.append(f"• {category} – {target}: {row['count']}")
    rest = len(failures) - limit
    lines.append(text(code, "report_more", count=rest) if rest > 0 else text(code, "report_hint"))
    return "\n".join(lines)


def language(value) -> str:
    """Normalise an HA language code (``de-AT``, ``de_DE``, ``en``) to ``de`` or ``en``."""
    code = str(value or "en").lower().replace("_", "-").split("-")[0]
    return "de" if code == "de" else "en"


def text(lang, key: str, **values) -> str:
    return TEXTS[key][language(lang)].format(**values)


def ha_text(hass, key: str, **values) -> str:
    """Text in the HA system language (used where no user profile language exists)."""
    return text(getattr(getattr(hass, "config", None), "language", None), key, **values)
