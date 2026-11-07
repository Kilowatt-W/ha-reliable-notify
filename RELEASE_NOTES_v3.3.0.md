# Reliable Notify v3.3.0

## Deutsch
- **Klarnamen für Ziele, Gruppen und Personen:** Unter *Ziele & Personen* gibt es das neue Feld **Anzeigename (Klarname)**, zum Beispiel „Telegram Wölfi – Büro“. Der **interne Name (ID)** wird beim Anlegen automatisch daraus vorgeschlagen (`telegram_woelfi_buero`) und bleibt danach fest.
- Klarnamen erscheinen in der Zielliste, bei der Auswahl von Gruppenmitgliedern, Personenkanälen, Profil- und Eskalationsempfängern, beim Zuweisen zurückgestellter Nachrichten, in Testnachrichten und als Name der Notify-Entität. Die Entitäts-ID bleibt `notify.reliable_<ID>`; bestehende Automationen funktionieren unverändert.
- Klarnamen lassen sich auch in `reliable_notify_routes.yaml` unter `labels:` setzen.
- **Durchgehend zweisprachig:** Aktionsknöpfe in Companion-App und Telegram („Bestätigen“, „15 Min. später“, „Eskalieren“) und die Telegram-Rückmeldung folgen jetzt der HA-Systemsprache. Auswahlwerte (Priorität, Strategie, Testmodus, Loglevel, Archivierung, Status …) erscheinen in HA-Formularen, Aktionen, Panel und Karte auf Deutsch oder Englisch. Fehlermeldungen des Backends werden im Panel übersetzt angezeigt.
- Gespeicherte Werte, Zielnamen, Nachrichten und YAML-Schlüssel bleiben unverändert.
- Die Python-Tests laufen jetzt auch unter Windows.

## English
- **Display names for targets, groups and people:** *Targets & people* has a new **Display name** field, for example "Telegram Wölfi – Office". The **internal name (ID)** is suggested from it when creating an entry (`telegram_woelfi_office`) and stays fixed afterwards.
- Display names appear in the target list, when choosing group members, person channels, profile and escalation recipients, when assigning staged messages, in test notifications and as the name of the notify entity. The entity ID stays `notify.reliable_<ID>`; existing automations keep working.
- Display names can also be set in `reliable_notify_routes.yaml` under `labels:`.
- **Fully bilingual:** Companion app and Telegram action buttons and the Telegram callback answer now follow the HA system language (previously always German). Select values (priority, strategy, test mode, log level, archive, status …) appear in German or English in HA forms, actions, panel and card. Backend error messages are translated in the panel.
- Stored values, target names, messages and YAML keys are unchanged.
- The Python test suite now also passes on Windows.

Update through Marketplace, restart Home Assistant and reload the browser. / Über Marketplace aktualisieren, Home Assistant neu starten und die Browseransicht neu laden.
