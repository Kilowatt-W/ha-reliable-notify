# Reliable Notify v3.7.0

## Deutsch
- **Ursache selbst beobachten:** Mit `incident.source_entity` und `problem_state` (Standard `on`) verfolgt Reliable Notify die Entität selbst. Ist die Störung `resolve_after` Sekunden weg, wird der Vorfall „behoben“; tritt sie vor dem Quittieren erneut auf, ist er wieder aktiv. Die „Aus“-Hälfte der Automationen entfällt. `unavailable`/`unknown` lösen nie etwas aus. Wartezeiten überstehen einen Neustart; nach dem Start werden alle beobachteten Entitäten neu abonniert und bewertet.
- **Automatisch erledigen:** `incident.auto_close_after` schließt einen behobenen, nicht quittierten Vorfall nach der angegebenen Zeit (nicht bei `critical`).
- **Verlauf je Vorfall:** gemeldet, quittiert, geschlummert, eskaliert, behoben, wieder aktiv, wieder geöffnet, automatisch erledigt – 90 Tage, im Panel unter *Eskalationen → Verlauf*.
- **Alarm-Karte:** zeigt die Ursache („Ursache: …“), ein Tippen öffnet die Entität.
- **Fehlerbehebung:** Telegram-Knöpfe, Companion-App-Aktionen und Telegram-Empfangsbestätigungen werden wieder zuverlässig verarbeitet. Home Assistant hat diese Handler in einem Hintergrund-Thread ausgeführt, in dem sie keine Aufgaben starten durften – Tastendrücke konnten verloren gehen. Dasselbe galt für die Live-Aktualisierung der Alarm-Karte.

```yaml
incident:
  display_text: "An der Ecomatic prüfen und entstören."
  area: heizraum
  source_entity: binary_sensor.brennerstoerung
  problem_state: "on"
  resolve_after: 120
```

## English
- **Watch the cause:** with `incident.source_entity` and `problem_state` (default `on`) Reliable Notify follows the entity itself. Once the fault has been gone for `resolve_after` seconds the incident is resolved; if it returns before anyone acknowledged, it is active again. The “off” half of automations is no longer needed. `unavailable`/`unknown` never trigger anything. Waiting periods survive a restart; after start all watched entities are subscribed and evaluated again.
- **Close automatically:** `incident.auto_close_after` closes a resolved, unacknowledged incident after the given time (not for `critical`).
- **History per incident:** reported, acknowledged, snoozed, escalated, resolved, active again, reopened, closed automatically – 90 days, shown in the panel under *Escalations → History*.
- **Alarm card:** shows the cause (“Cause: …”); tapping opens the entity.
- **Fix:** Telegram buttons, Companion app actions and Telegram receipts are processed reliably again. Home Assistant ran these handlers in a worker thread where they were not allowed to start tasks – button presses could be lost. The alarm card's live updates had the same problem.

Update through Marketplace, restart Home Assistant and reload the browser. / Über Marketplace aktualisieren, Home Assistant neu starten und die Browseransicht neu laden.
