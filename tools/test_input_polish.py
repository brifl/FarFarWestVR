"""Angular stabilization and native marker discovery (lupa)."""
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]


def run(name, code, fixture=''):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().script_path = str(ROOT / 'scripts/?.lua')
    lua.execute("package.path=script_path..';'..package.path")
    lua.execute(fixture)
    lua.execute(code)
    print('PASS', name)


run('angular smoothing crosses yaw wrap by the short path and resets after gaps', '''
local f=require('libs/aim_stabilization')()
f.step(179,0,.01,1)
local y=f.step(-179,0,.01,1);assert(math.abs(y)>170)
y=f.step(10,5,.3,1);assert(y==10)
f.reset();local y,p=f.step(-40,20,.01,1);assert(y==-40 and p==20)
y,p=f.step(60,30,.01,0);assert(y==60 and p==30)
''')
run('stronger stabilization filters more jitter while rapid sweeps catch up', '''
local factory=require('libs/aim_stabilization')
local function jitter(strength)
 local f=factory();f.step(0,0,.01,strength);local sum=0
 for i=1,100 do local y=f.step(i%2==0 and .3 or -.3,0,.01,strength);sum=sum+math.abs(y) end
 return sum
end
assert(jitter(1)<jitter(.3) and jitter(.3)<jitter(0))
local f=factory();f.step(0,0,.01,1)
local y
for i=1,100 do y=f.step(i*2,0,.01,1) end
local error=(200-y+180)%360-180;assert(math.abs(error)<9)
''')

NATIVE = r'''
state={objects={},next=1,calls=0,handled={},logs={}}
local function object(name)
 local o={index=state.next,name=name};state.next=state.next+1;state.objects[o.index]=o
 function o:get_address() return self.index*256 end
 function o:read_dword(n) assert(n==12);return self.index end
 function o:get_short_name() return self.name end
 return o
end
state.target=object('BP_ObjectPing_C');state.component_class={};state.viewport_class={}
state.actor=object('BP_ObjectPing_Default_C_1')
function state.actor:is_a(c) return c==state.target end
state.component=object('Widget')
function state.component:is_a(c) return c==state.component_class end
state.components={state.component};state.actors={state.actor}
function state.actor:K2_GetComponentsByClass(c) assert(c==state.component_class);return state.components end
state.viewport={is_a=function(_,c) return c==state.viewport_class end}
local methods={GetAllActorsOfClass={32,{WorldContextObject=0,ActorClass=8,OutActors=16}},
 K2_GetComponentsByClass={24,{ComponentClass=0,ReturnValue=8}}}
local function class(default)
 return {get_class_default_object=function() return default end,
 find_function=function(_,n) return {get_properties_size=function() return state.bad and 0 or methods[n][1] end,
 find_property=function(_,p) return {get_offset=function() return methods[n][2][p] end} end} end}
end
local library={GetAllActorsOfClass=function(_,v,c,out)
 assert(v==state.viewport and c==state.target);state.calls=state.calls+1
 for _,actor in ipairs(state.actors) do out[#out+1]=actor end
end}
state.engine={get_property=function(_,n) assert(n=='GameViewport');return state.viewport end,
 get_class=function() return {find_property=function(_,n) assert(n=='GameViewport');return {get_offset=function() return 3448 end} end} end}
local array={get_objects_offset=function() return 0 end,get_item_distance=function() return 24 end,
 get_object=function(_,i) return state.objects[i] end}
uevr={api={get_uobject_array=function() return array end,find_uobject=function(_,path)
 if path=='Class /Script/Engine.GameplayStatics' then return class(library) end
 if path=='Class /Script/Engine.Actor' then return class() end
 if path=='Class /Script/Engine.GameViewportClient' then return state.viewport_class end
 if path=='BlueprintGeneratedClass /Game/Interfaces/Pings/BP_ObjectPing.BP_ObjectPing_C' then return state.target end
 return nil
end},params={functions={log_warn=function(s) state.logs[#state.logs+1]=s end}}}
feature=require('libs/marker_discovery')(state.component_class,function(c) state.handled[#state.handled+1]=c end)
'''
run('native queries find reused marker slots without any UObject-count growth', '''
feature.tick(state.engine,.01);assert(state.handled[1]==state.component)
local replacement={is_a=function(_,c) return c==state.component_class end}
state.components={replacement}
for i=1,4 do feature.tick(state.engine,.016) end
assert(state.handled[#state.handled]==replacement and #state.logs==0 and state.calls==2)
''', NATIVE)
run('marker queries follow the current viewport and stay inside their time interval', '''
feature.tick(state.engine,.01);local calls=state.calls
feature.tick(state.engine,.01);assert(state.calls==calls)
state.viewport={is_a=function(_,c) return c==state.viewport_class end}
feature.tick(state.engine,.1);assert(state.calls==calls+1 and #state.logs==0)
''', NATIVE)
run('unknown metadata and excessive actor counts disable only the fast discovery path', '''
state.bad=true;feature.tick(state.engine,.1);assert(state.calls==0 and #state.logs==1)
state.bad=false;feature.tick(state.engine,.1);assert(state.calls==0)
feature=require('libs/marker_discovery')(state.component_class,function() error('must not iterate excessive result') end)
for i=1,129 do state.actors[i]=state.actor end
feature.tick(state.engine,.1);assert(#state.logs==2)
''', NATIVE)
