/* Reliable Notify Alarm Card 3.8.3 — open incidents for every dashboard (residents). No external dependencies. */
import { rnTranslate, rnLanguage, rnIcon, rnValueLabel, rnPageLanguage } from './reliable-notify-card.js?v=3.8.3';

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
  .compact .band{padding:8px 12px}.compact .head{font-size:14px}
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
    this._config={areas:list(c.areas,'areas'),message_types:list(c.message_types,'message_types'),
      min_priority:c.min_priority||'info',show_acknowledged:c.show_acknowledged===true,snooze_minutes:snooze,
      confirm_acknowledge:c.confirm_acknowledge!==false,compact:c.compact===true};
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
  getCardSize(){return Math.max(1,(this._data?.incidents||[]).length*2);}
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
  button(label,icon,className,handler){
    const node=document.createElement('button');node.type='button';node.className=className;
    node.append(rnIcon(icon),document.createTextNode(label));node.addEventListener('click',handler);return node;
  }
  band(incident,permissions){
    const band=document.createElement('div');band.className='band';
    band.dataset.priority=incident.priority;band.dataset.state=incident.state;band.setAttribute('role','alert');
    const head=document.createElement('div');head.className='head';
    const icon=incident.state==='resolved'?'mdi:check-circle-outline':incident.state==='acknowledged'?'mdi:check':'mdi:alarm-light-outline';
    const title=document.createElement('span');title.textContent=incident.title||incident.dedup_key;
    if(incident.source_entity){
      // Tap on the title opens the cause entity (HA more-info dialog).
      title.className='source';title.tabIndex=0;title.setAttribute('role','button');
      const open=()=>this.dispatchEvent(new CustomEvent('hass-more-info',{detail:{entityId:incident.source_entity},bubbles:true,composed:true}));
      title.addEventListener('click',open);title.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();open();}});
    }
    head.append(rnIcon(icon),title);band.append(head);
    if(incident.text&&!this._config.compact){const text=document.createElement('p');text.className='text';text.textContent=incident.text;band.append(text);}
    const meta=[this.t('seit {time}',{time:this.time(incident.opened_at)})];
    if(incident.source_entity){
      const cause=this._hass?.states?.[incident.source_entity];
      meta.push(this.t('Ursache: {name}',{name:cause?.attributes?.friendly_name||incident.source_entity}));
    }
    if(incident.state==='resolved'&&incident.resolved_at)meta.push(this.t('behoben um {time}',{time:this.time(incident.resolved_at)}));
    if(incident.state==='acknowledged')meta.push(this.t('quittiert von {name}, besteht noch',{name:incident.acknowledged_by||'?'}));
    if(incident.snoozed_until)meta.push(this.t('Erinnerungen pausiert bis {time}',{time:this.time(incident.snoozed_until)}));
    const line=document.createElement('p');line.className='meta';line.textContent=meta.join(' · ');band.append(line);
    if(incident.state!=='acknowledged'){
      const actions=document.createElement('div');actions.className='actions';
      if(permissions.ack)actions.append(this.button(this.t('Quittieren'),'mdi:check-circle-outline','ack',()=>this.act(incident,'ack')));
      if(permissions.snooze)for(const minutes of this._config.snooze_minutes)
        actions.append(this.button(this.t('Schlummern {minutes} min',{minutes}),'mdi:alarm-snooze','snooze',()=>this.act(incident,'snooze',minutes)));
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
    for(const incident of incidents)card.append(this.band(incident,permissions));
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
      input[type=text],select{padding:8px;border-radius:6px;border:1px solid var(--divider-color);background:var(--card-background-color);color:var(--primary-text-color);font:inherit}
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
    root.append(
      this.field(this.t('Bereiche (kommagetrennt, leer = alle)'),areas),
      this.field(this.t('Nachrichtentypen (kommagetrennt, leer = alle)'),types),
      this.field(this.t('Mindestpriorität'),priority),
      this.field(this.t('Schlummer-Knöpfe in Minuten (bis zu 3, kommagetrennt)'),snooze),error,
      check('show_acknowledged',this.t('Quittierte, noch bestehende Vorfälle anzeigen'),false),
      check('confirm_acknowledge',this.t('Vor dem Quittieren nachfragen'),true),
      check('compact',this.t('Kompakte Darstellung'),false));
  }
}
if(!customElements.get('reliable-notify-alarm-card-editor'))customElements.define('reliable-notify-alarm-card-editor',ReliableNotifyAlarmCardEditor);
if(!customElements.get('reliable-notify-alarm-card'))customElements.define('reliable-notify-alarm-card',ReliableNotifyAlarmCard);
window.customCards=window.customCards||[];
if(!window.customCards.some(card=>card.type==='reliable-notify-alarm-card'))window.customCards.push({type:'reliable-notify-alarm-card',name:'Reliable Notify Alarm',
  description:rnTranslate(rnPageLanguage(),'Offene Vorfälle mit Quittieren und Schlummern')});
