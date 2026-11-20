# Reliable Notify v3.5.0

## Deutsch
- **Zeitgesteuerte Nachrichten:** `send_at` (Datum/Uhrzeit) und `delay` (Sekunden) in `reliable_notify.enqueue`, bis zu 31 Tage im Voraus. Ruhezeiten gelten ab dem Sendezeitpunkt, `ttl` zählt ab dann. Abbrechen mit `reliable_notify.cancel` und dem `dedup_key`. Die Simulation zeigt den geplanten Zeitpunkt je Ziel.
- **Ruhezeiten je Ziel und Person:** Eigene Ruhezeiten im Panel über „Feld hinzufügen“. Personen-Ruhezeiten gelten auch, wenn die Person über eine Gruppe erreicht wird; die Einstellung des Ziels selbst hat Vorrang.
- **ntfy mit Buttons und Bildern:** `actions` (bis zu 3 Buttons), `click`, `attach`, `icon`, `tags`. Versand jetzt als JSON – Umlaute in Titel und Buttons sind kein Problem mehr. **Gotify:** Klick-Link und großes Bild. **Webhook:** Zusatzfelder unter `data`.
- **Gruppierung am Handy:** Companion-App-Nachrichten werden nach Nachrichtentyp gruppiert (abschaltbar unter Allgemein).
- **Täglicher Fehlerbericht:** optional an ein Ziel zu einer festen Uhrzeit – nur wenn es in den letzten 24 Stunden Fehler gab, ohne Nachrichtentexte.
- Neue Hilfe-Beispiele für zeitgesteuerte Nachrichten und ntfy.

## English
- **Scheduled notifications:** `send_at` (date/time) and `delay` (seconds) in `reliable_notify.enqueue`, up to 31 days ahead. Quiet hours apply from the send time, `ttl` counts from then. Cancel with `reliable_notify.cancel` and the `dedup_key`. The simulation shows the planned time per target.
- **Quiet hours per target and person:** own quiet hours in the panel via “Add field”. A person's quiet hours also apply when reached through a group; the target's own setting wins.
- **ntfy with buttons and images:** `actions` (up to 3 buttons), `click`, `attach`, `icon`, `tags`. Now published as JSON – accents in titles and buttons are no longer a problem. **Gotify:** click link and large image. **Webhook:** extra fields under `data`.
- **Grouping on the phone:** Companion app notifications are grouped by message type (can be switched off under General).
- **Daily failure report:** optionally to a target at a fixed time – only when there were failures in the last 24 hours, without message texts.
- New help examples for scheduled notifications and ntfy.

Update through Marketplace, restart Home Assistant and reload the browser. / Über Marketplace aktualisieren, Home Assistant neu starten und die Browseransicht neu laden.
