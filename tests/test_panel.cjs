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
  dom.window.eval(readFileSync('custom_components/reliable_notify/reliable-notify-card.js','utf8').replace(/^export /gm,''));
  dom.window.eval(source);
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
    const name=box.querySelector('input[placeholder]');name.value='RN-KW-Telegram';
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
