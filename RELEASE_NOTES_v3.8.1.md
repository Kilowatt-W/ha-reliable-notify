# Reliable Notify v3.8.1

## Deutsch
Fehlerbehebungen aus der Prüfung einer echten Installation:
- **Telegram-Notify-Entitäten:** Ziele, die eine Telegram-Notify-Entität sind (auch das Standardziel), sendet Reliable jetzt über `telegram_bot.send_message` mit `entity_id`. Bisher lehnte `notify.send_message` Telegram-Felder wie `parse_mode: HTML` ab – HTML-formatierte Statusmeldungen (z. B. PV- und Klima-Meldungen) landeten deshalb nach mehreren Versuchen als Dead Letter. Jetzt funktionieren Formatierung, Tastaturen, Empfangsbestätigungen und Quittier-Knöpfe auch für diese Ziele. Eskalationen nutzen denselben Weg.
- **Schnellerer Neustart:** Die Hintergrundschleifen von Reliable werden beim Herunterfahren von Home Assistant beendet; die Warnungen „still running after final writes shutdown stage“ entfallen.

Hinweis: Bereits vorhandene Dead Letters bleiben unverändert. Sie können unter Nachrichten → Dead letters erneut gesendet oder gelöscht werden.

## English
Fixes from checking a live installation:
- **Telegram notify entities:** targets that are Telegram notify entities (including the default target) are now sent through `telegram_bot.send_message` with `entity_id`. `notify.send_message` rejected Telegram fields such as `parse_mode: HTML`, so HTML-formatted status messages ended up as dead letters after several attempts. Formatting, keyboards, message receipts and acknowledgement buttons now work for these targets; escalations use the same path.
- **Faster restart:** Reliable Notify's background loops are cancelled when Home Assistant shuts down; the warnings “still running after final writes shutdown stage” are gone.

Note: existing dead letters are not changed. They can be resent or deleted under Messages → Dead letters.

Update through Marketplace, restart Home Assistant and reload the browser. / Über Marketplace aktualisieren, Home Assistant neu starten und die Browseransicht neu laden.
