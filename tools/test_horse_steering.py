"""Mounted steering curve, possession changes and input isolation (lupa)."""
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
MOCK = r'''
state={mounted=true,exponent=2,active=true,using=true,objects={},logs={}}
farfarwest_gameplay_ready=true
local function object(o,index,name)
 state.objects[index]=o
 function o:get_address() return index*256 end
 function o:read_dword(n) assert(n==12);return index end
 function o:get_short_name() return name end
 return o
end
local offsets={WorldContextObject=0,PlayerIndex=8,ReturnValue=16,GameViewport=3448,
 Pawn=744,Controller=728,isLocallyMounted=2016}
local function field(_,n) return {get_offset=function() return state.bad and 0 or offsets[n] end} end
local mount=object({find_property=field},1,'BP_Mount_C')
state.mount=mount
local viewport_class={}
local viewport={is_a=function(_,c) return c==viewport_class end}
local pc={get_class=function() return {find_property=field} end,get_address=function() return 500 end}
function pc:get_property(n) assert(n=='Pawn');return state.pawn end
state.pc=pc
function make_pawn(is_mount)
 local o={is_a=function(_,c) return is_mount and c==mount end}
 function o:get_property(n)
  assert(not self.dead,'Stale pawn read')
  if n=='Controller' then return not state.foreign and pc or nil end
  assert(n=='isLocallyMounted');return state.mounted
 end
 return o
end
state.pawn=make_pawn(true)
local library={GetPlayerController=function(_,v,i) assert(v==viewport and i==0);return state.pc end}
local fn={get_properties_size=function() return 24 end,find_property=field}
local array={get_objects_offset=function() return 0 end,get_item_distance=function() return 24 end,
 get_object_count=function() return 3 end,get_object=function(_,i) return state.objects[i] end}
uevr={api={get_uobject_array=function() return array end,find_uobject=function(_,path)
 if path=='Class /Script/Engine.GameplayStatics' then
  return {find_function=function() return fn end,get_class_default_object=function() return library end}
 elseif path=='Class /Script/Engine.GameViewportClient' then return viewport_class
 elseif path=='BlueprintGeneratedClass /Game/Mounts/BP_Mount.BP_Mount_C' then return not state.missing and mount end
 error(path)
end},params={vr={is_runtime_ready=function() return not state.runtime_off end,
 is_hmd_active=function() return state.active end,is_using_controllers=function() return state.using end,
 get_mod_value=function() return state.menu and 'true' or 'false' end,get_lowest_xinput_index=function() return 0 end},
 functions={is_drawing_ui=function() return state.panel end,log_info=function(s) state.logs[#state.logs+1]=s end,
 log_warn=function(s) state.logs[#state.logs+1]=s end}}}
state.engine={get_class=function() return {find_property=field} end,
 get_property=function(_,n) assert(n=='GameViewport');return viewport end}
local tuning={get=function(n) assert(n=='horse.steering_exponent');return state.exponent end}
feature=require('libs/horse_steering')(tuning)
function tick() feature.tick(state.engine,.016) end
function input(x,user)
 local s={Gamepad={sThumbLX=x,sThumbLY=25000,sThumbRX=19000,sThumbRY=-9000,
  wButtons=123,bLeftTrigger=100,bRightTrigger=200}}
 feature.input(nil,user or 0,s)
 assert(s.Gamepad.sThumbLY==25000 and s.Gamepad.sThumbRX==19000 and s.Gamepad.sThumbRY==-9000)
 assert(s.Gamepad.wButtons==123 and s.Gamepad.bLeftTrigger==100 and s.Gamepad.bRightTrigger==200)
 return s.Gamepad.sThumbLX
end
function healthy() for _,s in ipairs(state.logs) do assert(not s:find('stopped safely',1,true),s) end end
'''


def run(name, code):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().script_path = str(ROOT / 'scripts/?.lua')
    lua.execute("package.path=script_path..';'..package.path")
    lua.execute(MOCK)
    lua.execute(code)
    print('PASS', name)


run('power curve softens small steering and retains zero, sign, symmetry and full lock', '''
tick();healthy();assert(input(0)==0 and input(32767)==32767 and input(-32768)==-32768)
assert(math.abs(input(16384)-8192)<=1 and input(-16384)==-8192)
assert(input(8192)>0 and input(8192)<input(16384))
local previous=-32769
for x=-32768,32767,127 do local y=input(x);assert(y>=previous);previous=y end
''')
run('only mounted local left steering changes; other controllers and walking stay native', '''
tick();assert(input(16384,1)==16384)
state.foreign=true;tick();assert(input(16384)==16384)
state.foreign=false;state.mounted=false;tick();assert(input(16384)==16384)
state.mounted=true;state.pawn=make_pawn(false);tick();assert(input(16384)==16384)
healthy()
''')
run('dismount and replacement possession never access the old pawn from XInput', '''
tick();local old=state.pawn;old.dead=true;state.pawn=make_pawn(false)
tick();assert(input(16384)==16384)
state.pawn=nil;tick();assert(input(16384)==16384)
state.pawn=make_pawn(true);tick();assert(input(16384)<10000);healthy()
''')
run('menus, panel, inactive runtime, tracking and reset bypass the curve immediately', '''
tick();state.menu=true;assert(input(16384)==16384)
state.menu=false;state.panel=true;assert(input(16384)==16384)
state.panel=false;state.active=false;assert(input(16384)==16384)
state.active=true;state.runtime_off=true;assert(input(16384)==16384)
state.runtime_off=false;state.using=false;assert(input(16384)==16384)
state.using=true;feature.reset();assert(input(16384)==16384);healthy()
''')
run('live exponent one preserves native integers; stronger values soften more', '''
tick();local initial=input(16384)
state.exponent=3;tick();assert(input(16384)<initial)
state.exponent=1;tick()
for x=-32768,32767,127 do assert(input(x)==x) end
healthy()
''')
run('missing class retries; recycled class or unknown metadata leaves input untouched', '''
state.missing=true;tick();assert(input(16384)==16384)
state.missing=false;for i=1,65 do tick() end;assert(input(16384)<10000)
state.objects[1]=nil;tick();assert(input(16384)==16384);healthy()
''')
run('native layout failure stops only the steering helper before any input write', '''
state.bad=true;tick();assert(input(16384)==16384)
assert(#state.logs==1);state.bad=false;tick();assert(input(16384)==16384 and #state.logs==1)
''')
