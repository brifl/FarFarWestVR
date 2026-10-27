"""Gesture, bounded retrospective capture, log counters and screenshot correlation (lupa)."""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch
import zipfile
from lupa import LuaRuntime
import issue_report

ROOT=Path(__file__).resolve().parents[1]
MOCK=r'''
state={files={},clock=0,logs={},haptics={},ready=true,left=false,right=false}
os.clock=function() state.clock=state.clock+.000001;return state.clock end
local date=os.date
os.time=function() return 1793059200 end
os.date=function(fmt,epoch) return date(fmt,epoch or 1793059200) end
io.open=function(name,mode)
 if mode=='rb' and state.files[name]==nil then return nil end
 if mode=='wb' then
  if state.disk_full then return nil,'disk full' end
  state.files[name]=''
 end
 local position=0
 return {
  read=function(_,n) local s=state.files[name]:sub(position+1,position+n);position=position+#s;return s end,
  write=function(_,s)
   if state.disk_full then return nil,'disk full' end
   state.files[name]=(state.files[name] or '')..s;return true
  end,
  seek=function(_,mode,offset)
   if mode=='end' then position=#state.files[name]+(offset or 0)
   elseif mode=='set' then position=offset end
   return position
  end,flush=function() return true end,close=function() return true end,
 }
end
recorder=require('libs/incident');recorder.configure(true)
function advance(seconds)
 for i=1,math.floor(seconds/.1+.5) do recorder.tick(.1) end
end
function observe(id,owner,instance)
 recorder.observe(id,{visible=true,class='UI_Test_C',path=id,owner_class=owner or 'BP_Target_C',kind='world_widget',
  target={x=state.target or 1,y=2,z=3}},instance or 1)
end
function report()
 local saved,name=recorder.trigger('test');assert(saved,name);state.report=name
 advance(6);return state.files[name]
end
'''


def run(name,code,check=None):
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.globals().script_path=str(ROOT/'scripts/?.lua')
    lua.execute("package.path=script_path..';'..package.path")
    lua.execute(MOCK);lua.execute(code)
    if check:check(lua)
    print('PASS',name)


def rows(lua):
    s=lua.globals().state
    return [json.loads(x) for x in s.files[s.report].splitlines()]


