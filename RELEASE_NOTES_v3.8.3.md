# Reliable Notify v3.8.3

## Deutsch
Fehlerbehebungen aus der Umstellung der Heizraum-Störmeldungen auf das Alarmfenster:
- **Telegram-Quittierknöpfe:** Nachrichten mit Quittierung („Bestätigen“, „15 Min. später“, „Eskalieren“) scheiterten an Telegram-Zielen mit `Button_data_invalid` und wurden endlos wiederholt. Die Knöpfe werden jetzt so übergeben, dass Telegram nur das signierte Kürzel erhält. Schon wartende Nachrichten werden beim nächsten Versuch automatisch repariert und zugestellt.
- **„Alle Benachrichtigungen entfernen“ quittiert nichts mehr:** `persistent_notification.dismiss_all`, z. B. in einer Automation nach dem HA-Start, hat bisher alle offenen Vorfälle in der Glocke quittiert. Jetzt erscheinen sie wieder. Einzeln weggeklickt gilt ein Eintrag weiterhin als quittiert; das steht jetzt auch im Log.

## English
Fixes from moving the boiler-room alarms to the alarm window:
- **Telegram acknowledgement buttons:** messages with acknowledgement (“Acknowledge”, “Remind in 15 min”, “Escalate”) failed on Telegram targets with `Button_data_invalid` and were retried forever. The buttons are now passed so that Telegram only receives the signed token. Messages already waiting are repaired automatically on the next attempt and delivered.
- **“Dismiss all” no longer acknowledges:** `persistent_notification.dismiss_all`, for example in an automation after HA start, used to acknowledge every open incident in the bell. They are now shown again. Dismissing a single entry still acknowledges it; this is now logged.

Update through Marketplace, restart Home Assistant and reload the browser. / Über Marketplace aktualisieren, Home Assistant neu starten und die Browseransicht neu laden.
