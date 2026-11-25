# Reliable Notify v3.8.4

## Deutsch
Kompaktere Alarm-Karte:
- **Kompakte Darstellung (eine Zeile pro Alarm):** Der vorhandene Haken `compact` zeigt jetzt Farbbalken, Symbol, Titel, „seit …“ und die Knöpfe in einer Zeile; am Handy rutschen die Knöpfe in eine zweite Zeile. Die Schlummer-Knöpfe heißen kurz „15 min“ (Bildschirmleser hören weiter „Schlummern 15 min“). Die Beschreibung erscheint als Tooltip und klappt beim Tippen auf den Titel auf; gibt es eine Ursachen-Entität, öffnet der Titel wie bisher deren Detail-Fenster.
- **Zusammenfassen ab N Alarmen:** Neue Option `collapse_from` (2–50, im Karten-Editor „Ab so vielen Alarmen zu einer Zeile zusammenfassen“). Ab dieser Anzahl werden Warnungen und Infos zu einer Zeile „2 weitere Alarme · 2 × Warnung · Anzeigen“ zusammengefasst. **Kritische, nicht quittierte Alarme bleiben immer als eigene Zeile sichtbar.**

```yaml
type: custom:reliable-notify-alarm-card
compact: true
collapse_from: 3
snooze_minutes: [15, 60]
```

## English
A more compact alarm card:
- **Compact layout (one row per alarm):** the existing `compact` option now shows colour bar, icon, title, “since …” and the buttons in one row; on phones the buttons wrap to a second row. Snooze buttons read “15 min” (screen readers still hear “Snooze 15 min”). The description is shown as a tooltip and opens on tap on the title; with a cause entity the title opens its details as before.
- **Combine from N alarms:** new option `collapse_from` (2–50, card editor “Combine into one row from this many alarms”). From that many incidents, warnings and infos are combined into one row “2 more alarms · 2 × Warning · Show”. **Critical incidents that are not acknowledged always stay visible as their own row.**

Update through Marketplace, restart Home Assistant and reload the browser. / Über Marketplace aktualisieren, Home Assistant neu starten und die Browseransicht neu laden.