run('gesture requires opposite ears, tolerates head rotation and rejects invalid tracking',r'''
local g=require('libs/report_gesture')
local h={x=0,y=1.6,z=0};local l={x=-.2,y=1.6,z=0};local r={x=.2,y=1.6,z=0}
assert(g.at_ears(h,l,r,{x=0,y=0,z=0,w=1},.4))
assert(not g.at_ears(h,{x=-.15,y=1.6,z=-.28},{x=.15,y=1.6,z=-.28},{x=0,y=0,z=0,w=1},.4))
r.x=-.1;assert(not g.at_ears(h,l,r,{x=0,y=0,z=0,w=1},.4))
r.x=.5;assert(not g.at_ears(h,l,r,{x=0,y=0,z=0,w=1},.4))
l={x=0,y=1.6,z=.2};r={x=0,y=1.6,z=-.2}
assert(g.at_ears(h,l,r,{x=0,y=.70710678,z=0,w=.70710678},.4))
assert(not g.at_ears(h,l,r,{x=0,y=0,z=0,w=0},.4))
''')
run('gesture holds deliberately, rearms only after release and ignores presses during cooldown',r'''
local g=require('libs/report_gesture').new()
for i=1,10 do assert(not g.step(true,true,true,true,.1,.6,3)) end
g.step(true,true,false,false,.1,.6,3)
for i=1,5 do assert(not g.step(true,true,true,true,.1,.6,3)) end
assert(g.step(true,true,true,true,.1,.6,3))
for i=1,50 do assert(not g.step(true,true,true,true,.1,.6,3)) end
g.step(true,true,false,false,.1,.6,3)
for i=1,5 do assert(not g.step(true,true,true,true,.1,.6,3)) end
assert(g.step(true,true,true,true,.1,.6,3))
g.step(true,true,false,false,.1,.6,3)
for i=1,40 do assert(not g.step(true,true,true,true,.1,.6,3)) end
''')
run('menu/tracking loss cancels a partial gesture without altering inputs',r'''
local g=require('libs/report_gesture').new();g.step(true,true,false,false,.1,.6,3)
for i=1,4 do g.step(true,true,true,true,.1,.6,3) end
assert(not g.step(false,true,true,true,.1,.6,3))
for i=1,10 do assert(not g.step(true,true,true,true,.1,.6,3)) end
g.step(true,true,false,false,.1,.6,3)
for i=1,10 do assert(not g.step(true,false,true,true,.1,.6,3)) end
''')
run('right-ear feedback matches the native head range and protects native confirmation',r'''
local g=require('libs/report_gesture')
local head={x=0,y=1.6,z=0};local q={x=0,y=0,z=0,w=1}
assert(g.head_feedback_range(head,{x=.15,y=1.6,z=0},q,1))
assert(not g.head_feedback_range(head,{x=-.15,y=1.6,z=0},q,1))
assert(not g.head_feedback_range(head,{x=.21,y=1.6,z=0},q,1))
assert(not g.head_feedback_range(head,{x=.01,y=1.6,z=-.15},q,1))
local vr={get_mod_value=function() return '1' end,set_mod_value=function(_,key,value)
 assert(key=='FFW_ReportHaptics' and value=='1');state.command=true end,
 get_right_joystick_source=function() return 2 end,
 trigger_haptic_vibration=function(delay,duration,frequency,amplitude,source)
 state.haptics[#state.haptics+1]={delay,duration,frequency,amplitude,source} end}
local f=require('libs/report_feedback').new(vr)
f.tick(true,0);assert(#state.haptics==1)
local h=state.haptics[1];assert(h[1]==0 and h[2]==.1 and h[3]==1 and h[4]==5 and h[5]==2)
f.tick(true,.01);assert(#state.haptics==1)
f.confirm(.1);assert(state.command and f.priority())
f.tick(true,.2);f.tick(false,.3);assert(#state.haptics==1)
f.tick(true,.8);assert(#state.haptics==2)
''')
run('performance history polls sparsely, records hitches and remains bounded',r'''
local p=require('libs/performance');state.wall=1000;state.native_calls=0
os.time=function() return state.wall end
uevr={api={get_uobject_array=function() return {get_object_count=function() return 150000 end} end},params={
 vr={get_mod_value=function(_,key) assert(key=='FFW_DiagnosticStats');state.native_calls=state.native_calls+1
 return 'v=1;ws=4000;commit=5000;free=30000;gpu=12.0;interval=11.1;drop=3;lp=.2;lq=.5;ls=.1;li=.1' end},
 functions={log_info=function(s) state.logs[#state.logs+1]=s end}}}
for i=1,600 do state.wall=1000+i*.1;p.frame(.1) end
assert(state.native_calls<=13 and p.snapshot().frames==600)
state.wall=1061;p.frame(.75);assert(p.needs_flush());assert(not p.needs_flush())
assert(p.context().peak.engine_delta_ms==750)
assert(p.context().latest.object_slots==150000 and p.context().latest.commit==5000)
for i=1,520 do state.wall=1061+i*31;p.frame(.01) end
assert(#p.snapshot().windows==512 and p.snapshot().discarded_history>0)
assert(p.parse('v=1;ws=4000;commit=5000')==nil)
''')
run('capture isolation pauses observations while leaving gesture and log recording enabled',r'''
recorder.set_capture_enabled(false);observe('must-not-capture')
recorder.count('important','failure','game','error',1,'now')
assert(recorder.enabled() and not recorder.capture_enabled())
local saved,name=recorder.trigger('capture-paused');assert(saved);advance(6)
assert(not state.files[name]:find('must%-not%-capture'))
assert(state.files[name]:find('important',1,true))
recorder.set_capture_enabled(true);assert(recorder.capture_enabled())
''')

def check_window(lua):
    data=rows(lua);header=data[0];samples=[x for x in data if x['type']=='sample']
    assert samples and all(x['time']>=header['time']-10 for x in samples)
    assert any(x['target']['x']==120 for x in samples)
    assert data[-1]['type']=='end'
    assert header['utc'].endswith('Z') and isinstance(header['unix_time'],int)

run('ring wraps without losing recent samples and excludes observations older than ten seconds',r'''
for i=1,120 do state.target=i;observe('marker');advance(.1) end
report()
''',check_window)

