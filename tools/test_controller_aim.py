"""Controller aim, input isolation and world-change checks; requires lupa.

Runs the real Lua callbacks. Native setter conversion also needs live validation.
"""
from pathlib import Path

from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
MOCK = r'''
state={yaw=0,pitch=0,stick=0,offset={x=0,y=0,z=0,w=1},camera={x=0,y=30,z=0},
    logs={},writes={},active=true,runtime=true,hmd=true,drawing=false,screen='false',
    tag='ffw-ue58-sdk-v1',ignored=false,pawn={},bad_parameters=false}
farfarwest_gameplay_ready=true
local function log(s) table.insert(state.logs,s) end
io.open=function(name)
    assert(name=='controller_aim_backend.txt')
    return {read=function() return 'ue5-camera-aim-pose-v1\n' end,close=function() end}
end
for _,n in ipairs({'UEVR_Vector3f','UEVR_Vector2f','UEVR_Quaternionf'}) do
    _G[n]={new=function() return {x=0,y=0,z=0,w=1} end}
end
local sizes={GetPlayerController=24,GetControlRotation=24,SetControlRotation=24,IsLookInputIgnored=1}
local offsets={WorldContextObject=0,PlayerIndex=8,ReturnValue=16,NewRotation=0}
local controller_class,viewport_class={},{}
local function fn(name)
    return {get_properties_size=function()
        return state.bad_parameters and name=='SetControlRotation' and 12 or sizes[name]
    end,find_property=function(_,field)
        return {get_offset=function() return name=='GetControlRotation' and 0 or offsets[field] end}
    end}
end
function controller_class:find_function(name) return fn(name) end
function controller_class:find_property(name)
    assert(name=='Pawn');return {get_offset=function() return 744 end}
end
function make_controller(name)
    local pc={name=name}
    function pc:is_a(c) assert(not self.dead);return c==controller_class end
    function pc:get_property(field) assert(not self.dead and field=='Pawn');return state.pawn end
    function pc:IsLookInputIgnored() assert(not self.dead);return state.ignored end
    function pc:GetControlRotation()
        assert(not self.dead)
        return {Pitch=state.camera.x,Yaw=state.camera.y,Roll=0,__typed=true}
    end
    function pc:SetControlRotation(t)
        assert(not self.dead and t.__typed,'Setter requires the typed double rotation')
        state.camera={x=t.Pitch,y=t.Yaw,z=t.Roll}
        table.insert(state.writes,{controller=self,Pitch=t.Pitch,Yaw=t.Yaw,Roll=t.Roll})
    end
    return pc
end
state.controller=make_controller('first')
state.viewport={is_a=function(_,c) return c==viewport_class end}
local statics={GetPlayerController=function(_,context,index)
    assert(context==state.viewport and index==0);return state.controller
end}
local statics_class={find_function=function(_,name) return fn(name) end,
    get_class_default_object=function() return statics end}
local engine={get_class=function() return {find_property=function(_,field)
    assert(field=='GameViewport');return {get_offset=function() return 3448 end} end} end,
    get_property=function(_,field) assert(field=='GameViewport');return state.viewport end}
local vr={is_runtime_ready=function() return state.runtime end,is_hmd_active=function() return state.hmd end,
    is_using_controllers=function() return true end,get_mod_value=function() return state.screen end,
    get_right_joystick_source=function() return 2 end,get_lowest_xinput_index=function() return 0 end,
    get_right_controller_index=function() return 2 end,
    get_joystick_axis=function(_,stick) stick.x=state.stick;stick.y=0 end,
    get_rotation_offset=function(q) for k,v in pairs(state.offset) do q[k]=v end end,
    set_rotation_offset=function(q) for k,v in pairs(q) do state.offset[k]=v end end}
function vr.get_pose(_,position,q)
    local y,p=math.rad(state.yaw)/2,math.rad(state.pitch)/2
    q.x=math.cos(y)*math.sin(p);q.y=-math.sin(y)*math.cos(p)
    q.z=math.sin(y)*math.sin(p);q.w=math.cos(y)*math.cos(p)
end
uevr={params={vr=vr,functions={log_info=log,log_warn=log,
    get_tag=function() return state.tag end,is_drawing_ui=function() return state.drawing end}},
    api={find_uobject=function(_,path)
        return ({['Class /Script/Engine.GameplayStatics']=statics_class,
            ['Class /Script/Engine.Controller']=controller_class,
            ['Class /Script/Engine.GameViewportClient']=viewport_class})[path]
    end},sdk={callbacks={on_pre_engine_tick=function(fn) state.pre=fn end,
        on_early_calculate_stereo_view_offset=function(fn) state.camera_tick=fn end,
        on_xinput_get_state=function(fn) state.input=fn end}}}
function frame()
    state.pre(engine,.01)
    state.camera_tick(nil,0,100,nil,state.camera,true)
end
function warmup() frame();frame() end
function input(index)
    local result={Gamepad={sThumbRX=111,sThumbRY=222,sThumbLX=333,sThumbLY=444,wButtons=0xffff,
        bLeftTrigger=55,bRightTrigger=66}}
    state.input(nil,index or 0,result);return result.Gamepad
end
function near(a,b) assert(math.abs(a-b)<.000001,tostring(a)..' differs from '..tostring(b)) end
function healthy() for _,s in ipairs(state.logs) do assert(not s:find('unavailable',1,true),s) end end
'''


