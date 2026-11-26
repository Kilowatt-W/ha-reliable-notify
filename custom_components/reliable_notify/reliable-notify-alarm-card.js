/* Reliable Notify Alarm Card 3.9.0 — open incidents for every dashboard (residents). No external dependencies. */
import { rnTranslate, rnLanguage, rnIcon, rnValueLabel, rnPageLanguage } from './reliable-notify-card.js?v=3.9.0';

const RN_ALARM_PRIORITIES=['info','warning','critical'];
const RN_ALARM_STYLES=`
  :host{display:block}
  ha-card{padding:8px;display:flex;flex-direction:column;gap:8px;background:none;box-shadow:none;border:none}
  .band{--rn-band:var(--info-color,#039be5);border-radius:12px;padding:12px 14px;border-left:6px solid var(--rn-band);
    background:color-mix(in srgb,var(--rn-band) 14%,var(--card-background-color,#fff));color:var(--primary-text-color)}
  .band[data-priority=critical]{--rn-band:var(--error-color,#db4437)}
  .band[data-priority=warning]{--rn-band:var(--warning-color,#f4b400)}
  .band[data-state=resolved]{border-left-style:dashed}
  .band[data-state=acknowledged]{--rn-band:var(--secondary-text-color,#727272);opacity:.85}
  .head{display:flex;align-items:center;gap:10px;font-weight:700;font-size:16px;line-height:1.3}
  .head ha-icon{color:var(--rn-band);--mdc-icon-size:24px;flex:none}
  .source{cursor:pointer;text-decoration:underline dotted;text-underline-offset:3px}
  .text{margin:6px 0 0;line-height:1.45;overflow-wrap:anywhere}
  .meta{margin:6px 0 0;font-size:13px;color:var(--secondary-text-color)}
  .actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
  button{display:inline-flex;align-items:center;gap:6px;min-height:36px;padding:6px 12px;border-radius:8px;cursor:pointer;font:inherit;
    border:1px solid color-mix(in srgb,var(--rn-band) 55%,var(--divider-color,#ccc));
    background:var(--card-background-color,#fff);color:var(--primary-text-color)}
  button.ack{font-weight:700}
  button:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}
  button ha-icon{--mdc-icon-size:18px;color:var(--rn-band)}
  .compact{gap:6px}
  .compact .band{display:flex;flex-wrap:wrap;align-items:center;gap:4px 10px;padding:6px 10px;border-left-width:5px;border-radius:10px}
  .compact .head{flex:1 1 14em;min-width:0;font-size:14px;gap:8px;flex-wrap:wrap}
  .compact .head ha-icon{--mdc-icon-size:20px}
  .compact .meta{margin:0;font-size:12px;font-weight:400}
  .compact .text{flex:1 1 100%;margin:0;font-size:13px}
  .compact .actions{margin:0;gap:6px;flex:none}
  .compact button{min-height:32px;padding:4px 10px}
  .toggle{cursor:pointer;text-decoration:underline dotted;text-underline-offset:3px}
  .summary{width:100%;justify-content:flex-start;text-align:left;border-left:6px solid var(--rn-band);border-radius:12px;min-height:44px;padding:8px 12px;
    background:color-mix(in srgb,var(--rn-band) 14%,var(--card-background-color,#fff));font-weight:700;flex-wrap:wrap}
  .summary[data-priority=critical]{--rn-band:var(--error-color,#db4437)}
  .summary[data-priority=warning]{--rn-band:var(--warning-color,#f4b400)}
  .summary[data-priority=info]{--rn-band:var(--info-color,#039be5)}
  .summary .label{flex:1 1 auto}
  .pill{font-size:12px;font-weight:600;padding:2px 8px;border-radius:999px;border:1px solid var(--rn-pill);color:var(--primary-text-color);
    background:color-mix(in srgb,var(--rn-pill) 18%,transparent)}
  .pill[data-priority=critical]{--rn-pill:var(--error-color,#db4437)}
  .pill[data-priority=warning]{--rn-pill:var(--warning-color,#f4b400)}
  .pill[data-priority=info]{--rn-pill:var(--info-color,#039be5)}
  .summary .more{font-weight:400;display:inline-flex;align-items:center;gap:4px}
  .error{color:var(--error-color,#db4437);font-size:13px;margin:4px 0 0}
`;

