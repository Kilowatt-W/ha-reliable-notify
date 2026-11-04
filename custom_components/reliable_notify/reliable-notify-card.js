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
      this._timer = setInterval(() => this.refresh(), 15000);
      this.refresh();
    }
  }
  disconnectedCallback() {
    if (this._timer) clearInterval(this._timer);
    this._timer = null;
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
  render(data) {
    const root = this.shadowRoot;
    root.replaceChildren();
    const style = document.createElement('style');
    style.textContent = `:host{display:block;color:var(--primary-text-color)}ha-card{padding:18px}h2{margin:0 0 12px} .stats{display:flex;gap:18px;flex-wrap:wrap} .tabs{margin:12px 0}button{border:1px solid var(--divider-color);border-radius:8px;padding:5px 10px;background:var(--card-background-color);color:inherit;cursor:pointer}button:hover{background:var(--secondary-background-color)}table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:7px;text-align:left;border-bottom:1px solid var(--divider-color)} .scroll{overflow-x:auto} .muted{color:var(--secondary-text-color)} .actions{white-space:nowrap}`;
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
    const refresh=document.createElement('button');refresh.textContent='Refresh';refresh.addEventListener('click',()=>this.refresh());tabs.append(refresh);card.append(tabs);
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
    const info=document.createElement('pre');info.textContent=JSON.stringify(data.policies,null,2);details.append(info);
    const recent=document.createElement('div');recent.textContent=(data.history||[]).slice(0,15).map(r=>`#${r.id} ${r.status} ${r.action} (${r.attempts})`).join('\n');recent.style.whiteSpace='pre-line';details.append(recent);card.append(details);
    root.append(card);
  }
}
customElements.define('reliable-notify-card', ReliableNotifyCard);
window.customCards=window.customCards||[];
window.customCards.push({type:'reliable-notify-card',name:'Reliable Notify',description:'Persistent notification queue and interactive administration'});