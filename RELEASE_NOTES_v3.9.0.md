# Reliable Notify v3.9.0

## Deutsch
- **„Bestehende Automationen prüfen“ macht echte Vorschläge:** Auf einer echten Installation bekommen jetzt 183 von 206 Benachrichtigungen einen Vorschlag (vorher 31). Das leere `metadata: {}` aus dem HA-Editor blockiert nicht mehr, Companion-Daten (Tag, Kanal, sticky …) und Telegram-Felder werden übernommen, `target: device_id` wird auf die Notify-Entität des Geräts aufgelöst. Für den Rest gibt es klare Gründe, z. B. „Antwort wird weiterverwendet“ oder „Dienst existiert nicht mehr“.
- **Übersichtlichere Liste:** Gründe zusammengefasst, Vorschläge zuerst, Ersatz als kopierbares YAML, „Automation im HA-Editor öffnen“ und – wenn das Ziel fehlt – stattdessen „Ziel dafür anlegen“ mit vorausgefülltem Formular.
- **Fehlerbehebung:** Die klassischen Dienste `notify.reliable_<ziel>` haben Companion-Felder in `data` (z. B. `tag`, `channel`, `sticky`) verworfen. Sie kommen jetzt in der App an und ergänzen die Standarddaten des Ziels.
- **Kompaktere Ziele-Liste:** Jedes Ziel steht in einer Zeile – Symbol, Name, daneben die Notify-Entität bzw. HA-Aktion (bei Gruppen der Inhalt, bei Personen die Kanäle) und „Test senden“ am rechten Rand. Lange Angaben werden gekürzt und erscheinen vollständig beim Darüberfahren; auf schmalen Bildschirmen rutscht die Angabe unter den Namen.
- **Einheitliche Symbole:** Jeder Bereich zeigt in seiner Überschrift dasselbe Symbol und dieselbe Farbe wie sein Knopf in der Navigation – z. B. „Ziele“ das Personen-Symbol, die Nachrichten-Karte im Panel das Nachrichten-Symbol.

## English
- **“Check existing automations” makes real proposals:** on a real installation 183 of 206 notify actions now get a proposal (before: 31). The empty `metadata: {}` from HA's editor no longer blocks, Companion data (tag, channel, sticky …) and Telegram fields are carried over, `target: device_id` is resolved to the device's notify entity. The rest gets clear reasons, e.g. “response used later” or “service no longer exists”.
- **Clearer list:** reasons summarised, proposals first, replacement as copyable YAML, “Open the automation in the HA editor” and – when the target is missing – “Create a target for it” with a prefilled form instead.
- **Fix:** the classic `notify.reliable_<route>` services dropped Companion fields in `data` (e.g. `tag`, `channel`, `sticky`). They now reach the app and are merged with the target's default data.
- **More compact target list:** every target takes one row – icon, name, next to it the notify entity or HA action (group members, person channels) and “Send test” at the right edge. Long details are shortened and shown in full on hover; on narrow screens the detail moves below the name.
- **Consistent icons:** every section heading uses the same icon and colour as its navigation button – e.g. “Targets” the people icon, the message card in the panel the messages icon.

Update through Marketplace, restart Home Assistant and reload the browser. / Über Marketplace aktualisieren, Home Assistant neu starten und die Browseransicht neu laden.
