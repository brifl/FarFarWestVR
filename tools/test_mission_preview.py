"""Check mission-card detection and menu transitions using the actual Lua helpers.

Requires lupa. Native rendering still needs a headset playtest.
"""
from pathlib import Path

from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
MOCK = r'''
state={objects={},count=48,logs={},values={VR_2DScreenMode='false'},screen_writes=0,queries=0,reads=0,
    runtime=true,hmd=true,tag='ffw-ue58-sdk-v1',bad_layout=false}
local function log(s) table.insert(state.logs,s) end
local widget_class={find_function=function(_,name)
    assert(name=='IsInViewport');return {get_properties_size=function() return 1 end}
end,find_property=function(_,name)
    assert(name=='Visibility');return {get_offset=function() return state.bad_layout and 0 or 221 end}
end}
function make_widget(index,name,kind,viewport,visibility)
    local o={viewport=viewport,visibility=visibility or 3,index=index,kind=kind}
    function o:get_address() return index*256 end
    function o:get_short_name() return name end
    function o:read_dword(offset) assert(offset==12);return index end
    function o:get_class() return {get_short_name=function() return kind end} end
    function o:is_a(c) return c==widget_class end
    function o:get_property(n) assert(not self.dead and n=='Visibility');return self.visibility end
    function o:IsInViewport() assert(not self.dead);return self.viewport end
    state.objects[index]=o;return o
end
state.card=make_widget(42,'UI_LoadingScreen_C_1','UI_LoadingScreen_C',false)
state.map=make_widget(43,'UI_Map_C_1','UI_Map_C',true)
state.card_class=make_widget(47,'UI_LoadingScreen_C','WidgetBlueprintGeneratedClass',false)
local viewport_class={}
state.viewport={is_a=function(_,c) return c==viewport_class end}
state.engine={get_class=function() return {find_property=function(_,name)
    assert(name=='GameViewport');return {get_offset=function() return 3448 end} end} end,
    get_property=function(_,name) assert(name=='GameViewport');return state.viewport end}
local library={}
function library:GetAllWidgetsOfClass(viewport,found,kind,top_level)
    assert(viewport==state.viewport and kind==state.card_class and top_level)
    state.queries=state.queries+1
    for _,o in pairs(state.objects) do
        if o.kind=='UI_LoadingScreen_C' and o.viewport then found[#found+1]=o end
    end
end
local library_class={get_class_default_object=function() return library end,
    find_function=function(_,name)
        assert(name=='GetAllWidgetsOfClass')
        return {get_properties_size=function() return 40 end,find_property=function(_,field)
            return {get_offset=function()
                return ({WorldContextObject=0,FoundWidgets=8,WidgetClass=24,TopLevelOnly=32})[field]
            end}
        end}
    end}
local array={get_objects_offset=function() return 0 end,get_item_distance=function() return 24 end,
    get_object_count=function() return state.count end,get_object=function(_,i)
        state.reads=state.reads+1;return state.objects[i] end}
local vr={is_runtime_ready=function() return state.runtime end,is_hmd_active=function() return state.hmd end,
    recenter_view=function() end,get_rotation_offset=function() end,set_rotation_offset=function() end,
    get_action_handle=function() return 1 end,get_right_joystick_source=function() return 2 end,
    is_action_active=function() return false end}
function vr:get_mod_value(name) return state.values[name] end
function vr.set_mod_value(name,value)
    state.values[name]=value
    if name=='VR_2DScreenMode' then state.screen_writes=state.screen_writes+1 end
end
UEVR_Quaternionf={new=function() return {} end}
uevr={api={get_uobject_array=function() return array end,find_uobject=function(_,name)
    if name=='Class /Script/UMG.UserWidget' then return widget_class end
    if name=='Class /Script/UMG.WidgetBlueprintLibrary' then return library_class end
    if name=='Class /Script/Engine.GameViewportClient' then return viewport_class end
    assert(name=='WidgetBlueprintGeneratedClass /Game/Interfaces/UI_LoadingScreen.UI_LoadingScreen_C')
    if state.class_missing then return nil end
    return state.card_class end},
    params={vr=vr,functions={get_tag=function() return state.tag end,
        log_info=log,log_warn=log,is_drawing_ui=function() return false end}},
    sdk={callbacks={on_xinput_get_state=function(fn) state.input=fn end,
        on_pre_engine_tick=function(fn) state.tick=fn end,on_script_reset=function(fn) state.reset=fn end}}}
state.game_log='LogLoad: LoadMap: /Game/Levels/L_Lobby\n'
    ..'LogLoadingScreen: Hiding loading screen\n'
    ..'LogViewport: Viewport MouseCaptureMode Changed, NoCapture -> CapturePermanently\n'
io.open=function(name)
    assert(name=='FarFarWest.log')
    local position=0
    return {seek=function(_,mode,offset)
        if mode=='end' then return #state.game_log end
        assert(mode=='set');position=offset;return position
    end,read=function(_,n)
        local text=state.game_log:sub(position+1,position+n);position=position+#text;return text
    end,close=function() end}
end
function frames(n) for i=1,n or 40 do state.tick(state.engine,.016) end end
function capture(mode)
    state.game_log=state.game_log..'LogViewport: Viewport MouseCaptureMode Changed, old -> '..mode..'\n'
    frames(8)
end
function healthy()
    for _,s in ipairs(state.logs) do
        assert(not s:find('stopped safely',1,true) and not s:find('Helper unavailable',1,true),s)
    end
end
'''