def check_dedup(lua):
    data=rows(lua)
    samples=[x for x in data if x['type']=='sample'];defs=[x for x in data if x['type']=='definition']
    assert len(samples)==1 and samples[0]['count']==200 and len(defs)==1
    assert sum(x['count'] for x in data if x['type']=='log_count')==10000

run('repeated observations and spam become one dictionary entry and a counter',r'''
for i=1,200 do observe('marker') end
recorder.count('remap.invalid_shift.0','invalid shift 0','uevr','error',10000,'time')
report()
''',check_dedup)
run('pre-event context is flushed before the post-event window finishes',r'''
observe('before');local saved,name=recorder.trigger('test');assert(saved);state.report=name
recorder.tick(.1)
assert(state.files[name]:find('"type":"sample"',1,true))
assert(not state.files[name]:find('"type":"end"',1,true))
recorder.reset();assert(state.files[name]:find('"type":"sample"',1,true))
''')
run('post-event samples and new definitions are included with bounded incremental writes',r'''
observe('before');local saved,name=recorder.trigger('test');assert(saved);state.report=name
advance(1);observe('after');advance(5)
assert(state.files[name]:find('after',1,true))
assert(state.files[name]:find('"type":"end"',1,true))
''')
run('bucket limits count omissions instead of growing an unbounded capture',r'''
for i=1,1000 do observe('marker-'..i) end
report();assert(state.files[state.report]:find('"skipped_samples":744',1,true))
''')
run('ordinary UI noise cannot consume the reserved marker and transform slots',r'''
for i=1,1000 do recorder.observe('leaf-'..i,{visible=true,class='Image',kind='widget'},i) end
observe('important-marker');report()
assert(state.files[state.report]:find('important%-marker'))
''')

def check_cap(lua):
    s=lua.globals().state;assert len(s.files[s.report])<=2097152
    assert rows(lua)[-1]['truncated']

run('large verbose metadata respects the two-MiB file cap and emits a final truncation record',r'''
for i=1,256 do recorder.observe('large-'..i,{visible=true,class='UI_Test_C',fields=string.rep('x',10000)},i) end
report()
''',check_cap)
run('disabled diagnostics and a full disk do not create apparently successful markers',r'''
recorder.configure(false);observe('ignored');assert(not recorder.trigger('test'))
recorder.configure(true);state.disk_full=true;assert(not recorder.trigger('test'))
''')
run('known spam and generated widget instance names normalize without hiding unknown errors',r'''
local d=require('libs/log_digest')
local key,message,level,known=d.classify('[x] [error] [Plugin] The shift value seems to be invalid 0','uevr')
assert(key=='remap.invalid_shift.0' and known and level=='error')
local a=d.classify('[x] [warning] [Plugin] Failed UI_Test_C_12345','uevr')
local b=d.classify('[x] [warning] [Plugin] Failed UI_Test_C_54321','uevr');assert(a==b)
assert(d.classify('[x] [info] ordinary render message','uevr')==nil)
''')
run('Unreal timestamps, frame numbers and CRLF do not multiply one warning into dictionary entries',r'''
local d=require('libs/log_digest')
local a,message=d.classify('[2026.10.26-08.06.02:113][ 83]LogEOSSDK: Warning: Missing user\r','game')
local b=d.classify('[2026.10.26-10.06.06:193][248]LogEOSSDK: Warning: Missing user\r','game')
assert(a==b and message=='LogEOSSDK: Warning: Missing user')
local c=d.classify('[2026.10.26-10.06.06:193][248]LogEOSSDK: Warning: Different warning','game')
assert(c~=a)
''')
run('warning noise leaves dictionary capacity for a subsequent new error',r'''
state.files['UEVR.log']='';state.files['FarFarWest.log']=''
local d=require('libs/log_digest').new(recorder);state.digest=d.output()
for i=1,200 do state.files['FarFarWest.log']=state.files['FarFarWest.log']..'[t][ 42]LogTest: Warning: unique-'..i..'\r\n' end
state.files['FarFarWest.log']=state.files['FarFarWest.log']..'[t][ 43]LogTest: Error: Important new failure\r\n'
d.flush()
assert(state.files[state.digest]:find('Important new failure',1,true))
assert(state.files[state.digest]:find('"overflow":8',1,true))
''')

