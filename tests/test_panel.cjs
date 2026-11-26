/* Functional DOM tests: edit the same controls an administrator uses. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {readFileSync}=require('node:fs');
const {JSDOM}=require('jsdom');
const source=readFileSync('custom_components/reliable_notify/reliable-notify-panel.js','utf8').replace(/^import .*;$/m,'');
function setup(responses={}){
  const dom=new JSDOM('<body></body>',{runScripts:'outside-only',url:'https://ha.test/'});
  dom.window.structuredClone=structuredClone;
  dom.window.confirm=()=>true;
  dom.window.eval(readFileSync('custom_components/reliable_notify/reliable-notify-card.js','utf8').replace(/^export /gm,'')+'\n'+source);
  const panel=dom.window.document.createElement('reliable-notify-panel');
  const calls=[];
  panel._hass={language:'de',states:{},services:{},callWS:async msg=>{calls.push(msg);return structuredClone(responses[msg.type.split('/')[1]]||{saved:true});}};
  const box=dom.window.document.createElement('main');
  panel.shadowRoot.append(box);
  const plain=value=>JSON.parse(JSON.stringify(value));
  return {dom,panel,box,calls,plain};
}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function control(node,label){
  const l=[...node.querySelectorAll('label')].find(l=>l.textContent===label);
  assert.ok(l,'Missing label '+label);
  return l.control;
}
function click(node,text){
  const button=[...node.querySelectorAll('button')].find(b=>b.textContent===text);
  assert.ok(button,'Missing button '+text);button.click();
}

test('nested typed fields retain secrets, optional values and lists without JSON input',()=>{
  const {panel,box,plain}=setup();
  const original={action:'reliable_notify.gotify',data:{base_url:'https://notify.test',token:'secret',allow_private:false},
    extra:{nullable:null,items:['on',0,true,{message:'{{ value }}: hello\nworld'}]}};
  const editor=panel.fieldEditor(original,{defaults:panel.fieldDefaults('recipient')});box.append(editor.node);
  assert.deepEqual(plain(editor.read()),original);
  assert.equal(control(box,'Token').type,'password');
  control(box,'Private Zieladressen erlauben').click();
  assert.equal(editor.read().data.allow_private,true);
  assert.equal(box.querySelector('textarea').value,'{{ value }}: hello\nworld');
});

test('profiles save form edits and preserve guards and acknowledgements',async()=>{
  const definition={priority:'warning',archive_days:7,only_if:{entity_id:'binary_sensor.window',state:'on'},
    acknowledgement:{required:true,escalation:[{after:300,recipients:['phone']}]}};
  const {panel,box,calls,plain}=setup({profiles:{profiles:{windows:definition}}});
  await panel.profiles(box);
  control(box,'Aufbewahrung (Tage)').value='12';
  click(box,'Speichern');await tick();
  const saved=calls.find(c=>c.type.endsWith('/set_profiles'));
  assert.deepEqual(plain(saved.profiles.windows),{...definition,archive_days:12});
  const details=box.querySelector('details');assert.equal(details.open,false);
  details.open=true;details.dispatchEvent(new panel.ownerDocument.defaultView.Event('toggle'));
  assert.match(details.querySelector('pre').textContent,/"archive_days": 12/);
});

test('existing route is loaded in full before saving, and all categories stay visible',async()=>{
  const definition={action:'telegram_bot.send_message',data:{chat_id:-100123,parse_mode:'HTML',disable_notification:true}};
  const {panel,box,calls,plain}=setup({admin_inventory:{routes:{recipients:{telegram:{}},groups:{},persons:{}}},route_definition:{definition}});
  await panel.routes(box);
  assert.deepEqual([...box.querySelectorAll('h2')].map(n=>n.textContent),['Ziele']);
  click(box,'telegram');await tick();
  click(box,'Speichern');await tick();
  assert.deepEqual(plain(calls.find(c=>c.type.endsWith('/set_route')).definition),definition);
});

test('duplicate profile names and invalid numbers never issue a save',async()=>{
  const {panel,box,calls}=setup({profiles:{profiles:{one:{priority:'info',archive_days:7},two:{priority:'info'}}}});
  await panel.profiles(box);
  control(box,'Aufbewahrung (Tage)').value='366';click(box,'Speichern');await tick();
  assert.equal(calls.filter(c=>c.type.endsWith('/set_profiles')).length,0);
  control(box,'Aufbewahrung (Tage)').value='2';
  const names=[...box.querySelectorAll('input')].filter(n=>n.placeholder==='Name');names[1].value='one';
  click(box,'Speichern');await tick();
  assert.equal(calls.filter(c=>c.type.endsWith('/set_profiles')).length,0);
  assert.match(box.textContent,/Doppelter Name/);
});

test('settings render every section and logging uses seven level selectors',async()=>{
  const {panel,box}=setup({dashboard:{policies:{info:{max_attempts:8,base_seconds:30,max_delay:1800}},retention:{info:1},
    smart:{quiet_hours:{enabled:false,start:'22:00',end:'07:00',allow_priorities:['critical']},rate_limit_per_minute:10,digest_window_seconds:300}},statistics:{}});
  await panel.settings(box);
  assert.equal(box.querySelectorAll('h2').length,6);
  for(const label of ['Telegram','SMTP','Companion-App','HA Notify','Webhook','ntfy','Gotify']){
    assert.equal(control(box,label).tagName,'SELECT');
    assert.equal(control(box,label).options.length,5);
  }
  assert.equal(box.querySelectorAll('textarea').length,0);
});

test('settings can reset all errors after a confirmation, in German and English',async()=>{
  const settings={dashboard:{policies:{info:{max_attempts:8,base_seconds:30,max_delay:1800}},retention:{info:1},
    smart:{quiet_hours:{enabled:false,start:'22:00',end:'07:00',allow_priorities:['critical']},rate_limit_per_minute:10,digest_window_seconds:300}},
    statistics:{},reset_errors:{dead_letters:204,history:210,daily:7}};
  const {dom,panel,box,calls}=setup(settings);
  await panel.settings(box);
  const section=box.querySelector('section.reset-errors');
  assert.ok(section);assert.equal(section.querySelector('h2').textContent,'Fehler zurücksetzen');
  dom.window.confirm=()=>false;
  click(section,'Alle Fehler löschen');await tick();
  assert.equal(calls.filter(c=>c.type==='reliable_notify/reset_errors').length,0);
  dom.window.confirm=()=>true;
  click(section,'Alle Fehler löschen');await tick();await tick();
  assert.deepEqual(calls.filter(c=>c.type==='reliable_notify/reset_errors').map(c=>Object.keys(c)),[['type']]);
  assert.match(section.textContent,/Zurückgesetzt: 204 unzustellbare Nachrichten, 210 Einträge der Fehleranalyse\./);
  const english=setup(settings);english.panel._hass.language='en';
  await english.panel.settings(english.box);
  const en=english.box.querySelector('section.reset-errors');
  assert.equal(en.querySelector('h2').textContent,'Reset errors');
  click(en,'Delete all errors');await tick();await tick();
  assert.match(en.textContent,/Reset: 204 undeliverable messages, 210 failure analysis entries\./);
});

test('YAML preview is valid for strings, Jinja, arrays, null and empty objects',()=>{
  const {panel}=setup();
  const value={yes:'on',colon:'a: b',jinja:'{{ sensor }}\nsecond line',list:[{x:true},[],null],empty:{},number:3};
  // Compare through Python's YAML parser, independent from the frontend serializer.
  const parsed=JSON.parse(require('node:child_process').execFileSync('python',['-c',
    'import sys,yaml,json;print(json.dumps(yaml.safe_load(sys.stdin.read())))'],{input:panel.yaml(value),encoding:'utf8'}));
  assert.deepEqual(parsed,value);
});


test('new target entry is discoverable from settings and opens a blank recipient form',async()=>{
  const {panel,box}=setup({dashboard:{policies:{},retention:{},smart:{}},statistics:{},
    admin_inventory:{routes:{recipients:{},groups:{},persons:{}}}});
  await panel.settings(box);
  click(box,'Neues Ziel anlegen');await tick();
  assert.equal(panel._section,'routes');
  assert.match(panel.shadowRoot.textContent,/Ziele \& Personen/);
  click(panel.shadowRoot,'Neues Ziel anlegen');
  const name=panel.shadowRoot.querySelector('input[placeholder="Eindeutiger Name"]');
  assert.equal(name.value,'');
});

test('target and person browsers use existing HA entities and preserve missing configured IDs',()=>{
  const {panel,box,plain}=setup();
  panel._hass.states={
    'notify.mail':{attributes:{friendly_name:'Clinic mail'}},
    'notify.phone':{attributes:{friendly_name:'My phone'}},
    'person.wolfgang':{attributes:{friendly_name:'Wolfgang'}},
    'sensor.noise':{attributes:{friendly_name:'Not a target'}}
  };
  panel._hass.services={notify:{mobile_app_phone:{name:'Phone push'},send_message:{name:'Send'}},
    light:{turn_on:{name:'Light'}}};
  const editor=panel.fieldEditor({action:'notify.send_message',target_entity:'notify.removed',entity:'person.wolfgang'});
  box.append(editor.node);
  const notify=control(box,'Notify-Zielentität'),person=control(box,'Person-Entität');
  assert.equal(notify.tagName,'SELECT');assert.equal(person.tagName,'SELECT');
  assert.deepEqual([...notify.options].map(o=>o.value),['','notify.mail','notify.phone','notify.removed']);
  assert.match(notify.textContent,/Clinic mail — notify.mail/);
  assert.deepEqual([...person.options].map(o=>o.value),['','person.wolfgang']);
  assert.equal(notify.value,'notify.removed');
  notify.value='notify.mail';person.value='person.wolfgang';
  assert.deepEqual(plain(editor.read()),{action:'notify.send_message',target_entity:'notify.mail',entity:'person.wolfgang'});
  assert.deepEqual([...box.querySelectorAll('datalist option')].map(o=>o.value),['notify.mobile_app_phone','notify.send_message']);
  notify.value='';assert.equal(editor.read().target_entity,'');
});

test('invalid target name gives a localized example and never reaches the backend',async()=>{
  for(const [language,label,expected] of [['de','Speichern',/Ungültiger interner Name/],['en','Save',/Invalid internal name/]]){
    const {panel,box,calls}=setup({admin_inventory:{routes:{recipients:{},groups:{},persons:{}}}});
    panel._hass.language=language;
    await panel.routes(box);
    const name=box.querySelector('input[name=route_id]');name.value='RN-KW-Telegram';
    click(box,label);await tick();
    assert.match(box.textContent,expected);assert.match(box.textContent,/rn_kw_telegram/);
    assert.equal(name.getAttribute('aria-invalid'),'true');
    assert.equal(calls.filter(c=>c.type.endsWith('/set_route')).length,0);
    name.value='rn_kw_telegram';click(box,label);await tick();
    assert.equal(calls.find(c=>c.type.endsWith('/set_route')).name,'rn_kw_telegram');
    assert.equal(name.hasAttribute('aria-invalid'),false);
  }
});

test('English panel labels and YAML preview keep technical keys and user data unchanged',async()=>{
  const definition={action:'notify.send_message',target_entity:'notify.missing',data:{message:'Nachricht',token:'Speichern'}};
  const {panel,box,calls,plain}=setup({admin_inventory:{routes:{recipients:{Speichern:{}},groups:{},persons:{}}},route_definition:{definition}});
  panel._hass.language='en-GB';
  await panel.routes(box);
  assert.deepEqual([...box.querySelectorAll('h2')].map(e=>e.textContent),['Targets']);
  assert.ok(control(box,'Notify target entity'));
  // Existing route aliases and message values are user data, never localized.
  click(box,'Speichern');await tick();
  assert.equal(box.querySelector('input[placeholder="Unique name"]').value,'Speichern');
  const editor=panel.fieldEditor(definition);assert.deepEqual(plain(editor.read()),definition);
  const yaml=panel.yaml(editor.read());assert.match(yaml,/"token": "Speichern"/);
  assert.match(box.querySelector('section summary').textContent,/Show YAML/);
  panel._hass.language='fr';assert.equal(panel.fieldLabel('target_entity'),'Notify target entity');
});

test('direct target entry works in a fully rendered panel and follows HA language changes',async()=>{
  const {panel}=setup({admin_inventory:{routes:{recipients:{},groups:{},persons:{}}},
    dashboard:{policies:{},retention:{},smart:{}},statistics:{}});
  panel._section='settings';panel.render();await tick();
  click(panel.shadowRoot,'Neues Ziel anlegen');await tick();
  assert.equal(panel._section,'routes');
  assert.ok(panel.shadowRoot.querySelector('#content input[placeholder="Eindeutiger Name"]'));
  assert.equal([...panel.shadowRoot.querySelectorAll('nav button.active')][0].textContent,'Ziele & Personen');
  panel.hass={...panel._hass,language:'en'};await tick();
  assert.ok(panel.shadowRoot.querySelector('#content input[placeholder="Unique name"]'));
  assert.equal([...panel.shadowRoot.querySelectorAll('nav button.active')][0].textContent,'Targets & people');
});

test('standalone card renders German and English without translating recipient aliases',async()=>{
  const {dom}=setup();
  const card=dom.window.document.createElement('reliable-notify-card');
  card.config={};card.attachShadow({mode:'open'});
  const data={count:0,dead:0,storage:{free_bytes:null},metrics:{},queue:[],dead_letters:[],policies:{},retention:{},smart:{},
    staged:[{id:7,title:'My title',message:'Meine Nachricht'}],recipient_names:['Save']};
  for(const [language,empty,heading] of [['de','Keine Nachrichten','Wartend:'],['en','No messages','Queued:']]){
    card._hass={language};card.render(data);
    assert.match(card.shadowRoot.textContent,new RegExp(empty));
    assert.match(card.shadowRoot.querySelector('.stats').textContent,new RegExp(heading));
    assert.equal(card.shadowRoot.querySelector('select option').textContent,'Save');
    assert.match(card.shadowRoot.textContent,/Meine Nachricht/);
  }
});

test('each saved target has an icon test button and reports transport acceptance',async()=>{
  const {panel,box,calls}=setup({admin_inventory:{routes:{recipients:{phone:{}},groups:{family:[]},persons:{wolfgang:{}}}},
    test_route:{ids:[5],not_before:0},archive_detail:{id:5,status:'sent'}});
  await panel.routes(box);
  assert.equal([...box.querySelectorAll('button')].filter(b=>b.textContent==='Test senden').length,3);
  assert.equal(box.querySelectorAll('.route-item button.test ha-icon[icon="mdi:bell-ring-outline"]').length,3);
  assert.equal(box.querySelectorAll('button.danger ha-icon[icon="mdi:delete-outline"]').length,1);
  // The list is sorted by name: family, phone, wolfgang.
  const phone=[...box.querySelectorAll('.route-item')].find(i=>i.querySelector('button[data-route=phone]'));
  phone.querySelector('button.test').click();await tick();await tick();
  assert.equal(calls.filter(c=>c.type.endsWith('/test_route')).length,1);
  assert.deepEqual([calls.find(c=>c.type.endsWith('/test_route')).name,calls.find(c=>c.type.endsWith('/test_route')).category],['phone','recipients']);
  assert.match(phone.querySelector('p').textContent,/Vom Transport angenommen/);
  assert.equal(phone.querySelector('p').className,'status');
  assert.equal(phone.querySelector('button.test').disabled,false);
});

test('test mode, delivery failures and quiet hours do not claim successful delivery',async()=>{
  for(const [status,expected] of [['staged',/Testmodus/],['dead',/fehlgeschlagen/],['queued',/Ruhezeiten aktiv/]]){
    const {panel,box,calls}=setup({admin_inventory:{routes:{recipients:{phone:{}},groups:{},persons:{}}},
      test_route:{ids:[9],not_before:Date.now()/1000+3600},archive_detail:{id:9,status}});
    await panel.routes(box);click(box,'Test senden');await tick();await tick();
    const result=box.querySelector('.route-item p');
    assert.match(result.textContent,expected);assert.notEqual(result.className,'status');
    assert.equal(calls.filter(c=>c.type.endsWith('/test_route')).length,1);
  }
});

test('display name suggests the internal ID, is saved as label and shown in the target list',async()=>{
  for(const [language,save,displayLabel,idLabel] of [['de','Speichern','Anzeigename (Klarname)','Interner Name (ID)'],['en','Save','Display name','Internal name (ID)']]){
    const {panel,box,calls,dom}=setup({admin_inventory:{routes:{recipients:{tg_buero:{}},groups:{},persons:{}},labels:{tg_buero:'Telegram Büro'}}});
    panel._hass.language=language;
    await panel.routes(box);
    const section=box.querySelector('section');
    const display=control(section,displayLabel),name=control(section,idLabel);
    assert.equal(display.name,'route_label');assert.equal(name.name,'route_id');
    // Existing entry is listed by display name and alias; aliases are never translated.
    assert.ok([...section.querySelectorAll('.route-item button')].some(b=>b.textContent==='Telegram Büro (tg_buero)'));
    display.value='Telegram Wölfi – Büro 2';display.dispatchEvent(new dom.window.Event('input',{bubbles:true}));
    assert.equal(name.value,'telegram_woelfi_buero_2');
    click(section,save);await tick();
    const saved=calls.find(c=>c.type.endsWith('/set_route'));
    assert.equal(saved.name,'telegram_woelfi_buero_2');assert.equal(saved.label,'Telegram Wölfi – Büro 2');
  }
});

test('a manually typed internal ID is not overwritten and existing IDs stay fixed',async()=>{
  const definition={action:'notify.mobile_app_phone'};
  const {panel,box,calls,dom}=setup({admin_inventory:{routes:{recipients:{tg_buero:{}},groups:{},persons:{}},labels:{tg_buero:'Telegram Büro'}},
    route_definition:{definition}});
  await panel.routes(box);
  const section=box.querySelector('section');
  const display=section.querySelector('input[name=route_label]'),name=section.querySelector('input[name=route_id]');
  name.value='my_phone';display.value='Mein Handy';display.dispatchEvent(new dom.window.Event('input',{bubbles:true}));
  assert.equal(name.value,'my_phone');
  click(section,'Telegram Büro (tg_buero)');await tick();
  assert.equal(name.value,'tg_buero');assert.equal(display.value,'Telegram Büro');
  display.value='Telegram Büro neu';display.dispatchEvent(new dom.window.Event('input',{bubbles:true}));
  assert.equal(name.value,'tg_buero');
  click(section,'Speichern');await tick();
  const saved=calls.find(c=>c.type.endsWith('/set_route'));
  assert.deepEqual([saved.name,saved.label],['tg_buero','Telegram Büro neu']);
  assert.deepEqual(JSON.parse(JSON.stringify(saved.definition)),definition);
});

test('group members offer known targets with display names',async()=>{
  const {panel,box}=setup({admin_inventory:{routes:{recipients:{tg_buero:{},mail:{}},groups:{family:['mail']},persons:{}},labels:{tg_buero:'Telegram Büro'}}});
  await panel.routes(box);
  const groups=box.querySelector('section');
  const type=groups.querySelector('select[name=route_type]');type.value='groups';type.dispatchEvent(new panel.ownerDocument.defaultView.Event('change'));
  click(groups,'Eintrag hinzufügen');
  const input=groups.querySelector('.list-fields input');
  const options=[...groups.querySelectorAll('datalist#'+input.getAttribute('list')+' option')];
  assert.deepEqual(options.map(o=>o.value),['family','mail','tg_buero']);
  assert.equal(options.find(o=>o.value==='tg_buero').label,'Telegram Büro (tg_buero)');
});

test('choice values and backend errors are shown in German and English',async()=>{
  for(const [language,priority,error] of [['de','Kritisch',/Ungültige Zielkonfiguration: tg requires a notify entity/],['en','Critical',/Invalid target configuration: tg requires a notify entity/]]){
    const {panel,box}=setup({admin_inventory:{routes:{recipients:{},groups:{},persons:{}}}});
    panel._hass.language=language;
    const editor=panel.fieldEditor({priority:'critical',strategy:'digest'});box.append(editor.node);
    const select=box.querySelector('select');
    assert.equal(select.value,'critical');assert.equal(select.selectedOptions[0].textContent,priority);
    assert.deepEqual(JSON.parse(JSON.stringify(editor.read())),{priority:'critical',strategy:'digest'});
    const status=panel.element('p');
    await panel.run(status,async()=>{throw Object.assign(Error('tg requires a notify entity'),{code:'invalid_route'});});
    assert.match(status.textContent,error);
    await panel.run(status,async()=>{throw {code:'unauthorized',message:'Administrator required'};});
    assert.doesNotMatch(status.textContent,/Administrator required/);
  }
});

test('card shows translated priorities and target display names without changing values',async()=>{
  const {dom}=setup();
  const card=dom.window.document.createElement('reliable-notify-card');
  card.config={};card.attachShadow({mode:'open'});
  const data={count:1,dead:0,storage:{free_bytes:null},metrics:{},dead_letters:[],policies:{critical:{max_attempts:0,base_seconds:5,max_delay:60}},
    retention:{},smart:{},queue:[{id:3,target:'notify.mail',priority:'critical',action:'notify.send_message',attempts:0}],
    staged:[{id:7,title:'T',message:'M'}],recipient_names:['tg_buero'],labels:{tg_buero:'Telegram Büro'}};
  for(const [language,priority,retries] of [['de','Kritisch','Maximale Versuche'],['en','Critical','Maximum attempts']]){
    card._hass={language};card.render(data);
    assert.equal(card.shadowRoot.querySelector('.rn-priority').textContent,priority);
    assert.equal(card.shadowRoot.querySelector('.rn-priority').title,'critical');
    const option=card.shadowRoot.querySelector('select option');
    assert.equal(option.value,'tg_buero');assert.equal(option.textContent,'Telegram Büro (tg_buero)');
    assert.match(card.shadowRoot.textContent,new RegExp(retries));
  }
});

test('help can be shown per section, follows the language and stays open across sections',async()=>{
  const {panel}=setup({dashboard:{policies:{},retention:{},smart:{}},statistics:{},admin_inventory:{routes:{recipients:{},groups:{},persons:{}}}});
  panel._section='settings';panel.render();await tick();
  const root=panel.shadowRoot;
  // A round "?" right after the title replaces the big help button; its label says what it does.
  const toggle=root.querySelector('.hero-title button.rn-help-toggle');
  assert.equal(toggle.textContent,'?');assert.ok(toggle.classList.contains('rn-help-icon'));
  assert.equal(toggle.getAttribute('aria-label'),'Hilfe einblenden');assert.equal(toggle.title,'Hilfe einblenden');
  assert.equal(toggle.getAttribute('aria-expanded'),'false');
  assert.equal(root.querySelector('.hero-title').firstElementChild.tagName,'H1');
  let help=root.querySelector('#content details.rn-help');
  assert.equal(help.open,false);assert.equal(help.querySelector('summary').textContent,'Hilfe zu diesem Bereich');
  assert.match(help.textContent,/Alle Optionen gibt es gesammelt/);
  assert.match(help.querySelector('a').href,/docs\/CONFIGURATION\.md$/);
  toggle.click();
  assert.equal(help.open,true);assert.equal(toggle.textContent,'?');assert.equal(toggle.getAttribute('aria-label'),'Hilfe ausblenden');
  assert.equal(toggle.getAttribute('aria-expanded'),'true');
  click(root.querySelector('nav'),'Ziele & Personen');await tick();
  help=root.querySelector('#content details.rn-help');
  assert.equal(help.open,true);assert.match(help.textContent,/Neues Ziel anlegen/);assert.match(help.querySelector('pre').textContent,/reliable_notify\.enqueue/);
  panel.hass={...panel._hass,language:'en'};await tick();
  help=root.querySelector('#content details.rn-help');
  assert.equal(help.querySelector('summary').textContent,'Help for this section');
  assert.match(help.textContent,/Create new target/);assert.equal(help.open,true);
  assert.equal(root.querySelector('button.rn-help-toggle').getAttribute('aria-label'),'Hide help');
  // A closed help takes no space: the hidden-when-closed rule applies to every section.
  assert.match(root.querySelector('style').textContent,/details\.rn-help:not\(\[open\]\)\{display:none\}/);
});

test('targets show group members and keep the section help behind a "?" after the intro text',async()=>{
  for(const [language,contains,empty,helpLabel,intro] of [['de','Enthält: Handy Tricorder, berniphone','Leere Gruppe','Hilfe zu diesem Bereich','Hier neue Ziele anlegen'],
    ['en','Contains: Handy Tricorder, berniphone','Empty group','Help for this section','Create targets here']]){
    const {panel}=setup({admin_inventory:{routes:{recipients:{tricorder:{},berniphone:{}},groups:{all_mobile:['tricorder','berniphone'],none:[]},persons:{}},
      labels:{tricorder:'Handy Tricorder',all_mobile:'Alle Mobile Apps'}}});
    panel._hass.language=language;panel._section='routes';panel.render();await tick();
    const root=panel.shadowRoot,content=root.querySelector('#content');
    // No help block above the targets: only the intro line with a "?" button.
    assert.equal(content.firstElementChild.className,'rn-intro');
    assert.match(content.querySelector('.rn-intro p').textContent,new RegExp('^'+intro));
    const icon=content.querySelector('.rn-intro button.rn-help-icon');
    assert.equal(icon.textContent,'?');assert.equal(icon.getAttribute('aria-label'),helpLabel);
    const help=root.getElementById(icon.getAttribute('aria-controls'));
    assert.ok(help.classList.contains('rn-help-inline'));assert.equal(help.open,false);
    assert.equal(content.querySelectorAll('details.rn-help').length,1);
    icon.click();await tick();
    assert.equal(help.open,true);assert.equal(icon.getAttribute('aria-expanded'),'true');
    assert.equal(root.querySelector('button.rn-help-toggle').getAttribute('aria-expanded'),'true');
    icon.click();await tick();assert.equal(help.open,false);
    const members=[...content.querySelectorAll('.route-item[data-kind=groups] .route-members')].map(p=>p.textContent);
    assert.deepEqual(members,[contains,empty]);
    // Recipients without action data do not get a detail line.
    assert.equal(content.querySelector('.route-item[data-kind=recipients] .route-members'),null);
  }
});

test('one target list shows type, details and filters; new entries choose their type',async()=>{
  for(const [language,heading,types,chips,channel] of [
    ['de','Ziele',['Gruppe','Person','Einzelziel','Einzelziel'],['Alle (4)','Einzelziele (2)','Gruppen (1)','Personen (1)'],'Kanäle: Handy'],
    ['en','Targets',['Group','Person','Single target','Single target'],['All (4)','Single targets (2)','Groups (1)','People (1)'],'Channels: Handy']]){
    const {panel,box,calls,dom}=setup({admin_inventory:{routes:{
        recipients:{phone:{action:'notify.mobile_app_phone',target_entity:''},tg:{action:'notify.send_message',target_entity:'notify.tg_chat'}},
        groups:{all_mobile:['phone']},persons:{anna:{entity:'person.anna',channels:{mobile:'phone'}}}},
      labels:{phone:'Handy',all_mobile:'Alle Mobile Apps',anna:'Anna'}},route_definition:{definition:['phone']}});
    panel._hass.language=language;await panel.routes(box);
    assert.equal(box.querySelectorAll('section').length,1);
    assert.deepEqual([...box.querySelectorAll('h2')].map(h=>h.textContent),[heading]);
    // Sorted by display name; the type badge is separate from the edit button (aliases stay untranslated).
    const items=[...box.querySelectorAll('.route-item')];
    assert.deepEqual(items.map(i=>i.querySelector('button').textContent),['Alle Mobile Apps (all_mobile)','Anna (anna)','Handy (phone)','tg']);
    // Type as icon only, with hover text and accessible name that explain it.
    const badges=items.map(i=>i.querySelector('.route-type'));
    assert.deepEqual(badges.map(b=>b.textContent),['','','','']);
    assert.deepEqual(badges.map(b=>b.getAttribute('aria-label').split(':')[0]),types);
    assert.deepEqual(badges.map(b=>b.title),badges.map(b=>b.getAttribute('aria-label')));
    assert.deepEqual(badges.map(b=>b.getAttribute('role')),['img','img','img','img']);
    assert.deepEqual(badges.map(b=>b.querySelector('ha-icon').getAttribute('icon')),['mdi:account-group','mdi:account','mdi:send-outline','mdi:send-outline']);
    assert.match(badges[0].title,language==='de'?/alle enthaltenen Ziele/:/every target it contains/);
    assert.deepEqual(items.map(i=>i.querySelector('.route-members')?.textContent),
      [language==='de'?'Enthält: Handy':'Contains: Handy',channel,'notify.mobile_app_phone','notify.tg_chat']);
    // The detail sits next to the name in one grid row; the full text stays available on hover.
    assert.equal(items[2].querySelector('.route-members').title,'notify.mobile_app_phone');
    const chipsNodes=[...box.querySelectorAll('.rn-filter button.rn-chip')];
    assert.deepEqual(chipsNodes.map(c=>c.textContent),chips);
    assert.equal(chipsNodes[0].getAttribute('aria-pressed'),'true');
    chipsNodes[2].click();
    assert.deepEqual(items.filter(i=>!i.hidden).map(i=>i.dataset.kind),['groups']);
    assert.equal(chipsNodes[2].getAttribute('aria-pressed'),'true');assert.equal(chipsNodes[0].getAttribute('aria-pressed'),'false');
    // A new entry starts with the filtered type; the type can be changed until saving.
    const type=box.querySelector('select[name=route_type]');
    click(box,language==='de'?'Neues Ziel anlegen':'Add target');
    assert.equal(type.value,'groups');assert.equal(type.disabled,false);
    type.value='persons';type.dispatchEvent(new dom.window.Event('change'));
    box.querySelector('input[name=route_id]').value='bert';
    click(box,language==='de'?'Speichern':'Save');await tick();
    const saved=calls.find(c=>c.type.endsWith('/set_route'));
    assert.equal(saved.category,'persons');assert.equal(type.disabled,true);
    // Opening an existing group locks its type.
    chipsNodes[0].click();
    items[0].querySelector('button').click();await tick();
    assert.equal(type.value,'groups');assert.equal(type.disabled,true);
    assert.equal(calls.find(c=>c.type.endsWith('/route_definition')).category,'groups');
  }
});

test('each section heading reuses the icon and colour of its navigation button',async()=>{
  const {panel}=setup({admin_inventory:{routes:{recipients:{},groups:{},persons:{}}},dashboard:{policies:{},retention:{},smart:{}},statistics:{}});
  panel._section='routes';panel.render();await tick();
  const root=panel.shadowRoot;
  const navIcon=label=>[...root.querySelectorAll('nav button')].find(b=>b.textContent===label);
  for(const [label,section] of [['Ziele & Personen','routes'],['Einstellungen','settings']]){
    const button=navIcon(label);button.click();await tick();await tick();
    const heading=root.querySelector('#content [data-section='+section+']');
    assert.ok(heading,section);
    assert.equal(heading.querySelector('ha-icon').getAttribute('icon'),button.querySelector('ha-icon').getAttribute('icon'));
    assert.equal(heading.dataset.tone,button.dataset.tone);
  }
  // The embedded message card shows the Messages icon instead of the app icon.
  navIcon('Nachrichten').click();await tick();
  const card=root.querySelector('#content reliable-notify-card');
  assert.equal(card.config.icon,navIcon('Nachrichten').querySelector('ha-icon').getAttribute('icon'));
});

test('automation check lists proposals first with copyable YAML, editor link, reason overview and target creation',async()=>{
  const report={proposed:1,manual:2,files:[{file:'/config/automations.yaml',relative_file:'automations.yaml',sha256:'c'.repeat(64),proposals:[
    {path:'root[0].actions[0]',automation:'Küche',status:'manual',source:'notify.send_message',reason_code:'no_route',
     suggested_target:{action:'notify.send_message',target_entity:'notify.echo_kueche'},edit_url:'/config/automation/edit/17'},
    {path:'root[1].actions[0]',automation:'Fenster',status:'proposed',source:'notify.mobile_app_phone',route:'phone',reason_code:'unambiguous_data',
     replacement:{action:'notify.reliable_phone',data:{message:'offen',data:{tag:'fenster'}}},edit_url:'/config/automation/edit/18'},
    {path:'root[2].actions[0]',automation:'Foto',status:'manual',source:'telegram_bot.send_photo',reason_code:'response_used'}]}]};
  for(const [language,overview,open,create,copy] of [['de','Manuell zu prüfen, nach Grund:','Automation im HA-Editor öffnen','Ziel dafür anlegen','Kopieren'],
    ['en','To check manually, by reason:','Open the automation in the HA editor','Create a target for it','Copy']]){
    const {panel,box}=setup({migration_scan:report,admin_inventory:{routes:{recipients:{phone:{}},groups:{},persons:{}}}});
    panel._hass.language=language;
    panel._hass.states={'notify.echo_kueche':{attributes:{friendly_name:'Echo Küche'}}};
    await panel.migration(box);
    [...box.querySelectorAll('button')].find(b=>b.textContent.startsWith(language==='de'?'Benachrichtigungen analysieren':'Analyse notifications')).click();await tick();await tick();
    assert.match(box.textContent,new RegExp(overview));
    assert.equal(box.querySelectorAll('ul.rn-reasons li').length,2);
    const entries=[...box.querySelectorAll('details')];
    assert.match(entries[0].querySelector('summary').textContent,/^Fenster/);  // proposal first
    assert.match(entries[0].querySelector('.rn-code pre').textContent,/action: notify.reliable_phone/);
    assert.match(entries[0].querySelector('.rn-code pre').textContent,/tag: fenster/);
    assert.equal(entries[0].querySelector('.rn-code button').textContent,copy);
    assert.equal(entries[0].querySelector('.rn-code button ha-icon').getAttribute('icon'),'mdi:content-copy');
    const link=[...entries[0].querySelectorAll('a')].find(a=>a.textContent===open);
    assert.equal(link.getAttribute('href'),'/config/automation/edit/18');
    // Missing target: one click opens Targets with the suggested definition (not saved).
    const kitchen=entries.find(e=>/^Küche/.test(e.querySelector('summary').textContent));
    // Nothing to replace yet: no editor link, only target creation.
    assert.equal(kitchen.querySelector('a'),null);
    const createButton=[...kitchen.querySelectorAll('button')].find(b=>b.textContent===create);
    assert.equal(createButton.querySelector('ha-icon').getAttribute('icon'),'mdi:plus');
    createButton.click();await tick();await tick();
    assert.equal(panel._section,'routes');
    const content=panel.shadowRoot.querySelector('#content');
    assert.equal(content.querySelector('input[name=route_label]').value,'Echo Küche');
    assert.equal(content.querySelector('input[name=route_id]').value,'echo_kueche');
    assert.equal(content.querySelector('select[name=route_type]').value,'recipients');
    assert.match(content.textContent,language==='de'?/Vorschlag aus der Automation-Prüfung/:/Suggestion from the automation check/);
  }
});

test('automation check shows translated reasons, skipped files and file errors',async()=>{
  const report={proposed:1,manual:1,files:[
    {file:'scripts.yaml',skipped:'not_present',proposals:[]},
    {file:'/config/packages/windows.yaml',relative_file:'packages/windows.yaml',sha256:'a'.repeat(64),proposed:1,manual:1,proposals:[
      {path:'root.automation[0].actions[0]',automation:'Fenster',status:'proposed',source:'telegram_bot.send_message',route:'tg_buero',
       reason_code:'unambiguous',reason:'Unambiguous static destination',replacement:{action:'notify.reliable_tg_buero',data:{message:'Hi'}},preview_diff:'+action: notify.reliable_tg_buero'},
      {path:'root.automation[0].actions[1]',automation:'Fenster',status:'manual',source:'notify.send_message',reason_code:'no_route',reason:'No configured matching route'}]},
    {file:'/config/automations.yaml',relative_file:'automations.yaml',sha256:'b'.repeat(64),proposals:[
      {path:'root[0].actions[0]',automation:'Licht',status:'proposed',source:'notify.mobile_app_x',route:'tg_buero',reason_code:'unambiguous',
       replacement:{action:'notify.reliable_tg_buero',data:{message:'x'}}}]},
    {file:'broken.yaml',error_code:'yaml_syntax',error:'YAML syntax error',line:4,proposals:[]}]};
  for(const [language,analyse,reason,skipped,error,manualHint,tip,failed] of [
    ['de','Benachrichtigungen analysieren','Eindeutiges festes Ziel','Nicht vorhanden – übersprungen: scripts.yaml','broken.yaml — YAML-Syntaxfehler in Zeile 4','HA-Automationseditor','Tipp:','Datei wurde seit der Analyse geändert'],
    ['en','Analyse notifications','Unique fixed destination','Not present – skipped: scripts.yaml','broken.yaml — YAML syntax error on line 4','HA automation editor','Tip:','The file changed since the analysis']]){
    const {panel,box,calls}=setup({migration_scan:report,admin_inventory:{routes:{recipients:{tg_buero:{}},groups:{},persons:{}},labels:{tg_buero:'Telegram Büro'}}});
    panel._hass.language=language;
    const original=panel._hass.callWS;
    panel._hass.callWS=async msg=>{if(msg.type.endsWith('/migration_apply')){calls.push(msg);throw {code:'migration_failed',message:'file_changed'};}return original(msg);};
    await panel.migration(box);
    const button=[...box.querySelectorAll('button')].find(b=>b.textContent.startsWith(analyse));assert.ok(button,analyse);
    button.click();await tick();await tick();
    assert.match(box.textContent,new RegExp(reason));assert.match(box.textContent,new RegExp(skipped));
    assert.ok([...box.querySelectorAll('h3')].some(h=>h.textContent===error));
    assert.match(box.textContent,new RegExp(manualHint));assert.match(box.textContent,new RegExp(tip));
    assert.match(box.querySelector('summary').textContent,/Telegram Büro \(tg_buero\)/);
    // Only the root packages file offers the single-change button.
    const applies=[...box.querySelectorAll('button.primary')].filter(b=>b!==button);
    assert.equal(applies.length,1);
    applies[0].click();await tick();await tick();
    assert.equal(calls.filter(c=>c.type.endsWith('/migration_apply')).length,1);
    assert.match(box.textContent,new RegExp(failed));
  }
});

test('own Reliable Notify entities and services are never offered as targets',()=>{
  const {panel,box}=setup();
  panel._hass.states={'notify.mail':{attributes:{friendly_name:'Mail'}},'notify.reliable_mail':{attributes:{friendly_name:'Reliable mail'}},
    'notify.renamed':{attributes:{friendly_name:'Renamed'}},'notify.registry_own':{attributes:{friendly_name:'Own'}}};
  panel._hass.entities={'notify.registry_own':{platform:'reliable_notify'},'notify.mail':{platform:'smtp'}};
  panel._hass.services={notify:{reliable_mail:{name:'Reliable'},mobile_app_phone:{name:'Phone'}}};
  panel.setRouteChoices({routes:{recipients:{},groups:{},persons:{}},own_entities:['notify.renamed']});
  const editor=panel.fieldEditor({action:'notify.send_message',target_entity:''});box.append(editor.node);
  assert.deepEqual([...control(box,'Notify-Zielentität').options].map(o=>o.value),['','notify.mail']);
  assert.deepEqual([...box.querySelectorAll('datalist option')].map(o=>o.value),['notify.mobile_app_phone']);
});

test('target help explains buttons and images per transport with copyable examples',async()=>{
  for(const [language,notes,example,copy] of [['de','Buttons, Bilder und Zusatzdaten je Transport','Telegram: Kamerabild senden','Kopieren'],
    ['en','Buttons, images and extra data per transport','Telegram: send a camera picture','Copy']]){
    const {panel}=setup({admin_inventory:{routes:{recipients:{},groups:{},persons:{}}}});
    panel._hass.language=language;panel._section='routes';panel.render();await tick();
    const help=panel.shadowRoot.querySelector('details.rn-help');
    assert.equal(help.querySelector('h4').textContent,notes);
    assert.ok([...help.querySelectorAll('.rn-example-title')].some(p=>p.textContent.startsWith(example)));
    const codes=[...help.querySelectorAll('.rn-code pre')].map(p=>p.textContent);
    assert.ok(codes.some(c=>/inline_keyboard/.test(c)));assert.ok(codes.some(c=>/actions:\n\s+- action: TUER_OEFFNEN/.test(c)));
    assert.ok(codes.some(c=>/media: photo/.test(c)&&/file: \/media\/haustuer\.jpg/.test(c)));
    assert.ok(codes.some(c=>/image: \/media\/local\//.test(c)));
    const buttons=[...help.querySelectorAll('.rn-code button')];
    assert.equal(buttons.length,codes.length);assert.equal(buttons[0].textContent,copy);
    buttons[0].click();await tick();
    assert.notEqual(buttons[0].textContent,copy); // clipboard is unavailable in jsdom: a hint replaces the label
  }
});

test('failure analysis shows causes per target with advice in German and English',async()=>{
  const stats={transports:[],timeline:[],labels:{tg_buero:'Telegram Büro'},failures:[
    {category:'invalid_payload',status:'dead',action:'telegram_bot.send_message',target:'tg_buero',count:3,last_seen:1700000000,detail:'[invalid_payload] MultipleInvalid: extra keys not allowed'},
    {category:'network',status:'retrying',action:'notify.mobile_app_phone',target:'phone',count:1,last_seen:1700000100,detail:'[network] OSError: down'}]};
  for(const [language,heading,cause,status,advice] of [['de','Fehleranalyse','Ungültiger Aufruf oder ungültige Daten','Fehlgeschlagen','Zusatzdaten, chat_id oder config_entry_id'],
    ['en','Failure analysis','Invalid call or invalid data','Failed','extra data, chat_id or config_entry_id']]){
    const {panel,box}=setup({statistics:stats});
    panel._hass.language=language;
    await panel.analytics(box);await tick();
    const section=[...box.querySelectorAll('section')].find(s=>s.querySelector('h3')?.textContent===heading);
    assert.ok(section,heading);
    const cells=[...section.querySelectorAll('tr')][1].querySelectorAll('td');
    assert.equal(cells[0].textContent,cause);assert.equal(cells[1].textContent,status);
    assert.equal(cells[2].textContent,'Telegram Büro (tg_buero)');assert.equal(cells[4].textContent,'3');
    assert.match(cells[6].textContent,/extra keys not allowed/);
    assert.match(section.querySelector('ul').textContent,new RegExp(advice));
    assert.equal(section.querySelectorAll('ul li').length,2);
  }
  const {panel,box}=setup({statistics:{transports:[],timeline:[],failures:[]}});
  await panel.analytics(box);await tick();
  assert.match(box.textContent,/Keine Fehler im gewählten Zeitraum/);
});

test('targets can get a fallback picked from known targets and retry rules show the time limit',async()=>{
  const {panel,box}=setup({admin_inventory:{routes:{recipients:{tg:{},phone:{}},groups:{family:[]},persons:{}},labels:{phone:'Handy'}},
    route_definition:{definition:{action:'notify.mobile_app_x',fallback:'phone'}}});
  await panel.routes(box);
  const section=box.querySelector('section');
  click(section,'tg');await tick();
  const fallback=control(section,'Ausweichziel bei endgültigem Fehler');
  assert.equal(fallback.value,'phone');
  const options=[...section.querySelectorAll('datalist#'+fallback.getAttribute('list')+' option')];
  assert.deepEqual(options.map(o=>o.value),['family','phone','tg']);
  assert.equal(options.find(o=>o.value==='phone').label,'Handy (phone)');
  const editor=panel.fieldEditor({info:{max_attempts:0,base_seconds:30,max_delay:1800,max_hours:6}},{fixed:true});box.append(editor.node);
  const hours=control(box,'Aufgeben nach Stunden mit Fehlern (0 = nie)');
  assert.equal([hours.min,hours.max].join('-'),'0-720');
});

function alarmSetup(language,payload){
  const dom=new JSDOM('<body></body>',{runScripts:'outside-only',url:'https://ha.test/'});
  dom.window.confirm=()=>true;
  const alarm=readFileSync('custom_components/reliable_notify/reliable-notify-alarm-card.js','utf8').replace(/^import .*;$/m,'');
  dom.window.eval(readFileSync('custom_components/reliable_notify/reliable-notify-card.js','utf8').replace(/^export /gm,'')+'\n'+alarm);
  const calls=[],subscriptions=[];let push=null;
  const hass={language,user:{is_admin:false},callWS:async msg=>{calls.push(msg);return {changed:true};},
    connection:{subscribeMessage:async(callback,msg)=>{subscriptions.push(msg);push=callback;callback(payload);return ()=>{subscriptions.push('closed');};}}};
  const card=dom.window.document.createElement('reliable-notify-alarm-card');
  dom.window.document.body.append(card);
  return {dom,card,hass,calls,subscriptions,push:value=>push(value)};
}

test('alarm card shows open incidents as bands, hides itself when none are open and lets residents act',async()=>{
  const now=Date.now()/1000;
  const payload={permissions:{ack:true,snooze:true,escalate:false},incidents:[
    {dedup_key:'brenner',title:'Brennerstörung',text:'An der Ecomatic entstören.',priority:'critical',state:'active',opened_at:now-600,escalation_step:0,escalation_steps:2},
    {dedup_key:'oel',title:'Ölstand',text:'Öl bestellen.',priority:'warning',state:'resolved',opened_at:now-3600,resolved_at:now-60,escalation_step:1,escalation_steps:1}]};
  for(const [language,ack,snooze,since,resolved] of [['de','Quittieren','Schlummern 15 min','seit','behoben um'],['en','Acknowledge','Snooze 15 min','since','resolved at']]){
    const {card,hass,calls,subscriptions,push}=alarmSetup(language,payload);
    card.setConfig({areas:['heizraum'],snooze_minutes:[15,60]});
    card.hass=hass;await tick();
    assert.deepEqual(JSON.parse(JSON.stringify(subscriptions[0])),{type:'reliable_notify/subscribe_incidents',min_priority:'info',include_acknowledged:false,areas:['heizraum']});
    const bands=[...card.shadowRoot.querySelectorAll('.band')];
    assert.deepEqual(bands.map(b=>[b.dataset.priority,b.dataset.state]),[['critical','active'],['warning','resolved']]);
    assert.match(bands[0].textContent,/Brennerstörung/);assert.match(bands[0].textContent,/An der Ecomatic entstören/);
    assert.match(bands[0].querySelector('.meta').textContent,new RegExp('^'+since));
    assert.match(bands[1].querySelector('.meta').textContent,new RegExp(resolved));
    const labels=[...bands[0].querySelectorAll('button')].map(b=>b.textContent);
    assert.deepEqual(labels,[ack,snooze,snooze.replace('15','60')]);  // no escalate for residents
    assert.equal(card.hidden,false);
    bands[0].querySelector('button.ack').click();await tick();
    assert.deepEqual(JSON.parse(JSON.stringify(calls[0])),{type:'reliable_notify/incident_action',key:'brenner',action:'ack'});
    bands[0].querySelectorAll('button.snooze')[1].click();await tick();
    assert.deepEqual(JSON.parse(JSON.stringify(calls[1])),{type:'reliable_notify/incident_action',key:'brenner',action:'snooze',minutes:60});
    push({permissions:{},incidents:[]});
    assert.equal(card.hidden,true);assert.equal(card.shadowRoot.querySelectorAll('.band').length,0);
    card.remove();assert.equal(subscriptions.at(-1),'closed');
  }
});

test('alarm card options: compact, acknowledged state, admin escalation and invalid configuration',async()=>{
  const now=Date.now()/1000;
  const payload={permissions:{ack:true,snooze:true,escalate:true},incidents:[
    {dedup_key:'a',title:'A',text:'Langer Text',priority:'critical',state:'active',opened_at:now,escalation_step:0,escalation_steps:1},
    {dedup_key:'b',title:'B',text:'',priority:'info',state:'acknowledged',acknowledged_by:'Anna',opened_at:now,escalation_step:0,escalation_steps:0}]};
  const {card,hass,subscriptions}=alarmSetup('de',payload);
  card.setConfig({compact:true,show_acknowledged:true,snooze_minutes:[]});
  card.hass=hass;await tick();
  assert.equal(subscriptions[0].include_acknowledged,true);
  const bands=[...card.shadowRoot.querySelectorAll('.band')];
  assert.equal(bands[0].querySelector('.text'),null);
  assert.deepEqual([...bands[0].querySelectorAll('button')].map(b=>b.textContent),['Quittieren','Eskalieren']);
  assert.match(bands[1].textContent,/quittiert von Anna, besteht noch/);
  assert.equal(bands[1].querySelectorAll('button').length,0);
  for(const bad of [{min_priority:'high'},{snooze_minutes:[0]},{snooze_minutes:[1,2,3,4]},{areas:'heizraum'}])
    assert.throws(()=>card.setConfig(bad));
  card.remove();
});

test('compact alarm card: one row per alarm with short labelled buttons, description on tap, German and English',async()=>{
  const now=Date.now()/1000;
  const payload={permissions:{ack:true,snooze:true,escalate:false},incidents:[
    {dedup_key:'heizung',title:'Alarm Heizung',text:'Brenner prüfen.',priority:'critical',state:'active',opened_at:now,escalation_step:0,escalation_steps:0},
    {dedup_key:'brand',title:'Alarm Brandmelder',text:'Batterie tauschen.',priority:'warning',state:'active',opened_at:now,escalation_step:0,escalation_steps:0,source_entity:'sensor.rauch'}]};
  for(const [language,ack,full] of [['de','Quittieren','Schlummern 15 min'],['en','Acknowledge','Snooze 15 min']]){
    const {card,hass,dom}=alarmSetup(language,payload);
    card.setConfig({compact:true,snooze_minutes:[15,60]});card.hass=hass;await tick();
    const root=card.shadowRoot,bands=[...root.querySelectorAll('.band')];
    assert.equal(root.querySelector('ha-card').classList.contains('compact'),true);
    // Title, "since" and buttons sit in one row: the meta line moves into the head, no description, no cause text.
    assert.equal(bands[0].querySelector('.head .meta')!==null,true);
    assert.equal(bands[0].querySelector('.text'),null);
    assert.equal(bands[0].title,'Brenner prüfen.');
    assert.doesNotMatch(bands[1].textContent,/Ursache|Cause/);
    const buttons=[...bands[0].querySelectorAll('button')];
    assert.deepEqual(buttons.map(b=>b.textContent),[ack,'15 min','60 min']);
    assert.deepEqual(buttons.slice(1).map(b=>b.getAttribute('aria-label')),[full,full.replace('15','60')]);
    // Without a cause entity the title shows the description; with one it opens the cause.
    const toggle=bands[0].querySelector('.toggle');
    assert.equal(toggle.getAttribute('aria-expanded'),'false');
    toggle.dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Enter'}));
    assert.equal(root.querySelector('.band .text').textContent,'Brenner prüfen.');
    assert.equal(root.querySelector('.band .toggle').getAttribute('aria-expanded'),'true');
    root.querySelector('.band .toggle').click();
    assert.equal(root.querySelector('.band .text'),null);
    const opened=[];card.addEventListener('hass-more-info',event=>opened.push(event.detail.entityId));
    root.querySelectorAll('.band')[1].querySelector('.source').click();
    assert.deepEqual(opened,['sensor.rauch']);
    assert.equal(card.getCardSize(),2);
    card.remove();
  }
});

test('alarm card combines many alarms into one row but never folds away critical ones',async()=>{
  const now=Date.now()/1000;
  const incident=(key,priority,state='active')=>({dedup_key:key,title:key,text:'',priority,state,opened_at:now,escalation_step:0,escalation_steps:0});
  const payload={permissions:{ack:true,snooze:true},incidents:[incident('heizung','critical'),incident('brand','warning'),incident('fenster','warning'),incident('info','info')]};
  for(const [language,more,show,less,warn] of [['de','3 weitere Alarme','Anzeigen','Weniger anzeigen','2 × Warnung'],['en','3 more alarms','Show','Show less','2 × Warning']]){
    const {card,hass}=alarmSetup(language,payload);
    card.setConfig({compact:true,collapse_from:3});card.hass=hass;await tick();
    const root=card.shadowRoot;
    assert.deepEqual([...root.querySelectorAll('.band')].map(b=>b.dataset.priority),['critical']);
    let summary=root.querySelector('button.summary');
    assert.equal(summary.querySelector('.label').textContent,more);
    assert.deepEqual([...summary.querySelectorAll('.pill')].map(p=>p.textContent),[warn,'1 × Information']);
    assert.equal(summary.dataset.priority,'warning');
    assert.equal(summary.getAttribute('aria-expanded'),'false');assert.match(summary.textContent,new RegExp(show+'$'));
    assert.equal(card.getCardSize(),2);
    summary.click();
    assert.equal(root.querySelectorAll('.band').length,4);
    summary=root.querySelector('button.summary');
    assert.equal(summary.getAttribute('aria-expanded'),'true');assert.match(summary.textContent,new RegExp(less+'$'));
    summary.click();assert.equal(root.querySelectorAll('.band').length,1);
    // Below the limit, or with only critical alarms, everything stays visible without a summary row.
    card.setConfig({collapse_from:5});await tick();
    assert.equal(root.querySelectorAll('.band').length,4);assert.equal(root.querySelector('.summary'),null);
    card.remove();
  }
  const {card,hass,push}=alarmSetup('de',{permissions:{},incidents:[incident('a','critical'),incident('b','critical'),incident('c','critical')]});
  card.setConfig({collapse_from:2});card.hass=hass;await tick();
  assert.equal(card.shadowRoot.querySelectorAll('.band').length,3);assert.equal(card.shadowRoot.querySelector('.summary'),null);
  push({permissions:{},incidents:[incident('a','warning'),incident('b','info')]});
  assert.equal(card.shadowRoot.querySelectorAll('.band').length,0);
  assert.equal(card.shadowRoot.querySelector('.summary .label').textContent,'2 offene Alarme');
  for(const bad of [{collapse_from:1},{collapse_from:2.5},{collapse_from:'3'},{collapse_from:51}])assert.throws(()=>card.setConfig(bad));
  card.remove();
});

test('alarm card names the watched cause and opens it on tap',async()=>{
  const payload={permissions:{ack:true,snooze:true},incidents:[{dedup_key:'brenner',title:'Brennerstörung',text:'Entstören',
    priority:'critical',state:'resolved',opened_at:Date.now()/1000-60,resolved_at:Date.now()/1000,escalation_step:0,escalation_steps:0,
    source_entity:'binary_sensor.brenner'}]};
  for(const [language,cause] of [['de','Ursache: Brenner Störung'],['en','Cause: Brenner Störung']]){
    const {card,hass,dom}=alarmSetup(language,payload);
    hass.states={'binary_sensor.brenner':{attributes:{friendly_name:'Brenner Störung'}}};
    card.setConfig({});card.hass=hass;await tick();
    assert.match(card.shadowRoot.querySelector('.meta').textContent,new RegExp(cause));
    const opened=[];card.addEventListener('hass-more-info',event=>opened.push(event.detail.entityId));
    card.shadowRoot.querySelector('.source').click();
    card.shadowRoot.querySelector('.source').dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Enter'}));
    assert.deepEqual(opened,['binary_sensor.brenner','binary_sensor.brenner']);
    card.remove();
  }
});

test('alarm card editor writes the YAML options and validates snooze minutes',async()=>{
  for(const [language,areasLabel,error] of [['de','Bereiche (kommagetrennt, leer = alle)','ganze Zahlen'],['en','Areas (comma separated, empty = all)','whole numbers']]){
    const {dom,hass,card}=alarmSetup(language,{incidents:[]});
    const Card=dom.window.customElements.get('reliable-notify-alarm-card');
    const editor=Card.getConfigElement();dom.window.document.body.append(editor);
    editor.hass=hass;editor.setConfig({areas:['heizraum'],compact:true});
    const configs=[];editor.addEventListener('config-changed',event=>configs.push(JSON.parse(JSON.stringify(event.detail.config))));
    const root=editor.shadowRoot,field=name=>root.querySelector('[name='+name+']');
    assert.ok([...root.querySelectorAll('label span')].some(s=>s.textContent===areasLabel));
    assert.equal(field('areas').value,'heizraum');assert.equal(field('compact').checked,true);
    const change=(input)=>input.dispatchEvent(new dom.window.Event('change'));
    field('areas').value='heizraum, bad';change(field('areas'));
    assert.deepEqual(configs.at(-1),{areas:['heizraum','bad'],compact:true});
    field('min_priority').value='warning';change(field('min_priority'));
    assert.equal(configs.at(-1).min_priority,'warning');
    const before=configs.length;
    field('snooze_minutes').value='0, 5000';change(field('snooze_minutes'));
    assert.equal(configs.length,before);assert.match(root.querySelector('.error').textContent,new RegExp(error));
    field('snooze_minutes').value='10, 30';change(field('snooze_minutes'));
    assert.deepEqual(configs.at(-1).snooze_minutes,[10,30]);assert.equal(root.querySelector('.error').textContent,'');
    field('compact').checked=false;change(field('compact'));
    assert.equal('compact' in configs.at(-1),false);
    field('areas').value='';change(field('areas'));
    assert.equal('areas' in configs.at(-1),false);
    // collapse_from: whole number 2–50, empty removes the option.
    assert.equal(field('collapse_from').value,'');
    const count=configs.length;
    field('collapse_from').value='1';change(field('collapse_from'));
    assert.equal(configs.length,count);
    assert.match([...root.querySelectorAll('.error')].at(-1).textContent,language==='de'?/ganze Zahl 2–50/:/whole number 2–50/);
    field('collapse_from').value='3';change(field('collapse_from'));
    assert.equal(configs.at(-1).collapse_from,3);assert.equal([...root.querySelectorAll('.error')].at(-1).textContent,'');
    field('collapse_from').value='';change(field('collapse_from'));
    assert.equal('collapse_from' in configs.at(-1),false);
    card.remove();
  }
});

test('saved-target test is disabled until saving and uses persisted alias in English',async()=>{
  const {panel,box,calls}=setup({admin_inventory:{routes:{recipients:{},groups:{},persons:{}}},
    test_route:{ids:[7],not_before:0},archive_detail:{id:7,status:'sent'}});
  panel._hass.language='en';await panel.routes(box);
  const section=box.querySelector('section');
  const test=[...section.querySelectorAll('button')].find(b=>b.textContent==='Test saved target');
  assert.equal(test.disabled,true);
  section.querySelector('input[placeholder="Unique name"]').value='new_phone';
  click(section,'Save');await tick();assert.equal(test.disabled,false);
  test.click();await tick();await tick();
  assert.equal(calls.find(c=>c.type.endsWith('/test_route')).name,'new_phone');
  assert.equal(calls.find(c=>c.type.endsWith('/test_route')).language,'en');
  assert.match(section.textContent,/Accepted by transport/);
});
