/* Shared German/English UI catalog. HA language selects German; all other languages fall back to English. */
const RN_TRANSLATIONS = [
  [
    "Erfolgreich",
    "Successful"
  ],
  [
    "HA-Aktion",
    "HA action"
  ],
  [
    "Notify-Zielentität",
    "Notify target entity"
  ],
  [
    "Transportparameter",
    "Transport parameters"
  ],
  [
    "Person-Entität",
    "Person entity"
  ],
  [
    "Kanäle und Empfänger",
    "Channels and recipients"
  ],
  [
    "Bevorzugte Kanäle nach Priorität",
    "Preferred channels by priority"
  ],
  [
    "Kanäle nach Zone und Priorität",
    "Channels by zone and priority"
  ],
  [
    "Priorität",
    "Priority"
  ],
  [
    "Empfänger",
    "Recipients"
  ],
  [
    "Nachricht",
    "Message"
  ],
  [
    "Titel",
    "Title"
  ],
  [
    "Nachrichtentyp",
    "Message type"
  ],
  [
    "Archivierung",
    "Archiving"
  ],
  [
    "Aufbewahrung (Tage)",
    "Retention (days)"
  ],
  [
    "Gültigkeit (Sekunden)",
    "Lifetime (seconds)"
  ],
  [
    "Zustellstrategie",
    "Delivery strategy"
  ],
  [
    "Nur senden, wenn",
    "Only send if"
  ],
  [
    "Entität",
    "Entity"
  ],
  [
    "Zustand",
    "State"
  ],
  [
    "Testmodus",
    "Test mode"
  ],
  [
    "Ruhezeiten",
    "Quiet hours"
  ],
  [
    "Loglevel je Transport",
    "Log level by transport"
  ],
  [
    "Betroffene Testempfänger (leer = alle)",
    "Affected test recipients (empty = all)"
  ],
  [
    "Aufträge pro Minute und Benutzer",
    "Requests per minute and user"
  ],
  [
    "Bestätigung und Eskalation",
    "Acknowledgement and escalation"
  ],
  [
    "Bestätigung erforderlich",
    "Acknowledgement required"
  ],
  [
    "Eskalationsstufen",
    "Escalation steps"
  ],
  [
    "Nach Sekunden",
    "After seconds"
  ],
  [
    "Aktiviert",
    "Enabled"
  ],
  [
    "Beginn (HH:MM)",
    "Start (HH:MM)"
  ],
  [
    "Ende (HH:MM)",
    "End (HH:MM)"
  ],
  [
    "Während Ruhezeit erlaubte Prioritäten",
    "Priorities allowed during quiet hours"
  ],
  [
    "Versuche pro Minute und Ziel",
    "Attempts per minute and target"
  ],
  [
    "Digest-Zeitfenster (Sekunden)",
    "Digest window (seconds)"
  ],
  [
    "Maximale Versuche (0 = unbegrenzt)",
    "Maximum attempts (0 = unlimited)"
  ],
  [
    "Basisabstand (Sekunden)",
    "Base delay (seconds)"
  ],
  [
    "Maximaler Abstand (Sekunden)",
    "Maximum delay (seconds)"
  ],
  [
    "Information",
    "Information"
  ],
  [
    "Warnung",
    "Warning"
  ],
  [
    "Kritisch",
    "Critical"
  ],
  [
    "Telegram-Chat-ID",
    "Telegram chat ID"
  ],
  [
    "Telegram-Konfiguration",
    "Telegram configuration"
  ],
  [
    "Thema",
    "Topic"
  ],
  [
    "HTTPS-Basis-URL",
    "HTTPS base URL"
  ],
  [
    "Private Zieladressen erlauben",
    "Allow private target addresses"
  ],
  [
    "HTTP-Header",
    "HTTP headers"
  ],
  [
    "HTTP-Methode",
    "HTTP method"
  ],
  [
    "Telegram-Textformat",
    "Telegram text format"
  ],
  [
    "Lautlos senden",
    "Send silently"
  ],
  [
    "Mobilgerät",
    "Mobile device"
  ],
  [
    "E-Mail",
    "Email"
  ],
  [
    "Companion-App",
    "Companion app"
  ],
  [
    "YAML-Ansicht einblenden (nur Vorschau, ggf. mit Zugangsdaten)",
    "Show YAML (preview only; may contain credentials)"
  ],
  [
    ": Zahl erforderlich",
    ": number required"
  ],
  [
    "Feld existiert bereits",
    "Field already exists"
  ],
  [
    "Eintrag",
    "Entry"
  ],
  [
    "Entfernen",
    "Remove"
  ],
  [
    "Name des Feldes / Kanals / der Zone",
    "Field / channel / zone name"
  ],
  [
    "Eigenes Transportfeld",
    "Custom transport field"
  ],
  [
    "Eigenes Transportfeld …",
    "Custom transport field …"
  ],
  [
    "Text",
    "Text"
  ],
  [
    "Zahl",
    "Number"
  ],
  [
    "Schalter",
    "Switch"
  ],
  [
    "Liste",
    "List"
  ],
  [
    "Felder",
    "Fields"
  ],
  [
    "Eintrag hinzufügen",
    "Add entry"
  ],
  [
    "Feld hinzufügen",
    "Add field"
  ],
  [
    "Name erforderlich",
    "Name required"
  ],
  [
    "Ungültiger Name",
    "Invalid name"
  ],
  [
    "Benachrichtigungen • Zustellung • Eskalation • Diagnose",
    "Notifications • Delivery • Escalation • Diagnostics"
  ],
  [
    "Nachrichten",
    "Messages"
  ],
  [
    "Ziele & Personen",
    "Targets & people"
  ],
  [
    "Eskalationen",
    "Escalations"
  ],
  [
    "Statistik",
    "Statistics"
  ],
  [
    "Vorlagen",
    "Templates"
  ],
  [
    "Profile & API",
    "Profiles & API"
  ],
  [
    "Automation-Migration",
    "Automation migration"
  ],
  [
    "Einstellungen",
    "Settings"
  ],
  [
    "Die Verwaltungsfunktionen sind nur für Home-Assistant-Administratoren freigegeben.",
    "Administration is only available to Home Assistant administrators."
  ],
  [
    "Queue, Dead Letters und Archiv",
    "Queue, dead letters and archive"
  ],
  [
    "Hier neue Ziele anlegen: Unter Ziele / Empfänger auf „Neues Ziel anlegen“ klicken, einen Namen vergeben, HA-Aktion und gegebenenfalls Zielentität oder Transportparameter ausfüllen und speichern. Diesen Namen anschließend als Empfänger verwenden. Das optionale Standardziel ist nur ein Fallback für Nachrichten ohne explizite Empfänger.",
    "Create targets here: under Targets / recipients, click “Add target”, enter a name, select the HA action and any target entity or transport parameters, then save. Use that name as the recipient. The optional default target is only a fallback for messages without explicit recipients."
  ],
  [
    "Empfänger werden geladen …",
    "Loading recipients …"
  ],
  [
    "Ziele / Empfänger",
    "Targets / recipients"
  ],
  [
    "Gruppen",
    "Groups"
  ],
  [
    "Personen",
    "People"
  ],
  [
    "Eindeutiger Name",
    "Unique name"
  ],
  [
    "Neues Ziel anlegen",
    "Add target"
  ],
  [
    "Neue Gruppe anlegen",
    "Add group"
  ],
  [
    "Neue Person anlegen",
    "Add person"
  ],
  [
    "Speichern",
    "Save"
  ],
  [
    "Zum Umbenennen neuen Eintrag anlegen und den alten gezielt löschen.",
    "To rename, create a new entry and explicitly delete the old one."
  ],
  [
    "Gespeichert. Zum Aktualisieren der Liste diesen Bereich erneut öffnen.",
    "Saved. Reopen this section to refresh the list."
  ],
  [
    "Eintrag löschen",
    "Delete entry"
  ],
  [
    "UI-Eintrag ",
    "UI entry "
  ],
  [
    " löschen?",
    ": delete?"
  ],
  [
    "Unbestätigte Alarme",
    "Unacknowledged alerts"
  ],
  [
    "Lade ...",
    "Loading ..."
  ],
  [
    "ID: ",
    "ID: "
  ],
  [
    "Bestätigen",
    "Acknowledge"
  ],
  [
    "15 Min. verschieben",
    "Snooze 15 minutes"
  ],
  [
    "Sofort eskalieren",
    "Escalate now"
  ],
  [
    "Keine offenen Bestätigungen.",
    "No pending acknowledgements."
  ],
  [
    "Testbare Eskalationskette anlegen",
    "Create a testable escalation chain"
  ],
  [
    "Alarmtext",
    "Alert text"
  ],
  [
    "Dedup-Schlüssel",
    "Deduplication key"
  ],
  [
    "Erster Empfänger",
    "Initial recipient"
  ],
  [
    "Eskalationsempfänger",
    "Escalation recipient"
  ],
  [
    "Eskalation nach Sekunden",
    "Escalation delay (seconds)"
  ],
  [
    "Nur simulieren",
    "Simulate only"
  ],
  [
    "Alarm wirklich einreihen",
    "Queue real alert"
  ],
  [
    "Dieser Alarm wird tatsächlich verschickt. Fortfahren?",
    "This alert will actually be sent. Continue?"
  ],
  [
    "Telegram: gesendete Nachricht bearbeiten / entfernen",
    "Telegram: edit / delete sent message"
  ],
  [
    "Erfordert bekannte telegram_sent-Nachrichtenkennung und passenden konfigurierten Chat. Direktaufruf ohne Queue-Retry.",
    "Requires a known telegram_sent message ID and a matching configured chat. Direct call without queue retry."
  ],
  [
    "z.B. telegram_wolfgang",
    "e.g. telegram_wolfgang"
  ],
  [
    "Dedup-Schlüssel der versendeten Meldung",
    "Deduplication key of sent message"
  ],
  [
    "Neuer Nachrichtentext (nur bei edit)",
    "New message text (edit only)"
  ],
  [
    "Reliable-Notify-Telegram-Empfänger",
    "Reliable Notify Telegram recipient"
  ],
  [
    "Aktion",
    "Action"
  ],
  [
    "Neue Nachricht",
    "New message"
  ],
  [
    "Telegram-Aktion ausführen",
    "Run Telegram action"
  ],
  [
    "Empfänger und Dedup-Schlüssel erforderlich",
    "Recipient and deduplication key required"
  ],
  [
    "Neuer Text fehlt",
    "New text is missing"
  ],
  [
    "Diese Aktion verändert eine bereits zugestellte Telegram-Nachricht. Fortfahren?",
    "This action changes an already delivered Telegram message. Continue?"
  ],
  [
    "Simulation ohne Versand",
    "Simulation without delivery"
  ],
  [
    "Zeigt Routing, Aufbewahrung und Ruhezeiten an. Keine Queue-Einträge oder Push-Nachrichten.",
    "Preview routing, retention and quiet hours. No queue entries or push messages."
  ],
  [
    "Fenster seit 90 Minuten offen",
    "Window open for 90 minutes"
  ],
  [
    "Versand simulieren",
    "Simulate delivery"
  ],
  [
    "Transportstatistik & Systemzustand",
    "Transport statistics & system health"
  ],
  [
    " Tage",
    " days"
  ],
  [
    "Aktualisieren",
    "Refresh"
  ],
  [
    "Diagnose (ohne Nachrichtentexte) exportieren",
    "Export diagnostics (without message bodies)"
  ],
  [
    "Tägliche Zustellungen (letzte 30 Tage)",
    "Daily deliveries (last 30 days)"
  ],
  [
    " versendet",
    " sent"
  ],
  [
    "Noch keine Tagesstatistiken",
    "No daily statistics yet"
  ],
  [
    "Lade …",
    "Loading …"
  ],
  [
    "Name: Kleinbuchstaben, Ziffern und Unterstriche; mit Buchstaben beginnen.",
    "Name: use lowercase letters, digits and underscores; start with a letter."
  ],
  [
    "Doppelter Name: ",
    "Duplicate name: "
  ],
  [
    "Neu anlegen",
    "Add new"
  ],
  [
    "Wiederverwendbare Vorlagen",
    "Reusable templates"
  ],
  [
    "Benachrichtigungsprofile",
    "Notification profiles"
  ],
  [
    "Externe API",
    "External API"
  ],
  [
    "Nur HA-Administratoren mit Bearer-Token und ausdrücklich freigegebene Empfänger.",
    "HA administrators with bearer tokens and explicitly allowed recipients only."
  ],
  [
    "API-Einstellungen speichern",
    "Save API settings"
  ],
  [
    "Bestehende Automationen prüfen",
    "Check existing automations"
  ],
  [
    "Liest automations.yaml und scripts.yaml ausschließlich lesend. Es werden keine Dateien, Automationen oder Skripte verändert. Vorschläge bei Mehrdeutigkeiten sind ausdrücklich zu prüfen.",
    "Read-only scan of automations.yaml and scripts.yaml. No files, automations or scripts are changed by scanning. Review ambiguous suggestions explicitly."
  ],
  [
    "Benachrichtigungen analysieren",
    "Analyse notifications"
  ],
  [
    "Vorschläge als JSON herunterladen",
    "Download suggestions as JSON"
  ],
  [
    " direkte Vorschläge • ",
    " direct suggestions • "
  ],
  [
    " manuell zu prüfen",
    " to review manually"
  ],
  [
    " Treffer",
    " matches"
  ],
  [
    "manuelle Prüfung",
    "manual review"
  ],
  [
    "Einzelne Änderung mit Backup übernehmen",
    "Apply single change with backup"
  ],
  [
    "Nur dieser EINE Paket-Eintrag wird geändert. Backup wird erstellt. Keine automatische HA-Neuladung. Fortfahren?",
    "Only this ONE package entry will change. A backup will be created. No automatic HA reload. Continue?"
  ],
  [
    "Geändert. Backup: ",
    "Changed. Backup: "
  ],
  [
    " — Paket-Automationen über HA neu laden.",
    " — Reload package automations in HA."
  ],
  [
    "Alle Betriebsoptionen stehen gemeinsam im HA-Konfigurationsdialog. Neue Ziele und Empfänger unter „Ziele & Personen“ anlegen; Profile und Vorlagen in den gleichnamigen Bereichen bearbeiten.",
    "All operating options are in the HA configuration dialog. Add new targets and recipients under “Targets & people”; edit profiles and templates in their respective tabs."
  ],
  [
    "Alle Integrationsoptionen öffnen",
    "Open all integration options"
  ],
  [
    "Wiederholungen",
    "Retries"
  ],
  [
    "Archiv-Aufbewahrung (Tage)",
    "Archive retention (days)"
  ],
  [
    "Ruhezeiten, Limits und Digest",
    "Quiet hours, limits and digest"
  ],
  [
    "Testmodus und Transport-Logging",
    "Test mode and transport logging"
  ],
  [
    "Home Assistant nicht verfügbar",
    "Home Assistant unavailable"
  ],
  [
    "Schließen",
    "Close"
  ],
  [
    "Benachrichtigung",
    "Notification"
  ],
  [
    "Archiv: ",
    "Archive: "
  ],
  [
    "Keine archivierten Benachrichtigungen",
    "No archived notifications"
  ],
  [
    "Archivfehler: ",
    "Archive error: "
  ],
  [
    "Warteschlange",
    "Queue"
  ],
  [
    "Fehlgeschlagene Nachrichten",
    "Dead letters"
  ],
  [
    "Alle fehlgeschlagenen erneut versuchen",
    "Retry all dead"
  ],
  [
    "Alle wartenden erneut versuchen",
    "Retry all pending"
  ],
  [
    "Bestätigung erforderlich: ",
    "Acknowledgement needed: "
  ],
  [
    "Datenbank: ",
    "Database: "
  ],
  [
    " MiB • Integrität: ",
    " MiB • Integrity: "
  ],
  [
    "Konfigurierte Personen: ",
    "Configured people: "
  ],
  [
    "Zurückgestellt (kein Empfänger): ",
    "Staged (no recipient): "
  ],
  [
    "Zuweisen und senden",
    "Assign and send"
  ],
  [
    "Löschen",
    "Delete"
  ],
  [
    "Zurückgestellte Nachricht löschen #",
    "Delete staged #"
  ],
  [
    "Ziel",
    "Target"
  ],
  [
    "Kanal",
    "Channel"
  ],
  [
    "Versuche",
    "Attempts"
  ],
  [
    "Letzter Fehler",
    "Last error"
  ],
  [
    "Aktionen",
    "Actions"
  ],
  [
    "Erneut versuchen",
    "Retry"
  ],
  [
    "Keine Nachrichten",
    "No messages"
  ],
  [
    "Wiederholungsregeln und Verlauf",
    "Retry policies and history"
  ],
  [
    "Wiederholungsregeln (0 Versuche = unbegrenzt)",
    "Retry policies (0 attempts = unlimited)"
  ],
  [
    "Wiederholungsregeln speichern",
    "Save retry policies"
  ],
  [
    "Wiederholungsregeln konnten nicht gespeichert werden: ",
    "Cannot save retry policies: "
  ],
  [
    "Intelligente Benachrichtigungen: Ruhezeiten, Limit, Digest",
    "Smart notifications: quiet hours, rate limit, digest"
  ],
  [
    "Max. Sendungen/Min./Ziel ",
    "Max sends/min/target "
  ],
  [
    " Digest-Sekunden ",
    " Digest seconds "
  ],
  [
    "Intelligente Einstellungen speichern",
    "Save smart settings"
  ],
  [
    "Intelligente Einstellungen: ",
    "Smart settings: "
  ],
  [
    "Archiv-Aufbewahrung je Typ (Tage; 0 = nach Versand löschen)",
    "Archive retention by type (days; 0 = purge on send)"
  ],
  [
    "Archiv-Aufbewahrungsregeln JSON",
    "Archive retention rules JSON"
  ],
  [
    "Archiv-Aufbewahrung speichern",
    "Save archive retention"
  ],
  [
    "Archiv-Aufbewahrung: ",
    "Archive retention: "
  ],
  [
    "Benachrichtigungsarchiv (Aufbewahrung je Typ, max. 2000 abgeschlossene)",
    "Notification archive (per-type retention, max 2000 completed)"
  ],
  [
    "Vollständigen Nachrichtentext durchsuchen",
    "Search full notification text"
  ],
  [
    "Benachrichtigungsarchiv durchsuchen",
    "Search notification archive"
  ],
  [
    "Suchen",
    "Search"
  ],
  [
    "Dauerhafte Nachrichtenwarteschlange und interaktive Verwaltung",
    "Persistent notification queue and interactive administration"
  ],
  [
    "unbekannt",
    "unknown"
  ],
  [
    "Wartend: {queued} · Fehlgeschlagen: {dead} · Versendet: {sent} · Fehler: {failures} · Freier Speicher: {free}",
    "Queued: {queued} · Dead letters: {dead} · Sent: {sent} · Failures: {failures} · Disk free: {free}"
  ],
  [
    "Nachricht #{id} löschen?",
    "Delete #{id}?"
  ],
  [
    "Entität auswählen (optional)",
    "Select entity (optional)"
  ],
  [
    "Keine passenden Entitäten gefunden. Klassische Notify-Ziele unter HA-Aktion auswählen.",
    "No matching entities found. Select classic notify targets under HA action."
  ],
  [
    "Vorhandene Notify-Entitäten durchsuchen. Klassische notify.mobile_app_* Ziele werden unter HA-Aktion ausgewählt.",
    "Browse existing notify entities. Select classic notify.mobile_app_* targets under HA action."
  ],
  [
    "Vorhandene person.*-Entität auswählen.",
    "Select an existing person.* entity."
  ],
  [
    "Interner Name: 1–64 Zeichen, mit Kleinbuchstaben beginnen; nur a–z, 0–9 und Unterstriche (_). Beispiel: rn_kw_telegram. Großbuchstaben, Leerzeichen und Bindestriche sind nicht erlaubt.",
    "Internal name: 1–64 characters, starting with a lowercase letter; use only a–z, 0–9 and underscores (_). Example: rn_kw_telegram. Uppercase letters, spaces and hyphens are not allowed."
  ],
  [
    "Ungültiger interner Name „{name}“. Nur Kleinbuchstaben, Ziffern und Unterstriche; mit einem Buchstaben beginnen, maximal 64 Zeichen. Beispiel: {example}.",
    "Invalid internal name “{name}”. Use lowercase letters, digits and underscores; start with a letter, maximum 64 characters. Example: {example}."
  ],
  [
    "max_attempts",
    "max_attempts"
  ],
  [
    "base_seconds",
    "base_seconds"
  ],
  [
    "max_delay",
    "max_delay"
  ],
  [
    " | Eskalationsstufe: ",
    " | Escalation step: "
  ]
];
RN_TRANSLATIONS.push(['Keine passenden person.*-Entitäten gefunden.','No matching person.* entities found.']);
RN_TRANSLATIONS.push(...[["Test senden", "Send test"], ["Gespeichertes Ziel testen", "Test saved target"], ["Test wird eingereiht …", "Queueing test …"], ["Keine Empfänger aufgelöst. Zielkonfiguration prüfen.", "No recipients resolved. Check target configuration."], ["Test eingereiht (IDs: {ids}).", "Test queued (IDs: {ids})."], ["Vom Transport angenommen", "Accepted by transport"], ["Testmodus: zurückgestellt, nicht gesendet", "Test mode: staged, not sent"], ["Wartet auf Versand", "Waiting for delivery"], ["Versandfehler, erneuter Versuch folgt", "Delivery error; retry scheduled"], ["Versand fehlgeschlagen", "Delivery failed"], ["Abgelaufen", "Expired"], ["Abgebrochen", "Cancelled"], ["Unterdrückt", "Suppressed"], ["Geplant ab {time} (Ruhezeiten aktiv).", "Scheduled from {time} (quiet hours active)."], ["Weitere Details unter Nachrichten / Archiv.", "More details under Messages / archive."], ["Test fehlgeschlagen. Zielkonfiguration und Diagnose prüfen.", "Test failed. Check target configuration and diagnostics."], ["Test senden verschickt eine echte Nachricht über die gespeicherte Konfiguration. Testmodus und Ruhezeiten bleiben aktiv. Bei Gruppen und Personen können mehrere Empfänger erreicht werden.", "Send test sends a real notification using the saved configuration. Test mode and quiet hours remain active. Groups and people may reach multiple recipients."]]);
RN_TRANSLATIONS.push(...[["Wartend:", "Queued:"], ["Versendet:", "Sent:"], ["Fehler:", "Failures:"], ["Freier Speicher:", "Disk free:"], ["Hauptnavigation", "Main navigation"]]);
// 3.3.0: display names (Klarnamen), translated value labels and backend error texts.
RN_TRANSLATIONS.push(...[
  ['Anzeigename (Klarname)','Display name'],
  ['z. B. Telegram Wolfgang','e.g. Telegram Wolfgang'],
  ['Frei wählbarer Name mit Leerzeichen, Umlauten und Sonderzeichen (höchstens 100 Zeichen). Er erscheint in Listen und als Name der Notify-Entität.','Free text with spaces, accents and special characters (up to 100 characters). Shown in lists and as the name of the notify entity.'],
  ['Interner Name (ID)','Internal name (ID)'],
  ['Wird beim Anlegen automatisch aus dem Anzeigenamen vorgeschlagen und danach nicht mehr geändert. Automationen verwenden diesen Namen; die Entität heißt notify.reliable_<ID>.','Suggested automatically from the display name when creating and kept unchanged afterwards. Automations use this name; the entity is notify.reliable_<ID>.'],
  ['Anzeigename: höchstens 100 Zeichen.','Display name: at most 100 characters.'],
  ['Nur für Home-Assistant-Administratoren.','Home Assistant administrators only.'],
  ['Reliable Notify ist nicht geladen.','Reliable Notify is not loaded.'],
  ['Eintrag nicht gefunden. Bitte zuerst speichern.','Entry not found. Please save it first.'],
  ['Nur in dieser Oberfläche angelegte Einträge können gelöscht werden.','Only entries created in this interface can be deleted.'],
  ['Eingabe unvollständig.','Input incomplete.'],
  ['Ungültige Eingabe:','Invalid input:'],
  ['Ungültige Zielkonfiguration:','Invalid target configuration:'],
  ['Anzeigename: 1–100 Zeichen, keine Steuerzeichen.','Display name: 1–100 characters, no control characters.'],
  ['Ungültige Profile:','Invalid profiles:'],
  ['Ungültige Vorlagen:','Invalid templates:'],
  ['Ungültige Empfänger:','Invalid recipients:'],
  ['Ungültige Wiederholungsregeln:','Invalid retry policies:'],
  ['Migration fehlgeschlagen:','Migration failed:'],
  ['z. B. fenster_offen','e.g. window_open'],
  ['Interner Zielname, z. B. telegram_wolfgang','Internal target name, e.g. telegram_wolfgang'],
  ['Persistente Benachrichtigungswarteschlange mit Verwaltung','Persistent notification queue and interactive administration'],
  ['Neuer Nachrichtentext (nur beim Bearbeiten)','New message text (only when editing)'],
]);
// 3.3.1: in-panel help and translated automation check.
RN_TRANSLATIONS.push(...[
  ['Hilfe einblenden','Show help'],
  ['Hilfe ausblenden','Hide help'],
  ['Hilfe zu diesem Bereich','Help for this section'],
  ['Beispiel für eine Automation:','Example for an automation:'],
  ['Ausführliche Anleitung auf GitHub (Englisch)','Detailed guide on GitHub'],
  ['Liest automations.yaml, scripts.yaml sowie YAML-Dateien in packages/, automations/ und scripts/ ausschließlich lesend. Es werden keine Dateien verändert, solange du nicht ausdrücklich eine einzelne Paket-Änderung übernimmst.','Reads automations.yaml, scripts.yaml and YAML files in packages/, automations/ and scripts/ read-only. No files are changed unless you explicitly apply a single package change.'],
  ['{proposed} direkte Vorschläge • {manual} manuell zu prüfen • {files} Dateien geprüft','{proposed} direct suggestions • {manual} to review manually • {files} files checked'],
  ['Nicht vorhanden – übersprungen','Not present – skipped'],
  ['{count} Treffer','{count} matches'],
  ['Keine Benachrichtigungsaktionen gefunden.','No notification actions found.'],
  ['in Zeile {line}','on line {line}'],
  ['Tipp: Unter „Ziele & Personen“ ein passendes Ziel anlegen und erneut analysieren.','Tip: create a matching target under “Targets & people” and analyse again.'],
  ['Vorschlag im HA-Automationseditor übernehmen (diese Datei wird von HA verwaltet).','Apply the suggestion in the HA automation editor (this file is managed by HA).'],
  ['Aktion oder Daten mit Vorlage (service_template/data_template)','Action or data uses a template (service_template/data_template)'],
  ['Die Daten der Aktion sind keine Feldliste','The action data is not a set of fields'],
  ['Ziel nutzt Bereiche, Geräte oder ist dynamisch','Target uses areas, devices or is dynamic'],
  ['Aktion enthält erweiterte Felder (z. B. response_variable)','Action contains advanced fields (e.g. response_variable)'],
  ['Notify-Entität steht in data statt in target','Notify entity is in data instead of target'],
  ['Telegram-Ziel nicht eindeutig (keine oder mehrere Chat-Angaben)','Telegram destination is ambiguous (none or several chat fields)'],
  ['Telegram-Aktion hat zusätzlich ein target','Telegram action also has a separate target'],
  ['Klassische Notify-Aktion hat zusätzlich ein target','Classic notify action also has a target'],
  ['Kein eindeutiges festes Ziel (z. B. notify.notify)','No unique fixed destination (e.g. notify.notify)'],
  ['Ziel ist dynamisch (Vorlage) oder hat mehrere Empfänger','Destination is dynamic (template) or has several recipients'],
  ['Für dieses Ziel ist noch kein Reliable-Notify-Ziel angelegt','No Reliable Notify target is configured for this destination yet'],
  ['Mehrere Reliable-Notify-Ziele passen zu diesem Ziel','Several Reliable Notify targets match this destination'],
  ['Zusätzliche Transportdaten (z. B. Bilder, Buttons) müssen geprüft werden','Extra transport data (e.g. images, buttons) must be reviewed'],
  ['Aktion enthält keine Nachricht','Action has no message'],
  ['Verwendet !secret, !include o. Ä. – bitte manuell übernehmen','Uses !secret, !include or similar – please migrate manually'],
  ['Eindeutiges festes Ziel – Vorschlag kann übernommen werden','Unique fixed destination – the suggestion can be applied'],
  ['Symbolischer Link – aus Sicherheitsgründen nicht geprüft','Symbolic link – not checked for safety reasons'],
  ['Datei größer als 4 MiB – nicht geprüft','File larger than 4 MiB – not checked'],
  ['YAML-Syntaxfehler','YAML syntax error'],
  ['Keine UTF-8-Textdatei','Not a UTF-8 text file'],
  ['Enthält keine Automationen, Skripte oder Pakete','Contains no automations, scripts or packages'],
  ['Datei konnte nicht gelesen werden','File could not be read'],
  ['Ausdrückliche Bestätigung fehlt.','Explicit confirmation is missing.'],
  ['Diese Datei kann nicht automatisch geändert werden.','This file cannot be changed automatically.'],
  ['Automatische Änderungen nur für packages/*.yaml.','Automatic changes only for packages/*.yaml.'],
  ['Datei zu groß.','File too large.'],
  ['Datei wurde seit der Analyse geändert – bitte erneut analysieren.','The file changed since the analysis – please analyse again.'],
  ['Vorschlag ist nicht mehr eindeutig – bitte erneut analysieren.','The suggestion is no longer unique – please analyse again.'],
  ['Keine Änderung nötig.','No change needed.'],
  ['Kommentare oder YAML-Anker in dieser Aktion – bitte manuell ändern.','Comments or YAML anchors in this action – please change it manually.'],
  ['Aktion wurde in der Datei nicht gefunden – bitte erneut analysieren.','The action was not found in the file – please analyse again.'],
  ['Diese Stelle ist keine einzelne Notify-Aktion.','This location is not a single notify action.'],
  ['YAML-Syntaxfehler in der Datei.','YAML syntax error in the file.'],
]);
// Labels for technical values; option values and stored data keep the raw value.
export const RN_VALUE_LABELS = {
  priority:{info:['Information','Information'],warning:['Warnung','Warning'],critical:['Kritisch','Critical']},
  archive:{keep:['Im Archiv behalten','Keep in archive'],delete_after_send:['Nach Zustellung löschen','Delete after delivery']},
  strategy:{always:['Immer senden','Always send'],replace:['Wartende Nachricht ersetzen','Replace waiting message'],digest:['Zu Sammelnachricht bündeln','Combine into digest']},
  test_mode:{off:['Aus (normal zustellen)','Off (deliver normally)'],stage:['Nur zurückstellen (nicht senden)','Stage only (do not send)']},
  level:{off:['Aus','Off'],error:['Fehler','Errors'],warning:['Warnungen','Warnings'],info:['Information','Information'],debug:['Debug','Debug']},
  operation:{edit:['Bearbeiten','Edit'],delete:['Löschen','Delete']},
  status:{queued:['Wartend','Queued'],retry:['Erneuter Versuch','Retrying'],sent:['Gesendet','Sent'],dead:['Fehlgeschlagen','Failed'],
    expired:['Abgelaufen','Expired'],dead_expired:['Abgelaufen (fehlgeschlagen)','Expired (failed)'],cancelled:['Abgebrochen','Cancelled'],
    suppressed:['Unterdrückt','Suppressed'],replaced:['Ersetzt','Replaced'],cleared:['Geleert','Cleared'],deleted:['Gelöscht','Deleted'],
    staged:['Zurückgestellt','Staged']},
};
const RN_CATALOG = new Map(RN_TRANSLATIONS.flatMap(([de,en])=>[[de,{de,en}],[en,{de,en}]]));
export function rnValueLabel(hass, kind, value) {
  const entry=RN_VALUE_LABELS[kind]?.[value];
  return entry ? entry[rnLanguage(hass)==='de'?0:1] : String(value);
}
// Suggest an internal route name from a display name: "Telegram Wölfi 2" -> "telegram_woelfi_2".
export function rnSlug(text) {
  const umlauts={ä:'ae',ö:'oe',ü:'ue',ß:'ss',Ä:'ae',Ö:'oe',Ü:'ue'};
  return String(text||'').replace(/[äöüßÄÖÜ]/g,c=>umlauts[c]).normalize('NFKD').replace(/[̀-ͯ]/g,'')
    .toLowerCase().replace(/[^a-z0-9]+/g,'_').replace(/^[^a-z]+/,'').slice(0,64).replace(/_+$/,'');
}
// "Display name (alias)" for pickers; the alias alone when no display name exists.
export function rnRouteLabel(labels, name) {
  const label=labels?.[name];
  return label && label!==name ? label+' ('+name+')' : name;
}
export function rnLanguage(hass) {
  return String(hass?.selectedLanguage || hass?.language || hass?.locale?.language || 'en').toLowerCase().split(/[-_]/)[0]==='de'?'de':'en';
}
export function rnTranslate(hass, text, values={}) {
  const entry=RN_CATALOG.get(text);
  const translated=entry?.[rnLanguage(hass)] ?? text;
  return String(translated).replace(/\{(\w+)\}/g,(match,key)=>Object.hasOwn(values,key)?String(values[key]):match);
}

