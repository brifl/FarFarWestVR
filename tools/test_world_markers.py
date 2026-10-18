"""Focused marker lifecycle checks; run with Python and lupa installed.

These model native calls; headset validation remains necessary.
"""
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
MOCK = r'''
state={objects={},next=10,logs={},family='UI_WorldIcon_C',active=true,created=0,
    world={X=1000,Y=0,Z=0},rotation={x=0,y=0,z=0},aim=0,moves=0}
farfarwest_gameplay_ready=true
io.open=function() return nil end
local function object(o,name)
    local index=state.next;state.next=index+1;state.objects[index]=o
    function o:get_address() return index*256 end
    function o:read_dword(offset) assert(offset==12);return index end
    function o:get_short_name() return name end
    return o
end
local sizes={K2_GetComponentLocation=24,GetOwner=8,GetOwningPlayer=8,GetDesiredSize=16,
    ForceLayoutPrepass=0,AddToViewport=4,RemoveFromParent=0,SetAlignmentInViewport=16,
    SetDesiredSizeInViewport=16,SetPositionInViewport=24,SetRenderOpacity=4,SetVisibility=1,
    SetBrush=176,SetColorAndOpacity=16,Create=32,GetViewportSize=24,
    K2_SetWorldLocation=296,K2_SetRelativeLocation=296,K2_GetActorLocation=24,
    DeprojectScreenPositionToWorld=64}
local function class(name)
    return {get_short_name=function() return name end,find_property=function(_,n)
        local offsets={Space=1512,WidgetClass=1520,Pivot=1568,Widget=1800,Image_Icon=808,Image_Aura=824}
        return {get_offset=function() return state.bad_layout and 1 or offsets[n] end}
    end,find_function=function(_,n) return {get_properties_size=function() return sizes[n] end,
        get_child_properties=function() return nil end} end}
end
local component_class,widget_class,image_class=class('component'),class('widget'),class('image')
local root=object({},'Billboard')
local actor=object({hidden=false},'owner')
function actor:get_property(n) if n=='RootComponent' then return root end;assert(n=='bHidden');return self.hidden end
function actor:get_class() return class('actor') end
function actor:K2_GetActorLocation() return state.world end
local player=object({},'player')
function player:get_class() return class('player') end
function player:DeprojectScreenPositionToWorld(x,y,origin,direction)
    if state.deproject_fails then return false end
    local angle=math.rad(state.aim);local c,s=math.cos(angle),math.sin(angle)
    local right=(x-1000)/1000;local up=(500-y)/500
    origin.result={X=0,Y=0,Z=0};direction.result={X=c-s*right,Y=s+c*right,Z=up}
    return true
end
local source=object({opacity=.7,visibility=0,icon={},label='Start Mission'},'source')
function source:get_class() return class(state.family) end
function source:GetOwningPlayer() return player end
function source:GetDesiredSize() return {X=64,Y=32} end
function source:get_float_property(n) assert(n=='RenderOpacity');return self.opacity end
function source:SetRenderOpacity(n) self.opacity=n end
function source:get_property(n)
    if n=='Visibility' then return self.visibility end
    assert(n==(state.family=='UI_Guide_C' and 'Image_Aura' or 'Image_Icon'));return self.icon
end
function source.icon:get_property(n) return {name=n} end
local component=object({visible=true,relative={X=0,Y=0,Z=0}},'Widget')
function component:get_class() return component_class end
function component:is_a(c) return c==component_class end
function component:get_outer() return {get_short_name=function()
    return state.family=='UI_Guide_C' and 'BP_LobbyGuide_C_2' or 'BP_WorldIcon_C_1' end} end
function component:GetOwner() return actor end
function component:GetAttachParent() return state.is_root and component or root end
function component:get_property(n)
    if n=='Widget' then return source elseif n=='bVisible' then return self.visible
    elseif n=='RelativeLocation' then return self.relative end
    assert(n=='Pivot');return {X=.5,Y=1}
end
function component:get_bool_property() error('native typed bool getter must not be used') end
function component:read_byte(offset) assert(offset==1512);return 1 end
function component:get_int_property(n) assert(n=='LayerZOrder');return -100 end
function component:K2_GetComponentLocation() return self.warp or state.world end
function component:K2_SetWorldLocation(p,sweep,hit,teleport)
    assert(not sweep and teleport);self.warp=p;state.moves=state.moves+1
    assert(not state.fail_move,'move failure after a partial write')
    local a=math.rad(state.aim);local c,s=math.cos(a),math.sin(a)
    local depth=p.X*c+p.Y*s
    state.display={X=(1+(-p.X*s+p.Y*c)/depth)*1000,Y=(1-p.Z/depth)*500}
end
function component:K2_SetRelativeLocation(p,sweep,hit,teleport)
    assert(not sweep and teleport);self.relative=p;self.warp=nil;state.restored=true
end
local factory={Create=function(_,context,c,owning_player)
    assert(state.family=='UI_WorldIcon_C','live guide must never be cloned')
    assert(context==source and owning_player==player);state.created=state.created+1
    local proxy=object({icon={}},'proxy')
    function proxy:is_a(c) return c==widget_class end
    function proxy:get_property(n) assert(n=='Image_Icon');return self.icon end
    function proxy:SetRenderOpacity(n) self.opacity=n end
    function proxy:AddToViewport(z) assert(z==-100) end
    function proxy:RemoveFromParent() self.removed=true end
    function proxy:SetAlignmentInViewport(p) assert(p.X==.5 and p.Y==1) end
    function proxy:SetDesiredSizeInViewport(p) assert(p.X==64 and p.Y==32) end
    function proxy:SetVisibility(n) assert(n==3) end
    function proxy:SetPositionInViewport(p,dpi) assert(dpi);self.pixel=p end
    function proxy.icon:SetBrush(v) assert(v.name=='Brush') end
    function proxy.icon:SetColorAndOpacity(v) assert(v.name=='ColorAndOpacity') end
    state.proxy=proxy;return proxy
end}
local layout={GetViewportSize=function() return {X=2000,Y=1000} end}
local classes={['Class /Script/UMG.WidgetComponent']=component_class,
    ['Class /Script/UMG.UserWidget']=widget_class,['Class /Script/UMG.Image']=image_class}
for name,value in pairs({WidgetBlueprintLibrary=factory,WidgetLayoutLibrary=layout}) do
    local c=class(name);c.get_class_default_object=function() return value end
    classes['Class /Script/UMG.'..name]=c
end
local array={get_objects_offset=function() return 0 end,get_item_distance=function() return 24 end,
    get_object_count=function() return state.next end,get_object=function(_,i) return state.objects[i] end}
local vr={is_runtime_ready=function() return true end,is_hmd_active=function() return true end,
    get_mod_value=function() return state.active and 'false' or 'true' end,
    get_ue_projection_matrix=function(eye,m) assert(eye==-1);m.values={
        [0]={[0]=1,[1]=0,[2]=0,[3]=0},[1]={[0]=0,[1]=1,[2]=0,[3]=0},
        [2]={[0]=0,[1]=0,[2]=0,[3]=1},[3]={[0]=0,[1]=0,[2]=.01,[3]=0}} end}
UEVR_Matrix4x4f={new=function() return {get=function(self,c,r) return self.values[c][r] end} end}
local function log(s) table.insert(state.logs,s) end
uevr={api={get_uobject_array=function() return array end,find_uobject=function(_,p) return classes[p] end},
    params={vr=vr,functions={get_tag=function() return 'ffw-ue58-sdk-v1' end,log_info=log,log_warn=log,
        is_drawing_ui=function() return false end}}}
state.source,state.component,state.actor=source,component,actor
function frame(camera)
    if camera~=false then feature.camera(nil,0,100,{x=0,y=0,z=0},state.rotation,true) end
    feature.tick(nil,.016)
end
function healthy() for _,s in ipairs(state.logs) do assert(not s:find('Stopped safely',1,true),s) end end
function near(a,b) assert(math.abs(a-b)<.001,tostring(a)..' differs from '..tostring(b)) end
'''


