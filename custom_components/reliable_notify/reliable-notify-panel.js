/* Reliable Notify Admin Panel 3.2 — no external CDN/dependencies. */
import { rnTranslate, rnLanguage } from './reliable-notify-card.js?v=3.2.0';

class ReliableNotifyPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:'open'});
    this._section='messages';
    this._rendered=false;
    this._hass=null;
  }
  t(text, values={}) { return rnTranslate(this._hass,text,values); }
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
    const button=this.element('button',null,className);
    const symbol=this.element('ha-icon');symbol.setAttribute('icon',icon);symbol.setAttribute('aria-hidden','true');
    button.append(symbol,this.element('span',text));return button;
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
  async run(node, fn){
    const oldText=node.textContent;
    try {
      await fn();
      if(node.textContent===oldText)this.status(node,this.t('Erfolgreich'));
    }catch(e){this.status(node,e.message||String(e),true);}
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
    details.append(this.element('summary',this.t('YAML-Ansicht einblenden (nur Vorschau, ggf. mit Zugangsdaten)')));
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
      const entityDomain=key==='target_entity'?'notify':key==='entity'?'person':null;
      const entities=entityDomain?Object.keys(this._hass?.states||{}).filter(id=>id.startsWith(entityDomain+'.')).sort():[];
      const options=entityDomain?['',...new Set([...entities,...(initial?[initial]:[])])]:choices||enums[key];
      const input=this.element(options?'select':key==='message'||(typeof initial==='string'&&initial.includes('\n'))?'textarea':'input');
      if(options){for(const value of new Set([...options,initial])){
        const entity=this._hass?.states?.[value];
        const label=entityDomain?(value?(entity?.attributes?.friendly_name?entity.attributes.friendly_name+' — '+value:value):this.t('Entität auswählen (optional)')):this.t(String(value));
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
      if(entityDomain){
        host.append(this.element('p',this.t(entityDomain==='person'?'Vorhandene person.*-Entität auswählen.':'Vorhandene Notify-Entitäten durchsuchen. Klassische notify.mobile_app_* Ziele werden unter HA-Aktion ausgewählt.'),'muted'));
        if(!entities.length)host.append(this.element('p',this.t(entityDomain==='person'?'Keine passenden person.*-Entitäten gefunden.':'Keine passenden Entitäten gefunden. Klassische Notify-Ziele unter HA-Aktion auswählen.'),'muted'));
      }
      if(key==='action'){
        const list=this.element('datalist');this._fieldId=(this._fieldId||0)+1;list.id='rn-actions-'+this._fieldId;input.setAttribute('list',list.id);
        for(const [domain,services] of Object.entries(this._hass?.services||{})){
          if(!['notify','telegram_bot','reliable_notify','smtp'].includes(domain))continue;
          for(const [service,definition] of Object.entries(services)){
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
      const label=this.element('label',array?this.t('Eintrag'):this.fieldLabel(name));
      const child=this.fieldEditor(value,{key:array?'':name,fixed:fixed&&value!==null&&typeof value==='object'&&!Array.isArray(value),choices:key==='transport_logging'?['off','error','warning','info','debug']:key==='allow_priorities'?['info','warning','critical']:null,defaults:!array&&name==='preferred'
        ?{info:[],warning:[],critical:[]}:!array&&name==='data'
        ?{chat_id:0,config_entry_id:'',entity_id:'',base_url:'',allow_private:false,url:'',topic:'',token:'',headers:{},method:'POST',parse_mode:'HTML',disable_notification:false}
        :!array&&name==='only_if'?{entity_id:'',state:''}:{}});
      const control=child.node.querySelector('input,textarea,select');
      if(control){if(!control.id){this._fieldId=(this._fieldId||0)+1;control.id='rn-field-'+this._fieldId;}label.htmlFor=control.id;}
      row.append(label,child.node);const record={name,child,row};rows.push(record);
      if(!fixed){const remove=this.element('button',this.t('Entfernen'));remove.type='button';
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
      const button=this.element('button',array?this.t('Eintrag hinzufügen'):this.t('Feld hinzufügen'));button.type='button';
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
      button ha-icon{--mdc-icon-size:19px}button:disabled{opacity:.55;cursor:default}
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
    root.append(style);
    const shell=this.element('div',null,'shell');
    shell.append(this.element('h1','🔔 Reliable Notify'));
    shell.append(this.element('p',this.t('Benachrichtigungen • Zustellung • Eskalation • Diagnose'),'muted'));
    const tabs=this.element('nav',null,'tabs');
    for(const [id,name] of [['messages',this.t('Nachrichten')],['routes',this.t('Ziele & Personen')],
       ['incidents',this.t('Eskalationen')],['simulation','Simulation'],['analytics',this.t('Statistik')],['templates',this.t('Vorlagen')],['profiles',this.t('Profile & API')],['migration',this.t('Automation-Migration')],['settings',this.t('Einstellungen')]]){
      const button=this.element('button',this.t(name));
      button.addEventListener('click',()=>{this._section=id;
        for(const sibling of tabs.children)sibling.classList.remove('active');
        button.classList.add('active');this.refreshSection();});
      if(id===this._section)button.classList.add('active');
      tabs.append(button);
    }
    shell.append(tabs);
    const content=this.element('main');content.id='content';shell.append(content);
    shell.append(this.element('p',this.t('Die Verwaltungsfunktionen sind nur für Home-Assistant-Administratoren freigegeben.'),'footer'));
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
      for(const [category,label,kind] of [['recipients',this.t('Ziele / Empfänger'),'recipient'],['groups',this.t('Gruppen'),'group'],['persons',this.t('Personen'),'person']]){
        const section=this.element('section',null,'panel');
        const heading=this.element('h2',null,'route-heading');const symbol=this.element('ha-icon');
        symbol.setAttribute('icon',category==='recipients'?'mdi:send-check':category==='groups'?'mdi:account-group':'mdi:account');
        heading.append(symbol,this.element('span',label));section.append(heading);
        const inventory=this.element('div',null,'tabs');section.append(inventory);
        const name=this.element('input');name.placeholder=this.t('Eindeutiger Name');
        name.maxLength=64;name.pattern='[a-z][a-z0-9_]{0,63}';
        const hint=this.element('p',this.t('Interner Name: 1–64 Zeichen, mit Kleinbuchstaben beginnen; nur a–z, 0–9 und Unterstriche (_). Beispiel: rn_kw_telegram. Großbuchstaben, Leerzeichen und Bindestriche sind nicht erlaubt.'),'muted');
        this._fieldId=(this._fieldId||0)+1;hint.id='rn-name-help-'+this._fieldId;name.setAttribute('aria-describedby',hint.id);
        const editorBox=this.element('div');let editor;
        let loaded=null,selectedTest=null;
        const draw=value=>{editor=this.fieldEditor(value,{defaults:this.fieldDefaults(kind)});editorBox.replaceChildren(editor.node);section.dispatchEvent(new Event('input',{bubbles:true}));};
        const reset=()=>{loaded=null;if(selectedTest)selectedTest.disabled=true;name.value='';draw(category==='groups'?[]:category==='persons'
          ?{entity:'',channels:{},preferred:{}}:{action:'notify.send_message',target_entity:'',data:{}});};
        reset();
        const result=this.element('p');result.setAttribute('role','status');
        for(const id of Object.keys(data.routes[category]||{})){
          const item=this.element('div',null,'route-item');const testResult=this.element('p');testResult.setAttribute('role','status');
          const test=this.actionButton(this.t('Test senden'),'mdi:bell-ring-outline','test');
          test.addEventListener('click',()=>this.testTarget(category,id,test,testResult));
          const button=this.actionButton(id,'mdi:pencil-outline');button.addEventListener('click',()=>this.run(result,async()=>{
            const response=await this.call('route_definition',{category,name:id});
            name.value=id;loaded=id;draw(response.definition);selectedTest.disabled=false;
          }));item.append(button,test,testResult);inventory.append(item);
        }
        const fresh=this.actionButton(category==='recipients'?this.t('Neues Ziel anlegen'):category==='groups'?this.t('Neue Gruppe anlegen'):this.t('Neue Person anlegen'),'mdi:plus','primary');fresh.addEventListener('click',()=>{reset();selectedTest.disabled=true;});inventory.append(fresh);
        section.append(this.element('p',this.t('Test senden verschickt eine echte Nachricht über die gespeicherte Konfiguration. Testmodus und Ruhezeiten bleiben aktiv. Bei Gruppen und Personen können mehrere Empfänger erreicht werden.'),'test-hint'));
        section.append(this.element('label','Name'),name,hint,editorBox);
        const save=this.actionButton(this.t('Speichern'),'mdi:content-save-outline','primary');save.addEventListener('click',()=>this.run(result,async()=>{
          name.value=name.value.trim();
          if(!/^[a-z][a-z0-9_]{0,63}$/.test(name.value)){
            const example=name.value.toLowerCase().replace(/[^a-z0-9_]+/g,'_').replace(/^[^a-z]+/,'').slice(0,64)||'rn_kw_telegram';
            name.setAttribute('aria-invalid','true');name.focus();
            throw Error(this.t('Ungültiger interner Name „{name}“. Nur Kleinbuchstaben, Ziffern und Unterstriche; mit einem Buchstaben beginnen, maximal 64 Zeichen. Beispiel: {example}.',{name:name.value,example}));
          }
          name.removeAttribute('aria-invalid');
          if(loaded&&name.value!==loaded)throw Error(this.t('Zum Umbenennen neuen Eintrag anlegen und den alten gezielt löschen.'));
          await this.call('set_route',{category,name:name.value,definition:editor.read()});
          loaded=name.value;selectedTest.disabled=false;this.status(result,this.t('Gespeichert. Zum Aktualisieren der Liste diesen Bereich erneut öffnen.'));
        }));
        const remove=this.actionButton(this.t('Eintrag löschen'),'mdi:delete-outline','danger');remove.addEventListener('click',()=>this.run(result,async()=>{
          if(!confirm(this.t('UI-Eintrag ')+name.value+this.t(' löschen?')))return;
          await this.call('set_route',{category,name:name.value,delete:true});reset();
        }));
        selectedTest=this.actionButton(this.t('Gespeichertes Ziel testen'),'mdi:bell-ring-outline','test');selectedTest.disabled=true;
        selectedTest.addEventListener('click',()=>this.testTarget(category,loaded,selectedTest,result));
        name.addEventListener('input',()=>{selectedTest.disabled=!loaded||name.value!==loaded;});
        section.append(save,selectedTest,remove,result);this.yamlView(section,()=>({[category]:{[name.value||'neuer_eintrag']:editor.read()}}));box.append(section);
      }
    }catch(e){this.status(status,e.message,true);if(!status.parentNode)box.append(status);}
  }
  async incidents(box){
    const incidents=this.element('div',null,'panel');incidents.append(this.element('h2',this.t('Unbestätigte Alarme')));
    const list=this.element('div',this.t('Lade ...'));incidents.append(list);box.append(incidents);
    try{
      const d=await this.call('dashboard');
      list.replaceChildren();
      for(const item of d.acknowledgements||[]){
        const row=this.element('div',null,'panel');
        row.append(this.element('b',(item.title||item.ack_key)+' • '+item.priority));
        row.append(this.element('p',this.t('ID: ')+item.ack_key+this.t(' | Eskalationsstufe: ')+item.next_step));
        const status=this.element('p');
        for(const [action,label] of [['ack',this.t('Bestätigen')],['snooze',this.t('15 Min. verschieben')],['escalate',this.t('Sofort eskalieren')]]){
          const button=this.element('button',label);
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
    const wizard=this.element('div',null,'panel');wizard.append(this.element('h2',this.t('Testbare Eskalationskette anlegen')));
    const key=this.element('input');key.placeholder='alarm_kennung';
    const target=this.element('input');target.placeholder='initial_recipient';
    const delayed=this.element('input');delayed.placeholder='fallback_recipient';
    const delay=this.element('input');delay.type='number';delay.value='300';
    const message=this.element('textarea');message.placeholder=this.t('Alarmtext');
    for(const [label,field] of [[this.t('Dedup-Schlüssel'),key],[this.t('Erster Empfänger'),target],
      [this.t('Eskalationsempfänger'),delayed],[this.t('Eskalation nach Sekunden'),delay],[this.t('Nachricht'),message]])wizard.append(this.element('label',label),field);
    const response=this.element('p');
    const plan=this.element('button',this.t('Nur simulieren'));
    plan.addEventListener('click',()=>this.run(response,async()=>{
      const result=await this.call('simulate',{notification:{recipients:[target.value],priority:'critical',
        message:message.value}});response.textContent=JSON.stringify(result,null,2);
    }));
    const send=this.element('button',this.t('Alarm wirklich einreihen'));
    send.addEventListener('click',()=>this.run(response,async()=>{
      if(!confirm(this.t('Dieser Alarm wird tatsächlich verschickt. Fortfahren?')))return;
      await this._hass.callService('reliable_notify','enqueue',{
        recipients:[target.value],message:message.value,priority:'critical',
        dedup_key:key.value,acknowledgement:{required:true,
          escalation:[{after:Number(delay.value),recipients:[delayed.value]}]}});
    }));
    wizard.append(plan,send,response);box.append(wizard);

    const telegram=this.element('div',null,'panel');
    telegram.append(this.element('h2',this.t('Telegram: gesendete Nachricht bearbeiten / entfernen')));
    telegram.append(this.element('p',this.t('Erfordert bekannte telegram_sent-Nachrichtenkennung und passenden konfigurierten Chat. Direktaufruf ohne Queue-Retry.'),'muted'));
    const route=this.element('input');route.placeholder=this.t('z.B. telegram_wolfgang');
    const keyInput=this.element('input');keyInput.placeholder=this.t('Dedup-Schlüssel der versendeten Meldung');
    const edit=this.element('select');for(const action of ['edit','delete']){
      const opt=this.element('option',action);opt.value=action;edit.append(opt);}
    const msg=this.element('textarea');msg.placeholder=this.t('Neuer Nachrichtentext (nur bei edit)');
    telegram.append(this.element('label',this.t('Reliable-Notify-Telegram-Empfänger')),route,
      this.element('label',this.t('Dedup-Schlüssel')),keyInput,
      this.element('label',this.t('Aktion')),edit,this.element('label',this.t('Neue Nachricht')),msg);
    const telegramStatus=this.element('p');const sendTelegram=this.element('button',this.t('Telegram-Aktion ausführen'));
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
    const wrapper=this.element('div',null,'panel');wrapper.append(this.element('h2',this.t('Simulation ohne Versand')));
    wrapper.append(this.element('p',this.t('Zeigt Routing, Aufbewahrung und Ruhezeiten an. Keine Queue-Einträge oder Push-Nachrichten.'),'muted'));
    const editor=this.fieldEditor({recipients:['wolfgang_phone'],priority:'warning',
      message_type:'windows',message:this.t('Fenster seit 90 Minuten offen')},{defaults:this.fieldDefaults('template')});
    const result=this.element('pre');
    const run=this.element('button',this.t('Versand simulieren'));
    run.addEventListener('click',()=>this.run(result,async()=>{
      const answer=await this.call('simulate',{notification:editor.read()});
      result.textContent=JSON.stringify(answer,null,2);
    }));
    wrapper.append(editor.node,run,result);this.yamlView(wrapper,editor.read);box.append(wrapper);
  }
  async analytics(box){
    const wrapper=this.element('div',null,'panel');wrapper.append(this.element('h2',this.t('Transportstatistik & Systemzustand')));
    const days=this.element('select');for(const day of [1,7,14,30]){
      const option=this.element('option',String(day)+this.t(' Tage'));option.value=day;
      if(day===7)option.selected=true;days.append(option);
    }
    const refresh=this.element('button',this.t('Aktualisieren'));
    const exportButton=this.element('button',this.t('Diagnose (ohne Nachrichtentexte) exportieren'));
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
    const title=this.element('h3',this.t('Tägliche Zustellungen (letzte 30 Tage)'));
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
    const section=this.element('section',null,'panel');section.append(this.element('h2',title));box.append(section);
    const status=this.element('p',this.t('Lade …'));section.append(status);
    try{
      const data=await this.call(load);
      const defaults=this.fieldDefaults(kind);
      const rows=[];const body=this.element('div');section.append(body);
      const add=(name,value)=>{
        const row=this.element('div',null,'panel');const input=this.element('input');input.value=name;input.placeholder='Name';
        const fields=this.fieldEditor(value,{defaults});
        row.append(this.element('label','Name'),input,fields.node);
        const record={input,fields};rows.push(record);
        const remove=this.element('button',this.t('Entfernen'));remove.addEventListener('click',()=>{
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
      const newButton=this.element('button',this.t('Neu anlegen'));newButton.addEventListener('click',()=>{
        add('',kind==='template'?{message:'',priority:'info'}:{priority:'info'});
        section.dispatchEvent(new Event('input',{bubbles:true}));});
      const submit=this.element('button',this.t('Speichern'));submit.addEventListener('click',()=>this.run(status,()=>this.call(save,{[property]:read()})));
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
    const api=this.element('section',null,'panel');api.append(this.element('h2',this.t('Externe API')));
    api.append(this.element('p',this.t('Nur HA-Administratoren mit Bearer-Token und ausdrücklich freigegebene Empfänger.'),'muted'));
    const editor=this.fieldEditor({enabled:Boolean(data.external_api_enabled),
      recipients:data.external_api_recipients||[],rate:data.external_api_rate||30},{fixed:true});
    const status=this.element('p'),save=this.element('button',this.t('API-Einstellungen speichern'));
    save.addEventListener('click',()=>this.run(status,()=>this.call('set_external_api',editor.read())));
    api.append(editor.node,save,status);this.yamlView(api,editor.read);box.append(api);
  }

  async migration(box){
    const wrapper=this.element('div',null,'panel');
    wrapper.append(this.element('h2',this.t('Bestehende Automationen prüfen')));
    wrapper.append(this.element('p',this.t('Liest automations.yaml und scripts.yaml ausschließlich lesend. Es werden keine Dateien, Automationen oder Skripte verändert. Vorschläge bei Mehrdeutigkeiten sind ausdrücklich zu prüfen.'),'muted'));
    const button=this.element('button',this.t('Benachrichtigungen analysieren'));
    const result=this.element('div');
    const download=this.element('button',this.t('Vorschläge als JSON herunterladen'));
    download.disabled=true;
    let last=null;
    button.addEventListener('click',()=>this.run(result,async()=>{
      const report=await this.call('migration_scan');
      last=report;download.disabled=false;
      result.replaceChildren();
      result.append(this.element('p',report.proposed+this.t(' direkte Vorschläge • ')+report.manual+this.t(' manuell zu prüfen')));
      for(const file of report.files||[]){
        const section=this.element('div',null,'panel');
        section.append(this.element('h3',file.file+' — '+(file.error||((file.proposals||[]).length+this.t(' Treffer')))));
        for(const item of file.proposals||[]){
          const details=this.element('details');
          const name=this.element('summary',(item.automation||item.path)+' • '+item.source+
            ' → '+(item.route||item.suggested_route||this.t('manuelle Prüfung')));
          details.append(name,this.element('p',item.reason));
          if(item.replacement){
            details.append(this.element('pre',JSON.stringify(item.replacement,null,2)));
            if(item.preview_diff){
              const diff=this.element('pre',item.preview_diff);
              diff.style.whiteSpace='pre-wrap';details.append(diff);
            }
            if(file.relative_file?.startsWith('packages/')&&file.sha256){
              const apply=this.element('button',this.t('Einzelne Änderung mit Backup übernehmen'));
              const status=this.element('p');
              apply.addEventListener('click',()=>this.run(status,async()=>{
                if(!confirm(this.t('Nur dieser EINE Paket-Eintrag wird geändert. Backup wird erstellt. Keine automatische HA-Neuladung. Fortfahren?')))return;
                const response=await this.call('migration_apply',{
                  file:file.relative_file,sha256:file.sha256,
                  path:item.path,confirmation:'APPLY_SINGLE_CHANGE'
                });
                status.textContent=this.t('Geändert. Backup: ')+response.backup+
                   this.t(' — Paket-Automationen über HA neu laden.');
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
    const intro=this.element('div',null,'panel');intro.append(this.element('h2',this.t('Einstellungen')),
      this.element('p',this.t('Alle Betriebsoptionen stehen gemeinsam im HA-Konfigurationsdialog. Neue Ziele und Empfänger unter „Ziele & Personen“ anlegen; Profile und Vorlagen in den gleichnamigen Bereichen bearbeiten.'),'muted'));
    const open=this.element('a',this.t('Alle Integrationsoptionen öffnen'));open.href='/config/integrations/integration/reliable_notify';intro.append(open);
    const targets=this.element('button',this.t('Neues Ziel anlegen'));targets.addEventListener('click',()=>{this._section='routes';this._rendered=false;this.shadowRoot.replaceChildren();this.render();});intro.append(targets);box.append(intro);
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
        const section=this.element('section',null,'panel');section.append(this.element('h2',title));
        const editor=this.fieldEditor(initial,{fixed:true});
        const result=this.element('p'),button=this.element('button',this.t('Speichern'));
        button.addEventListener('click',()=>this.run(result,()=>this.call(method,property?{[property]:editor.read()}:editor.read())));
        section.append(editor.node,button,result);this.yamlView(section,editor.read);box.append(section);
      }this.status(status,'');
    }catch(e){this.status(status,e.message,true);}
  }

}
if(!customElements.get('reliable-notify-panel'))customElements.define('reliable-notify-panel',ReliableNotifyPanel);