/* Reliable Notify v3.3.1 - interactive, admin-only Home Assistant Lovelace card. */
// Semantic styling is keyed by section/action, independent from translated labels.
export const RN_SECTIONS = {
  messages:{icon:'mdi:bell-badge-outline',tone:'teal'},
  routes:{icon:'mdi:account-multiple-outline',tone:'blue'},
  incidents:{icon:'mdi:alert-decagram-outline',tone:'amber'},
  simulation:{icon:'mdi:flask-outline',tone:'purple'},
  analytics:{icon:'mdi:chart-box-outline',tone:'cyan'},
  templates:{icon:'mdi:text-box-multiple-outline',tone:'indigo'},
  profiles:{icon:'mdi:shield-account-outline',tone:'purple'},
  migration:{icon:'mdi:source-branch',tone:'orange'},
  settings:{icon:'mdi:cog-outline',tone:'slate'},
};
export function rnIcon(name) {
  const icon=document.createElement('ha-icon');icon.setAttribute('icon',name);
  icon.setAttribute('aria-hidden','true');return icon;
}
export function rnDecorate(node,icon,tone='blue') {
  node.prepend(rnIcon(icon));node.dataset.tone=tone;node.classList.add('rn-icon-label');return node;
}
export const RN_UI_STYLES = `
  :host{--rn-teal:var(--success-color,#00897b);--rn-blue:var(--info-color,#1976d2);
    --rn-cyan:var(--cyan-color,#00838f);--rn-purple:var(--purple-color,#8e5bb7);
    --rn-indigo:var(--indigo-color,#5c6bc0);--rn-orange:var(--orange-color,#ef6c00);
    --rn-amber:var(--warning-color,#d99500);--rn-slate:var(--secondary-text-color,#607d8b);
    --rn-red:var(--error-color,#db4437);--rn-accent:var(--rn-blue)}
  [data-tone=teal]{--rn-accent:var(--rn-teal)}[data-tone=blue]{--rn-accent:var(--rn-blue)}
  [data-tone=cyan]{--rn-accent:var(--rn-cyan)}[data-tone=purple]{--rn-accent:var(--rn-purple)}
  [data-tone=indigo]{--rn-accent:var(--rn-indigo)}[data-tone=orange]{--rn-accent:var(--rn-orange)}
  [data-tone=amber]{--rn-accent:var(--rn-amber)}[data-tone=slate]{--rn-accent:var(--rn-slate)}
  [data-tone=red]{--rn-accent:var(--rn-red)}
  .rn-icon-label{display:flex;align-items:center;gap:8px;min-width:0}
  .rn-icon-label ha-icon{--mdc-icon-size:20px;flex:none;color:var(--rn-accent)}
  button.rn-icon-label,a.rn-icon-label{display:inline-flex}
  button{min-height:38px}button ha-icon{--mdc-icon-size:19px}
  button:focus-visible,a:focus-visible,summary:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{
    outline:2px solid var(--primary-color,#03a9f4);outline-offset:3px}
  .rn-icon-label.primary ha-icon{color:inherit}
  button[data-tone],a[data-tone]{border-color:color-mix(in srgb,var(--rn-accent) 42%,var(--divider-color));
    background:color-mix(in srgb,var(--rn-accent) 9%,var(--card-background-color));color:var(--primary-text-color)}
  button[data-tone]:hover,a[data-tone]:hover{background:color-mix(in srgb,var(--rn-accent) 17%,var(--card-background-color))}
  button:disabled{opacity:.55;cursor:default}
  h2.rn-icon-label,h3.rn-icon-label{gap:11px;line-height:1.35}
  h2.rn-icon-label ha-icon{--mdc-icon-size:24px;border-radius:10px;padding:8px;
    background:color-mix(in srgb,var(--rn-accent) 13%,var(--card-background-color))}
  summary.rn-icon-label{display:list-item}summary.rn-icon-label ha-icon{vertical-align:middle;margin-right:9px}
  .rn-stat{display:flex;align-items:center;gap:10px;padding:13px;border:1px solid var(--divider-color);border-radius:12px;
    border-top:3px solid var(--rn-accent);background:color-mix(in srgb,var(--rn-accent) 8%,var(--card-background-color))}
  .rn-stat ha-icon{color:var(--rn-accent);--mdc-icon-size:25px}.rn-stat-value{font-size:23px;font-weight:700;line-height:1.3}
  .rn-stat-label{font-size:12px;color:var(--secondary-text-color)}
  .rn-priority{display:inline-flex;align-items:center;gap:5px;border-radius:20px;padding:4px 8px;
    background:color-mix(in srgb,var(--rn-accent) 12%,var(--card-background-color))}
  .rn-priority ha-icon{--mdc-icon-size:16px;color:var(--rn-accent)}
  @media(prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
`;