def run(name, test, setup=""):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().script_path = str(ROOT / "scripts/?.lua")
    lua.execute("package.path=script_path..';'..package.path")
    lua.execute(MOCK)
    lua.execute(setup)
    lua.execute("feature=require('libs/world_marker_impl')()")
    lua.execute(test)
    print("PASS", name)


run("vendor projection and restoration", """
frame();frame();healthy();assert(state.created==1 and state.source.opacity==0)
near(state.proxy.pixel.X,1000);near(state.proxy.pixel.Y,500)
state.rotation={x=10,y=10,z=0};frame();assert(state.proxy.pixel.X<1000 and state.proxy.pixel.Y>500)
feature.reset();assert(state.proxy.removed and state.source.opacity==.7)
""")
run("live label and actor preserved; both axes independent of aim", """
frame();frame();healthy();assert(state.created==0 and state.moves>0)
assert(state.source.label=='Start Mission' and state.world.X==1000 and state.world.Y==0)
near(state.display.X,1000);near(state.display.Y,500)
state.source.label='Launch selected mission';state.aim=70;frame();healthy()
near(state.display.X,1000);near(state.display.Y,500);assert(state.source.label=='Launch selected mission')
state.rotation={x=10,y=10,z=0};frame();healthy();assert(state.display.X<1000 and state.display.Y>500)
local x,y=state.display.X,state.display.Y
for i=1,120 do frame() end;healthy();near(state.display.X,x);near(state.display.Y,y)
""", "state.family='UI_Guide_C'")
run("pause and reset restore original attachment and opacity", """
frame();frame();healthy();state.active=false;frame();assert(state.restored and not state.component.warp)
assert(state.source.opacity==.7 and state.created==0)
state.active=true;frame();frame();healthy();assert(state.component.warp)
feature.reset();assert(not state.component.warp and state.source.opacity==.7)
""", "state.family='UI_Guide_C'")
run("failed partial move restores attachment without changing actor", """
frame();assert(state.restored and not state.component.warp and state.source.opacity==.7)
assert(state.world.X==1000 and state.world.Y==0)
""", "state.family='UI_Guide_C';state.fail_move=true")
run("root component rejected before mutation", """
frame();assert(state.moves==0 and state.source.opacity==.7 and state.created==0)
""", "state.family='UI_Guide_C';state.is_root=true")
run("visibility, behind-camera, stale camera and failed deprojection", """
frame();frame();healthy();state.component.visible=false;frame();assert(state.source.opacity==0)
state.component.visible=true;state.actor.hidden=true;frame();assert(state.source.opacity==0)
state.actor.hidden=false;state.source.visibility=2;frame();assert(state.source.opacity==0)
state.source.visibility=0;frame();assert(state.source.opacity==.7)
state.world={X=-1000,Y=0,Z=0};frame();assert(state.source.opacity==0)
state.world={X=1000,Y=0,Z=0};frame();assert(state.source.opacity==.7)
for i=1,20 do frame(false) end;assert(state.source.opacity==0)
state.deproject_fails=true;frame();assert(state.source.opacity==0)
state.deproject_fails=false;frame();healthy();assert(state.source.opacity==.7)
""", "state.family='UI_Guide_C'")
run("stale component receives no restore write", """
frame();frame();local moves=state.moves
for i,o in pairs(state.objects) do if o==state.component then state.objects[i]=nil end end
frame();healthy();assert(state.moves==moves and not state.restored and state.source.opacity==.7)
""", "state.family='UI_Guide_C'")
