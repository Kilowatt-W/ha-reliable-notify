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
  dom.window.eval(source);
  const panel=dom.window.document.createElement('reliable-notify-panel');
  const calls=[];
  panel._hass={callWS:async msg=>{calls.push(msg);return structuredClone(responses[msg.type.split('/')[1]]||{saved:true});}};
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
