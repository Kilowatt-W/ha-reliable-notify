# Reliable Notify v3.8.0

## Deutsch
- **Glocke und Reparaturen spiegeln:** Mit `incident.mirror` oder der neuen Option „Offene Vorfälle standardmäßig spiegeln“ erscheint ein offener Vorfall zusätzlich in der Benachrichtigungsglocke – **Wegklicken quittiert ihn** – oder als Reparaturhinweis (critical = Fehler, warning = Warnung). Nach dem Quittieren verschwindet der Eintrag; nach einem Neustart wird er wiederhergestellt. Die Glocken-Automation und das Quittier-Skript aus dem Heizraum-Aufbau entfallen damit.
- **Sensor pro Bereich:** „Offene Vorfälle <Bereich>“ (`sensor.reliable_notify_open_incidents_<area>`) für jeden verwendeten Bereich, neue Bereiche kommen automatisch dazu.
- **Karteneditor:** Die Alarm-Karte lässt sich im Dashboard-Editor per Formular einstellen – Bereiche, Nachrichtentypen, Mindestpriorität, Schlummer-Knöpfe, quittierte Vorfälle, Rückfrage, kompakte Darstellung.

```yaml
incident:
  area: heizraum
  source_entity: binary_sensor.brennerstoerung
  resolve_after: 120
  mirror: persistent_notification
```

## English
- **Mirror to the bell and repairs:** with `incident.mirror` or the new option “Mirror open incidents by default” an open incident also appears in the notification bell – **dismissing it acknowledges it** – or as a repair issue (critical = error, warning = warning). The entry disappears after acknowledgement and is restored after a restart.
- **Sensor per area:** “Open incidents <area>” (`sensor.reliable_notify_open_incidents_<area>`) for every area in use; new areas are added automatically.
- **Card editor:** the alarm card can be configured with a form in the dashboard editor – areas, message types, minimum priority, snooze buttons, acknowledged incidents, confirmation, compact layout.

Update through Marketplace, restart Home Assistant and reload the browser. / Über Marketplace aktualisieren, Home Assistant neu starten und die Browseransicht neu laden.