def check_logs(lua):
    s=lua.globals().state
    digest=json.loads(s.files[s.digest])
    assert digest['messages']['remap.invalid_shift.0']['count']==500
    assert digest['messages']['remap.invalid_shift.0']['documented']

run('tailing counts new lines once, ignores routine chatter and leaves raw logs unchanged',r'''
state.files['UEVR.log']='';state.files['FarFarWest.log']=''
local d=require('libs/log_digest').new(recorder);state.digest=d.output()
for i=1,5 do
 state.files['UEVR.log']=state.files['UEVR.log']..string.rep('[x] [error] [Plugin] The shift value seems to be invalid 0\n',100)
 d.tick(.25);d.tick(.25)
end
local original=state.files['UEVR.log'];d.flush();d.flush();assert(state.files['UEVR.log']==original)
''',check_logs)

FEATURE=r'''
local settings={['diagnostics.gesture_enabled']=1,['diagnostics.head_radius_m']=.4,
 ['diagnostics.hold_seconds']=.6,['diagnostics.cooldown_seconds']=8,['diagnostics.capture_enabled']=1}
package.loaded['libs/tuning']={get=function(k) return assert(settings[k]) end,snapshot=function() return settings end}
local function log(s) state.logs[#state.logs+1]=s end
UEVR_Vector3f={new=function() return {} end};UEVR_Quaternionf={new=function() return {} end}
local vr={is_runtime_ready=function() return state.ready end,is_hmd_active=function() return state.ready end,
 is_using_controllers=function() return true end,get_hmd_index=function() return 0 end,
 get_left_controller_index=function() return 1 end,get_right_controller_index=function() return 2 end,
 get_left_joystick_source=function() return 1 end,get_right_joystick_source=function() return 2 end,
 get_action_handle=function(path) assert(path=='/actions/default/in/Trigger');return 10 end,
 is_action_active=function(_,source) return source==1 and state.left or source==2 and state.right end,
 trigger_haptic_vibration=function(...) state.haptics[#state.haptics+1]={...} end}
function vr.get_pose(index,p,q)
 p.x,p.y,p.z=index==1 and -.2 or index==2 and .2 or 0,1.6,0
 q.x,q.y,q.z,q.w=0,0,0,1
end
uevr={params={vr=vr,functions={get_tag=function() return 'ffw-ue58-sdk-v1' end,
 is_drawing_ui=function() return false end,log_info=log,log_warn=log}},sdk={callbacks={
 on_pre_engine_tick=function(fn) state.pre=fn end,on_post_engine_tick=function(fn) state.post=fn end,
 on_script_reset=function(fn) state.reset=fn end}}}
dofile(script_path:gsub('%?%.lua$','issues.lua'))
function frame(n) for i=1,n do state.pre(nil,.1);state.post(nil,.1) end end
'''
run('the deployed script marks the full physical chord and gives confirmation without screenshot or input APIs',FEATURE+r'''
frame(1);observe('visible-widget');state.left=true;state.right=true;frame(6)
assert(#state.haptics>=4)
local status=state.files['issue_capture_status.json'];assert(status and status:find('ears%-and%-both%-triggers'))
frame(60)
for _,line in ipairs(state.logs) do assert(not line:find('stopped safely',1,true),line) end
assert(recorder.gesture_status().marked==1)
''')
run('a rejected physical chord records the failed geometry test without claiming a report',FEATURE+r'''
local native_pose=uevr.params.vr.get_pose
uevr.params.vr.get_pose=function(index,p,q) native_pose(index,p,q);if index>0 then p.z=-.28 end end
frame(1);state.left=true;state.right=true;frame(10)
local status=recorder.gesture_status()
assert(status.marked==0 and status.attempts==1)
assert(status.last_attempt.reason=='left_too_far_forward_back')
assert(status.last_attempt.pose.left.distance_m<.4 and status.last_attempt.pose.left.depth_m>.22)
assert(status.closest_attempt.attempt.reason=='left_too_far_forward_back')
state.left=false;state.right=false;frame(1)
local found=false
for name,contents in pairs(state.files) do
 if name:find('log%-digest%-') and contents:find('left_too_far_forward_back',1,true) then found=true end
end
assert(found)
''')

