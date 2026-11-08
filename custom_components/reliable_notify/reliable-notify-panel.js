/* Reliable Notify Admin Panel 3.3.2 — no external CDN/dependencies. */
import { rnTranslate, rnLanguage, rnIcon, rnDecorate, rnValueLabel, rnSlug, rnRouteLabel, RN_UI_STYLES, RN_SECTIONS } from './reliable-notify-card.js?v=3.3.2';

/* In-panel help per section (German/English). Technical names in examples stay untranslated. */
const RN_DOCS='https://github.com/Kilowatt-W/ha-reliable-notify/blob/main/docs/';
const RN_HELP={
  messages:{doc:'OPERATIONS.md',
    de:{intro:'Überblick über alle Nachrichten, die Reliable Notify zustellt, wiederholt oder archiviert.',steps:[
      'Die Kacheln zeigen wartende und fehlgeschlagene Nachrichten, Versand, Fehler und freien Speicher.',
      '„Queue“ zeigt wartende Nachrichten, „Dead letters“ endgültig fehlgeschlagene. Einzelne Einträge lassen sich erneut versuchen oder löschen.',
      '„Zurückgestellt“ enthält Nachrichten ohne Empfänger oder aus dem Testmodus. Dort einem Ziel zuweisen und senden.',
      'Im Archiv nach Nachrichtentext suchen. Die Aufbewahrung je Nachrichtentyp wird unter Einstellungen festgelegt.',
      '„Gesendet“ bedeutet: vom Transport angenommen. Ob die Nachricht auf dem Gerät angezeigt oder gelesen wurde, ist damit nicht bestätigt.']},
    en:{intro:'Overview of all notifications Reliable Notify delivers, retries or archives.',steps:[
      'The tiles show queued and failed notifications, sent messages, failures and free disk space.',
      '“Queue” lists waiting notifications, “Dead letters” the ones that finally failed. Single entries can be retried or deleted.',
      '“Staged” holds notifications without recipients or from test mode. Assign them to a target there and send.',
      'Search the archive by message text. Retention per message type is set under Settings.',
      '“Sent” means accepted by the transport. It does not confirm that the device displayed or read the notification.']}},
  routes:{doc:'CONFIGURATION.md',example:'action: reliable_notify.enqueue\ndata:\n  recipients: [telegram_wolfgang]\n  message: "Fenster im Bad seit 30 Minuten offen"\n  priority: warning',
    de:{intro:'Hier legst du fest, wohin Nachrichten gehen: einzelne Ziele, Gruppen und Personen.',steps:[
      '„Neues Ziel anlegen“ klicken und einen Anzeigenamen (Klarname) eingeben, z. B. „Telegram Wolfgang“. Die interne ID wird daraus vorgeschlagen.',
      'HA-Aktion wählen: notify.send_message mit einer Notify-Entität, notify.mobile_app_… für die Companion-App oder telegram_bot.send_message mit chat_id unter Transportparameter.',
      'Speichern und mit „Test senden“ prüfen. Der Test verschickt eine echte Nachricht; Testmodus und Ruhezeiten gelten.',
      'Gruppen fassen mehrere Ziele zusammen. Personen wählen je Priorität und Zone (person.*) passende Kanäle.',
      'In Automationen die interne ID unter recipients verwenden (Beispiel unten) oder die Entität notify.reliable_<ID>.']},
    en:{intro:'Define where notifications go: single targets, groups and people.',steps:[
      'Click “Create new target” and enter a display name, e.g. “Telegram Wolfgang”. The internal ID is suggested from it.',
      'Choose the HA action: notify.send_message with a notify entity, notify.mobile_app_… for the Companion app, or telegram_bot.send_message with chat_id under transport parameters.',
      'Save and check with “Send test”. The test sends a real notification; test mode and quiet hours apply.',
      'Groups combine several targets. People pick channels per priority and zone (person.*).',
      'In automations, use the internal ID under recipients (example below) or the entity notify.reliable_<ID>.']}},
  incidents:{doc:'CONFIGURATION.md',example:'action: reliable_notify.enqueue\ndata:\n  recipients: [telegram_wolfgang]\n  message: "Wasseralarm Keller"\n  priority: critical\n  dedup_key: water_cellar\n  acknowledgement:\n    required: true\n    escalation:\n      - after: 300\n        recipients: [family]',
    de:{intro:'Kritische Meldungen können auf eine Bestätigung warten und sonst stufenweise eskalieren.',steps:[
      'Eine Nachricht mit dedup_key und acknowledgement wartet auf Bestätigung (Beispiel unten).',
      'Ohne Bestätigung wird nach der eingestellten Zeit an die nächste Stufe gesendet.',
      'Offene Alarme hier bestätigen, um 15 Minuten verschieben oder sofort eskalieren. Empfänger können auch direkt per Companion-App- oder Telegram-Knopf bestätigen.',
      'Mit dem Assistenten eine Kette zuerst nur simulieren. „Alarm wirklich einreihen“ sendet echt.',
      'Bereits gesendete Telegram-Nachrichten lassen sich über ihren dedup_key bearbeiten oder löschen.']},
    en:{intro:'Critical notifications can wait for an acknowledgement and otherwise escalate step by step.',steps:[
      'A notification with dedup_key and acknowledgement waits for confirmation (example below).',
      'Without acknowledgement it is sent to the next step after the configured time.',
      'Acknowledge open alarms here, snooze them for 15 minutes or escalate immediately. Recipients can also acknowledge with the Companion app or Telegram button.',
      'Use the wizard to simulate a chain first. “Really queue alarm” sends for real.',
      'Telegram messages that were already sent can be edited or deleted via their dedup_key.']}},
  simulation:{doc:'API_V2.md',example:'action: reliable_notify.simulate\ndata:\n  recipients: [family]\n  message: Test\n  priority: warning\nresponse_variable: preview',
    de:{intro:'Zeigt, was mit einer Nachricht passieren würde – ohne Versand und ohne Eintrag in der Warteschlange.',steps:[
      'Empfänger, Priorität und Text eintragen und „Versand simulieren“ klicken.',
      'Das Ergebnis zeigt die aufgelösten Ziele, Ruhezeiten-Verschiebung und Aufbewahrung.',
      'In Automationen steht dieselbe Prüfung als Aktion reliable_notify.simulate mit response_variable zur Verfügung.']},
    en:{intro:'Shows what would happen to a notification – without sending and without queueing.',steps:[
      'Enter recipients, priority and text and click “Simulate delivery”.',
      'The result lists resolved targets, quiet-hour delays and retention.',
      'In automations the same check is available as the action reliable_notify.simulate with response_variable.']}},
  analytics:{doc:'OPERATIONS.md',
    de:{intro:'Zustellstatistik je Transport und Tag sowie Systemzustand.',steps:[
      'Zeitraum wählen und „Aktualisieren“ klicken.',
      'Der Balkenverlauf zeigt die täglich versendeten Nachrichten der letzten 30 Tage.',
      'Der Diagnose-Export enthält keine Nachrichtentexte und eignet sich für Fehlermeldungen.']},
    en:{intro:'Delivery statistics per transport and day plus system health.',steps:[
      'Choose a period and click “Refresh”.',
      'The bar chart shows notifications sent per day over the last 30 days.',
      'The diagnostics export contains no message texts and is suitable for bug reports.']}},
  templates:{doc:'CONFIGURATION.md',example:'action: reliable_notify.send_template\ndata:\n  template: window_open\n  variables:\n    room: Bad\n  recipients: [family]',
    de:{intro:'Wiederverwendbare Nachrichten mit Platzhaltern.',steps:[
      '„Neu anlegen“, einen Namen (Kleinbuchstaben, Ziffern, _) und den Nachrichtentext eingeben. Jinja-Platzhalter wie {{ room }} sind erlaubt.',
      'Optional Titel, Priorität, Empfänger und Aufbewahrung vorgeben und speichern.',
      'Senden mit der Aktion reliable_notify.send_template und Variablen (Beispiel unten).']},
    en:{intro:'Reusable notifications with placeholders.',steps:[
      'Click “Create”, enter a name (lowercase letters, digits, _) and the message text. Jinja placeholders such as {{ room }} are allowed.',
      'Optionally preset title, priority, recipients and retention, then save.',
      'Send with the action reliable_notify.send_template and variables (example below).']}},
  profiles:{doc:'PROFILES.md',example:'action: reliable_notify.enqueue\ndata:\n  profile: window\n  recipients: [family]\n  message: "Fenster offen"',
    de:{intro:'Profile bündeln Vorgaben wie Priorität, Gültigkeit, Bedingung oder Bestätigung.',steps:[
      'Profil anlegen und nur die gewünschten Felder hinzufügen.',
      'In Automationen mit profile: <name> verwenden; Angaben im Aufruf haben Vorrang.',
      'Externe API: nur für HA-Administratoren mit Bearer-Token und nur an ausdrücklich freigegebene Empfänger.']},
    en:{intro:'Profiles bundle defaults such as priority, validity, condition or acknowledgement.',steps:[
      'Create a profile and add only the fields you need.',
      'Use it in automations with profile: <name>; values in the call take precedence.',
      'External API: only for HA administrators with a bearer token and only to explicitly allowed recipients.']}},
  migration:{doc:'NOTIFY_MIGRATION.md',
    de:{intro:'Findet Benachrichtigungen in bestehenden Automationen und Skripten und schlägt die Umstellung auf Reliable Notify vor.',steps:[
      'Zuerst die benötigten Ziele unter „Ziele & Personen“ anlegen, z. B. mit derselben Notify-Entität oder Telegram-chat_id wie in der Automation.',
      '„Benachrichtigungen analysieren“ klicken. Es wird nur gelesen; !secret und !include werden nicht aufgelöst.',
      'Grüne Einträge sind eindeutige Vorschläge. Gelbe Einträge müssen manuell geprüft werden; die Begründung steht darunter.',
      'automations.yaml und scripts.yaml verwaltet HA: Vorschlag im Automationseditor übernehmen. Nur packages/*.yaml kann hier einzeln mit Backup geändert werden.',
      'Nach einer Änderung Automationen bzw. YAML in HA neu laden.']},
    en:{intro:'Finds notifications in existing automations and scripts and suggests moving them to Reliable Notify.',steps:[
      'First create the required targets under “Targets & people”, e.g. with the same notify entity or Telegram chat_id as in the automation.',
      'Click “Analyse notifications”. Files are only read; !secret and !include are not resolved.',
      'Green entries are unique suggestions. Yellow entries need manual review; the reason is shown below them.',
      'automations.yaml and scripts.yaml are managed by HA: apply the suggestion in the automation editor. Only packages/*.yaml can be changed here, one entry at a time with a backup.',
      'After a change, reload automations or YAML in HA.']}},
  settings:{doc:'CONFIGURATION.md',
    de:{intro:'Betriebseinstellungen der Integration.',steps:[
      'Alle Optionen gibt es gesammelt im HA-Dialog „Alle Integrationsoptionen öffnen“: optionales Standardziel, Wiederholungen, Ruhezeiten, Testmodus, Logging und Backups.',
      'Hier direkt änderbar: Wiederholungen je Priorität, Archiv-Aufbewahrung, Ruhezeiten mit Limits sowie Testmodus und Logging.',
      'Testmodus „Nur zurückstellen“ hält Nachrichten zurück, statt sie zu senden – ideal zum Ausprobieren.',
      'Neue Ziele werden unter „Ziele & Personen“ angelegt, nicht im HA-Dialog.']},
    en:{intro:'Operating settings of the integration.',steps:[
      'All options are collected in the HA dialog “Open all integration options”: optional default target, retries, quiet hours, test mode, logging and backups.',
      'Directly editable here: retries per priority, archive retention, quiet hours with limits, and test mode and logging.',
      'Test mode “Stage only” holds notifications back instead of sending – ideal for trying things out.',
      'New targets are created under “Targets & people”, not in the HA dialog.']}},
};

