/* Reliable Notify v0.6 - interactive, admin-only Home Assistant Lovelace card. */
class ReliableNotifyCard extends HTMLElement {
  setConfig(config) {
    this.config = config || {};
    if (!this.shadowRoot) this.attachShadow({mode: 'open'});
    this.showDead = false;
    this.refresh();
  }
  set hass(value) {
    const changed = this._hass !== value;
    this._hass = value;
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
      const close=document.createElement('button');close.textContent='Close';close.addEventListener('click',()=>panel.remove());
      const heading=document.createElement('h3');heading.textContent=(entry.title||'Notification')+' #'+entry.id;
      const meta=document.createElement('div');meta.className='muted';
      meta.textContent=[entry.status,entry.priority,entry.target,new Date(entry.created_at*1000).toLocaleString()].join(' • ');
      const body=document.createElement('pre');body.style.whiteSpace='pre-wrap';body.style.overflowWrap='anywhere';body.textContent=entry.message;
      panel.append(close,heading,meta,body);root.querySelector('ha-card')?.prepend(panel);
    } catch(e) {alert('Archive: '+e.message);}
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
      if(!(result.items||[]).length) box.textContent='No archived notifications';
    } catch(e) { box.textContent='Archive error: '+e.message; }
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
    const free = data.storage.free_bytes == null ? 'unknown' : `${(data.storage.free_bytes/1048576).toFixed(0)} MiB`;
    stats.textContent = `Queued: ${data.count}  |  Dead letters: ${data.dead}  |  Sent: ${data.metrics.sent || 0}  |  Failures: ${data.metrics.failures || 0}  |  Disk free: ${free}`;
    card.append(stats);
    const tabs=document.createElement('div');tabs.className='tabs';
    for (const [label,value] of [['Queue',false],['Dead letters',true]]) {
      const button=document.createElement('button'); button.textContent=label; button.disabled=this.showDead===value;
      button.addEventListener('click',()=>{this.showDead=value;this.render(data);}); tabs.append(button);
    }
    const refresh=document.createElement('button');refresh.textContent='Refresh';refresh.addEventListener('click',()=>this.refresh());tabs.append(refresh);
    const bulk=document.createElement('button');bulk.textContent=this.showDead?'Retry all dead':'Retry all pending';
    bulk.addEventListener('click',async()=>{try {await this._hass.callService('reliable_notify',this.showDead?'retry_dead':'retry_all',{});await this.refresh();}catch(e){alert(e.message);}});
    tabs.append(bulk);card.append(tabs);
    const acks=document.createElement('details');
    const ackTitle=document.createElement('summary');
    ackTitle.textContent='Acknowledgement needed: '+(data.acknowledgements||[]).length;
    acks.append(ackTitle);
    for(const ack of data.acknowledgements||[]) {
      const row=document.createElement('div');row.style.margin='9px 0';
      const label=document.createElement('span');
      label.textContent=(ack.title||ack.ack_key)+' • '+ack.priority+' • '+ack.ack_key+' ';
      const button=document.createElement('button');button.textContent='Acknowledge';
      button.addEventListener('click',async()=>{
        try {await this._hass.callWS({type:'reliable_notify/acknowledge',key:ack.ack_key});await this.refresh();}
        catch(error){alert(error.message);}
      });
      row.append(label,button);acks.append(row);
    }
    card.append(acks);
    if(data.maintenance?.database_bytes) {
      const health=document.createElement('p');
      health.textContent='Database: '+(data.maintenance.database_bytes/1048576).toFixed(1)+' MiB • Integrity: '+data.maintenance.integrity;
      card.append(health);
    }
    if((data.persons||[]).length) {
      const persons=document.createElement('p');
      persons.className='muted';
      persons.textContent='Configured people: '+data.persons.join(', ');
      card.append(persons);
    }
    const stagedBox=document.createElement('details');
    const stagedSummary=document.createElement('summary');stagedSummary.textContent='Staged (no recipient): '+(data.staged_count||0);stagedBox.append(stagedSummary);
    for(const item of data.staged||[]){
      const row=document.createElement('div');row.style.margin='12px 0';
      const preview=document.createElement('div');preview.style.whiteSpace='pre-wrap';
      preview.textContent='#'+item.id+' '+(item.title||'')+' — '+item.message;row.append(preview);
      const select=document.createElement('select');
      for(const name of data.recipient_names||[]){const opt=document.createElement('option');opt.value=name;opt.textContent=name;select.append(opt);}row.append(select);
      const send=document.createElement('button');send.textContent='Assign and send';send.disabled=!select.options.length;
      send.addEventListener('click',async()=>{try{await this._hass.callWS({type:'reliable_notify/send_staged',id:item.id,recipient:select.value});await this.refresh();}catch(e){alert(e.message);}});row.append(send);
      const del=document.createElement('button');del.textContent='Delete';del.addEventListener('click',()=>{if(confirm('Delete staged #'+item.id+'?'))this.command('delete_one',item.id,false);});row.append(del);
      stagedBox.append(row);
    }
    card.append(stagedBox);
    const wrap=document.createElement('div');wrap.className='scroll';
    const table=document.createElement('table');
    const head=document.createElement('tr');
    for(const name of ['ID','Target','Priority','Channel','Attempts','Last error','Actions']){const th=document.createElement('th');th.textContent=name;head.append(th);} table.append(head);
    const rows=this.showDead?data.dead_letters:data.queue;
    for (const row of rows) {
      const tr=document.createElement('tr');
      for(const value of [row.id,row.target,row.priority,row.action,row.attempts,row.last_error||'-']){
        const td=document.createElement('td');td.textContent=String(value);tr.append(td);
      }
      const actions=document.createElement('td'); actions.className='actions';
      for (const [name,service] of [['Retry','retry_one'],['Delete','delete_one']]) {
        const b=document.createElement('button');b.textContent=name;
        b.addEventListener('click',()=>{if(service==='delete_one' && !confirm(`Delete #${row.id}?`))return;this.command(service,row.id,this.showDead);});actions.append(b);
      }
      tr.append(actions);table.append(tr);
    }
    if(!rows.length){const tr=document.createElement('tr');const td=document.createElement('td');td.colSpan=7;td.className='muted';td.textContent='No messages';tr.append(td);table.append(tr);}
    wrap.append(table);card.append(wrap);
    const details=document.createElement('details');const summary=document.createElement('summary');summary.textContent='Retry policies and history';details.append(summary);
    const policyTitle=document.createElement('p');policyTitle.textContent='Retry policies (0 attempts = unlimited)';details.append(policyTitle);
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
    const save=document.createElement('button');save.textContent='Save retry policies';
    save.addEventListener('click',async()=>{
      const policies={};
      for(const [priority, fields] of Object.entries(policyFields)) {
        policies[priority]={};
        for(const [key,input] of Object.entries(fields)) policies[priority][key]=Number(input.value);
      }
      try {await this._hass.callWS({type:'reliable_notify/set_retry_policies',policies}); await this.refresh();}
      catch(error){alert('Cannot save retry policies: '+error.message);}
    });
    details.append(save);
    const recent=document.createElement('div');recent.textContent=(data.history||[]).slice(0,15).map(r=>`#${r.id} ${r.status} ${r.action} (${r.attempts})`).join('\n');recent.style.whiteSpace='pre-line';details.append(recent);card.append(details);
    const retentionBox=document.createElement('details');
    const retentionHeading=document.createElement('summary');
    retentionHeading.textContent='Archive retention by type (days; 0 = purge on send)';
    retentionBox.append(retentionHeading);
    const retentionEditor=document.createElement('textarea');
    retentionEditor.value=JSON.stringify(data.retention||{},null,2);
    retentionEditor.rows=7;retentionEditor.style.width='100%';
    retentionEditor.setAttribute('aria-label','Archive retention rules JSON');
    const retentionSave=document.createElement('button');
    retentionSave.textContent='Save archive retention';
    retentionSave.addEventListener('click',async()=>{
      try {
        const retention=JSON.parse(retentionEditor.value);
        await this._hass.callWS({type:'reliable_notify/set_archive_retention',retention});
        await this.refresh();
      } catch(e) { alert('Archive retention: '+e.message); }
    });
    retentionBox.append(retentionEditor,retentionSave);
    card.append(retentionBox);
    const archive=document.createElement('details');
    const archiveHeading=document.createElement('summary');archiveHeading.textContent='Notification archive (per-type retention, max 2000 completed)';archive.append(archiveHeading);
    const search=document.createElement('input');search.type='search';search.placeholder='Search full notification text';search.style.margin='10px 8px 10px 0';
    search.setAttribute('aria-label','Search notification archive');
    const find=document.createElement('button');find.textContent='Search';
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
customElements.define('reliable-notify-card', ReliableNotifyCard);
window.customCards=window.customCards||[];
window.customCards.push({type:'reliable-notify-card',name:'Reliable Notify',description:'Persistent notification queue and interactive administration'});