# Reliable Notify v3.4.0

## Deutsch
- **Fehler sind jetzt nachvollziehbar:** Zu jedem Fehlschlag speichert Reliable einen bereinigten Fehlertext (Adressen, Token, E-Mail-Adressen und lange IDs sind maskiert) – sichtbar bei Dead Letters, im Archiv und im Verlauf.
- **Neue Fehleranalyse** unter *Statistik*: fehlgeschlagene, abgelaufene und gerade wiederholte Nachrichten, gruppiert nach Ursache und Ziel, mit Empfehlung. Auch im Diagnose-Export enthalten.
- **Nichts verschwindet mehr still:** Abgelaufene Nachrichten (ttl) erscheinen im Verlauf und in der Statistik.
- **Hinweis bei Problemen:** Solange unzustellbare Nachrichten warten, zeigt HA einen Reparaturhinweis; zusätzlich gibt es das Ereignis `reliable_notify_dead_letter` für eigene Automationen.
- **Länger durchhalten:** Wiederholungen enden jetzt nach einer Zeitspanne mit Fehlern (`max_hours`: info 6 h, warning 24 h, critical nie) statt nach 8 bzw. 20 Versuchen. Unveränderte alte Standardwerte werden automatisch umgestellt.
- **HA-Start zählt nicht:** Ist die Integration eines Transports (z. B. Telegram) noch nicht geladen, wartet Reliable, ohne Versuche zu verbrauchen.
- **Sinnlose Wiederholungen entfallen:** Lehnt HA einen Aufruf als ungültig ab, ist die Nachricht sofort endgültig fehlgeschlagen – mit lesbarem Grund.
- **Kein falsches „gesendet“:** Fehlt eine Notify-Entität oder ist sie nicht verfügbar, wird wiederholt statt als gesendet gemeldet.
- **Zusatzdaten passend je Transport:** Felder, die ein Transport nicht kennt, werden ihm nicht geschickt. Bei einem einzelnen Ziel meldet der Aufruf sofort, welche Felder nicht passen.
- **Ausweichziel:** Pro Ziel optional `fallback` – scheitert die Zustellung endgültig, geht die Nachricht einmalig dorthin (z. B. Telegram → App).
- Telegram-Ziele mit `data.entity_id` funktionieren wieder.

## English
- **Failures are traceable:** every failure keeps a sanitised error text (addresses, tokens, e-mail addresses and long IDs masked) – visible for dead letters, in the archive and in history.
- **New failure analysis** under *Statistics*: failed, expired and retrying notifications grouped by cause and target, with advice. Also part of the diagnostics export.
- **Nothing disappears silently:** expired notifications (ttl) appear in history and statistics.
- **Notice when something is wrong:** while undeliverable notifications are waiting, HA shows a repair issue; the event `reliable_notify_dead_letter` is available for your own automations.
- **Longer staying power:** retries now end after a span of failures (`max_hours`: info 6 h, warning 24 h, critical never) instead of after 8 or 20 attempts. Untouched old defaults are migrated automatically.
- **HA start-up does not count:** if a transport's integration (e.g. Telegram) is not loaded yet, Reliable waits without using up attempts.
- **No pointless retries:** if HA rejects a call as invalid, the notification fails immediately – with a readable reason.
- **No false "sent":** a missing or unavailable notify entity is retried instead of being reported as sent.
- **Extra data per transport:** fields a transport does not know are not sent to it. For a single target the call reports the unsupported fields immediately.
- **Fallback target:** optional `fallback` per target – if delivery finally fails, the notification is sent once to it (e.g. Telegram → app).
- Telegram targets with `data.entity_id` work again.

Update through Marketplace, restart Home Assistant and reload the browser. / Über Marketplace aktualisieren, Home Assistant neu starten und die Browseransicht neu laden.