// Buttons and images per transport (help of "Targets & people"). YAML stays untranslated except sample texts.
RN_HELP.routes.notes={
  de:['Companion-App (Ziel mit HA-Aktion notify.mobile_app_…): Buttons über actions und Bilder über image – beides unter data → data.',
    'Telegram (telegram_bot.send_message): Buttons über inline_keyboard, Fotos mit media: photo und file (lokale Datei) oder url.',
    'Notify-Entitäten (notify.send_message), ntfy, Gotify und Webhook übertragen nur Titel und Text.',
    'Die Entität notify.reliable_<ID> überträgt nur Titel und Text. Für Buttons und Bilder die Aktion reliable_notify.enqueue verwenden.',
    'Eigene Buttons bleiben erhalten, auch wenn eine Bestätigung (acknowledgement) eigene Knöpfe ergänzt. strategy: digest funktioniert nur mit reinem Text.',
    'Zusatzdaten gelten für alle Ziele eines Aufrufs. Bei Gruppen mit gemischten Transporten (z. B. App und Telegram) je Transport einen eigenen Aufruf verwenden.'],
  en:['Companion app (target with HA action notify.mobile_app_…): buttons via actions and images via image – both under data → data.',
    'Telegram (telegram_bot.send_message): buttons via inline_keyboard, photos with media: photo and file (local file) or url.',
    'Notify entities (notify.send_message), ntfy, Gotify and webhook only transmit title and text.',
    'The entity notify.reliable_<ID> only transmits title and text. Use the action reliable_notify.enqueue for buttons and images.',
    'Your own buttons are kept even when an acknowledgement adds its buttons. strategy: digest works with plain text only.',
    'Extra data applies to every target of a call. For groups with mixed transports (e.g. app and Telegram) use one call per transport.']};
RN_HELP.routes.examples=[
  {de:'Companion-App: Nachricht mit Buttons',en:'Companion app: notification with buttons',
   code:'action: reliable_notify.enqueue\ndata:\n  recipients: [handy_wolfgang]\n  title: Haustür\n  message: "Es hat geläutet"\n  data:\n    data:\n      actions:\n        - action: TUER_OEFFNEN\n          title: Tür öffnen\n        - action: IGNORIEREN\n          title: Ignorieren'},
  {de:'Companion-App: auf einen Button reagieren (eigene Automation)',en:'Companion app: react to a button (separate automation)',
   code:'triggers:\n  - trigger: event\n    event_type: mobile_app_notification_action\n    event_data:\n      action: TUER_OEFFNEN\nactions:\n  - action: lock.unlock\n    target:\n      entity_id: lock.haustuer'},
  {de:'Companion-App: Bild anzeigen (/media/garten.jpg ist als /media/local/garten.jpg erreichbar; das Bild wird erst beim Anzeigen geladen)',
   en:'Companion app: show an image (/media/garden.jpg is served as /media/local/garden.jpg; the image is loaded when displayed)',
   code:'action: reliable_notify.enqueue\ndata:\n  recipients: [handy_wolfgang]\n  message: "Bewegung im Garten"\n  data:\n    data:\n      image: /media/local/garten.jpg'},
  {de:'Telegram: Nachricht mit Buttons',en:'Telegram: message with buttons',
   code:'action: reliable_notify.enqueue\ndata:\n  recipients: [telegram_wolfgang]\n  message: "Waschmaschine fertig"\n  data:\n    inline_keyboard:\n      - "Erledigt:/waesche_erledigt, Später:/waesche_spaeter"'},
  {de:'Telegram: auf einen Button reagieren (eigene Automation; Reliable Notify verarbeitet nur seine eigenen Bestätigungsknöpfe)',
   en:'Telegram: react to a button (separate automation; Reliable Notify only handles its own acknowledgement buttons)',
   code:'triggers:\n  - trigger: event\n    event_type: telegram_callback\n    event_data:\n      data: /waesche_erledigt\nactions:\n  - action: input_boolean.turn_off\n    target:\n      entity_id: input_boolean.waesche_fertig'},
  {de:'Telegram: Kamerabild senden (Reliable Notify kopiert die Datei beim Einreihen, ein späterer Schnappschuss überschreibt sie nicht)',
   en:'Telegram: send a camera picture (Reliable Notify copies the file when queueing, so a later snapshot does not overwrite it)',
   code:'- action: camera.snapshot\n  target:\n    entity_id: camera.haustuer\n  data:\n    filename: /media/haustuer.jpg\n- action: reliable_notify.enqueue\n  data:\n    recipients: [telegram_wolfgang]\n    media: photo\n    message: "Es hat geläutet"\n    data:\n      file: /media/haustuer.jpg'},
  {de:'Telegram: Bild aus dem Internet senden',en:'Telegram: send an image from the internet',
   code:'action: reliable_notify.enqueue\ndata:\n  recipients: [telegram_wolfgang]\n  media: photo\n  message: "Wetterradar"\n  data:\n    url: https://example.com/radar.png'},
];

class ReliableNotifyPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:'open'});
    this._section='messages';
    this._rendered=false;
    this._hass=null;
  }
  t(text, values={}) { return rnTranslate(this._hass,text,values); }
  // Help visibility is a per-browser convenience; storage may be unavailable.
  get helpOpen(){
    if(this._helpOpen===undefined){try{this._helpOpen=localStorage.getItem('reliable-notify-help')==='open';}catch(_){this._helpOpen=false;}}
    return this._helpOpen;
  }
  setHelpOpen(open){
    this._helpOpen=open;
    try{localStorage.setItem('reliable-notify-help',open?'open':'closed');}catch(_){/* private mode */}
    for(const box of this.shadowRoot.querySelectorAll('details.rn-help'))if(box.open!==open)box.open=open;
    const toggle=this.shadowRoot.querySelector('button.rn-help-toggle');
    if(toggle){toggle.setAttribute('aria-expanded',String(open));
      toggle.lastChild.textContent=open?this.t('Hilfe ausblenden'):this.t('Hilfe einblenden');}
  }
  // YAML example with a copy button; clipboard access may be blocked (http, permissions).
  codeBlock(code){
    const wrap=this.element('div',null,'rn-code');const pre=this.element('pre',code);
    const copy=this.actionButton(this.t('Kopieren'),'mdi:content-copy');copy.type='button';
    copy.addEventListener('click',async()=>{
      try{await navigator.clipboard.writeText(code);copy.lastChild.textContent=this.t('Kopiert');}
      catch(_){copy.lastChild.textContent=this.t('Kopieren nicht möglich – Text markieren');}
      setTimeout(()=>{copy.lastChild.textContent=this.t('Kopieren');},2500);
    });
    wrap.append(pre,copy);return wrap;
  }
  helpBox(section){
    const help=RN_HELP[section];if(!help)return null;
    const text=help[rnLanguage(this._hass)==='de'?'de':'en'];
    const box=this.element('details',null,'rn-help panel');box.open=this.helpOpen;
    box.append(this.heading(this.t('Hilfe zu diesem Bereich'),'mdi:help-circle-outline','cyan','summary'));
    box.append(this.element('p',text.intro));
    const steps=this.element('ol');for(const step of text.steps)steps.append(this.element('li',step));box.append(steps);
    const lang=rnLanguage(this._hass)==='de'?'de':'en';
    if(help.example)box.append(this.element('p',this.t('Beispiel für eine Automation:'),'muted'),this.codeBlock(help.example));
    if(help.notes){
      box.append(this.heading(this.t('Buttons, Bilder und Zusatzdaten je Transport'),'mdi:image-multiple-outline','cyan','h4'));
      const notes=this.element('ul');for(const note of help.notes[lang])notes.append(this.element('li',note));box.append(notes);
    }
    for(const example of help.examples||[])box.append(this.element('p',example[lang],'rn-example-title'),this.codeBlock(example.code));
    const link=rnDecorate(this.element('a',this.t('Ausführliche Anleitung auf GitHub (Englisch)')),'mdi:book-open-variant','cyan');
    link.href=RN_DOCS+help.doc;link.target='_blank';link.rel='noopener noreferrer';box.append(link);
    box.addEventListener('toggle',()=>{if(box.open!==this.helpOpen)this.setHelpOpen(box.open);});
    return box;
  }
  set hass(value) {
    const changedLanguage=this._hass && rnLanguage(this._hass)!==rnLanguage(value);
    this._hass=value;
    const card=this.shadowRoot.querySelector('reliable-notify-card');
    if(card)card.hass=value;
    if(changedLanguage){this._rendered=false;this.shadowRoot.replaceChildren();}
    if(!this._rendered)this.render();
  }
  set panel(value){this._panel=value;}
  set narrow(value){this._narrow=value;}
  connectedCallback(){if(this._rendered&&this._hass)this.refreshSection();}
  disconnectedCallback(){this._destroyed=true;}
  element(tag,txt,cls) {
    const n=document.createElement(tag);
    if(txt!==undefined && txt!==null)n.textContent=txt;
    if(cls)n.className=cls;
    return n;
  }
  actionButton(text, icon, className='') {
    const button=this.element('button',text,className);
    return rnDecorate(button,icon,className==='danger'?'red':className==='primary'?'teal':className==='test'?'cyan':'blue');
  }
  heading(text,icon,tone='blue',tag='h2') {
    return rnDecorate(this.element(tag,text),icon,tone);
  }
  fieldIcon(key) {
    return ({action:'mdi:gesture-tap-button',target_entity:'mdi:send-outline',entity:'mdi:account-outline',
      channels:'mdi:transit-connection-variant',data:'mdi:tune',preferred:'mdi:sort-variant',preferred_by_zone:'mdi:map-marker-radius-outline',
      priority:'mdi:flag-outline',recipients:'mdi:account-multiple-outline',message:'mdi:message-text-outline',title:'mdi:format-title',
      archive:'mdi:archive-outline',archive_days:'mdi:calendar-clock-outline',quiet_hours:'mdi:weather-night',transport_logging:'mdi:math-log',
      test_mode:'mdi:flask-outline',only_if:'mdi:filter-check-outline',acknowledgement:'mdi:check-decagram-outline',
      escalation:'mdi:alert-decagram-outline',token:'mdi:key-outline',headers:'mdi:code-json',rate:'mdi:speedometer',
      max_attempts:'mdi:reload',base_seconds:'mdi:timer-outline',max_delay:'mdi:timer-sand'})[key]||'mdi:form-textbox';
  }
  async testTarget(category,name,button,result){
    button.disabled=true;
    this.status(result,this.t('Test wird eingereiht …'));result.className='pending';
    try{
      const response=await this.call('test_route',{category,name,language:rnLanguage(this._hass)});
      const ids=response.ids||[];
      if(!ids.length)throw Error(this.t('Keine Empfänger aufgelöst. Zielkonfiguration prüfen.'));
      this.status(result,this.t('Test eingereiht (IDs: {ids}).',{ids:ids.join(', ')}));result.className='pending';
      // Read only the IDs returned for this test, with a bounded polling window.
      for(let attempt=0;attempt<15;attempt++){
        if(!result.isConnected && !this.shadowRoot.contains(result))return;
        const entries=await Promise.all(ids.map(message_id=>this.call('archive_detail',{message_id})));
        const summary=entries.map(e=>'#'+e.id+': '+this.t(({sent:'Vom Transport angenommen',staged:'Testmodus: zurückgestellt, nicht gesendet',
          queued:'Wartet auf Versand',retry:'Versandfehler, erneuter Versuch folgt',dead:'Versand fehlgeschlagen',expired:'Abgelaufen',
          cancelled:'Abgebrochen',suppressed:'Unterdrückt'})[e.status]||e.status)+(e.last_error?' ('+e.last_error+')':'')).join(' · ');
        this.status(result,summary);result.className=entries.every(e=>e.status==='sent')?'status':entries.some(e=>['dead','expired','retry'].includes(e.status))?'error':'pending';
        if(entries.every(e=>['sent','staged','dead','expired','cancelled','suppressed'].includes(e.status)))return;
        if(response.not_before>Date.now()/1000+2){
          result.textContent+=' '+this.t('Geplant ab {time} (Ruhezeiten aktiv).',{time:new Date(response.not_before*1000).toLocaleString(rnLanguage(this._hass))});return;
        }
        if(attempt<14)await new Promise(resolve=>setTimeout(resolve,2000));
      }
      result.textContent+=' '+this.t('Weitere Details unter Nachrichten / Archiv.');
    }catch(e){this.status(result,this.t('Test fehlgeschlagen. Zielkonfiguration und Diagnose prüfen.')+' '+(e.code||''),true);}
    finally{button.disabled=false;}
  }
  async call(type,other={}){
    if(!this._hass)throw Error(this.t('Home Assistant unavailable'));
    return this._hass.callWS({type:'reliable_notify/'+type,...other});
  }
  status(node,value,error=false){node.textContent=value;node.className=error?'error':'status';}
  // Backend errors carry stable codes; show them in the HA language and keep technical details.
  errorText(e){
    const texts={unauthorized:'Nur für Home-Assistant-Administratoren.',not_loaded:'Reliable Notify ist nicht geladen.',
      not_found:'Eintrag nicht gefunden. Bitte zuerst speichern.',not_managed:'Nur in dieser Oberfläche angelegte Einträge können gelöscht werden.',
      bad_input:'Eingabe unvollständig.',invalid_input:'Ungültige Eingabe:',invalid_format:'Ungültige Eingabe:',
      invalid_route:'Ungültige Zielkonfiguration:',invalid_label:'Anzeigename: 1–100 Zeichen, keine Steuerzeichen.',
      invalid_profiles:'Ungültige Profile:',invalid_templates:'Ungültige Vorlagen:',invalid_recipients:'Ungültige Empfänger:',
      invalid_policy:'Ungültige Wiederholungsregeln:',migration_failed:'Migration fehlgeschlagen:',
      test_failed:'Test fehlgeschlagen. Zielkonfiguration und Diagnose prüfen.',
      own_entity:'Eine Reliable-Notify-Entität kann kein Ziel sein (Endlosschleife). Bitte die Notify-Entität des eigentlichen Geräts wählen.'};
    const text=texts[e?.code];
    if(!text)return e?.message||String(e);
    return text.endsWith(':')&&e.message?this.t(text)+' '+e.message:this.t(text);
  }
  async run(node, fn){
    const oldText=node.textContent;
    try {
      await fn();
      if(node.textContent===oldText)this.status(node,this.t('Erfolgreich'));
    }catch(e){this.status(node,this.errorText(e),true);}
  }
  // Known route aliases with display names, for pickers in groups, people, profiles and wizards.
  isOwnEntity(id){
    return id.startsWith('notify.reliable_')||this._hass?.entities?.[id]?.platform==='reliable_notify'||(this._ownEntities||[]).includes(id);
  }
  setRouteChoices(data){
    const labels=data?.labels||{},names=new Set();
    for(const kind of ['recipients','groups','persons'])for(const id of Object.keys(data?.routes?.[kind]||{}))names.add(id);
    this._routeLabels=labels;this._routeChoices=[...names].sort().map(id=>[id,labels[id]||'']);
    if(Array.isArray(data?.own_entities))this._ownEntities=data.own_entities;
  }
  async loadRouteChoices(){
    if(this._routeChoices)return;
    try{this.setRouteChoices(await this.call('admin_inventory'));}catch(_){this._routeChoices=[];}
  }
  routeList(input){
    const list=this.element('datalist');this._fieldId=(this._fieldId||0)+1;list.id='rn-routes-'+this._fieldId;
    for(const [id,label] of this._routeChoices||[]){const option=this.element('option');option.value=id;if(label)option.label=label+' ('+id+')';list.append(option);}
    input.setAttribute('list',list.id);return list;
  }
  fieldLabel(key){
    return ({action:this.t('HA-Aktion'),target_entity:this.t('Notify-Zielentität'),data:this.t('Transportparameter'),
      entity:this.t('Person-Entität'),channels:this.t('Kanäle und Empfänger'),preferred:this.t('Bevorzugte Kanäle nach Priorität'),
      preferred_by_zone:this.t('Kanäle nach Zone und Priorität'),priority:this.t('Priorität'),recipients:this.t('Empfänger'),
      message:this.t('Nachricht'),title:this.t('Titel'),message_type:this.t('Nachrichtentyp'),archive:this.t('Archivierung'),
      archive_days:this.t('Aufbewahrung (Tage)'),ttl:this.t('Gültigkeit (Sekunden)'),strategy:this.t('Zustellstrategie'),
      only_if:this.t('Nur senden, wenn'),entity_id:this.t('Entität'),state:this.t('Zustand'),test_mode:this.t('Testmodus'),
      quiet_hours:this.t('Ruhezeiten'),transport_logging:this.t('Loglevel je Transport'),test_recipients:this.t('Betroffene Testempfänger (leer = alle)'),rate:this.t('Aufträge pro Minute und Benutzer'),acknowledgement:this.t('Bestätigung und Eskalation'),required:this.t('Bestätigung erforderlich'),
      escalation:this.t('Eskalationsstufen'),after:this.t('Nach Sekunden'),enabled:this.t('Aktiviert'),start:this.t('Beginn (HH:MM)'),
      end:this.t('Ende (HH:MM)'),allow_priorities:this.t('Während Ruhezeit erlaubte Prioritäten'),
      rate_limit_per_minute:this.t('Versuche pro Minute und Ziel'),digest_window_seconds:this.t('Digest-Zeitfenster (Sekunden)'),
      max_attempts:this.t('Maximale Versuche (0 = unbegrenzt)'),base_seconds:this.t('Basisabstand (Sekunden)'),
      max_delay:this.t('Maximaler Abstand (Sekunden)'),info:'Information',warning:this.t('Warnung'),critical:this.t('Kritisch'),
      chat_id:this.t('Telegram-Chat-ID'),config_entry_id:this.t('Telegram-Konfiguration'),url:'URL',topic:this.t('Thema'),
      token:'Token',base_url:this.t('HTTPS-Basis-URL'),allow_private:this.t('Private Zieladressen erlauben'),headers:this.t('HTTP-Header'),method:this.t('HTTP-Methode'),parse_mode:this.t('Telegram-Textformat'),
      disable_notification:this.t('Lautlos senden'),mobile:this.t('Mobilgerät'),email:this.t('E-Mail'),telegram:'Telegram',
      smtp:'SMTP',companion:this.t('Companion-App'),notify:'HA Notify',webhook:'Webhook',ntfy:'ntfy',gotify:'Gotify'
    })[key]||key;
  }
  fieldDefaults(kind){
    const common={priority:'info',recipients:[],message_type:'',archive:'keep',archive_days:7};
    if(kind==='profile')return {...common,ttl:3600,strategy:'always',
      only_if:{entity_id:'',state:'on'},test_mode:'off',acknowledgement:{required:true,escalation:[]}};
    if(kind==='template')return {title:'',message:'',...common};
    if(kind==='recipient')return {action:'notify.send_message',target_entity:'',data:{}};
    if(kind==='person')return {entity:'',channels:{},preferred:{},preferred_by_zone:{}};
    return {};
  }
  // Scalar values are quoted, so Jinja, colons, newlines and YAML-looking strings round-trip.
  yaml(value,indent=0){
    const pad=' '.repeat(indent);
    if(value===null||typeof value!=='object')return JSON.stringify(value);
    if(Array.isArray(value))return value.length?value.map(v=>pad+'- '+
      (v!==null&&typeof v==='object'&&Object.keys(v).length?'\n'+this.yaml(v,indent+2):v!==null&&typeof v==='object'?(Array.isArray(v)?'[]':'{}'):this.yaml(v))).join('\n'):'[]';
    const entries=Object.entries(value);
    return entries.length?entries.map(([key,v])=>pad+JSON.stringify(key)+': '+
      (v!==null&&typeof v==='object'&&Object.keys(v).length?'\n'+this.yaml(v,indent+2):
        v!==null&&typeof v==='object'?(Array.isArray(v)?'[]':'{}'):this.yaml(v))).join('\n'):'{}';
  }
  yamlView(parent,read){
    const details=this.element('details',null,'yaml-view');
    details.append(this.heading(this.t('YAML-Ansicht einblenden (nur Vorschau, ggf. mit Zugangsdaten)'),'mdi:code-braces','slate','summary'));
    const preview=this.element('pre');details.append(preview);parent.append(details);
    const refresh=()=>{if(details.open){try{preview.textContent=this.yaml(read());}
      catch(e){preview.textContent=e.message;}}};
    details.addEventListener('toggle',refresh);
    parent.addEventListener('input',refresh);parent.addEventListener('change',refresh);
    return refresh;
  }
  fieldEditor(initial,{defaults={},fixed=false,key='',choices=null,routes=false,valueKind=null}={}){
    const host=this.element('div',null,'field-editor');
    if(initial===null||typeof initial!=='object'){
      const enums={priority:['info','warning','critical'],archive:['keep','delete_after_send'],
        strategy:['always','replace','digest'],test_mode:['off','stage']};
      const kind=valueKind||(Object.hasOwn(enums,key)?key:null);
      const entityDomain=key==='target_entity'?'notify':key==='entity'?'person':null;
      // Reliable Notify's own notify entities are never offered as targets (loop).
      const entities=entityDomain?Object.keys(this._hass?.states||{}).filter(id=>id.startsWith(entityDomain+'.')&&!this.isOwnEntity(id)).sort():[];
      const options=entityDomain?['',...new Set([...entities,...(initial?[initial]:[])])]:choices||enums[key];
      const input=this.element(options?'select':key==='message'||(typeof initial==='string'&&initial.includes('\n'))?'textarea':'input');
      if(options){for(const value of new Set([...options,initial])){
        const entity=this._hass?.states?.[value];
        const label=entityDomain?(value?(entity?.attributes?.friendly_name?entity.attributes.friendly_name+' — '+value:value):this.t('Entität auswählen (optional)')):kind?rnValueLabel(this._hass,kind,value):this.t(String(value));
        const opt=this.element('option',label);opt.value=value;input.append(opt);}}
      const type=initial===null?'null':typeof initial;
      if(!options&&input.tagName==='INPUT')input.type=type==='boolean'?'checkbox':type==='number'?'number':
        /token|password|secret|authorization/i.test(key)?'password':'text';
      if(type==='number')input.step='any';
      if(type==='boolean')input.checked=initial;else input.value=initial===null?'':initial;
      if(type==='null'){input.disabled=true;input.placeholder='null';}
      const numeric={rate:[1,60],rate_limit_per_minute:[1,1000],digest_window_seconds:[10,3600],archive_days:[0,365],ttl:[0,2678400],max_attempts:[0,10000],
        base_seconds:[1,3600],max_delay:[1,86400]};
      if(numeric[key]){[input.min,input.max]=numeric[key];input.step='1';}
      host.append(input);
      if(routes&&!options&&input.tagName==='INPUT'&&type==='string')host.append(this.routeList(input));
      if(entityDomain){
        host.append(this.element('p',this.t(entityDomain==='person'?'Vorhandene person.*-Entität auswählen.':'Vorhandene Notify-Entitäten durchsuchen. Klassische notify.mobile_app_* Ziele werden unter HA-Aktion ausgewählt.'),'muted'));
        if(!entities.length)host.append(this.element('p',this.t(entityDomain==='person'?'Keine passenden person.*-Entitäten gefunden.':'Keine passenden Entitäten gefunden. Klassische Notify-Ziele unter HA-Aktion auswählen.'),'muted'));
      }
      if(key==='action'){
        const list=this.element('datalist');this._fieldId=(this._fieldId||0)+1;list.id='rn-actions-'+this._fieldId;input.setAttribute('list',list.id);
        for(const [domain,services] of Object.entries(this._hass?.services||{})){
          if(!['notify','telegram_bot','reliable_notify','smtp'].includes(domain))continue;
          for(const [service,definition] of Object.entries(services)){
            if(domain==='notify'&&service.startsWith('reliable_'))continue;
            const option=this.element('option');option.value=domain+'.'+service;option.label=definition.name||option.value;list.append(option);
          }
        }host.append(list);
      }
      return {node:host,read:()=>{
        if(!input.checkValidity())throw Error(this.fieldLabel(key)+': '+input.validationMessage);
        if(type==='null')return null;
        if(type==='boolean')return input.checked;
        if(type==='number'){
          if(input.value.trim()===''||!Number.isFinite(Number(input.value)))throw Error(this.fieldLabel(key)+this.t(': Zahl erforderlich'));
          return Number(input.value);
        }
        return input.value;
      }};
    }
    const array=Array.isArray(initial),rows=[];
    const fields=this.element('div',null,array?'list-fields':'grid');host.append(fields);
    const add=(name,value)=>{
      if(!array&&rows.some(r=>r.name===name))throw Error(this.t('Feld existiert bereits'));
      const row=this.element('div',null,'field-row');
      const label=this.element('label',array?this.t('Eintrag'):this.fieldLabel(name));rnDecorate(label,array?'mdi:format-list-bulleted':this.fieldIcon(name),'slate');
      // Lists of recipients and person channels offer known targets with their display names.
      const childRoutes=array||key==='channels'?routes:['channels','recipients'].includes(name);
      const child=this.fieldEditor(value,{key:array?'':name,routes:childRoutes,
        valueKind:key==='transport_logging'?'level':key==='allow_priorities'?'priority':null,
        fixed:fixed&&value!==null&&typeof value==='object'&&!Array.isArray(value),choices:key==='transport_logging'?['off','error','warning','info','debug']:key==='allow_priorities'?['info','warning','critical']:null,defaults:!array&&name==='preferred'
        ?{info:[],warning:[],critical:[]}:!array&&name==='data'
        ?{chat_id:0,config_entry_id:'',entity_id:'',base_url:'',allow_private:false,url:'',topic:'',token:'',headers:{},method:'POST',parse_mode:'HTML',disable_notification:false}
        :!array&&name==='only_if'?{entity_id:'',state:''}:{}});
      const control=child.node.querySelector('input,textarea,select');
      if(control){if(!control.id){this._fieldId=(this._fieldId||0)+1;control.id='rn-field-'+this._fieldId;}label.htmlFor=control.id;}
      row.append(label,child.node);const record={name,child,row};rows.push(record);
      if(!fixed){const remove=this.actionButton(this.t('Entfernen'),'mdi:minus-circle-outline','danger');remove.type='button';
        remove.addEventListener('click',()=>{rows.splice(rows.indexOf(record),1);row.remove();host.dispatchEvent(new Event('input',{bubbles:true}));});row.append(remove);}
      fields.append(row);
    };
    if(array)initial.forEach((v,i)=>add(String(i),v));else Object.entries(initial).forEach(([k,v])=>add(k,v));
    if(!fixed){
      const controls=this.element('div',null,'add-field');
      const name=this.element(Object.keys(defaults).length?'select':'input');
      if(name.tagName==='SELECT')for(const k of Object.keys(defaults)){
        const opt=this.element('option',this.fieldLabel(k));opt.value=k;name.append(opt);
      }
      else name.placeholder=this.t('Name des Feldes / Kanals / der Zone');
      const custom=this.element('input');custom.placeholder=this.t('Eigenes Transportfeld');custom.hidden=true;
      if(key==='data'){const opt=this.element('option',this.t('Eigenes Transportfeld …'));opt.value='__custom';name.append(opt);
        name.addEventListener('change',()=>{custom.hidden=name.value!=='__custom';});}
      const type=this.element('select');
      for(const [value,label] of [['text','Text'],['number',this.t('Zahl')],['boolean',this.t('Schalter')],['list',this.t('Liste')],['object',this.t('Felder')]]){
        const opt=this.element('option',label);opt.value=value;type.append(opt);}
      const button=this.actionButton(array?this.t('Eintrag hinzufügen'):this.t('Feld hinzufügen'),'mdi:plus-circle-outline');button.type='button';
      const error=this.element('p',null,'error');
      button.addEventListener('click',()=>{
        try{
          const k=array?String(rows.length):(name.value==='__custom'?custom.value:name.value).trim();
          if(!k)throw Error(this.t('Name erforderlich'));
          if(['__proto__','constructor','prototype'].includes(k))throw Error(this.t('Ungültiger Name'));
          let value=({text:'',number:0,boolean:false,list:[],object:{}})[type.value];
          if(!array&&Object.hasOwn(defaults,k))value=structuredClone(defaults[k]);
          if(array&&key==='escalation')value={after:300,recipients:[]};
          add(k,value);error.textContent='';host.dispatchEvent(new Event('input',{bubbles:true}));
        }catch(e){error.textContent=e.message;}
      });
      if(!array)controls.append(name);
      if(key==='data')controls.append(custom);
      if((!Object.keys(defaults).length||key==='data')&&key!=='escalation')controls.append(type);
      controls.append(button,error);host.append(controls);
    }
    return {node:host,read:()=>array?rows.map(r=>r.child.read()):Object.fromEntries(rows.map(r=>[r.name,r.child.read()]))};
  }
  refreshSection(){
    const container=this.shadowRoot.querySelector('#content');
    if(!container)return;
    container.replaceChildren();
    const help=this.helpBox(this._section);if(help)container.append(help);
    ({messages:()=>this.messages(container),routes:()=>this.routes(container),
      incidents:()=>this.incidents(container),simulation:()=>this.simulation(container),
      analytics:()=>this.analytics(container),templates:()=>this.templates(container),profiles:()=>this.profiles(container),migration:()=>this.migration(container),settings:()=>this.settings(container)
    }[this._section]||(()=>{}))();
  }
  render(){
    if(this._rendered||!this._hass)return;
    this._rendered=true;
    const root=this.shadowRoot;
    const style=this.element('style');
    style.textContent=`
      :host{display:block;min-height:100%;color:var(--primary-text-color);background:var(--primary-background-color)}
      .shell{max-width:1280px;margin:0 auto;padding:20px}
      h1{font-size:26px;margin:5px 0 16px;font-weight:700}h2{font-size:20px}
      .tabs{display:flex;flex-wrap:wrap;gap:7px;margin:8px 0 22px}
      button{border:1px solid var(--divider-color);padding:9px 13px;border-radius:8px;
        background:var(--card-background-color);color:var(--primary-text-color);cursor:pointer}
      button:hover{filter:brightness(.94)}
      button{display:inline-flex;align-items:center;justify-content:center;gap:7px}
      button ha-icon{--mdc-icon-size:19px}button:disabled{opacity:.55;cursor:default}button{overflow-wrap:anywhere}
      button.primary{background:var(--primary-color);color:var(--text-primary-color,#fff)}
      button.test{color:var(--primary-text-color);border-color:var(--info-color,#039be5);background:color-mix(in srgb,var(--info-color,#039be5) 13%,var(--card-background-color))}
      button.danger{color:var(--error-color);border-color:var(--error-color)}
      .route-item{display:flex;align-items:center;flex-wrap:wrap;gap:8px;padding:9px;border-radius:9px;background:var(--secondary-background-color);width:100%;box-sizing:border-box}
      .route-item p{flex-basis:100%;margin:3px 0;overflow-wrap:anywhere}.pending{color:var(--primary-text-color)}
      .route-heading{display:flex;align-items:center;gap:10px}.route-heading ha-icon{color:var(--primary-color)}
      .test-hint{border-left:3px solid var(--info-color,#039be5);padding:10px;background:color-mix(in srgb,var(--info-color,#039be5) 8%,var(--card-background-color));border-radius:5px}button.active{background:var(--primary-color);color:var(--text-primary-color)}
      .panel{background:var(--card-background-color);border-radius:12px;padding:18px;margin:12px 0;
        border:1px solid var(--divider-color)}
      input,textarea,select{box-sizing:border-box;max-width:100%;width:100%;padding:9px;
        margin:5px 0 12px;border-radius:7px;border:1px solid var(--divider-color);
        background:var(--primary-background-color);color:var(--primary-text-color)}
      textarea{font-family:monospace;min-height:115px}
      input[type=checkbox]{width:auto;min-width:22px;min-height:22px}fieldset{min-width:0}\n      .field-row{min-width:0;border:1px solid var(--divider-color);border-radius:8px;padding:10px}\n      .field-editor .grid{grid-template-columns:repeat(auto-fit,minmax(min(100%,230px),1fr))}\n      .add-field{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:12px}\n      .add-field input,.add-field select{width:auto;flex:1;min-width:120px}\n      .yaml-view{margin:18px 0}summary{cursor:pointer;font-weight:600;padding:8px 0}\n      label{display:block;font-weight:600;font-size:13px;margin-top:6px}
      .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(275px,1fr));gap:14px}
      .chip{display:inline-block;padding:5px 9px;margin:4px;border-radius:6px;background:var(--secondary-background-color)}
      .muted{color:var(--secondary-text-color)}
      .error{color:var(--error-color)}.status{color:var(--success-color,var(--primary-color))}
      pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:400px;overflow:auto}
      .footer{font-size:12px;margin-top:20px;color:var(--secondary-text-color)}
      @media(max-width:600px){.shell{padding:9px}.panel{padding:10px}.tabs button{flex:1 1 40%}}
    `;
    style.textContent+=RN_UI_STYLES;
    style.textContent+=`
      .shell{padding:24px;--rn-accent:var(--primary-color)}
      .hero{border:1px solid var(--divider-color);border-top:4px solid var(--rn-accent);border-radius:16px;
        padding:18px 20px;background:linear-gradient(110deg,color-mix(in srgb,var(--rn-accent) 13%,var(--card-background-color)),var(--card-background-color));margin-bottom:16px}
      .hero h1{font-size:25px;gap:12px}.hero h1 ha-icon{--mdc-icon-size:30px}.hero p{margin:8px 0 0}
      .hero .rn-help-toggle{margin-top:12px}
      details.rn-help{border-left:4px solid var(--rn-cyan);background:color-mix(in srgb,var(--rn-cyan) 7%,var(--card-background-color))}
      details.rn-help ol{margin:6px 0 10px;padding-left:22px;line-height:1.5}details.rn-help li{margin:4px 0}
      details.rn-help pre{background:var(--secondary-background-color);border-radius:8px;padding:10px;font-size:13px}
      details.rn-help a{display:inline-flex;margin-top:4px;color:var(--primary-color)}
      details.rn-help h4{margin:16px 0 6px}details.rn-help ul{margin:4px 0 10px;padding-left:22px;line-height:1.5}
      .rn-example-title{font-weight:600;margin:14px 0 4px}.rn-code{position:relative}
      .rn-code pre{margin:0 0 6px}.rn-code button{font-size:12px;min-height:30px;padding:4px 10px}
      nav.tabs{padding:8px;border:1px solid var(--divider-color);border-radius:14px;background:var(--card-background-color);gap:7px}
      nav.tabs button{flex:1 1 145px;justify-content:flex-start;padding:12px 13px;line-height:1.25;border-radius:10px;min-height:47px}
      nav.tabs button.active{background:color-mix(in srgb,var(--rn-accent) 17%,var(--card-background-color));color:var(--primary-text-color);
        border:1px solid var(--rn-accent);box-shadow:inset 0 -3px 0 var(--rn-accent);font-weight:700}
      .panel{border-top:3px solid color-mix(in srgb,var(--rn-accent) 65%,var(--divider-color));border-radius:14px;
        background:linear-gradient(160deg,color-mix(in srgb,var(--rn-accent) 4%,var(--card-background-color)),var(--card-background-color))}
      .field-row{border-top:2px solid color-mix(in srgb,var(--rn-accent) 22%,var(--divider-color));background:color-mix(in srgb,var(--rn-accent) 2%,var(--card-background-color))}
      label.rn-icon-label{display:flex;gap:7px;line-height:1.4;margin-bottom:6px}label ha-icon{--mdc-icon-size:17px}
      .yaml-view{padding:0 10px;border:1px dashed var(--divider-color);border-radius:9px;background:var(--secondary-background-color)}
      .panel>button{margin:4px 6px 4px 0}.panel>a.rn-icon-label{margin:8px 12px 8px 0;padding:9px;border:1px solid var(--divider-color);border-radius:8px;text-decoration:none}
      .route-item{border-left:3px solid var(--rn-accent)}button.primary{background:color-mix(in srgb,var(--rn-teal) 16%,var(--card-background-color));color:var(--primary-text-color);border-color:var(--rn-teal);font-weight:600}
      button.primary ha-icon{color:var(--rn-teal)}.footer{display:flex;align-items:center;gap:8px}
      @media(max-width:600px){.shell{padding:10px}.hero{padding:14px}nav.tabs button{flex:1 1 130px;padding:10px}.panel{padding:12px}}
    `;
    root.append(style);
    const shell=this.element('div',null,'shell');
    shell.dataset.tone=RN_SECTIONS[this._section]?.tone||'blue';
    const hero=this.element('header',null,'hero');hero.append(this.heading('Reliable Notify','mdi:bell-check-outline',RN_SECTIONS[this._section]?.tone||'blue','h1'),
      this.element('p',this.t('Benachrichtigungen • Zustellung • Eskalation • Diagnose'),'muted'));
    const helpToggle=this.actionButton(this.helpOpen?this.t('Hilfe ausblenden'):this.t('Hilfe einblenden'),'mdi:help-circle-outline','rn-help-toggle');
    helpToggle.dataset.tone='cyan';helpToggle.setAttribute('aria-expanded',String(this.helpOpen));
    helpToggle.addEventListener('click',()=>this.setHelpOpen(!this.helpOpen));
    hero.append(helpToggle);shell.append(hero);
    const tabs=this.element('nav',null,'tabs');tabs.setAttribute('aria-label',this.t('Hauptnavigation'));
    for(const [id,name] of [['messages',this.t('Nachrichten')],['routes',this.t('Ziele & Personen')],
       ['incidents',this.t('Eskalationen')],['simulation','Simulation'],['analytics',this.t('Statistik')],['templates',this.t('Vorlagen')],['profiles',this.t('Profile & API')],['migration',this.t('Automation-Migration')],['settings',this.t('Einstellungen')]]){
      const button=this.actionButton(this.t(name),RN_SECTIONS[id].icon);button.dataset.tone=RN_SECTIONS[id].tone;
      button.addEventListener('click',()=>{this._section=id;
        for(const sibling of tabs.children){sibling.classList.remove('active');sibling.removeAttribute('aria-current');}
        button.classList.add('active');button.setAttribute('aria-current','page');shell.dataset.tone=RN_SECTIONS[id].tone;this.refreshSection();});
      if(id===this._section){button.classList.add('active');button.setAttribute('aria-current','page');}
      tabs.append(button);
    }
    shell.append(tabs);
    const content=this.element('main');content.id='content';shell.append(content);
    shell.append(rnDecorate(this.element('p',this.t('Die Verwaltungsfunktionen sind nur für Home-Assistant-Administratoren freigegeben.'),'footer'),'mdi:shield-lock-outline','slate'));
    root.append(shell);this.refreshSection();
  }
  messages(box){
    const card=this.element('reliable-notify-card');
    card.setConfig({title:this.t('Queue, Dead Letters und Archiv')});
    card.hass=this._hass;
    box.append(card);
  }
  async routes(box){
    box.append(this.element('p',this.t('Hier neue Ziele anlegen: Unter Ziele / Empfänger auf „Neues Ziel anlegen“ klicken, einen Namen vergeben, HA-Aktion und gegebenenfalls Zielentität oder Transportparameter ausfüllen und speichern. Diesen Namen anschließend als Empfänger verwenden. Das optionale Standardziel ist nur ein Fallback für Nachrichten ohne explizite Empfänger.'),'muted'));
    const status=this.element('p',this.t('Empfänger werden geladen …'));box.append(status);
    try{
      const data=await this.call('admin_inventory');status.remove();
      this.setRouteChoices(data);
      const labels=data.labels||{};
      for(const [category,label,kind] of [['recipients',this.t('Ziele / Empfänger'),'recipient'],['groups',this.t('Gruppen'),'group'],['persons',this.t('Personen'),'person']]){
        const section=this.element('section',null,'panel');
        const heading=this.heading(label,category==='recipients'?'mdi:send-check':category==='groups'?'mdi:account-group':'mdi:account',category==='recipients'?'blue':category==='groups'?'purple':'teal');section.append(heading);
        const inventory=this.element('div',null,'tabs');section.append(inventory);
        // Display name (free text) first; the internal alias is suggested from it.
        const display=this.element('input');display.name='route_label';display.placeholder=this.t('z. B. Telegram Wolfgang');display.maxLength=100;
        const displayHint=this.element('p',this.t('Frei wählbarer Name mit Leerzeichen, Umlauten und Sonderzeichen (höchstens 100 Zeichen). Er erscheint in Listen und als Name der Notify-Entität.'),'muted');
        const name=this.element('input');name.name='route_id';name.placeholder=this.t('Eindeutiger Name');
        name.maxLength=64;name.pattern='[a-z][a-z0-9_]{0,63}';
        const hint=this.element('p',this.t('Interner Name: 1–64 Zeichen, mit Kleinbuchstaben beginnen; nur a–z, 0–9 und Unterstriche (_). Beispiel: rn_kw_telegram. Großbuchstaben, Leerzeichen und Bindestriche sind nicht erlaubt.')+' '+
          this.t('Wird beim Anlegen automatisch aus dem Anzeigenamen vorgeschlagen und danach nicht mehr geändert. Automationen verwenden diesen Namen; die Entität heißt notify.reliable_<ID>.'),'muted');
        for(const [input,help] of [[display,displayHint],[name,hint]]){this._fieldId=(this._fieldId||0)+1;input.id='rn-route-input-'+this._fieldId;help.id='rn-name-help-'+this._fieldId;input.setAttribute('aria-describedby',help.id);}
        const editorBox=this.element('div');let editor;
        // autoId: last suggested alias; a different value means the admin typed an own ID.
        let loaded=null,selectedTest=null,autoId='';
        const draw=value=>{editor=this.fieldEditor(value,{defaults:this.fieldDefaults(kind),routes:category==='groups'});editorBox.replaceChildren(editor.node);section.dispatchEvent(new Event('input',{bubbles:true}));};
        const reset=()=>{loaded=null;autoId='';if(selectedTest)selectedTest.disabled=true;name.value='';display.value='';draw(category==='groups'?[]:category==='persons'
          ?{entity:'',channels:{},preferred:{}}:{action:'notify.send_message',target_entity:'',data:{}});};
        reset();
        display.addEventListener('input',()=>{if(!loaded&&name.value===autoId){autoId=rnSlug(display.value);name.value=autoId;name.dispatchEvent(new Event('input',{bubbles:true}));}});
        const result=this.element('p');result.setAttribute('role','status');
        for(const id of Object.keys(data.routes[category]||{})){
          const item=this.element('div',null,'route-item');const testResult=this.element('p');testResult.setAttribute('role','status');
          const test=this.actionButton(this.t('Test senden'),'mdi:bell-ring-outline','test');
          test.addEventListener('click',()=>this.testTarget(category,id,test,testResult));
          const button=this.actionButton(rnRouteLabel(labels,id),'mdi:pencil-outline');button.dataset.route=id;
          button.addEventListener('click',()=>this.run(result,async()=>{
            const response=await this.call('route_definition',{category,name:id});
            name.value=id;display.value=labels[id]||'';loaded=id;draw(response.definition);selectedTest.disabled=false;
          }));item.append(button,test,testResult);inventory.append(item);
        }
        const fresh=this.actionButton(category==='recipients'?this.t('Neues Ziel anlegen'):category==='groups'?this.t('Neue Gruppe anlegen'):this.t('Neue Person anlegen'),'mdi:plus','primary');fresh.addEventListener('click',()=>{reset();selectedTest.disabled=true;});inventory.append(fresh);
        section.append(this.element('p',this.t('Test senden verschickt eine echte Nachricht über die gespeicherte Konfiguration. Testmodus und Ruhezeiten bleiben aktiv. Bei Gruppen und Personen können mehrere Empfänger erreicht werden.'),'test-hint'));
        const displayLabel=rnDecorate(this.element('label',this.t('Anzeigename (Klarname)')),'mdi:card-account-details-outline','slate');displayLabel.htmlFor=display.id;
        const nameLabel=rnDecorate(this.element('label',this.t('Interner Name (ID)')),'mdi:tag-text-outline','slate');nameLabel.htmlFor=name.id;
        section.append(displayLabel,display,displayHint,nameLabel,name,hint,editorBox);
        const save=this.actionButton(this.t('Speichern'),'mdi:content-save-outline','primary');save.addEventListener('click',()=>this.run(result,async()=>{
          name.value=name.value.trim();
          if(!/^[a-z][a-z0-9_]{0,63}$/.test(name.value)){
            const example=rnSlug(name.value)||'rn_kw_telegram';
            name.setAttribute('aria-invalid','true');name.focus();
            throw Error(this.t('Ungültiger interner Name „{name}“. Nur Kleinbuchstaben, Ziffern und Unterstriche; mit einem Buchstaben beginnen, maximal 64 Zeichen. Beispiel: {example}.',{name:name.value,example}));
          }
          name.removeAttribute('aria-invalid');
          const shown=display.value.trim();
          if(shown.length>100)throw Error(this.t('Anzeigename: höchstens 100 Zeichen.'));
          if(loaded&&name.value!==loaded)throw Error(this.t('Zum Umbenennen neuen Eintrag anlegen und den alten gezielt löschen.'));
          await this.call('set_route',{category,name:name.value,definition:editor.read(),label:shown});
          this._routeChoices=null;
          loaded=name.value;labels[name.value]=shown;selectedTest.disabled=false;this.status(result,this.t('Gespeichert. Zum Aktualisieren der Liste diesen Bereich erneut öffnen.'));
        }));
        const remove=this.actionButton(this.t('Eintrag löschen'),'mdi:delete-outline','danger');remove.addEventListener('click',()=>this.run(result,async()=>{
          if(!confirm(this.t('UI-Eintrag ')+name.value+this.t(' löschen?')))return;
          await this.call('set_route',{category,name:name.value,delete:true});this._routeChoices=null;reset();
        }));
        selectedTest=this.actionButton(this.t('Gespeichertes Ziel testen'),'mdi:bell-ring-outline','test');selectedTest.disabled=true;
        selectedTest.addEventListener('click',()=>this.testTarget(category,loaded,selectedTest,result));
        name.addEventListener('input',()=>{selectedTest.disabled=!loaded||name.value!==loaded;});
        section.append(save,selectedTest,remove,result);this.yamlView(section,()=>{
          const id=name.value||rnSlug(display.value)||'neuer_eintrag',shown=display.value.trim();
          return {[category]:{[id]:editor.read()},...(shown&&shown!==id?{labels:{[id]:shown}}:{})};
        });box.append(section);
      }
    }catch(e){this.status(status,e.message,true);if(!status.parentNode)box.append(status);}
  }
  async incidents(box){
    const incidents=this.element('div',null,'panel');incidents.append(this.heading(this.t('Unbestätigte Alarme'),'mdi:alert-decagram-outline','amber','h2'));
    const list=this.element('div',this.t('Lade ...'));incidents.append(list);box.append(incidents);
    try{
      const d=await this.call('dashboard');
      list.replaceChildren();
      for(const item of d.acknowledgements||[]){
        const row=this.element('div',null,'panel');
        row.append(this.element('b',(item.title||item.ack_key)+' • '+rnValueLabel(this._hass,'priority',item.priority)));
        row.append(this.element('p',this.t('ID: ')+item.ack_key+this.t(' | Eskalationsstufe: ')+item.next_step));
        const status=this.element('p');
        for(const [action,label] of [['ack',this.t('Bestätigen')],['snooze',this.t('15 Min. verschieben')],['escalate',this.t('Sofort eskalieren')]]){
          const button=this.actionButton(label,({ack:'mdi:check-circle-outline',snooze:'mdi:clock-plus-outline',escalate:'mdi:alert-outline'})[action]||'mdi:gesture-tap-button');
          button.addEventListener('click',()=>this.run(status,async()=>{
            await this.call('incident_action',{key:item.ack_key,action});
            box.replaceChildren();await this.incidents(box);
          }));
          row.append(button);
        }
        row.append(status);list.append(row);
      }
      if(!(d.acknowledgements||[]).length)list.textContent=this.t('Keine offenen Bestätigungen.');
    }catch(e){list.textContent=e.message;}
    const wizard=this.element('div',null,'panel');wizard.append(this.heading(this.t('Testbare Eskalationskette anlegen'),'mdi:timeline-alert-outline','orange','h2'));
    await this.loadRouteChoices();
    const key=this.element('input');key.placeholder=this.t('z. B. fenster_offen');
    const target=this.element('input');target.placeholder=this.t('Interner Zielname, z. B. telegram_wolfgang');
    const delayed=this.element('input');delayed.placeholder=this.t('Interner Zielname, z. B. telegram_wolfgang');
    wizard.append(this.routeList(target),this.routeList(delayed));
    const delay=this.element('input');delay.type='number';delay.value='300';
    const message=this.element('textarea');message.placeholder=this.t('Alarmtext');
    for(const [label,field] of [[this.t('Dedup-Schlüssel'),key],[this.t('Erster Empfänger'),target],
      [this.t('Eskalationsempfänger'),delayed],[this.t('Eskalation nach Sekunden'),delay],[this.t('Nachricht'),message]])wizard.append(this.element('label',label),field);
    const response=this.element('p');
    const plan=this.actionButton(this.t('Nur simulieren'),'mdi:flask-outline','test');
    plan.addEventListener('click',()=>this.run(response,async()=>{
      const result=await this.call('simulate',{notification:{recipients:[target.value],priority:'critical',
        message:message.value}});response.textContent=JSON.stringify(result,null,2);
    }));
    const send=this.actionButton(this.t('Alarm wirklich einreihen'),'mdi:bell-alert-outline','primary');
    send.addEventListener('click',()=>this.run(response,async()=>{
      if(!confirm(this.t('Dieser Alarm wird tatsächlich verschickt. Fortfahren?')))return;
      await this._hass.callService('reliable_notify','enqueue',{
        recipients:[target.value],message:message.value,priority:'critical',
        dedup_key:key.value,acknowledgement:{required:true,
          escalation:[{after:Number(delay.value),recipients:[delayed.value]}]}});
    }));
    wizard.append(plan,send,response);box.append(wizard);

    const telegram=this.element('div',null,'panel');
    telegram.append(this.heading(this.t('Telegram: gesendete Nachricht bearbeiten / entfernen'),'mdi:send-circle-outline','blue','h2'));
    telegram.append(this.element('p',this.t('Erfordert bekannte telegram_sent-Nachrichtenkennung und passenden konfigurierten Chat. Direktaufruf ohne Queue-Retry.'),'muted'));
    const route=this.element('input');route.placeholder=this.t('z.B. telegram_wolfgang');telegram.append(this.routeList(route));
    const keyInput=this.element('input');keyInput.placeholder=this.t('Dedup-Schlüssel der versendeten Meldung');
    const edit=this.element('select');for(const action of ['edit','delete']){
      const opt=this.element('option',rnValueLabel(this._hass,'operation',action));opt.value=action;edit.append(opt);}
    const msg=this.element('textarea');msg.placeholder=this.t('Neuer Nachrichtentext (nur beim Bearbeiten)');
    telegram.append(this.element('label',this.t('Reliable-Notify-Telegram-Empfänger')),route,
      this.element('label',this.t('Dedup-Schlüssel')),keyInput,
      this.element('label',this.t('Aktion')),edit,this.element('label',this.t('Neue Nachricht')),msg);
    const telegramStatus=this.element('p');const sendTelegram=this.actionButton(this.t('Telegram-Aktion ausführen'),'mdi:send-circle-outline','primary');
    sendTelegram.addEventListener('click',()=>this.run(telegramStatus,async()=>{
      if(!route.value||!keyInput.value)throw Error(this.t('Empfänger und Dedup-Schlüssel erforderlich'));
      if(edit.value==='edit'&&!msg.value)throw Error(this.t('Neuer Text fehlt'));
      if(!confirm(this.t('Diese Aktion verändert eine bereits zugestellte Telegram-Nachricht. Fortfahren?')))return;
      const data={recipient:route.value,dedup_key:keyInput.value,operation:edit.value};
      if(edit.value==='edit')data.message=msg.value;
      await this._hass.callService('reliable_notify','telegram_lifecycle',data);
    }));
    telegram.append(sendTelegram,telegramStatus);box.append(telegram);
  }
  async simulation(box){
    const wrapper=this.element('div',null,'panel');wrapper.append(this.heading(this.t('Simulation ohne Versand'),'mdi:flask-outline','purple','h2'));
    wrapper.append(this.element('p',this.t('Zeigt Routing, Aufbewahrung und Ruhezeiten an. Keine Queue-Einträge oder Push-Nachrichten.'),'muted'));
    await this.loadRouteChoices();
    const editor=this.fieldEditor({recipients:['wolfgang_phone'],priority:'warning',
      message_type:'windows',message:this.t('Fenster seit 90 Minuten offen')},{defaults:this.fieldDefaults('template')});
    const result=this.element('pre');
    const run=this.actionButton(this.t('Versand simulieren'),'mdi:flask-outline','test');
    run.addEventListener('click',()=>this.run(result,async()=>{
      const answer=await this.call('simulate',{notification:editor.read()});
      result.textContent=JSON.stringify(answer,null,2);
    }));
    wrapper.append(editor.node,run,result);this.yamlView(wrapper,editor.read);box.append(wrapper);
  }
  async analytics(box){
    const wrapper=this.element('div',null,'panel');wrapper.append(this.heading(this.t('Transportstatistik & Systemzustand'),'mdi:chart-box-outline','cyan','h2'));
    const days=this.element('select');for(const day of [1,7,14,30]){
      const option=this.element('option',String(day)+this.t(' Tage'));option.value=day;
      if(day===7)option.selected=true;days.append(option);
    }
    const refresh=this.actionButton(this.t('Aktualisieren'),'mdi:refresh');
    const exportButton=this.actionButton(this.t('Diagnose (ohne Nachrichtentexte) exportieren'),'mdi:download-outline');
    const report=this.element('pre',this.t('Lade ...'));
    const load=async()=>{const data=await this.call('statistics',{days:Number(days.value)});
      this._lastStats=data;report.textContent=JSON.stringify(data,null,2);};
    // Refresh callback is set after the chart loader is constructed.
    exportButton.addEventListener('click',()=>{
      if(!this._lastStats)return;
      const blob=new Blob([JSON.stringify(this._lastStats,null,2)],{type:'application/json'});
      const url=URL.createObjectURL(blob);const link=this.element('a');
      link.href=url;link.download='reliable-notify-diagnostics.json';link.click();
      setTimeout(()=>URL.revokeObjectURL(url),250);
    });
    const trend=this.element('div',null,'panel');
    const title=this.heading(this.t('Tägliche Zustellungen (letzte 30 Tage)'),'mdi:chart-timeline-variant','cyan','h3');
    trend.append(title);
    const bars=this.element('div');
    bars.style.cssText='display:flex;align-items:flex-end;gap:3px;height:145px;overflow-x:auto;';
    trend.append(bars);
    const oldLoad=load;
    const loadWithChart=async()=>{
      await oldLoad();
      bars.replaceChildren();
      const daily={};
      for(const row of (this._lastStats?.daily_trends||[])){
        const day=row.day;daily[day]=(daily[day]||0)+Number(row.sent||0);
      }
      const points=Object.entries(daily).sort(([a],[b])=>a.localeCompare(b)).slice(-30);
      const maximum=Math.max(1,...points.map(([,value])=>value));
      for(const [day,value] of points){
        const bar=this.element('div');
        bar.title=day+': '+value+this.t(' versendet');
        bar.style.cssText='flex:1 0 8px;min-width:8px;max-width:24px;background:var(--primary-color);border-radius:4px 4px 0 0;';
        bar.style.height=Math.max(2,Math.round(value/maximum*130))+'px';
        bars.append(bar);
      }
      if(!points.length)bars.append(this.element('p',this.t('Noch keine Tagesstatistiken'),'muted'));
    };
    refresh.onclick=()=>this.run(report,loadWithChart);
    wrapper.append(days,refresh,exportButton,report);box.append(wrapper);
    box.append(trend);
    await this.run(report,loadWithChart);
    await this.run(report,load);
  }
  async namedSettings(box,{title,kind,load,save,property}){
    const section=this.element('section',null,'panel');section.append(this.heading(title,kind==='template'?'mdi:text-box-multiple-outline':'mdi:shield-account-outline',kind==='template'?'indigo':'purple'));box.append(section);
    const status=this.element('p',this.t('Lade …'));section.append(status);
    try{
      const data=await this.call(load);
      await this.loadRouteChoices();
      const defaults=this.fieldDefaults(kind);
      const rows=[];const body=this.element('div');section.append(body);
      const add=(name,value)=>{
        const row=this.element('div',null,'panel');const input=this.element('input');input.value=name;input.placeholder='Name';
        const fields=this.fieldEditor(value,{defaults});
        row.append(rnDecorate(this.element('label','Name'),'mdi:tag-text-outline','slate'),input,fields.node);
        const record={input,fields};rows.push(record);
        const remove=this.actionButton(this.t('Entfernen'),'mdi:minus-circle-outline','danger');remove.addEventListener('click',()=>{
          rows.splice(rows.indexOf(record),1);row.remove();section.dispatchEvent(new Event('input',{bubbles:true}));});
        row.append(remove);body.append(row);
      };
      Object.entries(data[property]||{}).forEach(([name,value])=>add(name,value));
      const read=()=>{
        const result={};for(const row of rows){const name=row.input.value.trim();
          if(!/^[a-z][a-z0-9_]{0,63}$/.test(name))throw Error(this.t('Name: Kleinbuchstaben, Ziffern und Unterstriche; mit Buchstaben beginnen.'));
          if(Object.hasOwn(result,name))throw Error(this.t('Doppelter Name: ')+name);
          Object.defineProperty(result,name,{value:row.fields.read(),enumerable:true});
        }return result;
      };
      const newButton=this.actionButton(this.t('Neu anlegen'),'mdi:plus','primary');newButton.addEventListener('click',()=>{
        add('',kind==='template'?{message:'',priority:'info'}:{priority:'info'});
        section.dispatchEvent(new Event('input',{bubbles:true}));});
      const submit=this.actionButton(this.t('Speichern'),'mdi:content-save-outline','primary');submit.addEventListener('click',()=>this.run(status,()=>this.call(save,{[property]:read()})));
      section.append(newButton,submit);this.yamlView(section,read);this.status(status,'');
      return data;
    }catch(e){this.status(status,e.message,true);return null;}
  }
  async templates(box){
    await this.namedSettings(box,{title:this.t('Wiederverwendbare Vorlagen'),kind:'template',load:'templates',save:'set_templates',property:'templates'});
  }
  async profiles(box){
    const data=await this.namedSettings(box,{title:this.t('Benachrichtigungsprofile'),kind:'profile',load:'profiles',save:'set_profiles',property:'profiles'});
    if(!data)return;
    const api=this.element('section',null,'panel');api.append(this.heading(this.t('Externe API'),'mdi:api','purple','h2'));
    api.append(this.element('p',this.t('Nur HA-Administratoren mit Bearer-Token und ausdrücklich freigegebene Empfänger.'),'muted'));
    const editor=this.fieldEditor({enabled:Boolean(data.external_api_enabled),
      recipients:data.external_api_recipients||[],rate:data.external_api_rate||30},{fixed:true});
    const status=this.element('p'),save=this.actionButton(this.t('API-Einstellungen speichern'),'mdi:content-save-outline','primary');
    save.addEventListener('click',()=>this.run(status,()=>this.call('set_external_api',editor.read())));
    api.append(editor.node,save,status);this.yamlView(api,editor.read);box.append(api);
  }

  // Codes from migration_advisor/migration_scan/migration_apply; English originals stay in the JSON export.
  migrationText(kind,code){
    const texts={
      reason:{templated:'Aktion oder Daten mit Vorlage (service_template/data_template)',non_object_data:'Die Daten der Aktion sind keine Feldliste',
        complex_target:'Ziel nutzt Bereiche, Geräte oder ist dynamisch',advanced_fields:'Aktion enthält erweiterte Felder (z. B. response_variable)',
        entity_in_data:'Notify-Entität steht in data statt in target',telegram_ambiguous:'Telegram-Ziel nicht eindeutig (keine oder mehrere Chat-Angaben)',
        telegram_target:'Telegram-Aktion hat zusätzlich ein target',legacy_target:'Klassische Notify-Aktion hat zusätzlich ein target',
        no_static_destination:'Kein eindeutiges festes Ziel (z. B. notify.notify)',dynamic_destination:'Ziel ist dynamisch (Vorlage) oder hat mehrere Empfänger',
        no_route:'Für dieses Ziel ist noch kein Reliable-Notify-Ziel angelegt',multiple_routes:'Mehrere Reliable-Notify-Ziele passen zu diesem Ziel',
        transport_data:'Zusätzliche Transportdaten (z. B. Bilder, Buttons) müssen geprüft werden',missing_message:'Aktion enthält keine Nachricht',
        yaml_tags:'Verwendet !secret, !include o. Ä. – bitte manuell übernehmen',unambiguous:'Eindeutiges festes Ziel – Vorschlag kann übernommen werden'},
      file:{symlink:'Symbolischer Link – aus Sicherheitsgründen nicht geprüft',too_large:'Datei größer als 4 MiB – nicht geprüft',
        yaml_syntax:'YAML-Syntaxfehler',encoding:'Keine UTF-8-Textdatei',not_automation_yaml:'Enthält keine Automationen, Skripte oder Pakete',
        read_failed:'Datei konnte nicht gelesen werden'},
      apply:{approval_required:'Ausdrückliche Bestätigung fehlt.',not_eligible:'Diese Datei kann nicht automatisch geändert werden.',
        packages_only:'Automatische Änderungen nur für packages/*.yaml.',too_large:'Datei zu groß.',
        file_changed:'Datei wurde seit der Analyse geändert – bitte erneut analysieren.',not_unique:'Vorschlag ist nicht mehr eindeutig – bitte erneut analysieren.',
        no_change:'Keine Änderung nötig.',manual_edit:'Kommentare oder YAML-Anker in dieser Aktion – bitte manuell ändern.',
        invalid_path:'Aktion wurde in der Datei nicht gefunden – bitte erneut analysieren.',not_action:'Diese Stelle ist keine einzelne Notify-Aktion.',
        yaml_syntax:'YAML-Syntaxfehler in der Datei.'}};
    const text=texts[kind]?.[code];
    return text?this.t(text):null;
  }
  async migration(box){
    const wrapper=this.element('div',null,'panel');
    wrapper.append(this.heading(this.t('Bestehende Automationen prüfen'),'mdi:source-branch','orange','h2'));
    wrapper.append(this.element('p',this.t('Liest automations.yaml, scripts.yaml sowie YAML-Dateien in packages/, automations/ und scripts/ ausschließlich lesend. Es werden keine Dateien verändert, solange du nicht ausdrücklich eine einzelne Paket-Änderung übernimmst.'),'muted'));
    const button=this.actionButton(this.t('Benachrichtigungen analysieren'),'mdi:file-search-outline','primary');
    const result=this.element('div');result.setAttribute('role','status');
    const download=this.actionButton(this.t('Vorschläge als JSON herunterladen'),'mdi:download-outline');
    download.disabled=true;
    let last=null;
    button.addEventListener('click',()=>this.run(result,async()=>{
      this.status(result,this.t('Lade …'));
      const [report]=await Promise.all([this.call('migration_scan'),this.loadRouteChoices()]);
      const labels=this._routeLabels||{};
      last=report;download.disabled=false;
      result.replaceChildren();result.className='';
      const files=report.files||[];
      result.append(this.element('p',this.t('{proposed} direkte Vorschläge • {manual} manuell zu prüfen • {files} Dateien geprüft',
        {proposed:report.proposed||0,manual:report.manual||0,files:files.filter(f=>!f.skipped).length})));
      const skipped=files.filter(f=>f.skipped);
      if(skipped.length)result.append(this.element('p',this.t('Nicht vorhanden – übersprungen')+': '+skipped.map(f=>f.file).join(', '),'muted'));
      for(const file of files.filter(f=>!f.skipped)){
        const section=this.element('div',null,'panel');
        const name=file.relative_file||file.file;
        const proposals=file.proposals||[];
        const failed=Boolean(file.error_code||file.error);
        let summary;
        if(failed)summary=(this.migrationText('file',file.error_code)||file.error)+(file.line?' '+this.t('in Zeile {line}',{line:file.line}):'');
        else summary=proposals.length?this.t('{count} Treffer',{count:proposals.length}):this.t('Keine Benachrichtigungsaktionen gefunden.');
        section.append(this.heading(name+' — '+summary,failed?'mdi:file-alert-outline':'mdi:file-document-outline',failed?'red':'orange','h3'));
        const editable=Boolean(file.sha256&&/^packages\/[^/]+\.ya?ml$/.test(file.relative_file||''));
        for(const item of proposals){
          const proposed=item.status==='proposed';
          const details=this.element('details');
          const route=item.route||item.suggested_route;
          const title=this.element('summary',(item.automation||item.path)+' • '+item.source+
            ' → '+(route?rnRouteLabel(labels,route):this.t('manuelle Prüfung')));
          rnDecorate(title,proposed?'mdi:check-circle-outline':'mdi:alert-circle-outline',proposed?'teal':'amber');
          details.append(title,this.element('p',this.migrationText('reason',item.reason_code)||item.reason));
          if(item.reason_code==='no_route')details.append(this.element('p',this.t('Tipp: Unter „Ziele & Personen“ ein passendes Ziel anlegen und erneut analysieren.'),'muted'));
          if(item.replacement){
            if(item.preview_diff){
              const diff=this.element('pre',item.preview_diff);
              diff.style.whiteSpace='pre-wrap';details.append(diff);
            }else details.append(this.element('pre',JSON.stringify(item.replacement,null,2)));
            if(editable){
              const apply=this.actionButton(this.t('Einzelne Änderung mit Backup übernehmen'),'mdi:content-save-check-outline','primary');
              const status=this.element('p');status.setAttribute('role','status');
              apply.addEventListener('click',()=>this.run(status,async()=>{
                if(!confirm(this.t('Nur dieser EINE Paket-Eintrag wird geändert. Backup wird erstellt. Keine automatische HA-Neuladung. Fortfahren?')))return;
                try{
                  const response=await this.call('migration_apply',{
                    file:file.relative_file,sha256:file.sha256,
                    path:item.path,confirmation:'APPLY_SINGLE_CHANGE'
                  });
                  status.textContent=this.t('Geändert. Backup: ')+response.backup+
                     this.t(' — Paket-Automationen über HA neu laden.');
                  apply.disabled=true;
                }catch(e){
                  const text=e?.code==='migration_failed'?this.migrationText('apply',e.message):null;
                  throw text?Error(this.t('Migration fehlgeschlagen:')+' '+text):e;
                }
              }));
              details.append(apply,status);
            }else details.append(this.element('p',this.t('Vorschlag im HA-Automationseditor übernehmen (diese Datei wird von HA verwaltet).'),'muted'));
          }
          section.append(details);
        }
        result.append(section);
      }
    }));
    download.addEventListener('click',()=>{
      if(!last)return;
      const blob=new Blob([JSON.stringify(last,null,2)],{type:'application/json'});
      const url=URL.createObjectURL(blob);const link=this.element('a');
      link.href=url;link.download='reliable-notify-migration-proposals.json';link.click();
      setTimeout(()=>URL.revokeObjectURL(url),300);
    });
    wrapper.append(button,download,result);box.append(wrapper);
  }
  async settings(box){
    const intro=this.element('div',null,'panel');intro.append(this.heading(this.t('Einstellungen'),'mdi:cog-outline','slate','h2'),
      this.element('p',this.t('Alle Betriebsoptionen stehen gemeinsam im HA-Konfigurationsdialog. Neue Ziele und Empfänger unter „Ziele & Personen“ anlegen; Profile und Vorlagen in den gleichnamigen Bereichen bearbeiten.'),'muted'));
    const open=rnDecorate(this.element('a',this.t('Alle Integrationsoptionen öffnen')),'mdi:open-in-new','slate');open.href='/config/integrations/integration/reliable_notify';intro.append(open);
    const targets=this.actionButton(this.t('Neues Ziel anlegen'),'mdi:plus','primary');targets.addEventListener('click',()=>{this._section='routes';this._rendered=false;this.shadowRoot.replaceChildren();this.render();});intro.append(targets);box.append(intro);
    const status=this.element('p',this.t('Lade …'));box.append(status);
    try{
      const [d,stats]=await Promise.all([this.call('dashboard'),this.call('statistics')]);
      const specs=[
        [this.t('Wiederholungen'),d.policies,'set_retry_policies','policies'],
        [this.t('Archiv-Aufbewahrung (Tage)'),d.retention,'set_archive_retention','retention'],
        [this.t('Ruhezeiten, Limits und Digest'),d.smart,'set_smart_settings',null],
        [this.t('Testmodus und Transport-Logging'),{test_mode:stats.test_mode||'off',
          test_recipients:stats.test_recipients||[],transport_logging:Object.fromEntries(
            ['telegram','smtp','companion','notify','webhook','ntfy','gotify'].map(k=>[k,stats.transport_logging?.[k]||'warning']))},'settings_v2',null]
      ];
      for(const [title,initial,method,property] of specs){
        const section=this.element('section',null,'panel');section.append(this.heading(title,({set_retry_policies:'mdi:reload',set_archive_retention:'mdi:archive-clock-outline',set_smart_settings:'mdi:weather-night',settings_v2:'mdi:flask-outline'})[method]||'mdi:cog-outline','slate'));
        const editor=this.fieldEditor(initial,{fixed:true});
        const result=this.element('p'),button=this.actionButton(this.t('Speichern'),'mdi:content-save-outline','primary');
        button.addEventListener('click',()=>this.run(result,()=>this.call(method,property?{[property]:editor.read()}:editor.read())));
        section.append(editor.node,button,result);this.yamlView(section,editor.read);box.append(section);
      }this.status(status,'');
    }catch(e){this.status(status,e.message,true);}
  }

}
if(!customElements.get('reliable-notify-panel'))customElements.define('reliable-notify-panel',ReliableNotifyPanel);
