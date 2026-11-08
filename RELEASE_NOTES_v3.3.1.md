# Reliable Notify v3.3.1

## Deutsch
- **„Bestehende Automationen prüfen“ repariert:** In echten Home-Assistant-Installationen endeten Dateien mit Vorschlägen oder `!secret`-Werten bisher mit einer Fehlermeldung. Die Prüfung nutzt jetzt einen eigenen, rein lesenden YAML-Leser.
- `!secret`, `!include` und ähnliche Angaben werden nie aufgelöst; betroffene Aktionen erscheinen zur manuellen Prüfung. Geheimnisse gelangen nicht ins Panel.
- Fehlende Standarddateien (z. B. keine `scripts.yaml`) werden als „übersprungen“ angezeigt statt als Fehler. YAML-Syntaxfehler nennen die Zeile.
- Übernehmen einer einzelnen Paket-Änderung funktioniert jetzt auch, wenn die Aktion nicht die letzte in ihrer Liste ist.
- Begründungen, Dateifehler und Ablehnungen erscheinen auf Deutsch oder Englisch; Vorschläge zeigen den Klarnamen des Ziels.
- **Neue Hilfe:** Jeder Bereich des Panels hat eine einblendbare Anleitung mit Schritten, Automationsbeispiel und Link zur Dokumentation. Der Knopf „Hilfe einblenden“ im Kopfbereich merkt sich die Einstellung im Browser.

## English
- **“Check existing automations” fixed:** On real Home Assistant installations, files with suggestions or `!secret` values used to end with an error. The check now uses its own read-only YAML reader.
- `!secret`, `!include` and similar values are never resolved; affected actions are listed for manual review. Secrets never reach the panel.
- Missing default files (e.g. no `scripts.yaml`) are shown as skipped instead of errors. YAML syntax errors show the line number.
- Applying a single package change now also works when the action is not the last one in its list.
- Reasons, file errors and refusals are shown in German or English; suggestions show the target's display name.
- **New help:** Every panel section has an optional guide with steps, an automation example and a link to the documentation. The “Show help” button in the header remembers the choice in the browser.

Update through Marketplace, restart Home Assistant and reload the browser. / Über Marketplace aktualisieren, Home Assistant neu starten und die Browseransicht neu laden.
