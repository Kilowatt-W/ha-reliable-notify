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
  assert.deepEqual([...box.querySelectorAll('h2')].map(n=>n.textContent),['Ziele / Empfänger','Gruppen','Personen']);
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
  assert.equal(box.querySelectorAll('h2').length,5);
  for(const label of ['Telegram','SMTP','Companion-App','HA Notify','Webhook','ntfy','Gotify']){
    assert.equal(control(box,label).tagName,'SELECT');
    assert.equal(control(box,label).options.length,5);
  }
  assert.equal(box.querySelectorAll('textarea').length,0);
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
  assert.deepEqual([...box.querySelectorAll('h2')].map(e=>e.textContent),['Targets / recipients','Groups','People']);
  assert.ok(control(box,'Notify target entity'));
  // Existing route aliases and message values are user data, never localized.
  click(box,'Speichern');await tick();
  assert.equal(box.querySelector('input[placeholder="Unique name"]').value,'Speichern');
  const editor=panel.fieldEditor(definition);assert.deepEqual(plain(editor.read()),definition);
  const yaml=panel.yaml(editor.read());assert.match(yaml,/"token": "Speichern"/);
  assert.match(box.querySelector('summary').textContent,/Show YAML/);
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
  assert.equal(box.querySelectorAll('button.danger ha-icon[icon="mdi:delete-outline"]').length,3);
  click(box,'Test senden');await tick();await tick();
  assert.equal(calls.filter(c=>c.type.endsWith('/test_route')).length,1);
  assert.equal(calls.find(c=>c.type.endsWith('/test_route')).name,'phone');
  assert.match(box.querySelector('.route-item p').textContent,/Vom Transport angenommen/);
  assert.equal(box.querySelector('.route-item p').className,'status');
  assert.equal(box.querySelector('.route-item button.test').disabled,false);
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
  const groups=box.querySelectorAll('section')[1];
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
  const toggle=root.querySelector('button.rn-help-toggle');
  assert.equal(toggle.textContent,'Hilfe einblenden');assert.equal(toggle.getAttribute('aria-expanded'),'false');
  let help=root.querySelector('#content details.rn-help');
  assert.equal(help.open,false);assert.equal(help.querySelector('summary').textContent,'Hilfe zu diesem Bereich');
  assert.match(help.textContent,/Alle Optionen gibt es gesammelt/);
  assert.match(help.querySelector('a').href,/docs\/CONFIGURATION\.md$/);
  toggle.click();
  assert.equal(help.open,true);assert.equal(toggle.textContent,'Hilfe ausblenden');assert.equal(toggle.getAttribute('aria-expanded'),'true');
  click(root.querySelector('nav'),'Ziele & Personen');await tick();
  help=root.querySelector('#content details.rn-help');
  assert.equal(help.open,true);assert.match(help.textContent,/Neues Ziel anlegen/);assert.match(help.querySelector('pre').textContent,/reliable_notify\.enqueue/);
  panel.hass={...panel._hass,language:'en'};await tick();
  help=root.querySelector('#content details.rn-help');
  assert.equal(help.querySelector('summary').textContent,'Help for this section');
  assert.match(help.textContent,/Create new target/);assert.equal(help.open,true);
  assert.equal(root.querySelector('button.rn-help-toggle').textContent,'Hide help');
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