with TemporaryDirectory() as temp:
    path=Path(temp)/'issue-20261026T000000Z-0001.jsonl'
    path.write_text(json.dumps({'type':'issue','unix_time':1000,'file':path.name,'local_time':'local','utc':'utc'})+'\n')
    issue=issue_report.read_issue(path)
    matches,unmatched=issue_report.match_screenshots([issue],{'screenshots/near.png':{'mtime':1005},'screenshots/far.png':{'mtime':2000}})
    assert len(matches[path.name])==1 and unmatched==['screenshots/far.png']
    (Path(temp)/'source-files.json').write_text(json.dumps({'screenshots/near.png':{'mtime':1005}}))
    (Path(temp)/'screenshots').mkdir();(Path(temp)/'screenshots/near.png').write_bytes(b'manual test image')
    notes=path.with_suffix('.notes.md');notes.write_text('Keep my description')
    issue_report.write_report(Path(temp))
    assert notes.read_text()=='Keep my description'
    assert 'still writing or interrupted' in (Path(temp)/'REPORT.md').read_text()
    print('PASS screenshot timestamp matching, interrupted reports and personal-note preservation')
    def remote(host,body):
        scope={};exec(body,scope);return 'Marker requested'
    with patch.object(issue_report,'PROFILE',temp),patch.object(issue_report,'remote',remote), \
         patch.object(sys,'argv',['issue_report.py','mark']),redirect_stdout(io.StringIO()):issue_report.main()
    assert (Path(temp)/'issue_capture_command.txt').read_bytes()==b'mark\n'
    print('PASS manual capture command contains a real newline')

with TemporaryDirectory() as temp:
    root=Path(temp);source=root/'remote';source.mkdir()
    shots=source/'issue_screenshots';shots.mkdir()
    issue_name='issue-20261026T000000Z-0001.jsonl'
    (source/issue_name).write_text(json.dumps({'type':'issue','unix_time':1000,'file':issue_name})+'\n'+json.dumps({'type':'end'})+'\n')
    (shots/'original.png').write_bytes(b'manual image');os.utime(shots/'original.png',(1003,1003))
    class Output:
        def __init__(self):self.buffer=io.BytesIO()
    def fake_remote(host,body,binary=False):
        output=Output()
        with patch.object(sys,'stdout',output):exec(body,{})
        return output.buffer.getvalue()
    with patch.object(issue_report,'PROFILE',str(source)),patch.object(issue_report,'remote',fake_remote):
        dest=issue_report.collect('robot1-x',root/'archive')
        assert issue_report.write_report(dest)==(1,1,0)
        (shots/'original.png').unlink()
        issue_report.collect('robot1-x',root/'archive')
        assert issue_report.write_report(dest)==(1,1,0)
        (dest/'screenshots/local.png').write_bytes(b'local manual image');os.utime(dest/'screenshots/local.png',(1004,1004))
        assert issue_report.write_report(dest)==(1,2,0)
    print('PASS collection preserves screenshot associations across sessions and accepts locally dropped images')
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w') as z:z.writestr('../outside.png',b'bad')
    with patch.object(issue_report,'remote',return_value=output.getvalue()):
        try:issue_report.collect('robot1-x',root/'unsafe')
        except ValueError:pass
        else:raise AssertionError('unsafe ZIP path accepted')
    assert not (root/'outside.png').exists()
    print('PASS collector rejects unsafe screenshot archive paths')

with TemporaryDirectory() as temp:
    root=Path(temp)
    messages={}
    for frame,count in [(83,5),(248,2)]:
        message=f'[{frame:3}]LogEOSSDK: Warning: Missing user\r'
        messages['game:'+message]={'message':message,'source':'game','severity':'warning','count':count}
    digest={'messages':messages,'overflow':8,'gesture':{'frames':100,'ready_frames':80,
        'attempts':1,'marked':0,'last_attempt':{'reason':'left_too_far_forward_back'}}}
    (root/'log-digest-20261026T000000Z.json').write_text(json.dumps(digest))
    issue_report.write_report(root)
    text=(root/'REPORT.md').read_text()
    assert text.count('Missing user')==1 and '| 7 | no |' in text
    assert 'Dictionary capacity omitted 8' in text
    assert 'left_too_far_forward_back' in text and '80 / 100' in text
    print('PASS offline index merges legacy frame counters, flags omissions and explains rejected gestures')