class ReliableNotifyCard extends HTMLElement {
  t(text, values={}) { return rnTranslate(this._hass,text,values); }
  setConfig(config) {
    this.config = config || {};
    if (!this.shadowRoot) this.attachShadow({mode: 'open'});
    this.showDead = false;
    this.refresh();
  }
  set hass(value) {
    const changed = this._hass !== value;
    const changedLanguage=this._hass && rnLanguage(this._hass)!==rnLanguage(value);
    this._hass = value;
    if(changedLanguage && this._timer)this.refresh();
    if (changed && !this._timer) {
      this._timer = setInterval(() => this.refresh(), 60000);
      this._subscribe();
      this.refresh();
    }
  }
  disconnectedCallback() {
    if (this._timer) clearInterval(this._timer);
    this._timer = null;
    if (this._unsubscribe) this._unsubscribe();
    this._unsubscribe=null;
  }
  async _subscribe() {
    if (!this._hass?.connection?.subscribeEvents || this._unsubscribe) return;
    try {
      this._unsubscribe = await this._hass.connection.subscribeEvents(
        () => this.refresh(), 'reliable_notify_updated');
    } catch (_) { /* periodic refresh remains available */ }
  }
  static getStubConfig() { return {title: 'Reliable Notify'}; }
  getCardSize() { return 7; }
  async refresh() {
    if (!this._hass || this._loading) return;
    this._loading = true;
    try {
      const data = await this._hass.callWS({type:'reliable_notify/dashboard', limit:75});
      this.render(data);
    } catch (error) {
      this.shadowRoot.textContent = 'Reliable Notify: ' + error.message;
    } finally { this._loading = false; }
  }
  async command(service, id, dead) {
    try {
      await this._hass.callService('reliable_notify', service, {id, dead});
      await this.refresh();
    } catch (error) { alert('Reliable Notify: ' + error.message); }
  }
  async showArchiveMessage(id) {
    try {
      const entry = await this._hass.callWS({type:'reliable_notify/archive_detail', message_id:Number(id)});
      const root = this.shadowRoot;
      root.querySelector('.rn-message-overlay')?.remove();
      const panel=document.createElement('section');panel.className='rn-message-overlay';
      const close=document.createElement('button');close.textContent=this.t('Close');rnDecorate(close,'mdi:close','slate');close.addEventListener('click',()=>panel.remove());
      const heading=document.createElement('h3');heading.textContent=(entry.title||this.t('Notification'))+' #'+entry.id;rnDecorate(heading,'mdi:email-open-outline','teal');
      const meta=document.createElement('div');meta.className='muted';
      meta.textContent=[rnValueLabel(this._hass,'status',entry.status),rnValueLabel(this._hass,'priority',entry.priority),entry.target,new Date(entry.created_at*1000).toLocaleString(rnLanguage(this._hass))].join(' • ');
      const body=document.createElement('pre');body.style.whiteSpace='pre-wrap';body.style.overflowWrap='anywhere';body.textContent=entry.message;
      panel.append(close,heading,meta,body);root.querySelector('ha-card')?.prepend(panel);
    } catch(e) {alert(this.t('Archive: ')+e.message);}
  }
  async loadArchive(box, search='') {
    try {
      const result=await this._hass.callWS({type:'reliable_notify/archive',limit:75,search});
      box.replaceChildren();
      for(const entry of result.items||[]) {
        const button=document.createElement('button');button.style.margin='4px';
        button.textContent='#'+entry.id+' '+(entry.title||entry.action)+' — '+rnValueLabel(this._hass,'status',entry.status)+' ['+(entry.message_type||rnValueLabel(this._hass,'priority',entry.priority))+', '+entry.retention_days+'d]';
        rnDecorate(button,'mdi:email-open-outline','indigo');button.addEventListener('click',()=>this.showArchiveMessage(entry.id));box.append(button);
      }
      if(!(result.items||[]).length) box.textContent=this.t('No archived notifications');
    } catch(e) { box.textContent=this.t('Archive error: ')+e.message; }
  }
  render(data) {
    const root = this.shadowRoot;
    root.replaceChildren();
    const style = document.createElement('style');
    style.textContent = `:host{display:block;color:var(--primary-text-color)}ha-card{padding:18px}h2{margin:0 0 12px} .stats{display:flex;gap:18px;flex-wrap:wrap} .tabs{margin:12px 0}button{border:1px solid var(--divider-color);border-radius:8px;padding:5px 10px;background:var(--card-background-color);color:inherit;cursor:pointer}button:hover{background:var(--secondary-background-color)}table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:7px;text-align:left;border-bottom:1px solid var(--divider-color)} .scroll{overflow-x:auto} .muted{color:var(--secondary-text-color)} .actions{white-space:nowrap}`;
    style.textContent += '.rn-message-overlay{border:1px solid var(--divider-color);border-radius:10px;background:var(--card-background-color);padding:14px;margin-bottom:16px}.rn-message-overlay pre{max-height:55vh;overflow:auto}';
    style.textContent += '@media(max-width:600px){ha-card{padding:10px!important}.scroll{overflow-x:auto}table{min-width:630px}button{margin:2px}}';
    style.textContent+=RN_UI_STYLES;
    style.textContent+=`.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:10px;margin:16px 0}.tabs{display:flex;flex-wrap:wrap;gap:8px}details{border:1px solid var(--divider-color);border-radius:12px;padding:12px;margin:12px 0;background:color-mix(in srgb,var(--rn-blue) 3%,var(--card-background-color))}summary{cursor:pointer;font-weight:600}ha-card{border-radius:16px;border-top:4px solid var(--rn-teal)}th.rn-icon-label{display:table-cell;white-space:nowrap}th ha-icon{vertical-align:middle;margin-right:6px}button{gap:6px}.actions button{margin:3px}tbody tr:hover{background:var(--secondary-background-color)}`;
    root.append(style);
    const card = document.createElement('ha-card');
    const heading = document.createElement('h2'); heading.textContent = this.config.title || 'Reliable Notify'; rnDecorate(heading,'mdi:bell-check-outline','teal');card.append(heading);
    const stats = document.createElement('div'); stats.className='stats';
    const free = data.storage.free_bytes == null ? this.t('unknown') : `${(data.storage.free_bytes/1048576).toFixed(0)} MiB`;
    for(const [label,value,icon,tone] of [
      [this.t('Wartend:'),data.count,'mdi:tray-arrow-down','blue'],
      [this.t('Dead letters'),data.dead,'mdi:email-alert-outline','orange'],
      [this.t('Versendet:'),data.metrics.sent||0,'mdi:send-check-outline','teal'],
      [this.t('Fehler:'),data.metrics.failures||0,'mdi:alert-circle-outline','red'],
      [this.t('Freier Speicher:'),free,'mdi:harddisk','purple']]){
      const tile=document.createElement('div');tile.className='rn-stat';tile.dataset.tone=tone;tile.append(rnIcon(icon));
      const text=document.createElement('div'),caption=document.createElement('div'),amount=document.createElement('div');
      caption.className='rn-stat-label';caption.textContent=label;amount.className='rn-stat-value';amount.textContent=value;
      text.append(caption,amount);tile.append(text);stats.append(tile);
    }
    card.append(stats);
    const tabs=document.createElement('div');tabs.className='tabs';
    for (const [label,value] of [[this.t('Queue'),false],[this.t('Dead letters'),true]]) {
      const button=document.createElement('button'); button.textContent=this.t(label); button.disabled=this.showDead===value;rnDecorate(button,value?'mdi:email-alert-outline':'mdi:tray-full',value?'orange':'blue');
      button.addEventListener('click',()=>{this.showDead=value;this.render(data);}); tabs.append(button);
    }
    const refresh=document.createElement('button');refresh.textContent=this.t('Refresh');rnDecorate(refresh,'mdi:refresh','cyan');refresh.addEventListener('click',()=>this.refresh());tabs.append(refresh);
    const bulk=document.createElement('button');bulk.textContent=this.showDead?this.t('Retry all dead'):this.t('Retry all pending');rnDecorate(bulk,'mdi:reload','amber');
    bulk.addEventListener('click',async()=>{try {await this._hass.callService('reliable_notify',this.showDead?'retry_dead':'retry_all',{});await this.refresh();}catch(e){alert(e.message);}});
    tabs.append(bulk);card.append(tabs);
    const acks=document.createElement('details');
    const ackTitle=document.createElement('summary');
    ackTitle.textContent=this.t('Acknowledgement needed: ')+(data.acknowledgements||[]).length;rnDecorate(ackTitle,'mdi:check-decagram-outline','amber');
    acks.append(ackTitle);
    for(const ack of data.acknowledgements||[]) {
      const row=document.createElement('div');row.style.margin='9px 0';
      const label=document.createElement('span');
      label.textContent=(ack.title||ack.ack_key)+' • '+rnValueLabel(this._hass,'priority',ack.priority)+' • '+ack.ack_key+' ';
      const button=document.createElement('button');button.textContent=this.t('Acknowledge');rnDecorate(button,'mdi:check-circle-outline','teal');
      button.addEventListener('click',async()=>{
        try {await this._hass.callWS({type:'reliable_notify/acknowledge',key:ack.ack_key});await this.refresh();}
        catch(error){alert(error.message);}
      });
      row.append(label,button);acks.append(row);
    }
    card.append(acks);
    if(data.maintenance?.database_bytes) {
      const health=document.createElement('p');
      health.textContent=this.t('Database: ')+(data.maintenance.database_bytes/1048576).toFixed(1)+this.t(' MiB • Integrity: ')+data.maintenance.integrity;rnDecorate(health,'mdi:database-check-outline','teal');
      card.append(health);
    }
    if((data.persons||[]).length) {
      const persons=document.createElement('p');
      persons.className='muted';
      persons.textContent=this.t('Configured people: ')+data.persons.join(', ');rnDecorate(persons,'mdi:account-group-outline','blue');
      card.append(persons);
    }
    const stagedBox=document.createElement('details');
    const stagedSummary=document.createElement('summary');stagedSummary.textContent=this.t('Staged (no recipient): ')+(data.staged_count||0);rnDecorate(stagedSummary,'mdi:pause-circle-outline','purple');stagedBox.append(stagedSummary);
    for(const item of data.staged||[]){
      const row=document.createElement('div');row.style.margin='12px 0';
      const preview=document.createElement('div');preview.style.whiteSpace='pre-wrap';
      preview.textContent='#'+item.id+' '+(item.title||'')+' — '+item.message;row.append(preview);
      const select=document.createElement('select');
      for(const name of data.recipient_names||[]){const opt=document.createElement('option');opt.value=name;opt.textContent=rnRouteLabel(data.labels,name);select.append(opt);}row.append(select);
      const send=document.createElement('button');send.textContent=this.t('Assign and send');rnDecorate(send,'mdi:send-outline','teal');send.disabled=!select.options.length;
      send.addEventListener('click',async()=>{try{await this._hass.callWS({type:'reliable_notify/send_staged',id:item.id,recipient:select.value});await this.refresh();}catch(e){alert(e.message);}});row.append(send);
      const del=document.createElement('button');del.textContent=this.t('Delete');rnDecorate(del,'mdi:delete-outline','red');del.addEventListener('click',()=>{if(confirm(this.t('Delete staged #')+item.id+'?'))this.command('delete_one',item.id,false);});row.append(del);
      stagedBox.append(row);
    }
    card.append(stagedBox);
    const wrap=document.createElement('div');wrap.className='scroll';
    const table=document.createElement('table');
    const head=document.createElement('tr');
    for(const [index,name] of ['ID',this.t('Target'),this.t('Priority'),this.t('Channel'),this.t('Attempts'),this.t('Last error'),this.t('Actions')].entries()){const th=document.createElement('th');th.textContent=this.t(name);rnDecorate(th,['mdi:identifier','mdi:send-outline','mdi:flag-outline','mdi:transit-connection-variant','mdi:reload','mdi:alert-circle-outline','mdi:gesture-tap-button'][index]);head.append(th);} table.append(head);
    const rows=this.showDead?data.dead_letters:data.queue;
    for (const row of rows) {
      const tr=document.createElement('tr');
      for(const [index,value] of [row.id,row.target,row.priority,row.action,row.attempts,row.last_error||'-'].entries()){
        const td=document.createElement('td');
        if(index===2){const badge=document.createElement('span');badge.className='rn-priority';badge.textContent=rnValueLabel(this._hass,'priority',value);badge.title=String(value);
          rnDecorate(badge,value==='critical'?'mdi:alert-octagon-outline':value==='warning'?'mdi:alert-outline':'mdi:information-outline',value==='critical'?'red':value==='warning'?'amber':'blue');td.append(badge);
        }else td.textContent=String(value);tr.append(td);
      }
      const actions=document.createElement('td'); actions.className='actions';
      for (const [name,service] of [[this.t('Retry'),'retry_one'],[this.t('Delete'),'delete_one']]) {
        const b=document.createElement('button');b.textContent=this.t(name);rnDecorate(b,service==='delete_one'?'mdi:delete-outline':'mdi:reload',service==='delete_one'?'red':'amber');
        b.addEventListener('click',()=>{if(service==='delete_one' && !confirm(this.t('Delete #{id}?',{id:row.id})))return;this.command(service,row.id,this.showDead);});actions.append(b);
      }
      tr.append(actions);table.append(tr);
    }
    if(!rows.length){const tr=document.createElement('tr');const td=document.createElement('td');td.colSpan=7;td.className='muted';td.textContent=this.t('No messages');tr.append(td);table.append(tr);}
    wrap.append(table);card.append(wrap);
    const details=document.createElement('details');const summary=document.createElement('summary');summary.textContent=this.t('Retry policies and history');rnDecorate(summary,'mdi:history','blue');details.append(summary);
    const policyTitle=document.createElement('p');policyTitle.textContent=this.t('Retry policies (0 attempts = unlimited)');details.append(policyTitle);
    const policyFields={};
    for(const [priority, values] of Object.entries(data.policies)) {
      const row=document.createElement('div');row.style.margin='8px 0';
      const label=document.createElement('strong');label.textContent=rnValueLabel(this._hass,'priority',priority)+' ';row.append(label);
      policyFields[priority]={};
      const fieldNames={max_attempts:'Maximale Versuche (0 = unbegrenzt)',base_seconds:'Basisabstand (Sekunden)',max_delay:'Maximaler Abstand (Sekunden)'};
      for(const [key,val] of Object.entries(values)) {
        const name=document.createElement('label');name.textContent=(fieldNames[key]?this.t(fieldNames[key]):key)+' ';
        const input=document.createElement('input');input.type='number';input.min=key==='max_attempts'?'0':'1';
        input.max=key==='max_attempts'?'10000':key==='max_delay'?'86400':'3600';
        input.value=val;input.style.width='68px';input.style.marginRight='8px';
        policyFields[priority][key]=input;name.append(input);row.append(name);
      }
      details.append(row);
    }
    const save=document.createElement('button');save.textContent=this.t('Save retry policies');rnDecorate(save,'mdi:content-save-outline','teal');
    save.addEventListener('click',async()=>{
      const policies={};
      for(const [priority, fields] of Object.entries(policyFields)) {
        policies[priority]={};
        for(const [key,input] of Object.entries(fields)) policies[priority][key]=Number(input.value);
      }
      try {await this._hass.callWS({type:'reliable_notify/set_retry_policies',policies}); await this.refresh();}
      catch(error){alert(this.t('Cannot save retry policies: ')+error.message);}
    });
    details.append(save);
    const recent=document.createElement('div');recent.textContent=(data.history||[]).slice(0,15).map(r=>`#${r.id} ${rnValueLabel(this._hass,'status',r.status)} ${r.action} (${r.attempts})`).join('\n');recent.style.whiteSpace='pre-line';details.append(recent);card.append(details);
    const smartBox=document.createElement('details');
    const smartHeading=document.createElement('summary');
    smartHeading.textContent=this.t('Smart notifications: quiet hours, rate limit, digest');rnDecorate(smartHeading,'mdi:weather-night','purple');
    smartBox.append(smartHeading);
    const current=data.smart||{};
    const policyInput=document.createElement('textarea');
    policyInput.rows=6;policyInput.style.width='100%';
    policyInput.value=JSON.stringify(current.quiet_hours||{},null,2);
    const settingsRow=document.createElement('div');
    const maxRate=document.createElement('input');maxRate.type='number';maxRate.min='1';maxRate.max='1000';
    maxRate.value=current.rate_limit_per_minute||10;maxRate.style.width='85px';
    const digest=document.createElement('input');digest.type='number';digest.min='10';digest.max='3600';
    digest.value=current.digest_window_seconds||300;digest.style.width='85px';
    const rateLabel=document.createElement('label');rateLabel.textContent=this.t('Max sends/min/target ');rateLabel.append(maxRate);
    const digestLabel=document.createElement('label');digestLabel.textContent=this.t(' Digest seconds ');digestLabel.append(digest);
    settingsRow.append(rateLabel,digestLabel);
    const saveSmart=document.createElement('button');saveSmart.textContent=this.t('Save smart settings');rnDecorate(saveSmart,'mdi:content-save-outline','teal');
    saveSmart.addEventListener('click',async()=>{
      try {
        await this._hass.callWS({type:'reliable_notify/set_smart_settings',
          quiet_hours:JSON.parse(policyInput.value),
          rate_limit_per_minute:Number(maxRate.value),
          digest_window_seconds:Number(digest.value)});
        await this.refresh();
      }catch(e){alert(this.t('Smart settings: ')+e.message);}
    });
    smartBox.append(policyInput,settingsRow,saveSmart);card.append(smartBox);
    const retentionBox=document.createElement('details');
    const retentionHeading=document.createElement('summary');
    retentionHeading.textContent=this.t('Archive retention by type (days; 0 = purge on send)');rnDecorate(retentionHeading,'mdi:archive-clock-outline','orange');
    retentionBox.append(retentionHeading);
    const retentionEditor=document.createElement('textarea');
    retentionEditor.value=JSON.stringify(data.retention||{},null,2);
    retentionEditor.rows=7;retentionEditor.style.width='100%';
    retentionEditor.setAttribute('aria-label',this.t('Archive retention rules JSON'));
    const retentionSave=document.createElement('button');
    retentionSave.textContent=this.t('Save archive retention');rnDecorate(retentionSave,'mdi:content-save-outline','teal');
    retentionSave.addEventListener('click',async()=>{
      try {
        const retention=JSON.parse(retentionEditor.value);
        await this._hass.callWS({type:'reliable_notify/set_archive_retention',retention});
        await this.refresh();
      } catch(e) { alert(this.t('Archive retention: ')+e.message); }
    });
    retentionBox.append(retentionEditor,retentionSave);
    card.append(retentionBox);
    const archive=document.createElement('details');
    const archiveHeading=document.createElement('summary');archiveHeading.textContent=this.t('Notification archive (per-type retention, max 2000 completed)');rnDecorate(archiveHeading,'mdi:archive-outline','indigo');archive.append(archiveHeading);
    const search=document.createElement('input');search.type='search';search.placeholder=this.t('Search full notification text');search.style.margin='10px 8px 10px 0';
    search.setAttribute('aria-label',this.t('Search notification archive'));
    const find=document.createElement('button');find.textContent=this.t('Search');rnDecorate(find,'mdi:magnify','blue');
    const results=document.createElement('div');
    find.addEventListener('click',()=>this.loadArchive(results,search.value));
    search.addEventListener('keydown',e=>{if(e.key==='Enter')this.loadArchive(results,search.value);});
    archive.addEventListener('toggle',()=>{if(archive.open)this.loadArchive(results,search.value);});
    archive.append(search,find,results);card.append(archive);
    root.append(card);
    const linked = new URLSearchParams(window.location.search).get('rn_message');
    if(linked && /^\\d+$/.test(linked) && this._lastDeepLink !== linked) {
      this._lastDeepLink=linked;
      queueMicrotask(()=>this.showArchiveMessage(Number(linked)));
    }
  }
}
if(!customElements.get('reliable-notify-card'))customElements.define('reliable-notify-card', ReliableNotifyCard);
window.customCards=window.customCards||[];
// The card picker has no hass object yet; HA sets the page language on <html lang>.
window.customCards.push({type:'reliable-notify-card',name:'Reliable Notify',
  description:rnTranslate({language:document.documentElement?.lang},'Persistente Benachrichtigungswarteschlange mit Verwaltung')});