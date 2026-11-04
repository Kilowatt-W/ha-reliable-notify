/* Reliable Notify Admin Panel 2.0 — no external CDN/dependencies. */
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
      label{display:block;font-weight:600;font-size:13px;margin-top:6px}
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
    for(const [id,name] of [['messages','Nachrichten'],['routes','Empfänger & Personen'],
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
    const inventoryCard=this.element('div',null,'panel');
    inventoryCard.append(this.element('h2','Verfügbare Geräte und Empfänger'));
    const list=this.element('div','Lade Geräteliste ...');
    inventoryCard.append(list);box.append(inventoryCard);
    const editor=this.element('div',null,'panel');
    editor.append(this.element('h2','Empfänger, Gruppen und Personen verwalten'));
    const kind=this.element('select');for(const value of ['recipients','groups','persons']){
      const opt=this.element('option',value);opt.value=value;kind.append(opt);
    }
    const name=this.element('input');name.placeholder='Eindeutiger Name, z. B. wolfgang';
    const json=this.element('textarea');json.value=JSON.stringify({action:'notify.mobile_app_dein_handy'},null,2);
    const names=this.element('div',null,'muted');
    const status=this.element('p');
    for(const [label,node] of [['Kategorie',kind],['Name',name],['Definition (JSON; Gruppen als Liste)',json]]){
      editor.append(this.element('label',label),node);
    }
    const save=this.element('button','Speichern');
    save.addEventListener('click',()=>this.run(status,async()=>{
      await this.call('set_route',{category:kind.value,name:name.value,definition:JSON.parse(json.value)});
      await this.routesRefresh(list,names);
    }));
    const deleteButton=this.element('button','Eintrag löschen');
    deleteButton.addEventListener('click',()=>this.run(status,async()=>{
      if(!confirm('UI-Eintrag '+name.value+' löschen?'))return;
      await this.call('set_route',{category:kind.value,name:name.value,delete:true});
      await this.routesRefresh(list,names);
    }));
    editor.append(save,deleteButton,status,names);box.append(editor);
    kind.addEventListener('change',()=>{json.value=kind.value==='groups'
      ?'["empfaenger1"]':kind.value==='persons'
      ?JSON.stringify({entity:'person.wolfgang',channels:{mobile:'wolfgang_phone'},
                     preferred:{info:'mobile',warning:'mobile',critical:['mobile']}},null,2)
      :JSON.stringify({action:'notify.mobile_app_dein_handy'},null,2)});
    await this.routesRefresh(list,names);
  }
  async routesRefresh(list,names){
    try{
      const data=await this.call('admin_inventory');
      list.replaceChildren();
      for(const action of data.companion_actions||[]){
        const button=this.element('button','+ '+action);
        button.addEventListener('click',()=>this.run(names,async()=>{
          const key=action.replace('notify.mobile_app_','phone_');
          await this.call('set_route',{category:'recipients',name:key,definition:{action}});
          await this.routesRefresh(list,names);
        }));
        list.append(button);
      }
      for(const person of data.people||[])list.append(this.element('span',person,'chip'));
      names.textContent='Konfigurierte Gruppen: '+Object.keys(data.routes.groups||{}).join(', ')
        +' • Personen: '+Object.keys(data.routes.persons||{}).join(', ');
    }catch(e){list.textContent='Routing-Fehler: '+e.message;}
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
  }
  async simulation(box){
    const wrapper=this.element('div',null,'panel');wrapper.append(this.element('h2','Simulation ohne Versand'));
    wrapper.append(this.element('p','Zeigt Routing, Aufbewahrung und Ruhezeiten an. Keine Queue-Einträge oder Push-Nachrichten.','muted'));
    const input=this.element('textarea');input.value=JSON.stringify({
      recipients:['wolfgang_phone'],priority:'warning',message_type:'windows',
      message:'Fenster seit 90 Minuten offen'},null,2);
    const result=this.element('pre');
    const run=this.element('button','Versand simulieren');
    run.addEventListener('click',()=>this.run(result,async()=>{
      const answer=await this.call('simulate',{notification:JSON.parse(input.value)});
      result.textContent=JSON.stringify(answer,null,2);
    }));
    wrapper.append(input,run,result);box.append(wrapper);
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
    refresh.addEventListener('click',()=>this.run(report,load));
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
  async templates(box){
    const section=this.element('div',null,'panel');
    section.append(this.element('h2','Wiederverwendbare Vorlagen'));
    section.append(this.element('p','Vorlagen können mit reliable_notify.send_template verwendet werden. Jinja-Variablen werden beim Versand ausgewertet.','muted'));
    const json=this.element('textarea');json.rows=14;
    const status=this.element('pre');
    const save=this.element('button','Vorlagen speichern');
    save.addEventListener('click',()=>this.run(status,async()=>{
      await this.call('set_templates',{templates:JSON.parse(json.value)});
    }));
    section.append(json,save,status);box.append(section);
    try{
      const result=await this.call('templates');
      json.value=JSON.stringify(result.templates||{},null,2);
    }catch(e){this.status(status,e.message,true);}
  }
  async profiles(box){
    const section=this.element('div',null,'panel');
    section.append(this.element('h2','Benachrichtigungsprofile'));
    section.append(this.element('p','Definiere zentrale Standardwerte für Priorität, Aufbewahrung, Ziele und Zustellstrategie. Angaben beim Versand überschreiben Profilwerte.','muted'));
    const json=this.element('textarea');json.rows=13;
    const note=this.element('p');
    const save=this.element('button','Profile speichern');
    save.addEventListener('click',()=>this.run(note,()=>this.call('set_profiles',{
      profiles:JSON.parse(json.value)})));
    section.append(json,save,note);box.append(section);
    const api=this.element('div',null,'panel');
    api.append(this.element('h2','Externe API (standardmäßig deaktiviert)'));
    api.append(this.element('p','Authentifizierung durch Home Assistant, nur Admin-Bearer-Tokens. Keine eigenen API-Tokens. Erlaubte Ziele müssen ausdrücklich freigegeben werden.','muted'));
    const enabled=this.element('input');enabled.type='checkbox';enabled.style.width='auto';
    const targets=this.element('input');targets.placeholder='Erlaubte Empfänger (Komma-getrennt)';
    const limit=this.element('input');limit.type='number';limit.min='1';limit.max='60';limit.value='30';
    const result=this.element('p');
    api.append(this.element('label','HTTP API aktivieren'),enabled,
      this.element('label','Freigegebene Empfänger'),targets,
      this.element('label','Max. Aufträge pro Minute und Benutzer'),limit);
    const saveApi=this.element('button','API-Einstellungen speichern');
    saveApi.addEventListener('click',()=>this.run(result,()=>this.call('set_external_api',{
      enabled:enabled.checked,
      recipients:targets.value.split(',').map(x=>x.trim()).filter(Boolean),
      rate:Number(limit.value)})));
    api.append(saveApi,result);box.append(api);
    try{
      const data=await this.call('profiles');
      json.value=JSON.stringify(data.profiles,null,2);
      enabled.checked=Boolean(data.external_api_enabled);
      targets.value=(data.external_api_recipients||[]).join(',');
      limit.value=Number(data.external_api_rate||30);
    }catch(e){this.status(note,e.message,true);}
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
    const wrapper=this.element('div',null,'panel');wrapper.append(this.element('h2','Testmodus & Debug'));
    wrapper.append(this.element('p','Testmodus STAGE: Nachrichten werden nur gespeichert und niemals ausgeliefert.','muted'));
    const mode=this.element('select');
    for(const item of ['off','stage']){const opt=this.element('option',item);opt.value=item;mode.append(opt);}
    const recipients=this.element('input');recipients.placeholder='Empfängerfilter (Komma); leer = alle';
    const json=this.element('textarea');json.value=JSON.stringify({telegram:'warning',smtp:'warning',
      companion:'warning',notify:'warning',webhook:'warning'},null,2);
    const status=this.element('p');
    wrapper.append(this.element('label','Testmodus'),mode,
      this.element('label','Betroffene Empfänger'),recipients,
      this.element('label','Transport-Loglevel (JSON, keine Inhalte oder Tokens)'),json);
    const save=this.element('button','Einstellungen speichern');
    save.addEventListener('click',()=>this.run(status,()=>this.call('settings_v2',{
      test_mode:mode.value,test_recipients:recipients.value.split(',').map(x=>x.trim()).filter(Boolean),
      transport_logging:JSON.parse(json.value)})));
    wrapper.append(save,status);box.append(wrapper);
    try{
      const d=await this.call('statistics');
      mode.value=d.test_mode||'off';recipients.value=(d.test_recipients||[]).join(',');
      json.value=JSON.stringify(d.transport_logging||{},null,2);
    }catch(e){this.status(status,e.message,true);}
  }
}
customElements.define('reliable-notify-panel',ReliableNotifyPanel);
