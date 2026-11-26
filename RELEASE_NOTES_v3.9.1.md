# Reliable Notify v3.9.1

## Deutsch
Fehlerbehebungen für „Bestehende Automationen prüfen“:
- **Keine Event-Loop-Warnung mehr:** Beim Analysieren hat Home Assistant einen blockierenden Dateizugriff gemeldet („Detected blocking call to scandir“). Die Paket-Ordner werden jetzt im Hintergrund gelesen.
- **Übernehmen auch mit `*`, `&` oder `#` im Text:** Aktionen wurden abgelehnt, sobald ihr Text eines dieser Zeichen enthielt – etwa eine Jinja-Rechnung `{{ wert * preis }}` oder ein Titel `**Info**`. Jetzt werden nur echte YAML-Kommentare, -Anker und -Aliase erkannt; die bleiben weiterhin geschützt.

## English
Fixes for “Check existing automations”:
- **No event-loop warning any more:** while analysing, Home Assistant reported a blocking file access (“Detected blocking call to scandir”). The package folders are now listed in the background.
- **Apply works with `*`, `&` or `#` in the text:** actions were refused as soon as their text contained one of these characters – e.g. a Jinja calculation `{{ value * price }}` or a title `**Info**`. Now only real YAML comments, anchors and aliases are detected; those stay protected.

Update through Marketplace, restart Home Assistant and reload the browser. / Über Marketplace aktualisieren, Home Assistant neu starten und die Browseransicht neu laden.