def run(name, test, setup=""):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MOCK)
    lua.execute(setup)
    lua.execute((ROOT / "scripts/controller_aim.lua").read_text())
    lua.execute(test)
    print("PASS", name)


run("tiny pose changes reach native rotation without the stick dead band", """
warmup();healthy();near(state.camera.y,30)
for _,yaw in ipairs({.001,.002,.01,.05,.10,.249}) do
    state.yaw=yaw;frame();healthy();near(state.camera.y,30+yaw)
end
state.pitch=10;frame();near(state.camera.x,10)
local i=input();assert(i.sThumbRX==0 and i.sThumbRY==0)
assert(i.sThumbLX==333 and i.sThumbLY==444 and i.wButtons==0xffff)
assert(i.bLeftTrigger==55 and i.bRightTrigger==66)
""")
run("yaw wrap, pitch clamp and 45-degree snap latch stay intact", """
warmup();state.yaw=170;frame();near(state.camera.y,-160)
state.yaw=0;state.pitch=89;frame();near(state.camera.x,85)
state.pitch=-89;frame();near(state.camera.x,-85)
state.pitch=0;state.stick=1;frame();near(state.camera.y,75)
frame();near(state.camera.y,75)
state.stick=0;frame();state.stick=-1;frame();near(state.camera.y,30);healthy()
""")
run("aiming wrist changes camera compensation without rotating the world anchor", """
warmup();state.yaw=20;frame();near(state.camera.y,50)
local offset=-math.deg(2*math.atan(state.offset.y,state.offset.w))
near(state.camera.y+offset,30)
state.yaw=35;frame();offset=-math.deg(2*math.atan(state.offset.y,state.offset.w))
near(state.camera.y+offset,30);healthy()
""")
run("menu, panel and inactive headset retain their native input behavior", """
warmup();local writes=#state.writes
for _,mode in ipairs({'menu','panel','headset','runtime','gate'}) do
    state.screen=mode=='menu' and 'true' or 'false';state.drawing=mode=='panel'
    state.hmd=mode~='headset';state.runtime=mode~='runtime';farfarwest_gameplay_ready=mode~='gate'
    frame();assert(#state.writes==writes)
    local i=input();assert(i.sThumbRX==111 and i.sThumbRY==222 and i.wButtons==0xffff)
end
""")
run("look locks, no pawn and replacement controllers do not write stale objects", """
warmup();local writes=#state.writes
state.ignored=true;state.yaw=10;frame();assert(#state.writes==writes)
state.ignored=false;state.pawn=nil;frame();assert(#state.writes==writes)
state.pawn={};local old=state.controller;old.dead=true
state.controller=make_controller('replacement');state.viewport={is_a=function() return true end}
frame();healthy();assert(state.writes[#state.writes].controller==state.controller)
near(state.camera.y,40)
state.controller=nil;frame();healthy()
""")
run("other user indices are untouched", """
warmup();local i=input(1);assert(i.sThumbRX==111 and i.sThumbRY==222 and i.wButtons==0xffff)
""")
run("old backends keep the established analog aiming path", """
warmup();state.yaw=10;local i=input()
assert(#state.writes==0 and i.sThumbRX>8000 and i.wButtons==0xffff)
""", "state.tag='older-backend'")
run("unexpected native layout falls back once without stopping other controls", """
warmup();assert(#state.writes==0)
state.yaw=10;local i=input();assert(i.sThumbRX>8000 and i.wButtons==0xffff)
local warnings=0;for _,s in ipairs(state.logs) do if s:find('Native rotation unavailable',1,true) then warnings=warnings+1 end end
assert(warnings==1);frame();frame()
warnings=0;for _,s in ipairs(state.logs) do if s:find('Native rotation unavailable',1,true) then warnings=warnings+1 end end
assert(warnings==1)
""", "state.bad_parameters=true")
