"""Exercise the actual reticle callbacks across possession and HUD destruction.

Requires lupa; native calls are mocked, so a headset playtest is still needed.
An optional source path allows checking that the old implementation fails.
"""
from pathlib import Path
import sys

from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "scripts/reticle.lua"
MOCK = r'''
state={objects={},logs={},traces=0,active=true}
farfarwest_gameplay_ready=true
io.open=function() return nil end
local sizes={SetRenderTranslation=16,SetRenderOpacity=4,GetCachedGeometry=80,
    GetOwningPlayerPawn=8,GetLocalSize=96,LocalToViewport=128,
    GetViewportSize=24,LineTraceSingle=512}
local function class(default)
    return {find_property=function(_,name)
        return {get_offset=function() return ({RenderTransform=0x90,RenderOpacity=0xe0,Slot=0x30})[name] end}
    end,find_function=function(_,name)
        return {get_properties_size=function() return sizes[name] end,
            get_child_properties=function() return nil end}
    end,get_class_default_object=function() return default end}
end
local image_class,widget_class=class(),class()
local function object(index,name)
    local o={index=index}
    function o:get_address() return index*256 end
    function o:get_short_name() return name end
    function o:read_dword(offset) assert(offset==12);return index end
    state.objects[index]=o;return o
end
function make_pawn(index,name) return object(index,name) end
function make_hud(first)
    local owner=object(first+1,'UI_Player_C_'..first)
    function owner:is_a(c) return c==widget_class end
    function owner:GetOwningPlayerPawn()
        assert(not self.dead,'Dereferenced a destroyed HUD owner');return state.pawn
    end
    local image=object(first,'Crosshair_Top')
    image.opacity=.8;image.translation={X=3,Y=4}
    function image:is_a(c) return c==image_class end
    function image:get_outer() return {get_outer=function() return owner end} end
    function image:get_property(name)
        assert(name=='RenderTransform')
        return {Angle=0,Shear={X=0,Y=0},Translation=self.translation,Scale={X=1,Y=1}}
    end
    function image:get_float_property(name) assert(name=='RenderOpacity');return self.opacity end
    function image:SetRenderOpacity(value) self.opacity=value end
    function image:SetRenderTranslation(value) self.translation=value end
    function image:GetCachedGeometry() return {} end
    state.image,state.owner=image,owner
end
state.pawn=make_pawn(902,'original player');make_hud(900)
local layout={GetViewportSize=function(_,owner) assert(not owner.dead);return {X=1000,Y=500} end}
local slate={GetLocalSize=function() return {X=10,Y=10} end,
    LocalToViewport=function(_,owner,geometry,local_point,pixel)
        assert(not owner.dead);pixel.result={X=495+local_point.X,Y=245+local_point.Y}
    end}
local system={LineTraceSingle=function(_,pawn,from,to,channel,complex,ignored)
    assert(pawn==state.pawn and not pawn.dead,'Traced with a stale pawn')
    assert(ignored[1]==state.pawn,'Ignored a stale pawn')
    state.traces=state.traces+1;state.last_pawn=pawn
    if state.trace_error then error('simulated native trace failure') end
    return false
end}
local classes={Image=image_class,UserWidget=widget_class,
    WidgetLayoutLibrary=class(layout),SlateBlueprintLibrary=class(slate),KismetSystemLibrary=class(system)}
local callbacks={}
for _,name in ipairs({'on_early_calculate_stereo_view_offset','on_post_calculate_stereo_view_offset',
    'on_post_engine_tick','on_script_reset'}) do callbacks[name]=function(fn) state[name]=fn end end
uevr={api={get_uobject_array=function() return {
    get_objects_offset=function() return 0 end,get_item_distance=function() return 24 end,
    get_object_count=function() return 1000 end,get_object=function(_,i) return state.objects[i] end} end,
    find_uobject=function(_,path) return classes[path:match('%.([^%.]+)$')] end},
    params={functions={get_tag=function() return 'ffw-ue58-sdk-v1' end,
        is_drawing_ui=function() return false end,
        log_info=function(s) table.insert(state.logs,s) end,
        log_warn=function(s) table.insert(state.logs,s) end},vr={
        is_runtime_ready=function() return state.active end,is_hmd_active=function() return true end,
        get_mod_value=function() return 'false' end,get_ue_projection_matrix=function() end}},
    sdk={callbacks=callbacks}}
UEVR_Matrix4x4f={new=function() return {get=function(_,col,row)
    if (col==0 and row==0) or (col==1 and row==1) or (col==2 and row==3) then return 1 end
    return 0
end} end}
function frame(camera)
    if camera~=false then
        local p,r={x=0,y=0,z=0},{x=0,y=0,z=0}
        state.on_early_calculate_stereo_view_offset(nil,0,100,p,r,true)
        state.on_post_calculate_stereo_view_offset(nil,0,100,p,r,true)
    end
    state.on_post_engine_tick(nil,.016)
end
function healthy()
    for _,line in ipairs(state.logs) do assert(not line:find('Stopped safely',1,true),line) end
end
function warmup() for i=1,12 do frame() end;healthy();assert(state.traces>0) end
'''


def run(name, test):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().script_path = str(ROOT / "scripts/?.lua")
    lua.execute("package.path=script_path..';'..package.path")
    lua.execute(MOCK)
    lua.execute(SOURCE.read_text())
    lua.execute(test)
    print("PASS", name)


run("mount and dismount replace pawn without retaining freed objects", """
warmup()
local old=state.pawn
state.pawn=make_pawn(903,'horse');old.dead=true;state.objects[old.index]=nil
frame();healthy();assert(state.last_pawn==state.pawn)
old=state.pawn
state.pawn=make_pawn(904,'replacement player');old.dead=true;state.objects[old.index]=nil
for i=1,120 do frame() end
healthy();assert(state.last_pawn==state.pawn and state.traces>120)
""")
run("no pawn during possession gap hides reticle and resumes afterward", """
warmup();local traces=state.traces;state.pawn=nil
for i=1,20 do frame() end
healthy();assert(state.traces==traces and state.image.opacity==0)
state.pawn=make_pawn(904,'replacement player')
frame(false);assert(state.traces==traces)
frame();healthy();assert(state.traces==traces+1 and state.image.opacity==.8)
""")
run("destroyed HUD owner is rejected before native calls; new HUD rebinds", """
warmup();local old_image,old_owner=state.image,state.owner
old_owner.dead=true;state.objects[old_owner.index]=nil
-- The child image may survive the owner for a tick; discovery must not use it.
frame();healthy()
state.objects[old_image.index]=nil
make_hud(910)
for i=1,100 do frame() end
healthy();assert(state.last_pawn==state.pawn and state.image.opacity==.8)
""")
run("menus restore crosshair; genuine trace failure still stops safely", """
warmup();state.active=false;frame();assert(state.image.opacity==.8)
state.active=true;for i=1,12 do frame() end;healthy()
state.trace_error=true;frame();local traces=state.traces
frame();assert(state.traces==traces)
assert(state.logs[#state.logs]:find('Stopped safely during trace firing target using current pawn',1,true))
""")