class ReliableNotifyAlarmCard extends HTMLElement {
  static getStubConfig(){return {snooze_minutes:[15,60]};}
  static getConfigElement(){return document.createElement('reliable-notify-alarm-card-editor');}
  setConfig(config){
    const c=config||{};
    const list=(value,name)=>{
      if(value===undefined||value===null)return null;
      if(!Array.isArray(value)||value.some(v=>typeof v!=='string'))throw new Error(name+' must be a list of texts');
      return value;
    };
    if(c.min_priority!==undefined&&!RN_ALARM_PRIORITIES.includes(c.min_priority))throw new Error('min_priority must be info, warning or critical');
    const snooze=c.snooze_minutes===undefined?[15]:c.snooze_minutes;
    if(!Array.isArray(snooze)||snooze.length>3||snooze.some(m=>!Number.isInteger(m)||m<1||m>1440))
      throw new Error('snooze_minutes must be up to three whole numbers between 1 and 1440');
    const collapse=c.collapse_from===undefined||c.collapse_from===null?null:c.collapse_from;
    if(collapse!==null&&(!Number.isInteger(collapse)||collapse<2||collapse>50))throw new Error('collapse_from must be a whole number between 2 and 50');
    this._config={areas:list(c.areas,'areas'),message_types:list(c.message_types,'message_types'),
      min_priority:c.min_priority||'info',show_acknowledged:c.show_acknowledged===true,snooze_minutes:snooze,
      confirm_acknowledge:c.confirm_acknowledge!==false,compact:c.compact===true,collapse_from:collapse};
    this._expanded=false;this._openTexts=new Set();
    if(!this.shadowRoot)this.attachShadow({mode:'open'});
    this._unsubscribe();this._data=null;
    if(this._hass)this._subscribe();else this.render();
  }
  set hass(value){
    const first=!this._hass;
    const language=this._hass&&rnLanguage(this._hass)!==rnLanguage(value);
    this._hass=value;
    if(first)this._subscribe();else if(language)this.render();
  }
  connectedCallback(){
    if(this._hass&&!this._unsub)this._subscribe();
    if(!this._timer)this._timer=setInterval(()=>this.render(),60000); // keeps "since"/snooze texts current
  }
  disconnectedCallback(){
    clearInterval(this._timer);this._timer=null;this._unsubscribe();
  }
  t(text,values={}){return rnTranslate(this._hass,text,values);}
  _filters(){
    const c=this._config,filters={type:'reliable_notify/subscribe_incidents',min_priority:c.min_priority,include_acknowledged:c.show_acknowledged};
    if(c.areas)filters.areas=c.areas;
    if(c.message_types)filters.message_types=c.message_types;
    return filters;
  }
  async _subscribe(){
    if(!this._config||!this._hass?.connection?.subscribeMessage||this._unsub||this._subscribing)return;
    this._subscribing=true;
    try{
      // Live updates from the integration; no polling of the incident list.
      this._unsub=await this._hass.connection.subscribeMessage(message=>{this._data=message;this._error=null;this.render();},this._filters());
    }catch(error){this._error=error;this.render();}
    finally{this._subscribing=false;}
  }
  _unsubscribe(){
    const unsubscribe=this._unsub;this._unsub=null;
    if(unsubscribe){try{Promise.resolve(unsubscribe()).catch(()=>{});}catch(_){/* already closed */}}
  }
  _setVisible(visible){
    if(this.hidden===!visible)return;
    // Without open incidents the card takes no space (also in sections/grid views).
    this.hidden=!visible;this.style.display=visible?'':'none';
    this.dispatchEvent(new Event('card-visibility-changed',{bubbles:true,composed:true}));
  }
  getCardSize(){
    const incidents=this._data?.incidents||[],{shown,hidden}=this._split(incidents);
    return Math.max(1,shown.length*(this._config?.compact?1:2)+(hidden.length?1:0));
  }
  _split(incidents){
    // Critical incidents that are not acknowledged are never folded away; the rest is combined from collapse_from on.
    const limit=this._config?.collapse_from;
    const pinned=incident=>incident.priority==='critical'&&incident.state!=='acknowledged';
    const rest=incidents.filter(incident=>!pinned(incident));
    const foldable=Boolean(limit&&incidents.length>=limit&&rest.length>=2);
    if(!foldable||this._expanded)return {shown:incidents,hidden:[],rest,foldable};
    return {shown:incidents.filter(pinned),hidden:rest,rest,foldable};
  }
  summary(rest,collapsed,pinned){
    // One row for the folded incidents: count, coloured count per priority, show/hide.
    const node=document.createElement('button');node.type='button';node.className='summary';
    node.setAttribute('aria-expanded',String(!collapsed));
    node.dataset.priority=RN_ALARM_PRIORITIES.slice().reverse().find(p=>rest.some(i=>i.priority===p))||'info';
    const label=document.createElement('span');label.className='label';
    label.textContent=this.t(pinned?'{count} weitere Alarme':'{count} offene Alarme',{count:rest.length});
    node.append(rnIcon('mdi:alarm-light-outline'),label);
    for(const priority of RN_ALARM_PRIORITIES.slice().reverse()){
      const count=rest.filter(i=>i.priority===priority).length;if(!count)continue;
      const pill=document.createElement('span');pill.className='pill';pill.dataset.priority=priority;
      pill.textContent=count+' × '+rnValueLabel(this._hass,'priority',priority);node.append(pill);
    }
    const more=document.createElement('span');more.className='more';
    more.append(rnIcon(collapsed?'mdi:chevron-down':'mdi:chevron-up'),document.createTextNode(this.t(collapsed?'Anzeigen':'Weniger anzeigen')));
    node.append(more);
    node.addEventListener('click',()=>{this._expanded=collapsed;this.render();
      this.dispatchEvent(new Event('iron-resize',{bubbles:true,composed:true}));});
    return node;
  }
  time(seconds){
    const date=new Date(seconds*1000),now=new Date(),language=rnLanguage(this._hass);
    return date.toDateString()===now.toDateString()
      ?date.toLocaleTimeString(language,{hour:'2-digit',minute:'2-digit'})
      :date.toLocaleString(language,{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});
  }
  async act(incident,action,minutes){
    if(action==='ack'&&this._config.confirm_acknowledge&&!window.confirm(this.t('„{title}“ quittieren?',{title:incident.title||incident.dedup_key})))return;
    try{
      await this._hass.callWS({type:'reliable_notify/incident_action',key:incident.dedup_key,action,...(minutes?{minutes}:{})});
      this._actionError=null;
    }catch(error){this._actionError=error?.message||String(error);this.render();}
  }
  button(label,icon,className,handler,ariaLabel){
    const node=document.createElement('button');node.type='button';node.className=className;
    if(ariaLabel)node.setAttribute('aria-label',ariaLabel);
    node.append(rnIcon(icon),document.createTextNode(label));node.addEventListener('click',handler);return node;
  }
  _pressable(node,handler){
    node.tabIndex=0;node.setAttribute('role','button');
    node.addEventListener('click',handler);
    node.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();handler();}});
  }
  band(incident,permissions){
    const compact=this._config.compact;
    const band=document.createElement('div');band.className='band';
    band.dataset.priority=incident.priority;band.dataset.state=incident.state;band.setAttribute('role','alert');
    const head=document.createElement('div');head.className='head';
    const icon=incident.state==='resolved'?'mdi:check-circle-outline':incident.state==='acknowledged'?'mdi:check':'mdi:alarm-light-outline';
    const title=document.createElement('span');title.textContent=incident.title||incident.dedup_key;
    const textOpen=compact&&this._openTexts.has(incident.dedup_key);
    if(incident.source_entity){
      // Tap on the title opens the cause entity (HA more-info dialog).
      title.className='source';
      this._pressable(title,()=>this.dispatchEvent(new CustomEvent('hass-more-info',{detail:{entityId:incident.source_entity},bubbles:true,composed:true})));
    }else if(compact&&incident.text){
      // Compact: tap on the title shows or hides the description.
      title.className='toggle';title.setAttribute('aria-expanded',String(textOpen));
      this._pressable(title,()=>{
        if(this._openTexts.has(incident.dedup_key))this._openTexts.delete(incident.dedup_key);else this._openTexts.add(incident.dedup_key);
        this.render();
      });
    }
    if(compact&&incident.text)band.title=incident.text;
    head.append(rnIcon(icon),title);band.append(head);
    if(incident.text&&(!compact||textOpen)){const text=document.createElement('p');text.className='text';text.textContent=incident.text;band.append(text);}
    const meta=[this.t('seit {time}',{time:this.time(incident.opened_at)})];
    if(incident.source_entity&&!compact){
      const cause=this._hass?.states?.[incident.source_entity];
      meta.push(this.t('Ursache: {name}',{name:cause?.attributes?.friendly_name||incident.source_entity}));
    }
    if(incident.state==='resolved'&&incident.resolved_at)meta.push(this.t('behoben um {time}',{time:this.time(incident.resolved_at)}));
    if(incident.state==='acknowledged')meta.push(this.t('quittiert von {name}, besteht noch',{name:incident.acknowledged_by||'?'}));
    if(incident.snoozed_until)meta.push(this.t('Erinnerungen pausiert bis {time}',{time:this.time(incident.snoozed_until)}));
    const line=document.createElement(compact?'span':'p');line.className='meta';line.textContent=meta.join(' · ');
    if(compact)head.append(line);else band.append(line);
    if(incident.state!=='acknowledged'){
      const actions=document.createElement('div');actions.className='actions';
      if(permissions.ack)actions.append(this.button(this.t('Quittieren'),'mdi:check-circle-outline','ack',()=>this.act(incident,'ack')));
      if(permissions.snooze)for(const minutes of this._config.snooze_minutes){
        const label=this.t('Schlummern {minutes} min',{minutes});
        // Compact keeps a short visible label; screen readers still hear the full one.
        actions.append(compact
          ?this.button(this.t('{minutes} min',{minutes}),'mdi:alarm-snooze','snooze',()=>this.act(incident,'snooze',minutes),label)
          :this.button(label,'mdi:alarm-snooze','snooze',()=>this.act(incident,'snooze',minutes)));
      }
      if(permissions.escalate&&incident.state==='active'&&incident.escalation_step<incident.escalation_steps)
        actions.append(this.button(this.t('Eskalieren'),'mdi:alert-outline','escalate',()=>this.act(incident,'escalate')));
      if(actions.childElementCount)band.append(actions);
    }
    return band;
  }
  render(){
    const root=this.shadowRoot;if(!root)return;
    root.replaceChildren();
    const incidents=this._data?.incidents||[];
    if(!incidents.length&&!(this._error&&this._hass?.user?.is_admin)){this._setVisible(false);return;}
    this._setVisible(true);
    const style=document.createElement('style');style.textContent=RN_ALARM_STYLES;root.append(style);
    const card=document.createElement('ha-card');if(this._config?.compact)card.classList.add('compact');
    if(this._error){const error=document.createElement('p');error.className='error';
      error.textContent=this.t('Alarmfenster nicht verfügbar:')+' '+(this._error.message||this._error.code||'');card.append(error);}
    const permissions=this._data?.permissions||{};
    const {shown,hidden,rest,foldable}=this._split(incidents);
    for(const incident of shown)card.append(this.band(incident,permissions));
    if(foldable)card.append(this.summary(rest,hidden.length>0,incidents.length>rest.length));
    if(this._actionError){const error=document.createElement('p');error.className='error';
      error.textContent=this.t('Aktion nicht möglich:')+' '+this._actionError;card.append(error);}
    root.append(card);
  }
}
// Visual editor (Lovelace "edit card"): same options as YAML, German/English labels.
class ReliableNotifyAlarmCardEditor extends HTMLElement {
  setConfig(config){this._config={...(config||{})};this.render();}
  set hass(value){const language=this._hass&&rnLanguage(this._hass)!==rnLanguage(value);this._hass=value;if(!this._rendered||language)this.render();}
  t(text,values={}){return rnTranslate(this._hass,text,values);}
  _list(value){return value.split(',').map(item=>item.trim()).filter(Boolean);}
  _emit(){
    this.dispatchEvent(new CustomEvent('config-changed',{detail:{config:this._config},bubbles:true,composed:true}));
  }
  _set(key,value,fallback){
    // Defaults are left out so the YAML stays short.
    const config={...this._config};
    if(value===undefined||value===fallback||(Array.isArray(value)&&!value.length&&key!=='snooze_minutes'))delete config[key];else config[key]=value;
    this._config=config;this._emit();
  }
  field(label,input){
    const row=document.createElement('label');row.className='row';
    const text=document.createElement('span');text.textContent=label;
    row.append(text,input);return row;
  }
  render(){
    if(!this.shadowRoot)this.attachShadow({mode:'open'});
    this._rendered=true;
    const c=this._config||{};
    const root=this.shadowRoot;root.replaceChildren();
    const style=document.createElement('style');
    style.textContent=`.row{display:flex;flex-direction:column;gap:4px;margin:0 0 12px;font-size:14px;color:var(--primary-text-color)}
      .check{flex-direction:row;align-items:center;gap:8px}
      input[type=text],input[type=number],select{padding:8px;border-radius:6px;border:1px solid var(--divider-color);background:var(--card-background-color);color:var(--primary-text-color);font:inherit}
      .error{color:var(--error-color,#db4437);font-size:13px;margin:-6px 0 12px}`;
    root.append(style);
    const text=(key)=>{const input=document.createElement('input');input.type='text';input.name=key;input.value=(c[key]||[]).join(', ');return input;};
    const areas=text('areas');areas.addEventListener('change',()=>this._set('areas',this._list(areas.value)));
    const types=text('message_types');types.addEventListener('change',()=>this._set('message_types',this._list(types.value)));
    const priority=document.createElement('select');priority.name='min_priority';
    for(const value of ['info','warning','critical']){const option=document.createElement('option');option.value=value;option.textContent=rnValueLabel(this._hass,'priority',value);priority.append(option);}
    priority.value=c.min_priority||'info';priority.addEventListener('change',()=>this._set('min_priority',priority.value,'info'));
    const snooze=document.createElement('input');snooze.type='text';snooze.name='snooze_minutes';
    snooze.value=(c.snooze_minutes===undefined?[15]:c.snooze_minutes).join(', ');
    const error=document.createElement('p');error.className='error';error.setAttribute('role','alert');
    snooze.addEventListener('change',()=>{
      const values=this._list(snooze.value).map(Number);
      if(values.length>3||values.some(m=>!Number.isInteger(m)||m<1||m>1440)){error.textContent=this.t('Schlummer-Minuten: ganze Zahlen 1–1440, höchstens drei.');return;}
      error.textContent='';
      if(values.length===1&&values[0]===15){const config={...this._config};delete config.snooze_minutes;this._config=config;this._emit();}
      else this._set('snooze_minutes',values);
    });
    const check=(key,label,fallback)=>{
      const input=document.createElement('input');input.type='checkbox';input.name=key;
      input.checked=c[key]===undefined?fallback:c[key]===true;
      input.addEventListener('change',()=>this._set(key,input.checked,fallback));
      const row=this.field(label,input);row.classList.add('check');row.append(row.firstChild);return row;
    };
    const collapse=document.createElement('input');collapse.type='number';collapse.name='collapse_from';
    collapse.min='2';collapse.max='50';collapse.step='1';collapse.inputMode='numeric';
    collapse.value=c.collapse_from===undefined||c.collapse_from===null?'':String(c.collapse_from);
    const collapseError=document.createElement('p');collapseError.className='error';collapseError.setAttribute('role','alert');
    collapse.addEventListener('change',()=>{
      const raw=collapse.value.trim(),value=Number(raw);
      if(raw&&(!Number.isInteger(value)||value<2||value>50)){collapseError.textContent=this.t('Zusammenfassen: ganze Zahl 2–50 oder leer.');return;}
      collapseError.textContent='';
      this._set('collapse_from',raw?value:undefined);
    });
    root.append(
      this.field(this.t('Bereiche (kommagetrennt, leer = alle)'),areas),
      this.field(this.t('Nachrichtentypen (kommagetrennt, leer = alle)'),types),
      this.field(this.t('Mindestpriorität'),priority),
      this.field(this.t('Schlummer-Knöpfe in Minuten (bis zu 3, kommagetrennt)'),snooze),error,
      check('show_acknowledged',this.t('Quittierte, noch bestehende Vorfälle anzeigen'),false),
      check('confirm_acknowledge',this.t('Vor dem Quittieren nachfragen'),true),
      check('compact',this.t('Kompakte Darstellung (eine Zeile pro Alarm)'),false),
      this.field(this.t('Ab so vielen Alarmen zu einer Zeile zusammenfassen (leer = nie; kritische bleiben sichtbar)'),collapse),collapseError);
  }
}
if(!customElements.get('reliable-notify-alarm-card-editor'))customElements.define('reliable-notify-alarm-card-editor',ReliableNotifyAlarmCardEditor);
if(!customElements.get('reliable-notify-alarm-card'))customElements.define('reliable-notify-alarm-card',ReliableNotifyAlarmCard);
window.customCards=window.customCards||[];
if(!window.customCards.some(card=>card.type==='reliable-notify-alarm-card'))window.customCards.push({type:'reliable-notify-alarm-card',name:'Reliable Notify Alarm',
  description:rnTranslate(rnPageLanguage(),'Offene Vorfälle mit Quittieren und Schlummern')});