def run(name, test, setup=""):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().script_path = str(ROOT / "scripts/?.lua")
    lua.execute("package.path=script_path..';'..package.path")
    lua.execute(MOCK)
    lua.execute(setup)
    lua.execute((ROOT / "scripts/pause_screen.lua").read_text())
    lua.execute(test)
    print("PASS", name)


run("custom card outlives generic loading; removal clears screen overlay", """
frames();healthy();assert(state.values.VR_2DScreenMode=='false' and farfarwest_gameplay_ready)
state.card.viewport=true;frames(20);healthy()
assert(state.values.VR_2DScreenMode=='true' and state.values.VR_EnableGUI=='true')
assert(state.values.UI_Size=='1.800000' and state.values.UI_Distance=='3.000000')
assert(not farfarwest_gameplay_ready)
local writes,queries=state.screen_writes,state.queries;frames(120)
assert(state.screen_writes==writes and state.queries==queries)
state.card.viewport=false;frames(2);healthy()
assert(state.values.VR_2DScreenMode=='false' and state.values.VR_EnableGUI=='false')
assert(farfarwest_gameplay_ready)
""")
run("card transitions into native map and pause menus without a false resume", """
frames();state.card.viewport=true;frames(20)
capture('CaptureDuringMouseDown');state.card.viewport=false;frames(2);healthy()
assert(state.values.VR_2DScreenMode=='true' and not farfarwest_gameplay_ready)
capture('CapturePermanently');assert(state.values.VR_2DScreenMode=='false')
capture('CaptureDuringMouseDown');assert(state.values.VR_2DScreenMode=='true')
capture('CapturePermanently');healthy();assert(farfarwest_gameplay_ready)
""")
run("hidden/collapsed cards and unrelated map widgets do not force screen mode", """
state.card.viewport=true;state.card.visibility=1;frames();healthy()
assert(state.values.VR_2DScreenMode=='false')
state.card.visibility=2;frames(20);assert(state.values.VR_2DScreenMode=='false')
state.card.viewport=false;state.card.visibility=3;frames(20)
assert(state.values.VR_2DScreenMode=='false' and farfarwest_gameplay_ready)
""")
run("destroyed/reused slots and newly appended cards rebind safely", """
frames();state.card.viewport=true;frames(20)
state.card.dead=true;state.objects[42]=nil;frames(2)
assert(state.values.VR_2DScreenMode=='false')
state.card=make_widget(42,'UI_LoadingScreen_C_2','UI_LoadingScreen_C',true)
frames(30);healthy();assert(state.values.VR_2DScreenMode=='true')
state.card.viewport=false;frames(2)
state.card=make_widget(48,'UI_LoadingScreen_C_3','UI_LoadingScreen_C',true);state.count=49
frames(5);healthy();assert(state.values.VR_2DScreenMode=='true')
""")
run("layout mismatch disables detection while normal menu transitions work", """
frames();assert(state.values.VR_2DScreenMode=='false')
capture('CaptureDuringMouseDown');assert(state.values.VR_2DScreenMode=='true')
capture('CapturePermanently');assert(farfarwest_gameplay_ready)
local found=false
for _,s in ipairs(state.logs) do found=found or s:find('Detection stopped safely',1,true)~=nil end
assert(found)
""", "state.bad_layout=true")
run("other backends keep the existing log-driven menu helper", """
state.card.viewport=true;frames();healthy();assert(farfarwest_gameplay_ready)
capture('CaptureDuringMouseDown');assert(state.values.VR_2DScreenMode=='true')
capture('CapturePermanently');assert(farfarwest_gameplay_ready)
""", "state.tag='other-backend'")

run("large object arrays do not delay a low-index mission card", """
frames();assert(state.values.VR_2DScreenMode=='false')
local reads=state.reads;state.card.viewport=true;frames(4);healthy()
assert(state.values.VR_2DScreenMode=='true' and state.reads-reads<30)
""", "state.count=200000")

run("class availability and viewport replacement are retried without stale context", """
frames();healthy();assert(state.queries==0)
state.class_missing=false;state.card.viewport=true;frames(20);healthy()
assert(state.values.VR_2DScreenMode=='true')
state.card.viewport=false;frames(8);assert(state.values.VR_2DScreenMode=='false')
state.viewport={is_a=function() return true end}
state.card.viewport=true;frames(4);healthy();assert(state.values.VR_2DScreenMode=='true')
""", "state.class_missing=true")
