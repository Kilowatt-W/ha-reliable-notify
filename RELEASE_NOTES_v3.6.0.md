# Reliable Notify v3.6.0

## Deutsch
- **Alarmfenster:** Eine quittierpflichtige Meldung mit `incident` (`display_text`, `area`, `escalate_while_resolved`) bleibt sichtbar, bis sie jemand quittiert – auch wenn die Ursache schon behoben ist. Zustände: aktiv → behoben bzw. quittiert → erledigt.
- **Neue Dienste:** `reliable_notify.resolve` (Ursache weg, optional Erinnerungen beenden), `reliable_notify.snooze` (Minuten frei wählbar) und `reliable_notify.reopen`. Schlummern und Eskalieren verändern den Beginn („seit“) nicht mehr.
- **Ereignis `reliable_notify_incident`** mit Schlüssel bei jeder Änderung – egal ob über Telegram, Handy, Karte, Panel oder Dienst. So bleibt Home Assistant synchron.
- **Entitäten:** Sensor „Offene Vorfälle“ (mit Liste) und Binärsensor „Kritischer Vorfall offen“ für Badges und bedingte Karten.
- **Neue Karte `custom:reliable-notify-alarm-card`** für alle Bewohner, automatisch geladen: ein farbiges Band je Vorfall, „seit …“, „behoben um …“, Knöpfe Quittieren und Schlummern, Eskalieren für Admins, live aktualisiert, ohne offenen Vorfall unsichtbar. Deutsch/Englisch.
- Angemeldete Benutzer dürfen quittieren und schlummern (auf Admins beschränkbar); Eskalieren, als behoben markieren und wieder öffnen nur Admins.
- Offene Vorfälle bleiben unabhängig von der Priorität erhalten; bestehende Bestätigungen werden ohne Verlust übernommen.

```yaml
type: custom:reliable-notify-alarm-card
areas: [heizraum]
snooze_minutes: [15, 60]
```

## English
- **Alarm window:** an acknowledged notification with `incident` (`display_text`, `area`, `escalate_while_resolved`) stays visible until someone acknowledges it – even after the cause is gone. States: active → resolved or acknowledged → closed.
- **New services:** `reliable_notify.resolve` (cause gone, optionally stop reminders), `reliable_notify.snooze` (any number of minutes) and `reliable_notify.reopen`. Snoozing and escalating no longer change the opening time ("since").
- **Event `reliable_notify_incident`** with the key on every change – whether from Telegram, the phone, the card, the panel or a service. Home Assistant stays in sync.
- **Entities:** sensor “Open incidents” (with list) and binary sensor “Critical incident open” for badges and conditional cards.
- **New card `custom:reliable-notify-alarm-card`** for all residents, loaded automatically: one coloured band per incident, “since …”, “resolved at …”, acknowledge and snooze buttons, escalate for admins, live updates, invisible when nothing is open. German/English.
- Signed-in users may acknowledge and snooze (can be restricted to admins); escalating, resolving and reopening are admin-only.
- Open incidents are kept regardless of priority; existing acknowledgements are migrated without loss.

Update through Marketplace, restart Home Assistant and reload the browser. / Über Marketplace aktualisieren, Home Assistant neu starten und die Browseransicht neu laden.
