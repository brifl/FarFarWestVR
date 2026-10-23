"""Read-only census safety, lifecycle and catalog/report tests (requires lupa)."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ui_audit', ROOT / 'tools/ui_audit.py')
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)

MOCK = r'''
state={files={},logs={},objects={},query_count=0,reads=0,now=0,writes=0}
os.clock=function() state.now=state.now+.000001;return state.now end
io.open=function(name,mode)
    if mode=='rb' and state.files[name]==nil then return nil end
    if mode=='wb' or (mode=='ab' and state.files[name]==nil) then state.files[name]='' end
    return {read=function(_,n) return state.files[name]:sub(1,n) end,
        write=function(_,s)
            if state.fail_write then return nil,'disk full' end
            state.files[name]=(state.files[name] or '')..s;return true
        end,seek=function() return #(state.files[name] or '') end,
        flush=function() return true end,close=function() return true end}
end
local sizes={GetParent=8,GetCachedGeometry=80,GetChildrenCount=4,GetChildAt=16,
    IsInViewport=1,GetAllWidgetsOfClass=40,GetLocalSize=96,LocalToViewport=128,GetViewportSize=24}
local offsets={Slot=48,WidgetTree=704,Widget=1800,Space=1512,GameViewport=3448,
    Key=856,gamepadKeys=864,Image_GamepadIcon=848,Text_Key=832,Text_Hold=840}
state.offsets=offsets
local classes={}
function class(name,super)
    local c={name=name,super=super}
    function c:get_short_name() return name end
    function c:get_full_name() return 'Class /Test/'..name end
    function c:get_super_struct() return self.super end
    function c:get_child_properties() return nil end
    function c:find_property(n) return offsets[n] and {get_offset=function() return offsets[n] end} end
    function c:find_function(n) return sizes[n] and {get_properties_size=function() return sizes[n] end} end
    function c:get_class_default_object() return self.cdo end
    classes['Class /Script/UMG.'..name]=c;return c
end
local w=class('Widget');local u=class('UserWidget',w);local tree=class('WidgetTree')
local panel=class('PanelWidget',w);local comp=class('WidgetComponent')
local image=class('Image',w);local text=class('TextBlock',w)
local player=class('UI_Player_C',u);local marker=class('UI_UnknownMarker_C',u)
local keyclass=class('UI_Key_C',u)
local vpclass=class('GameViewportClient')
classes['Class /Script/Engine.GameViewportClient']=vpclass
local count=0
function object(c,name)
    count=count+1
    local o={class=c,index=count,name=name or c.name,props={Visibility=0,RenderOpacity=1},children={}}
    function o:get_address() return self.index*4096 end
    function o:read_dword(n) assert(n==12);return self.index end
    function o:read_byte(n) assert(n==1512);return self.props.Space or 1 end
    function o:get_short_name() assert(not self.dead);return self.name end
    function o:get_class() assert(not self.dead);return self.class end
    function o:is_a(c)
        assert(not self.dead);state.reads=state.reads+1
        local current=self.class
        while current do if current==c then return true end;current=current.super end
        return false
    end
    function o:get_outer() assert(not self.dead);return self.outer end
    function o:get_property(n) assert(not self.dead);return self.props[n] end
    function o:GetParent() assert(not self.dead);return self.parent end
    function o:GetChildrenCount() assert(not self.dead);return #self.children end
    function o:GetChildAt(i) assert(not self.dead);return self.children[i+1] end
    function o:IsInViewport() assert(not self.dead);return self.in_viewport==true end
    function o:GetCachedGeometry() assert(not self.dead);return self end
    state.objects[count]=o
    return o
end
function attach(p,o) o.parent=p;p.children[#p.children+1]=o;return o end
function widget_tree(owner,root)
    local t=object(tree);t.outer=owner;t.props.RootWidget=root
    owner.props.WidgetTree=t;root.outer=t
end
local hud=object(player,'UI_Player_C_2147478520');hud.in_viewport=true
local p=object(panel,'MovingCanvas');widget_tree(hud,p)
local health=attach(p,object(image,'HealProgressBar'));health.bounds={.01,.94,.27,.99}
local keys=attach(p,object(keyclass,'UI_Key_1'))
local keypanel=object(panel,'Keys');widget_tree(keys,keypanel)
local keytext=attach(keypanel,object(text,'Text_Key'));local keyimage=attach(keypanel,object(image,'Image_GamepadIcon'))
keyimage.props.Visibility=1
keys.props.Key=object(class('InputAction'),'IA_Interact')
keys.props.Text_Key=keytext;keys.props.Image_GamepadIcon=keyimage
local source=object(marker,'UI_UnknownMarker_C_2147460000')
local markimage=object(image,'Image_Icon');widget_tree(source,markimage)
local owner=object(class('BP_OtherPlayer_C'),'BP_OtherPlayer_C_2147478888');owner.props.bHidden=false
local component=object(comp,'NameTag');component.outer=owner;component.props.Widget=source;component.props.bVisible=true
state.found={hud,source,keys};state.health=health;state.keys=keys;state.hud=hud;state.panel=p
state.source=source;state.component=component;state.owner=owner;state.keytext=keytext;state.keyimage=keyimage
local viewport=object(vpclass);local engine=object(class('Engine'));engine.props.GameViewport=viewport
state.engine=engine
local lib=class('WidgetBlueprintLibrary')
lib.cdo={GetAllWidgetsOfClass=function(_,context,found,kind,top)
    assert(context==viewport and kind==u and top==true)
    state.query_count=state.query_count+1
    for _,o in ipairs(state.found) do if o:IsInViewport() then found[#found+1]=o end end
end}
local slate=class('SlateBlueprintLibrary')
slate.cdo={GetLocalSize=function() return {X=100,Y=100} end}
function slate.cdo:LocalToViewport(o,geometry,point,pixel,screen)
    local b=o.bounds or {.4,.4,.6,.6}
    pixel.result={X=(b[1]+(b[3]-b[1])*point.X/100)*1000,Y=(b[2]+(b[4]-b[2])*point.Y/100)*1000}
end
local layout=class('WidgetLayoutLibrary');layout.cdo={GetViewportSize=function() return {X=1000,Y=1000} end}
local array={get_objects_offset=function() return 0 end,get_item_distance=function() return 24 end,
    get_object_count=function() return state.object_count or count+1 end,
    get_object=function(_,i) return state.objects[i] end}
local function log(s) state.logs[#state.logs+1]=s end
uevr={api={get_uobject_array=function() return array end,find_uobject=function(_,path) return classes[path] end},
    params={vr={is_runtime_ready=function() return true end},functions={log_info=log,log_warn=log}}}
package.loaded['libs/tuning']={get=function(key)
    if key=='audit.auto_start' then return state.auto_start or 0 end
    if state.margins and state.margins[key] then return state.margins[key] end
    if key=='hud.left_margin' or key=='hud.right_margin' then return .1 end
    assert(key=='hud.top_margin' or key=='hud.bottom_margin');return .15
end}
function tick(n,dt) for _=1,n do feature.tick(state.engine,dt or .1) end end
function start(n) state.files['ui_audit_command.txt']='start '..(n or 3600);tick(11) end
function stop() state.files['ui_audit_command.txt']='stop';tick(11) end
function healthy()
    for _,s in ipairs(state.logs) do assert(not s:find('Stopped safely',1,true),s) end
end
'''


def run(name, code, check=None):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().script_path = str(ROOT / 'scripts/?.lua')
    lua.execute("package.path=script_path..';'..package.path")
    lua.execute(MOCK)
    lua.execute("feature=require('libs/ui_audit')()")
    lua.execute(code)
    if check:
        check(lua)
    print('PASS', name)


def capture(lua):
    return lua.globals().state.files['ui-audit-000001.jsonl']


run('idle helper performs no native discovery or gameplay writes', '''
tick(100);healthy();assert(state.reads==0 and state.query_count==0)
assert(state.files['ui_audit_status.json']==nil)
''')


run('automatic capture appends a session ledger and preserves previous launches', r'''
state.auto_start=1;tick(12);healthy()
assert(state.files['ui-audit-000001.jsonl'])
feature.reset();local first=state.files['ui-audit-000001.jsonl']
feature=require('libs/ui_audit')();tick(12);healthy()
assert(state.files['ui-audit-000002.jsonl'])
assert(state.files['ui-audit-000001.jsonl']==first)
stop();local queries=state.query_count;tick(100);assert(state.query_count==queries)
local ledger=state.files['ui_audit_sessions.md']
assert(ledger:find('ui%-audit%-000001.jsonl.*script reset'))
assert(ledger:find('ui%-audit%-000002.jsonl.*stopped'))
local _,headings=ledger:gsub('# Gameplay UI capture sessions','');assert(headings==1)
''')

run('explicit stop before startup suppresses automatic capture for that script load', '''
state.auto_start=1;state.files['ui_audit_command.txt']='stop';tick(100);healthy()
assert(state.query_count==0 and not state.files['ui-audit-000001.jsonl'])
''')


def inspect_capture(lua):
    rows, meta, errors = report.load_capture(capture(lua))
    assert not errors, errors
    assert meta['end']['reason'] == 'stopped'
    assert any('edge_hud_candidate' in r['flags'] and r['path'].endswith('HealProgressBar') for r in rows.values())
    assert any('unhandled_screen_marker_candidate' in r['flags'] and r['owners'] for r in rows.values())
    assert any('interact_keyboard_hint' in r['flags'] and 'keyboard' in r['modes'] for r in rows.values())
    assert all('2147478520' not in r['id'] for r in rows.values())
    with TemporaryDirectory() as d:
        result = report.summarize(capture(lua), Path(d))
        assert 'Unhandled screen-marker families: 1' in result
        assert (Path(d) / 'interaction-hints.csv').read_text().count('IA_Interact') >= 1


run('edge HUD, unknown marker owner and action-bound F hints are cataloged', '''
start();tick(100);stop();healthy()
''', inspect_capture)

run('0.3.0.0 hints use the shared schema without aborting the capture', '''
for _,name in ipairs({'Key','gamepadKeys','Image_GamepadIcon','Text_Key','Text_Hold'}) do
 state.offsets[name]=state.offsets[name]-16
end
start();tick(100);stop();healthy()
''', inspect_capture)


def check_edges(lua):
    rows, _, errors = report.load_capture(capture(lua))
    assert not errors, errors
    for name in ('EdgeLeft', 'EdgeRight', 'EdgeTop', 'EdgeBottom'):
        row = next(r for r in rows.values() if r['path'].endswith(name))
        assert row['edge_samples'] > 0, name


run('audit flags candidates against each independently configured edge', '''
state.margins={['hud.left_margin']=.05,['hud.right_margin']=.2,['hud.top_margin']=.25,['hud.bottom_margin']=.35}
for name,bounds in pairs({EdgeLeft={.04,.4,.1,.5},EdgeRight={.83,.4,.88,.5},
 EdgeTop={.4,.2,.5,.24},EdgeBottom={.4,.66,.5,.7}}) do
 local o=attach(state.panel,object(state.health:get_class(),name));o.bounds=bounds
end
start();tick(100);stop();healthy()
''', check_edges)

def assert_completed(lua):
    assert report.load_capture(capture(lua))[1]['end']['reason'] == 'completed'


run('retained menu instances do not exhaust query budget; component markers are still recorded', '''
for i=1,1100 do state.found[#state.found+1]=object(class('RetainedMenu'),'RetainedMenu_'..i) end
start();tick(200);stop();healthy()
''', inspect_capture)

def check_root_budget_error(lua):
    _, meta, errors = report.load_capture(capture(lua))
    assert meta['end']['reason'] == 'error' and meta['end']['errors'] == 1
    assert any('query exceeds budget' in message for message in errors)

run('a genuine viewport-root budget failure is saved as an explicit capture error', '''
state.found={}
for i=1,1025 do local o=object(class('ViewportMenu'),'ViewportMenu_'..i);o.in_viewport=true;state.found[i]=o end
start();tick(20)
assert(state.files['ui_audit_command.txt']=='error\\n')
''', check_root_budget_error)

run('automatic stop is one-shot and never restarts itself', '''
start(10);tick(250);healthy()
assert(state.files['ui_audit_command.txt']:find('done',1,true))
local queries=state.query_count;tick(200);assert(state.query_count==queries)
''', lambda lua: assert_completed(lua))


def check_hidden(lua):
    rows, _, errors = report.load_capture(capture(lua))
    assert not errors
    health = next(r for r in rows.values() if r['path'].endswith('HealProgressBar'))
    assert health['visible'] == 0 and health['edge_samples'] == 0
    assert not any('interact_keyboard_hint' in r['flags'] for r in rows.values())


run('hidden ancestor does not produce a false visible edge candidate', '''
state.panel.props.Visibility=1;start();tick(100);stop();healthy()
''', check_hidden)

def check_covered(lua):
    rows, _, errors = report.load_capture(capture(lua))
    assert not errors
    assert any(r['coverage'] for r in rows.values())
    assert not any('unhandled_screen_marker_candidate' in r['flags'] for r in rows.values())


run('corrected sources are recognized through shared registry metadata', r'''
local function ref(o) return {object=o,index=o.index,address=o:get_address(),name=o.name} end
require('libs/ui_audit_registry').set(ref(state.component),ref(state.source),nil,'existing fix')
start();tick(100);stop();healthy()
''', check_covered)


def check_hidden_marker(lua):
    rows, _, errors = report.load_capture(capture(lua))
    assert not errors
    assert not any('unhandled_screen_marker_candidate' in r['flags'] for r in rows.values())


run('hidden world owners do not become unhandled visible marker candidates', '''
state.owner.props.bHidden=true;start();tick(100);stop();healthy()
''', check_hidden_marker)


run('stale queued objects are validated before use', '''
start();local old=state.health;state.objects[old.index]=nil;old.dead=true
tick(100);stop();healthy()
''')

run('partial write failure stops only the audit', r'''
start();state.fail_write=true;tick(500)
local queries=state.query_count;tick(100);assert(state.query_count==queries)
assert(state.logs[#state.logs]:find('Stopped safely',1,true))
assert(state.hud.props.Visibility==0 and state.health.bounds[2]==.94)
''')

run('component discovery and widget traversal remain bounded on a large array', '''
state.object_count=250000;start();local before=state.reads;feature.tick(state.engine,.016)
assert(state.reads-before<1000);tick(10);stop();healthy()
''')

lua = LuaRuntime(unpack_returned_tuples=True)
lua.globals().script_path = str(ROOT / 'scripts/?.lua')
lua.execute("package.path=script_path..';'..package.path")
lua.execute(r'''
local m=require('libs/ui_audit_catalog');local lines={}
local c=m.new(function(s) lines[#lines+1]=s;return true end,{records=2,bytes=4096})
assert(m.normalize('Text_Key_1')=='Text_Key_1')
assert(m.normalize('UI_Player_C_2147478520')=='UI_Player_C')
c.observe('a',{visible=true,x0=.1,y0=.2,x1=.3,y1=.4,mode='keyboard'},1)
c.observe('b',{visible=false},1)
c.flush(1)
c.observe('a',{visible=true,x0=.2,y0=.3,x1=.4,y1=.5,mode='gamepad'},2)
c.observe('c',{visible=true},2)
c.flush(1) -- FIFO guarantees b is written before the newly-dirty a.
assert(lines[2]:find('"id":"b"',1,true))
c.flush();assert(c.stats().records==2 and c.stats().dropped==1)
local capped=m.new(function(s) return true end,{bytes=32})
assert(not capped.event({message=string.rep('x',100)}));assert(capped.stats().full)
''')
lua.execute(r'''
local m=require('libs/ui_audit_catalog');local lines={}
local c=m.new(function(s) lines[#lines+1]=s;return true end)
for i=1,10000 do
    c.observe('static',{visible=true,x0=.1,y0=.2,x1=.3,y1=.4,context='saloon'},i)
    c.flush()
end
assert(#lines==1,'Static UI must not exhaust the hour-long file budget')
c.flush_all();assert(#lines==2 and lines[2]:find('10000',1,true))
''')
print('PASS catalog capacity, fair checkpoints, stable IDs and byte cap')
print('PASS repeated static UI stays bounded through a long session')
lua.execute(r'''
local m=require('libs/ui_audit_catalog')
local c=m.new(function() return true end,{records=4,reserved_records=2})
c.observe('menu-a',{},1);c.observe('menu-b',{},1);c.observe('menu-c',{},1)
assert(c.stats().records==2 and c.stats().dropped==1)
assert(c.observe('late-marker',{priority=true,kind='world_widget'},2))
assert(c.observe('late-hint',{priority=true,kind='key_hint'},2))
assert(c.stats().records==4)
assert(not c.observe('extra',{priority=true},3) and c.stats().dropped==2)
assert(c.observe('menu-a',{},3),'Existing records must still update after the general quota is full')
''')
print('PASS late gameplay markers and hints retain reserved bounded catalog capacity')
rows, meta, errors = report.load_capture('{"type":"start"}\n{"type":"widget","id":"a","revision":2}\n{"type":"widget","id":"a","revision":1}\n{"type":')
assert rows['a']['revision'] == 2 and errors == ['Ignored incomplete final line']
print('PASS interrupted capture retains latest complete revision')

with TemporaryDirectory() as d:
    root = Path(d)
    archive = root / 'sessions'
    host = archive / 'robot1-x'
    host.mkdir(parents=True)
    first = host / 'ui-audit-000001.jsonl'
    second = host / 'ui-audit-000002.jsonl'
    def sample(revision, seen, **extra):
        return dict(type='widget', id='Class /Test/Key|HUD/Key', revision=revision,
                    **dict(dict(seen=seen, visible=seen, edge_samples=0, path='HUD/Key',
                                kind='key_hint', **{'class': 'Class /Test/Key'}), **extra))
    first.write_text('\n'.join(map(json.dumps, [dict(type='start'),
        sample(1, 2), sample(2, 7, flags={'interact_keyboard_hint': True}, modes={'keyboard': True}),
        dict(type='end', elapsed=60, reason='stopped', errors=0)]))+'\n')
    second.write_text('\n'.join(map(json.dumps, [dict(type='start'),
        sample(1, 3, modes={'gamepad': True}, coverage={'new fix': True})]))+'\n{"type":')
    records, sessions = report.merge_captures([first, second], archive)
    row = records['Class /Test/Key|HUD/Key']
    assert row['seen'] == 10 and len(row['sessions']) == 2
    assert row['flags']['interact_keyboard_hint'] and row['latest_coverage']['new fix']
    assert set(row['modes']) == {'keyboard', 'gamepad'}
    assert sessions[1]['reason'].startswith('unfinished')
    doc = root / 'UI-FINDINGS.md'
    report.write_history(archive, doc)
    saved = json.loads((root / 'history/catalog.json').read_text())
    report.write_history(archive, doc)
    assert json.loads((root / 'history/catalog.json').read_text()) == saved
    text = doc.read_text()
    assert '2 sessions, 1 distinct widget ID' in text and row['audit_id'] in text
    assert 'new fix' in text and 'Missing from a later session does not mean fixed' in text
print('PASS cumulative report deduplicates revisions and repeat collection across sessions')
print('PASS interrupted sessions retain findings and later coverage does not erase history')

with TemporaryDirectory() as d:
    archive = Path(d)
    source = archive / 'ui-audit-000016.jsonl'
    source.write_text('{"type":"start"}\n')
    source.with_suffix('.status.json').write_text(json.dumps(dict(
        file=source.name, state='error', elapsed=421.8, errors=0, dropped=17101)))
    _, sessions = report.merge_captures([source], archive)
    assert sessions[0]['ended'] and sessions[0]['reason'] == 'error'
    assert sessions[0]['elapsed'] == 421.8 and sessions[0]['dropped'] == 17101
print('PASS per-session status preserves an older capture failure with no end record')

with TemporaryDirectory() as d:
    root = Path(d)
    archive = root / 'sessions'
    document = root / 'findings.md'
    import io
    import zipfile
    def packet(files):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as z:
            for name, content in files.items():
                z.writestr(name, content)
        return buffer.getvalue()
    one = '\n'.join(map(json.dumps, [sample(1, 7), dict(type='end', elapsed=60, reason='stopped')]))+'\n'
    two = '\n'.join(map(json.dumps, [sample(1, 3), dict(type='end', elapsed=60, reason='completed')]))+'\n'
    packets = [packet({'ui-audit-000001.jsonl': one,
                       'manifest.json': json.dumps({'ui-audit-000001.jsonl': [len(one), 1]})}),
               packet({'ui-audit-000002.jsonl': two,
                       'manifest.json': json.dumps({'ui-audit-000001.jsonl': [len(one), 1],
                                                    'ui-audit-000002.jsonl': [len(two), 2]})}),
               packet({'manifest.json': '{}'})]
    calls = []
    original = report.remote
    def fake_remote(host, body, binary=False):
        assert host == 'robot1-x' and binary
        calls.append(body)
        return packets.pop(0)
    report.remote = fake_remote
    try:
        report.collect('robot1-x', archive, document)
        report.collect('robot1-x', archive, document)
        assert "'ui-audit-000001.jsonl':" in calls[1]
        report.collect('robot1-x', archive, document)
        merged, sessions = report.merge_captures(archive.glob('*/*.jsonl'), archive)
        assert len(sessions) == 2 and next(iter(merged.values()))['seen'] == 10
    finally:
        report.remote = original
print('PASS incremental collection preserves old sessions when remote files disappear')
