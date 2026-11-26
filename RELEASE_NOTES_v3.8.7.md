# Reliable Notify v3.8.7

## Deutsch
Eine gemeinsame Ziele-Liste:
- **Alles, wohin gesendet werden kann, steht in einer Liste „Ziele“** – Einzelziele, Gruppen und Personen, sortiert nach Anzeigename. Jeder Eintrag zeigt seine Art („Einzelziel“, „Gruppe“, „Person“), wohin er zeigt (Notify-Entität bzw. HA-Aktion, Gruppeninhalt, Kanäle der Person) sowie „Test senden“ und Bearbeiten.
- **Filter** „Alle / Einzelziele / Gruppen / Personen“ mit Anzahl.
- **„Neues Ziel anlegen“** fragt im selben Formular nach der Art; nach dem Speichern bleibt sie fest.
- Nur die Ansicht ändert sich: gespeicherte Konfiguration, YAML-Schlüssel, interne Namen und Entitäten `notify.reliable_<ID>` bleiben gleich – Automationen müssen nicht angepasst werden.

## English
One shared target list:
- **Everything a message can be sent to is in one “Targets” list** – single targets, groups and people, sorted by display name. Each entry shows its type (“Single target”, “Group”, “Person”), what it points to (notify entity or HA action, group members, person channels), plus “Send test” and edit.
- **Filters** “All / Single targets / Groups / People” with counts.
- **“Add target”** asks for the type in the same form; it is fixed after saving.
- Only the view changes: stored configuration, YAML keys, internal names and `notify.reliable_<ID>` entities stay the same – automations need no changes.

Update through Marketplace, restart Home Assistant and reload the browser. / Über Marketplace aktualisieren, Home Assistant neu starten und die Browseransicht neu laden.
