# Reliable Notify v3.8.2

## Deutsch
- **Fehler zurücksetzen:** In den Einstellungen gibt es jetzt den Bereich „Fehler zurücksetzen“. Der Knopf „Alle Fehler löschen“ entfernt nach einer Rückfrage alle unzustellbaren Nachrichten (Dead Letters), die Fehleranalyse und die Fehlerzähler; die Reparaturmeldung verschwindet. Erfolgreiche Zustellungen, das Archiv und Nachrichten, die noch erneut versucht werden, bleiben erhalten. Nur für Administratoren und nicht rückgängig zu machen.
- Dasselbe geht in Automationen und Skripten mit der Admin-Aktion `reliable_notify.reset_errors` (Antwort mit der Anzahl gelöschter Einträge).

Sinnvoll, nachdem die Ursache behoben ist: Die Statistik zeigt danach nur noch neue Fehler.

## English
- **Reset errors:** Settings now has a “Reset errors” section. After a confirmation, “Delete all errors” removes all undeliverable messages (dead letters), the failure analysis and the failure counters; the repair issue disappears. Successful deliveries, the archive and messages still waiting for a retry are kept. Administrators only; cannot be undone.
- The same is available to automations and scripts as the admin action `reliable_notify.reset_errors` (response with the deleted counts).

Useful once the cause is fixed: the statistics then only show new failures.

Update through Marketplace, restart Home Assistant and reload the browser. / Über Marketplace aktualisieren, Home Assistant neu starten und die Browseransicht neu laden.
