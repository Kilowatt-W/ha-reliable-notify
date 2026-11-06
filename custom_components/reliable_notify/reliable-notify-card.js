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
const RN_CATALOG = new Map(RN_TRANSLATIONS.flatMap(([de,en])=>[[de,{de,en}],[en,{de,en}]]));
export function rnLanguage(hass) {
  return String(hass?.selectedLanguage || hass?.language || hass?.locale?.language || 'en').toLowerCase().split(/[-_]/)[0]==='de'?'de':'en';
}
export function rnTranslate(hass, text, values={}) {
  const entry=RN_CATALOG.get(text);
  const translated=entry?.[rnLanguage(hass)] ?? text;
  return String(translated).replace(/\{(\w+)\}/g,(match,key)=>Object.hasOwn(values,key)?String(values[key]):match);
}

/* Reliable Notify v0.6 - interactive, admin-only Home Assistant Lovelace card. */
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
      const close=document.createElement('button');close.textContent=this.t('Close');close.addEventListener('click',()=>panel.remove());
      const heading=document.createElement('h3');heading.textContent=(entry.title||this.t('Notification'))+' #'+entry.id;
      const meta=document.createElement('div');meta.className='muted';
      meta.textContent=[entry.status,entry.priority,entry.target,new Date(entry.created_at*1000).toLocaleString()].join(' • ');
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
        button.textContent='#'+entry.id+' '+(entry.title||entry.action)+' — '+entry.status+' ['+(entry.message_type||entry.priority)+', '+entry.retention_days+'d]';
        button.addEventListener('click',()=>this.showArchiveMessage(entry.id));box.append(button);
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
    root.append(style);
    const card = document.createElement('ha-card');
    const heading = document.createElement('h2'); heading.textContent = this.config.title || 'Reliable Notify'; card.append(heading);
    const stats = document.createElement('div'); stats.className='stats';
    const free = data.storage.free_bytes == null ? this.t('unknown') : `${(data.storage.free_bytes/1048576).toFixed(0)} MiB`;
    stats.textContent = this.t('Queued: {queued} · Dead letters: {dead} · Sent: {sent} · Failures: {failures} · Disk free: {free}',{queued:data.count,dead:data.dead,sent:data.metrics.sent||0,failures:data.metrics.failures||0,free});
    card.append(stats);
    const tabs=document.createElement('div');tabs.className='tabs';
    for (const [label,value] of [[this.t('Queue'),false],[this.t('Dead letters'),true]]) {
      const button=document.createElement('button'); button.textContent=this.t(label); button.disabled=this.showDead===value;
      button.addEventListener('click',()=>{this.showDead=value;this.render(data);}); tabs.append(button);
    }
    const refresh=document.createElement('button');refresh.textContent=this.t('Refresh');refresh.addEventListener('click',()=>this.refresh());tabs.append(refresh);
    const bulk=document.createElement('button');bulk.textContent=this.showDead?this.t('Retry all dead'):this.t('Retry all pending');
    bulk.addEventListener('click',async()=>{try {await this._hass.callService('reliable_notify',this.showDead?'retry_dead':'retry_all',{});await this.refresh();}catch(e){alert(e.message);}});
    tabs.append(bulk);card.append(tabs);
    const acks=document.createElement('details');
    const ackTitle=document.createElement('summary');
    ackTitle.textContent=this.t('Acknowledgement needed: ')+(data.acknowledgements||[]).length;
    acks.append(ackTitle);
    for(const ack of data.acknowledgements||[]) {
      const row=document.createElement('div');row.style.margin='9px 0';
      const label=document.createElement('span');
      label.textContent=(ack.title||ack.ack_key)+' • '+ack.priority+' • '+ack.ack_key+' ';
      const button=document.createElement('button');button.textContent=this.t('Acknowledge');
      button.addEventListener('click',async()=>{
        try {await this._hass.callWS({type:'reliable_notify/acknowledge',key:ack.ack_key});await this.refresh();}
        catch(error){alert(error.message);}
      });
      row.append(label,button);acks.append(row);
    }
    card.append(acks);
    if(data.maintenance?.database_bytes) {
      const health=document.createElement('p');
      health.textContent=this.t('Database: ')+(data.maintenance.database_bytes/1048576).toFixed(1)+this.t(' MiB • Integrity: ')+data.maintenance.integrity;
      card.append(health);
    }
    if((data.persons||[]).length) {
      const persons=document.createElement('p');
      persons.className='muted';
      persons.textContent=this.t('Configured people: ')+data.persons.join(', ');
      card.append(persons);
    }
    const stagedBox=document.createElement('details');
    const stagedSummary=document.createElement('summary');stagedSummary.textContent=this.t('Staged (no recipient): ')+(data.staged_count||0);stagedBox.append(stagedSummary);
    for(const item of data.staged||[]){
      const row=document.createElement('div');row.style.margin='12px 0';
      const preview=document.createElement('div');preview.style.whiteSpace='pre-wrap';
      preview.textContent='#'+item.id+' '+(item.title||'')+' — '+item.message;row.append(preview);
      const select=document.createElement('select');
      for(const name of data.recipient_names||[]){const opt=document.createElement('option');opt.value=name;opt.textContent=name;select.append(opt);}row.append(select);
      const send=document.createElement('button');send.textContent=this.t('Assign and send');send.disabled=!select.options.length;
      send.addEventListener('click',async()=>{try{await this._hass.callWS({type:'reliable_notify/send_staged',id:item.id,recipient:select.value});await this.refresh();}catch(e){alert(e.message);}});row.append(send);
      const del=document.createElement('button');del.textContent=this.t('Delete');del.addEventListener('click',()=>{if(confirm(this.t('Delete staged #')+item.id+'?'))this.command('delete_one',item.id,false);});row.append(del);
      stagedBox.append(row);
    }
    card.append(stagedBox);
    const wrap=document.createElement('div');wrap.className='scroll';
    const table=document.createElement('table');
    const head=document.createElement('tr');
    for(const name of ['ID',this.t('Target'),this.t('Priority'),this.t('Channel'),this.t('Attempts'),this.t('Last error'),this.t('Actions')]){const th=document.createElement('th');th.textContent=this.t(name);head.append(th);} table.append(head);
    const rows=this.showDead?data.dead_letters:data.queue;
    for (const row of rows) {
      const tr=document.createElement('tr');
      for(const value of [row.id,row.target,row.priority,row.action,row.attempts,row.last_error||'-']){
        const td=document.createElement('td');td.textContent=String(value);tr.append(td);
      }
      const actions=document.createElement('td'); actions.className='actions';
      for (const [name,service] of [[this.t('Retry'),'retry_one'],[this.t('Delete'),'delete_one']]) {
        const b=document.createElement('button');b.textContent=this.t(name);
        b.addEventListener('click',()=>{if(service==='delete_one' && !confirm(this.t('Delete #{id}?',{id:row.id})))return;this.command(service,row.id,this.showDead);});actions.append(b);
      }
      tr.append(actions);table.append(tr);
    }
    if(!rows.length){const tr=document.createElement('tr');const td=document.createElement('td');td.colSpan=7;td.className='muted';td.textContent=this.t('No messages');tr.append(td);table.append(tr);}
    wrap.append(table);card.append(wrap);
    const details=document.createElement('details');const summary=document.createElement('summary');summary.textContent=this.t('Retry policies and history');details.append(summary);
    const policyTitle=document.createElement('p');policyTitle.textContent=this.t('Retry policies (0 attempts = unlimited)');details.append(policyTitle);
    const policyFields={};
    for(const [priority, values] of Object.entries(data.policies)) {
      const row=document.createElement('div');row.style.margin='8px 0';
      const label=document.createElement('strong');label.textContent=priority+' ';row.append(label);
      policyFields[priority]={};
      for(const [key,val] of Object.entries(values)) {
        const name=document.createElement('label');name.textContent=key+' ';
        const input=document.createElement('input');input.type='number';input.min=key==='max_attempts'?'0':'1';
        input.max=key==='max_attempts'?'10000':key==='max_delay'?'86400':'3600';
        input.value=val;input.style.width='68px';input.style.marginRight='8px';
        policyFields[priority][key]=input;name.append(input);row.append(name);
      }
      details.append(row);
    }
    const save=document.createElement('button');save.textContent=this.t('Save retry policies');
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
    const recent=document.createElement('div');recent.textContent=(data.history||[]).slice(0,15).map(r=>`#${r.id} ${r.status} ${r.action} (${r.attempts})`).join('\n');recent.style.whiteSpace='pre-line';details.append(recent);card.append(details);
    const smartBox=document.createElement('details');
    const smartHeading=document.createElement('summary');
    smartHeading.textContent=this.t('Smart notifications: quiet hours, rate limit, digest');
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
    const saveSmart=document.createElement('button');saveSmart.textContent=this.t('Save smart settings');
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
    retentionHeading.textContent=this.t('Archive retention by type (days; 0 = purge on send)');
    retentionBox.append(retentionHeading);
    const retentionEditor=document.createElement('textarea');
    retentionEditor.value=JSON.stringify(data.retention||{},null,2);
    retentionEditor.rows=7;retentionEditor.style.width='100%';
    retentionEditor.setAttribute('aria-label',this.t('Archive retention rules JSON'));
    const retentionSave=document.createElement('button');
    retentionSave.textContent=this.t('Save archive retention');
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
    const archiveHeading=document.createElement('summary');archiveHeading.textContent=this.t('Notification archive (per-type retention, max 2000 completed)');archive.append(archiveHeading);
    const search=document.createElement('input');search.type='search';search.placeholder=this.t('Search full notification text');search.style.margin='10px 8px 10px 0';
    search.setAttribute('aria-label',this.t('Search notification archive'));
    const find=document.createElement('button');find.textContent=this.t('Search');
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
window.customCards.push({type:'reliable-notify-card',name:'Reliable Notify',description:'Persistent notification queue and interactive administration'});