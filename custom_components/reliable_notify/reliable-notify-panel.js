/* Reliable Notify Admin Panel 3.1 — no external CDN/dependencies. */
import './reliable-notify-card.js';

class ReliableNotifyPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:'open'});
    this._section='messages';
    this._rendered=false;
    this._hass=null;
  }
  set hass(value) {
    this._hass=value;
    const card=this.shadowRoot.querySelector('reliable-notify-card');
    if(card)card.hass=value;
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
  async call(type,other={}){
    if(!this._hass)throw Error('Home Assistant unavailable');
    return this._hass.callWS({type:'reliable_notify/'+type,...other});
  }
  status(node,value,error=false){node.textContent=value;node.className=error?'error':'status';}
  async run(node, fn){
    const oldText=node.textContent;
    try {
      await fn();
      if(node.textContent===oldText)this.status(node,'Erfolgreich');
    }catch(e){this.status(node,e.message||String(e),true);}
  }
  fieldLabel(key){
    return ({action:'HA-Aktion',target_entity:'Notify-Zielentität',data:'Transportparameter',
      entity:'Person-Entität',channels:'Kanäle und Empfänger',preferred:'Bevorzugte Kanäle nach Priorität',
      preferred_by_zone:'Kanäle nach Zone und Priorität',priority:'Priorität',recipients:'Empfänger',
      message:'Nachricht',title:'Titel',message_type:'Nachrichtentyp',archive:'Archivierung',
      archive_days:'Aufbewahrung (Tage)',ttl:'Gültigkeit (Sekunden)',strategy:'Zustellstrategie',
      only_if:'Nur senden, wenn',entity_id:'Entität',state:'Zustand',test_mode:'Testmodus',
      quiet_hours:'Ruhezeiten',transport_logging:'Loglevel je Transport',test_recipients:'Betroffene Testempfänger (leer = alle)',rate:'Aufträge pro Minute und Benutzer',acknowledgement:'Bestätigung und Eskalation',required:'Bestätigung erforderlich',
      escalation:'Eskalationsstufen',after:'Nach Sekunden',enabled:'Aktiviert',start:'Beginn (HH:MM)',
      end:'Ende (HH:MM)',allow_priorities:'Während Ruhezeit erlaubte Prioritäten',
      rate_limit_per_minute:'Versuche pro Minute und Ziel',digest_window_seconds:'Digest-Zeitfenster (Sekunden)',
      max_attempts:'Maximale Versuche (0 = unbegrenzt)',base_seconds:'Basisabstand (Sekunden)',
      max_delay:'Maximaler Abstand (Sekunden)',info:'Information',warning:'Warnung',critical:'Kritisch',
      chat_id:'Telegram-Chat-ID',config_entry_id:'Telegram-Konfiguration',url:'URL',topic:'Thema',
      token:'Token',base_url:'HTTPS-Basis-URL',allow_private:'Private Zieladressen erlauben',headers:'HTTP-Header',method:'HTTP-Methode',parse_mode:'Telegram-Textformat',
      disable_notification:'Lautlos senden',mobile:'Mobilgerät',email:'E-Mail',telegram:'Telegram',
      smtp:'SMTP',companion:'Companion-App',notify:'HA Notify',webhook:'Webhook',ntfy:'ntfy',gotify:'Gotify'
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
    details.append(this.element('summary','YAML-Ansicht einblenden (nur Vorschau, ggf. mit Zugangsdaten)'));
    const preview=this.element('pre');details.append(preview);parent.append(details);
    const refresh=()=>{if(details.open){try{preview.textContent=this.yaml(read());}
      catch(e){preview.textContent=e.message;}}};
    details.addEventListener('toggle',refresh);
    parent.addEventListener('input',refresh);parent.addEventListener('change',refresh);
    return refresh;
  }
  fieldEditor(initial,{defaults={},fixed=false,key='',choices=null}={}){
    const host=this.element('div',null,'field-editor');
    if(initial===null||typeof initial!=='object'){
      const enums={priority:['info','warning','critical'],archive:['keep','delete_after_send'],
        strategy:['always','replace','digest'],test_mode:['off','stage']};
      const options=choices||enums[key];
      const input=this.element(options?'select':key==='message'||(typeof initial==='string'&&initial.includes('\n'))?'textarea':'input');
      if(options){for(const value of new Set([...options,initial])){
        const opt=this.element('option',String(value));opt.value=value;input.append(opt);}}
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
      return {node:host,read:()=>{
        if(!input.checkValidity())throw Error(this.fieldLabel(key)+': '+input.validationMessage);
        if(type==='null')return null;
        if(type==='boolean')return input.checked;
        if(type==='number'){
          if(input.value.trim()===''||!Number.isFinite(Number(input.value)))throw Error(this.fieldLabel(key)+': Zahl erforderlich');
          return Number(input.value);
        }
        return input.value;
      }};
    }
    const array=Array.isArray(initial),rows=[];
    const fields=this.element('div',null,array?'list-fields':'grid');host.append(fields);
    const add=(name,value)=>{
      if(!array&&rows.some(r=>r.name===name))throw Error('Feld existiert bereits');
      const row=this.element('div',null,'field-row');
      const label=this.element('label',array?'Eintrag':this.fieldLabel(name));
      const child=this.fieldEditor(value,{key:array?'':name,fixed:fixed&&value!==null&&typeof value==='object'&&!Array.isArray(value),choices:key==='transport_logging'?['off','error','warning','info','debug']:key==='allow_priorities'?['info','warning','critical']:null,defaults:!array&&name==='preferred'
        ?{info:[],warning:[],critical:[]}:!array&&name==='data'
        ?{chat_id:0,config_entry_id:'',entity_id:'',base_url:'',allow_private:false,url:'',topic:'',token:'',headers:{},method:'POST',parse_mode:'HTML',disable_notification:false}
        :!array&&name==='only_if'?{entity_id:'',state:''}:{}});
      const control=child.node.querySelector('input,textarea,select');
      if(control){if(!control.id){this._fieldId=(this._fieldId||0)+1;control.id='rn-field-'+this._fieldId;}label.htmlFor=control.id;}
      row.append(label,child.node);const record={name,child,row};rows.push(record);
      if(!fixed){const remove=this.element('button','Entfernen');remove.type='button';
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
      else name.placeholder='Name des Feldes / Kanals / der Zone';
      const custom=this.element('input');custom.placeholder='Eigenes Transportfeld';custom.hidden=true;
      if(key==='data'){const opt=this.element('option','Eigenes Transportfeld …');opt.value='__custom';name.append(opt);
        name.addEventListener('change',()=>{custom.hidden=name.value!=='__custom';});}
      const type=this.element('select');
      for(const [value,label] of [['text','Text'],['number','Zahl'],['boolean','Schalter'],['list','Liste'],['object','Felder']]){
        const opt=this.element('option',label);opt.value=value;type.append(opt);}
      const button=this.element('button',array?'Eintrag hinzufügen':'Feld hinzufügen');button.type='button';
      const error=this.element('p',null,'error');
      button.addEventListener('click',()=>{
        try{
          const k=array?String(rows.length):(name.value==='__custom'?custom.value:name.value).trim();
          if(!k)throw Error('Name erforderlich');
          if(['__proto__','constructor','prototype'].includes(k))throw Error('Ungültiger Name');
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
      button:hover{filter:brightness(.94)}button.active{background:var(--primary-color);color:var(--text-primary-color)}
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
    root.append(style);
    const shell=this.element('div',null,'shell');
    shell.append(this.element('h1','🔔 Reliable Notify'));
    shell.append(this.element('p','Benachrichtigungen • Zustellung • Eskalation • Diagnose','muted'));
    const tabs=this.element('nav',null,'tabs');
    for(const [id,name] of [['messages','Nachrichten'],['routes','Ziele & Personen'],
       ['incidents','Eskalationen'],['simulation','Simulation'],['analytics','Statistik'],['templates','Vorlagen'],['profiles','Profile & API'],['migration','Automation-Migration'],['settings','Einstellungen']]){
      const button=this.element('button',name);
      button.addEventListener('click',()=>{this._section=id;
        for(const sibling of tabs.children)sibling.classList.remove('active');
        button.classList.add('active');this.refreshSection();});
      if(id===this._section)button.classList.add('active');
      tabs.append(button);
    }
    shell.append(tabs);
    const content=this.element('main');content.id='content';shell.append(content);
    shell.append(this.element('p','Die Verwaltungsfunktionen sind nur für Home-Assistant-Administratoren freigegeben.','footer'));
    root.append(shell);this.refreshSection();
  }
  messages(box){
    const card=this.element('reliable-notify-card');
    card.setConfig({title:'Queue, Dead Letters und Archiv'});
    card.hass=this._hass;
    box.append(card);
  }
  async routes(box){
    box.append(this.element('p','Hier neue Ziele anlegen: Unter Ziele / Empfänger auf „Neues Ziel anlegen“ klicken, einen Namen vergeben, HA-Aktion und gegebenenfalls Zielentität oder Transportparameter ausfüllen und speichern. Diesen Namen anschließend als Empfänger verwenden. Das optionale Standardziel ist nur ein Fallback für Nachrichten ohne explizite Empfänger.','muted'));
    const status=this.element('p','Empfänger werden geladen …');box.append(status);
    try{
      const data=await this.call('admin_inventory');status.remove();
      for(const [category,label,kind] of [['recipients','Ziele / Empfänger','recipient'],['groups','Gruppen','group'],['persons','Personen','person']]){
        const section=this.element('section',null,'panel');section.append(this.element('h2',label));
        const inventory=this.element('div',null,'tabs');section.append(inventory);
        const name=this.element('input');name.placeholder='Eindeutiger Name';
        const editorBox=this.element('div');let editor;
        let loaded=null;
        const draw=value=>{editor=this.fieldEditor(value,{defaults:this.fieldDefaults(kind)});editorBox.replaceChildren(editor.node);section.dispatchEvent(new Event('input',{bubbles:true}));};
        const reset=()=>{loaded=null;name.value='';draw(category==='groups'?[]:category==='persons'
          ?{entity:'',channels:{},preferred:{}}:{action:'notify.send_message',target_entity:'',data:{}});};
        reset();
        const result=this.element('p');
        for(const id of Object.keys(data.routes[category]||{})){
          const button=this.element('button',id);button.addEventListener('click',()=>this.run(result,async()=>{
            const response=await this.call('route_definition',{category,name:id});
            name.value=id;loaded=id;draw(response.definition);
          }));inventory.append(button);
        }
        const fresh=this.element('button',category==='recipients'?'Neues Ziel anlegen':category==='groups'?'Neue Gruppe anlegen':'Neue Person anlegen');fresh.addEventListener('click',reset);inventory.append(fresh);
        section.append(this.element('label','Name'),name,editorBox);
        const save=this.element('button','Speichern');save.addEventListener('click',()=>this.run(result,async()=>{
          if(loaded&&name.value!==loaded)throw Error('Zum Umbenennen neuen Eintrag anlegen und den alten gezielt löschen.');
          await this.call('set_route',{category,name:name.value,definition:editor.read()});
          this.status(result,'Gespeichert. Zum Aktualisieren der Liste diesen Bereich erneut öffnen.');
        }));
        const remove=this.element('button','Eintrag löschen');remove.addEventListener('click',()=>this.run(result,async()=>{
          if(!confirm('UI-Eintrag '+name.value+' löschen?'))return;
          await this.call('set_route',{category,name:name.value,delete:true});reset();
        }));section.append(save,remove,result);this.yamlView(section,()=>({[category]:{[name.value||'neuer_eintrag']:editor.read()}}));box.append(section);
      }
    }catch(e){this.status(status,e.message,true);if(!status.parentNode)box.append(status);}
  }
  async incidents(box){
    const incidents=this.element('div',null,'panel');incidents.append(this.element('h2','Unbestätigte Alarme'));
    const list=this.element('div','Lade ...');incidents.append(list);box.append(incidents);
    try{
      const d=await this.call('dashboard');
      list.replaceChildren();
      for(const item of d.acknowledgements||[]){
        const row=this.element('div',null,'panel');
        row.append(this.element('b',(item.title||item.ack_key)+' • '+item.priority));
        row.append(this.element('p','ID: '+item.ack_key+' | Eskalationsstufe: '+item.next_step));
        const status=this.element('p');
        for(const [action,label] of [['ack','Bestätigen'],['snooze','15 Min. verschieben'],['escalate','Sofort eskalieren']]){
          const button=this.element('button',label);
          button.addEventListener('click',()=>this.run(status,async()=>{
            await this.call('incident_action',{key:item.ack_key,action});
            box.replaceChildren();await this.incidents(box);
          }));
          row.append(button);
        }
        row.append(status);list.append(row);
      }
      if(!(d.acknowledgements||[]).length)list.textContent='Keine offenen Bestätigungen.';
    }catch(e){list.textContent=e.message;}
    const wizard=this.element('div',null,'panel');wizard.append(this.element('h2','Testbare Eskalationskette anlegen'));
    const key=this.element('input');key.placeholder='alarm_kennung';
    const target=this.element('input');target.placeholder='initial_recipient';
    const delayed=this.element('input');delayed.placeholder='fallback_recipient';
    const delay=this.element('input');delay.type='number';delay.value='300';
    const message=this.element('textarea');message.placeholder='Alarmtext';
    for(const [label,field] of [['Dedup-Schlüssel',key],['Erster Empfänger',target],
      ['Eskalationsempfänger',delayed],['Eskalation nach Sekunden',delay],['Nachricht',message]])wizard.append(this.element('label',label),field);
    const response=this.element('p');
    const plan=this.element('button','Nur simulieren');
    plan.addEventListener('click',()=>this.run(response,async()=>{
      const result=await this.call('simulate',{notification:{recipients:[target.value],priority:'critical',
        message:message.value}});response.textContent=JSON.stringify(result,null,2);
    }));
    const send=this.element('button','Alarm wirklich einreihen');
    send.addEventListener('click',()=>this.run(response,async()=>{
      if(!confirm('Dieser Alarm wird tatsächlich verschickt. Fortfahren?'))return;
      await this._hass.callService('reliable_notify','enqueue',{
        recipients:[target.value],message:message.value,priority:'critical',
        dedup_key:key.value,acknowledgement:{required:true,
          escalation:[{after:Number(delay.value),recipients:[delayed.value]}]}});
    }));
    wizard.append(plan,send,response);box.append(wizard);

    const telegram=this.element('div',null,'panel');
    telegram.append(this.element('h2','Telegram: gesendete Nachricht bearbeiten / entfernen'));
    telegram.append(this.element('p','Erfordert bekannte telegram_sent-Nachrichtenkennung und passenden konfigurierten Chat. Direktaufruf ohne Queue-Retry.','muted'));
    const route=this.element('input');route.placeholder='z.B. telegram_wolfgang';
    const keyInput=this.element('input');keyInput.placeholder='Dedup-Schlüssel der versendeten Meldung';
    const edit=this.element('select');for(const action of ['edit','delete']){
      const opt=this.element('option',action);opt.value=action;edit.append(opt);}
    const msg=this.element('textarea');msg.placeholder='Neuer Nachrichtentext (nur bei edit)';
    telegram.append(this.element('label','Reliable-Notify-Telegram-Empfänger'),route,
      this.element('label','Dedup-Schlüssel'),keyInput,
      this.element('label','Aktion'),edit,this.element('label','Neue Nachricht'),msg);
    const telegramStatus=this.element('p');const sendTelegram=this.element('button','Telegram-Aktion ausführen');
    sendTelegram.addEventListener('click',()=>this.run(telegramStatus,async()=>{
      if(!route.value||!keyInput.value)throw Error('Empfänger und Dedup-Schlüssel erforderlich');
      if(edit.value==='edit'&&!msg.value)throw Error('Neuer Text fehlt');
      if(!confirm('Diese Aktion verändert eine bereits zugestellte Telegram-Nachricht. Fortfahren?'))return;
      const data={recipient:route.value,dedup_key:keyInput.value,operation:edit.value};
      if(edit.value==='edit')data.message=msg.value;
      await this._hass.callService('reliable_notify','telegram_lifecycle',data);
    }));
    telegram.append(sendTelegram,telegramStatus);box.append(telegram);
  }
  async simulation(box){
    const wrapper=this.element('div',null,'panel');wrapper.append(this.element('h2','Simulation ohne Versand'));
    wrapper.append(this.element('p','Zeigt Routing, Aufbewahrung und Ruhezeiten an. Keine Queue-Einträge oder Push-Nachrichten.','muted'));
    const editor=this.fieldEditor({recipients:['wolfgang_phone'],priority:'warning',
      message_type:'windows',message:'Fenster seit 90 Minuten offen'},{defaults:this.fieldDefaults('template')});
    const result=this.element('pre');
    const run=this.element('button','Versand simulieren');
    run.addEventListener('click',()=>this.run(result,async()=>{
      const answer=await this.call('simulate',{notification:editor.read()});
      result.textContent=JSON.stringify(answer,null,2);
    }));
    wrapper.append(editor.node,run,result);this.yamlView(wrapper,editor.read);box.append(wrapper);
  }
  async analytics(box){
    const wrapper=this.element('div',null,'panel');wrapper.append(this.element('h2','Transportstatistik & Systemzustand'));
    const days=this.element('select');for(const day of [1,7,14,30]){
      const option=this.element('option',String(day)+' Tage');option.value=day;
      if(day===7)option.selected=true;days.append(option);
    }
    const refresh=this.element('button','Aktualisieren');
    const exportButton=this.element('button','Diagnose (ohne Nachrichtentexte) exportieren');
    const report=this.element('pre','Lade ...');
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
    const title=this.element('h3','Tägliche Zustellungen (letzte 30 Tage)');
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
        bar.title=day+': '+value+' versendet';
        bar.style.cssText='flex:1 0 8px;min-width:8px;max-width:24px;background:var(--primary-color);border-radius:4px 4px 0 0;';
        bar.style.height=Math.max(2,Math.round(value/maximum*130))+'px';
        bars.append(bar);
      }
      if(!points.length)bars.append(this.element('p','Noch keine Tagesstatistiken','muted'));
    };
    refresh.onclick=()=>this.run(report,loadWithChart);
    wrapper.append(days,refresh,exportButton,report);box.append(wrapper);
    box.append(trend);
    await this.run(report,loadWithChart);
    await this.run(report,load);
  }
  async namedSettings(box,{title,kind,load,save,property}){
    const section=this.element('section',null,'panel');section.append(this.element('h2',title));box.append(section);
    const status=this.element('p','Lade …');section.append(status);
    try{
      const data=await this.call(load);
      const defaults=this.fieldDefaults(kind);
      const rows=[];const body=this.element('div');section.append(body);
      const add=(name,value)=>{
        const row=this.element('div',null,'panel');const input=this.element('input');input.value=name;input.placeholder='Name';
        const fields=this.fieldEditor(value,{defaults});
        row.append(this.element('label','Name'),input,fields.node);
        const record={input,fields};rows.push(record);
        const remove=this.element('button','Entfernen');remove.addEventListener('click',()=>{
          rows.splice(rows.indexOf(record),1);row.remove();section.dispatchEvent(new Event('input',{bubbles:true}));});
        row.append(remove);body.append(row);
      };
      Object.entries(data[property]||{}).forEach(([name,value])=>add(name,value));
      const read=()=>{
        const result={};for(const row of rows){const name=row.input.value.trim();
          if(!/^[a-z][a-z0-9_]{0,63}$/.test(name))throw Error('Name: Kleinbuchstaben, Ziffern und Unterstriche; mit Buchstaben beginnen.');
          if(Object.hasOwn(result,name))throw Error('Doppelter Name: '+name);
          Object.defineProperty(result,name,{value:row.fields.read(),enumerable:true});
        }return result;
      };
      const newButton=this.element('button','Neu anlegen');newButton.addEventListener('click',()=>{
        add('',kind==='template'?{message:'',priority:'info'}:{priority:'info'});
        section.dispatchEvent(new Event('input',{bubbles:true}));});
      const submit=this.element('button','Speichern');submit.addEventListener('click',()=>this.run(status,()=>this.call(save,{[property]:read()})));
      section.append(newButton,submit);this.yamlView(section,read);this.status(status,'');
      return data;
    }catch(e){this.status(status,e.message,true);return null;}
  }
  async templates(box){
    await this.namedSettings(box,{title:'Wiederverwendbare Vorlagen',kind:'template',load:'templates',save:'set_templates',property:'templates'});
  }
  async profiles(box){
    const data=await this.namedSettings(box,{title:'Benachrichtigungsprofile',kind:'profile',load:'profiles',save:'set_profiles',property:'profiles'});
    if(!data)return;
    const api=this.element('section',null,'panel');api.append(this.element('h2','Externe API'));
    api.append(this.element('p','Nur HA-Administratoren mit Bearer-Token und ausdrücklich freigegebene Empfänger.','muted'));
    const editor=this.fieldEditor({enabled:Boolean(data.external_api_enabled),
      recipients:data.external_api_recipients||[],rate:data.external_api_rate||30},{fixed:true});
    const status=this.element('p'),save=this.element('button','API-Einstellungen speichern');
    save.addEventListener('click',()=>this.run(status,()=>this.call('set_external_api',editor.read())));
    api.append(editor.node,save,status);this.yamlView(api,editor.read);box.append(api);
  }

  async migration(box){
    const wrapper=this.element('div',null,'panel');
    wrapper.append(this.element('h2','Bestehende Automationen prüfen'));
    wrapper.append(this.element('p','Liest automations.yaml und scripts.yaml ausschließlich lesend. Es werden keine Dateien, Automationen oder Skripte verändert. Vorschläge bei Mehrdeutigkeiten sind ausdrücklich zu prüfen.','muted'));
    const button=this.element('button','Benachrichtigungen analysieren');
    const result=this.element('div');
    const download=this.element('button','Vorschläge als JSON herunterladen');
    download.disabled=true;
    let last=null;
    button.addEventListener('click',()=>this.run(result,async()=>{
      const report=await this.call('migration_scan');
      last=report;download.disabled=false;
      result.replaceChildren();
      result.append(this.element('p',report.proposed+' direkte Vorschläge • '+report.manual+' manuell zu prüfen'));
      for(const file of report.files||[]){
        const section=this.element('div',null,'panel');
        section.append(this.element('h3',file.file+' — '+(file.error||((file.proposals||[]).length+' Treffer'))));
        for(const item of file.proposals||[]){
          const details=this.element('details');
          const name=this.element('summary',(item.automation||item.path)+' • '+item.source+
            ' → '+(item.route||item.suggested_route||'manuelle Prüfung'));
          details.append(name,this.element('p',item.reason));
          if(item.replacement){
            details.append(this.element('pre',JSON.stringify(item.replacement,null,2)));
            if(item.preview_diff){
              const diff=this.element('pre',item.preview_diff);
              diff.style.whiteSpace='pre-wrap';details.append(diff);
            }
            if(file.relative_file?.startsWith('packages/')&&file.sha256){
              const apply=this.element('button','Einzelne Änderung mit Backup übernehmen');
              const status=this.element('p');
              apply.addEventListener('click',()=>this.run(status,async()=>{
                if(!confirm('Nur dieser EINE Paket-Eintrag wird geändert. Backup wird erstellt. Keine automatische HA-Neuladung. Fortfahren?'))return;
                const response=await this.call('migration_apply',{
                  file:file.relative_file,sha256:file.sha256,
                  path:item.path,confirmation:'APPLY_SINGLE_CHANGE'
                });
                status.textContent='Geändert. Backup: '+response.backup+
                   ' — Paket-Automationen über HA neu laden.';
                apply.disabled=true;
              }));
              details.append(apply,status);
            }
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
    const intro=this.element('div',null,'panel');intro.append(this.element('h2','Einstellungen'),
      this.element('p','Alle Betriebsoptionen stehen gemeinsam im HA-Konfigurationsdialog. Neue Ziele und Empfänger unter „Ziele & Personen“ anlegen; Profile und Vorlagen in den gleichnamigen Bereichen bearbeiten.','muted'));
    const open=this.element('a','Alle Integrationsoptionen öffnen');open.href='/config/integrations/integration/reliable_notify';intro.append(open);
    const targets=this.element('button','Neues Ziel anlegen');targets.addEventListener('click',()=>{this._section='routes';this.render();});intro.append(targets);box.append(intro);
    const status=this.element('p','Lade …');box.append(status);
    try{
      const [d,stats]=await Promise.all([this.call('dashboard'),this.call('statistics')]);
      const specs=[
        ['Wiederholungen',d.policies,'set_retry_policies','policies'],
        ['Archiv-Aufbewahrung (Tage)',d.retention,'set_archive_retention','retention'],
        ['Ruhezeiten, Limits und Digest',d.smart,'set_smart_settings',null],
        ['Testmodus und Transport-Logging',{test_mode:stats.test_mode||'off',
          test_recipients:stats.test_recipients||[],transport_logging:Object.fromEntries(
            ['telegram','smtp','companion','notify','webhook','ntfy','gotify'].map(k=>[k,stats.transport_logging?.[k]||'warning']))},'settings_v2',null]
      ];
      for(const [title,initial,method,property] of specs){
        const section=this.element('section',null,'panel');section.append(this.element('h2',title));
        const editor=this.fieldEditor(initial,{fixed:true});
        const result=this.element('p'),button=this.element('button','Speichern');
        button.addEventListener('click',()=>this.run(result,()=>this.call(method,property?{[property]:editor.read()}:editor.read())));
        section.append(editor.node,button,result);this.yamlView(section,editor.read);box.append(section);
      }this.status(status,'');
    }catch(e){this.status(status,e.message,true);}
  }

}
customElements.define('reliable-notify-panel',ReliableNotifyPanel);
