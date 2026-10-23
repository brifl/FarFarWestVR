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
    DeprojectScreenPositionToWorld=64,ProjectWorldLocationToScreen=48,
    GetOwningPlayerPawn=8,SetRenderTranslation=16,GetCachedGeometry=80,
    SetRenderScale=16,SetRenderTransformPivot=16,
    GetLocalSize=96,LocalToViewport=128,K2_GetComponentToWorld=96,TransformLocation=144}
local function class(name)
    return {get_short_name=function() return name end,find_property=function(_,n)
        local offsets={Space=1512,WidgetClass=1520,Pivot=1568,Widget=name=='component' and 1800 or name=='BP_PlayerNameWidget_C' and 680 or 688,Image_Icon=808,Image_Aura=824,
            UI_Key=816,OwningActor=912,Location=state.family=='UI_ObjectPing_C' and 864 or 872,
            InteractTextHolder=816,Image_Logo=824,Scene=696,AttachParent=208,ProgressBar_Boss=808,Overlay_Transform=840,
            PlayerNameText=840,PlayerState=872,WidgetTree=704}
        return {get_offset=function() return state.bad_layout and 1 or offsets[n] end}
    end,find_function=function(_,n) return {get_properties_size=function() return sizes[n] end,
        get_child_properties=function() return nil end} end}
end
local component_class,widget_class,image_class=class('component'),class('widget'),class('image')
local root=object({},'Billboard')
local scene=object({parent=root},'Scene')
function scene:get_class() return class('SceneComponent') end
function scene:get_property(n) assert(n=='AttachParent');return self.parent end
function root:get_class() return class('SceneComponent') end
function root:get_property(n) assert(n=='AttachParent');return nil end
function root:K2_GetComponentToWorld()
    return {location=state.parent_location or state.world,rotation=state.parent_rotation or 0,
        scale=state.parent_scale or {X=1,Y=1,Z=1}}
end
function scene:K2_GetComponentToWorld()
    return {location=state.parent_location or state.world,rotation=state.parent_rotation or 0,
        scale=state.parent_scale or {X=1,Y=1,Z=1}}
end
local actor=object({hidden=false},'owner')
function actor:get_property(n)
    if n=='RootComponent' then return state.marker_root and state.component or root end
    if n=='Scene' then return scene end
    if n=='Widget' then return state.wrong_component and root or state.component end
    assert(n=='bHidden');return self.hidden
end
function actor:get_class() return class(state.owner_class or 'actor') end
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
function player:ProjectWorldLocationToScreen(point,pixel,relative)
    assert(not relative)
    if state.project_fails then return false end
    local a=math.rad(state.aim);local c,s=math.cos(a),math.sin(a)
    local depth=point.X*c+point.Y*s
    if depth<=0 then return false end
    pixel.result={X=(1+(-point.X*s+point.Y*c)/depth)*1000,Y=(1-point.Z/depth)*500}
    state.native_pixel=pixel.result
    return true
end
local source=object({opacity=.7,visibility=0,icon={},label='Start Mission',translation={X=3,Y=4}},'source')
source.scale={X=1.5,Y=.5};source.pivot={X=.5,Y=.5}
function source:get_class() return class(state.family) end
function source:GetOwningPlayer() return player end
function source:GetOwningPlayerPawn() return actor end
function source:GetCachedGeometry() return self end
function source:SetRenderTranslation(p)
    self.translation={X=p.X,Y=p.Y}
    if state.fail_translation and (p.X~=3 or p.Y~=4) then error('partial translation failure') end
end
function source:get_float_property(n) assert(n=='RenderOpacity');return self.opacity end
function source:SetRenderOpacity(n) self.opacity=n end
function source:get_property(n)
    if n=='Visibility' then return self.visibility end
    if n=='RenderTransformPivot' then return self.pivot end
    if n=='RenderTransform' then return {Translation=self.translation,Scale=self.scale,
        Angle=0,Shear={X=0,Y=0}} end
    if n=='WidgetTree' then return state.content_tree end
    if n=='OwningActor' then return state.wrong_actor and root or actor end
    if n=='Location' then return state.objective_location or state.world end
    if n=='ProgressBar_Boss' or n=='Overlay_Transform' then return self.icon end
    assert(n==(state.family=='UI_Guide_C' and 'Image_Aura' or state.family=='UI_ObjectPing_C' and 'Image_Logo' or 'Image_Icon'));return self.icon
end
function source:SetRenderScale(v) assert(v.typed);self.scale={X=v.X,Y=v.Y} end
function source:SetRenderTransformPivot(v) assert(v.typed);self.pivot={X=v.X,Y=v.Y} end
function source:GetDesiredSize() return {X=64,Y=32,typed=true} end
function source.icon:get_property(n) return {name=n} end
local component=object({visible=true,relative={X=0,Y=0,Z=0}},'Widget')
local component_name=component.get_short_name
function component:get_short_name() return state.family=='UI_Lifebar_C' and 'LifebarWidget' or state.family=='UI_Interact_C' and 'WidgetInteract' or component_name(self) end
function component:get_class() return component_class end
function component:is_a(c) return c==component_class end
function component:get_outer() return {get_short_name=function()
    if state.owner_name then return state.owner_name end
    if state.family=='UI_Interact_C' then return 'BP_Player_Lobby_C_1' end
    return state.family=='UI_Guide_C' and 'BP_LobbyGuide_C_2' or 'BP_WorldIcon_C_1' end,
    get_class=function() return actor:get_class() end} end
function component:GetOwner() return actor end
function component:GetAttachParent() return state.is_root and component or state.nested_parent and scene or root end
function component:get_property(n)
    if n=='AttachSocketName' then return state.socket or 'None' end
    if n=='bAbsoluteLocation' then return state.absolute or false end
    if n=='Widget' then return not state.no_widget and source or nil
    elseif n=='WidgetClass' then return source:get_class()
    elseif n=='bVisible' then return self.visible
    elseif n=='RelativeLocation' then return self.relative end
    if n=='AttachParent' then return self:GetAttachParent() end
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
    local proxy=object({icon={},scale={X=1,Y=1},pivot={X=.5,Y=.5}},'proxy')
    function proxy:is_a(c) return c==widget_class end
    function proxy:get_property(n)
        if n=='RenderTransform' then return {Scale=self.scale} end
        if n=='RenderTransformPivot' then return self.pivot end
        assert(n=='Image_Icon');return self.icon
    end
    function proxy:GetDesiredSize() return {X=64,Y=32,typed=true} end
    function proxy:SetRenderScale(v) assert(v.typed);self.scale={X=v.X,Y=v.Y} end
    function proxy:SetRenderTransformPivot(v) assert(v.typed);self.pivot={X=v.X,Y=v.Y} end
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
local slate={GetLocalSize=function() return state.no_geometry and {X=0,Y=0} or {X=64,Y=32} end}
function slate:LocalToViewport(widget,cached,point,pixel,viewport)
    assert(widget==source and cached==source)
    -- Deliberately stale position; only the inherited basis may be used.
    pixel.result={X=123+point.X*2*source.scale.X,Y=456+point.Y*2*source.scale.Y}
end
local classes={['Class /Script/UMG.WidgetComponent']=component_class,
    ['Class /Script/UMG.UserWidget']=widget_class,['Class /Script/UMG.Image']=image_class}
local math_library={TransformLocation=function(_,t,p)
    local yaw=math.rad(t.rotation);local c,s=math.cos(yaw),math.sin(yaw)
    return {X=t.location.X+p.X*t.scale.X*c-p.Y*t.scale.Y*s,
        Y=t.location.Y+p.X*t.scale.X*s+p.Y*t.scale.Y*c,Z=t.location.Z+p.Z*t.scale.Z}
end}
local math_class=class('KismetMathLibrary')
math_class.get_class_default_object=function() return math_library end
classes['Class /Script/Engine.KismetMathLibrary']=math_class
for name,value in pairs({WidgetBlueprintLibrary=factory,WidgetLayoutLibrary=layout,SlateBlueprintLibrary=slate}) do
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
state.scene,state.root=scene,root
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
near(state.proxy.scale.Y,.5);near(state.proxy.pivot.Y,1)
state.rotation={x=10,y=10,z=0};frame();assert(state.proxy.pixel.X<1000 and state.proxy.pixel.Y>500)
feature.reset();assert(state.proxy.removed and state.source.opacity==.7)
near(state.proxy.scale.Y,1);near(state.proxy.pivot.Y,.5)
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

run("live prompt corrects both axes, keeps text and never moves the target", """
frame();frame();healthy();assert(state.created==0 and state.moves==0)
near(state.source.translation.X,3);near(state.source.translation.Y,4)
state.rotation={x=10,y=10,z=0};frame();healthy()
local function display()
    return state.native_pixel.X+2*(state.source.translation.X-3),
        state.native_pixel.Y+2*(state.source.translation.Y-4)
end
local x,y=display();assert(x<1000 and y>500)
state.source.label='Hold X to talk';state.aim=60
for i=1,120 do frame() end;healthy()
local moved_x,moved_y=display();near(moved_x,x);near(moved_y,y)
assert(state.source.label=='Hold X to talk' and state.world.X==1000 and state.world.Y==0)
assert(state.created==0 and state.moves==0)
feature.reset();near(state.source.translation.X,3);near(state.source.translation.Y,4)
assert(state.source.opacity==.7)
""", "state.family='UI_Interact_C'")

run("prompt shape normalization preserves target projection and restores its pivot", """
frame();frame();healthy();near(state.source.scale.Y,.5);near(state.source.pivot.Y,1)
state.rotation={x=10,y=10,z=0};frame();healthy()
local x=state.native_pixel.X+2*(state.source.translation.X-3)
local y=state.native_pixel.Y+2*(state.source.translation.Y-4)
state.aim=60;for i=1,120 do frame() end;healthy()
near(state.native_pixel.X+2*(state.source.translation.X-3),x)
near(state.native_pixel.Y+2*(state.source.translation.Y-4),y)
assert(state.moves==0 and state.source.label=='Start Mission')
feature.reset();near(state.source.scale.Y,1);near(state.source.pivot.Y,.5)
near(state.source.translation.X,3);near(state.source.translation.Y,4)
""", "state.family='UI_Interact_C';state.source.scale={X=1,Y=1}")

run("live world-label shape keeps the actor and corrected attachment fixed", """
frame();frame();healthy();near(state.source.scale.Y,.5);near(state.source.pivot.Y,1)
near(state.display.X,1000);near(state.display.Y,500)
state.aim=70;state.rotation={x=10,y=10,z=0};frame();healthy()
assert(state.display.X<1000 and state.display.Y>500 and state.source.label=='Start Mission')
feature.reset();near(state.source.scale.Y,1);near(state.source.pivot.Y,.5)
assert(state.restored and state.world.X==1000 and state.world.Y==0)
""", "state.family='UI_Guide_C';state.source.scale={X=1,Y=1}")

run("prompt follows updated world target and restores for menus", """
frame();frame();state.world={X=1000,Y=200,Z=100};frame();healthy()
near(state.native_pixel.X+2*(state.source.translation.X-3),1200)
near(state.native_pixel.Y+2*(state.source.translation.Y-4),450)
state.active=false;frame();near(state.source.translation.X,3);near(state.source.translation.Y,4)
assert(state.source.opacity==.7 and state.moves==0)
""", "state.family='UI_Interact_C'")

run("prompt respects visibility, missing geometry, projection failure and stale camera", """
frame();frame();state.component.visible=false;frame();assert(state.source.opacity==0)
state.component.visible=true;state.no_geometry=true;frame();assert(state.source.opacity==0)
state.no_geometry=false;state.project_fails=true;frame();assert(state.source.opacity==0)
state.project_fails=false;frame();assert(state.source.opacity==.7)
for i=1,20 do frame(false) end;assert(state.source.opacity==0)
frame();healthy();assert(state.source.opacity==.7)
""", "state.family='UI_Interact_C'")

run("partial prompt write is restored and isolated from other marker adapters", """
state.rotation={x=10,y=10,z=0};frame()
near(state.source.translation.X,3);near(state.source.translation.Y,4)
assert(state.source.opacity==.7 and state.moves==0 and state.created==0)
local stopped=false
for _,message in ipairs(state.logs) do
    assert(not message:find('Stopped safely during',1,true))
    stopped=stopped or message:find('Interaction prompt stopped safely',1,true)~=nil
end
assert(stopped)
""", "state.family='UI_Interact_C';state.fail_translation=true")

TEAMMATE_SETUP = """
state.family='UI_PlayerInfos_C';state.owner_class='BP_PlayerNameWidget_C';state.marker_root=true
state.source.label='Partner';state.source.health=.6;state.source.level=12
function state.source:GetOwningPlayerPawn() error('Teammate marker must not require the local pawn') end
local content=state.source
-- A separate native content widget lives inside the animated nameplate root.
local child={scale={X=1,Y=1},pivot={X=.5,Y=.5}}
local index=state.next;state.next=index+1;state.objects[index]=child
function child:get_address() return index*256 end
function child:read_dword() return index end
function child:get_short_name() return 'VerticalBox_0' end
function child:get_class() return {get_short_name=function() return 'VerticalBox' end} end
function child:get_property(n)
 if n=='RenderTransformPivot' then return self.pivot end
 assert(n=='RenderTransform');return {Scale=self.scale}
end
function child:GetDesiredSize() return {X=107.5,Y=22.5,typed=true} end
function child:SetRenderScale(v) assert(v.typed);self.scale={X=v.X,Y=v.Y} end
function child:SetRenderTransformPivot(v) assert(v.typed);self.pivot={X=v.X,Y=v.Y} end
state.content=child
state.content_tree={get_property=function(_,n) assert(n=='RootWidget');if not state.no_content then return state.content end end}
"""
run('teammate root marker corrects both axes without moving its actor or copying live content', '''
frame();frame();healthy();assert(state.created==0 and state.moves==0)
state.rotation={x=10,y=10,z=0};frame();healthy()
local x=state.native_pixel.X+2*(state.source.translation.X-3)
local y=state.native_pixel.Y+2*(state.source.translation.Y-4)
assert(x<1000 and y>500)
state.aim=70;state.source.label='New title';state.source.health=.4;state.source.level=13
for i=1,120 do frame() end;healthy()
near(state.native_pixel.X+2*(state.source.translation.X-3),x)
near(state.native_pixel.Y+2*(state.source.translation.Y-4),y)
assert(state.source.label=='New title' and state.source.health==.4 and state.source.level==13)
assert(state.created==0 and state.moves==0 and state.world.X==1000)
''', TEAMMATE_SETUP)
run('teammate motion, native visibility and menu return retain attachment and restore translation', '''
frame();frame();state.world={X=1000,Y=200,Z=100};frame();healthy()
near(state.native_pixel.X+2*(state.source.translation.X-3),1200)
near(state.native_pixel.Y+2*(state.source.translation.Y-4),450)
state.source.visibility=2;frame();assert(state.source.opacity==0)
state.source.visibility=0;frame();assert(state.source.opacity==.7)
state.active=false;frame();near(state.source.translation.X,3);near(state.source.translation.Y,4)
assert(state.source.opacity==.7 and state.moves==0)
''', TEAMMATE_SETUP)
run('teammate root reassignment restores only its live widget', '''
frame();frame();state.rotation={x=10,y=10,z=0};frame();healthy()
state.marker_root=false;frame();healthy()
near(state.source.translation.X,3);near(state.source.translation.Y,4)
assert(state.moves==0 and state.source.opacity==.7)
''', TEAMMATE_SETUP)
run('teammate mismatched component binding is rejected before visual writes', '''
frame();frame();healthy();assert(state.moves==0 and state.created==0)
near(state.source.translation.X,3);near(state.source.translation.Y,4)
assert(state.source.opacity==.7)
''', TEAMMATE_SETUP+';state.wrong_component=true')
run('animated teammate scale keeps its native value while inner content gets the aspect correction', '''
state.source.scale={X=1.028,Y=1.028};frame();frame();healthy()
near(state.source.scale.Y,1.028);near(state.source.pivot.Y,.5)
near(state.content.scale.Y,.5);near(state.content.pivot.Y,1)
state.source.scale={X=.7,Y=.7};frame();healthy()
near(state.source.scale.Y,.7);near(state.content.scale.Y,.5)
feature.reset();near(state.content.scale.Y,1);near(state.content.pivot.Y,.5)
near(state.source.scale.Y,.7)
''', TEAMMATE_SETUP)
run('late teammate content waits without stopping stabilization; stale content gets no restore write', '''
state.no_content=true;frame();healthy();assert(state.source.opacity==.7)
state.no_content=false;frame();healthy();near(state.content.scale.Y,.5)
for i,o in pairs(state.objects) do if o==state.content then state.objects[i]=nil end end
state.content.SetRenderScale=function() error('Destroyed content written') end
feature.reset();healthy()
''', TEAMMATE_SETUP)

OBJECTIVE_SETUP = """
state.family='UI_PingObjective_C'
state.owner_class='BP_ObjectivePing_Main_C'
state.owner_name='BP_ObjectivePing_Tnt_C_0'
state.source.label='Deliver TNT';state.source.distance='125 m'
"""

run("objective retains title/distance and stays anchored even aiming backward", """
frame();frame();healthy();assert(state.created==0 and state.moves>0)
near(state.display.X,1000);near(state.display.Y,500)
state.rotation={x=10,y=10,z=0};frame();healthy()
local x,y=state.display.X,state.display.Y;assert(x<1000 and y>500)
state.aim=170;state.source.label='Carry TNT';state.source.distance='124 m'
for i=1,120 do frame() end;healthy();near(state.display.X,x);near(state.display.Y,y)
assert(state.source.label=='Carry TNT' and state.source.distance=='124 m')
assert(state.world.X==1000 and state.world.Y==0 and state.created==0)
near(state.source.translation.X,3);near(state.source.translation.Y,4)
feature.reset();assert(state.restored and state.source.opacity==.7)
""", OBJECTIVE_SETUP)

run("objective uses its live target field and restores only its visual child", """
frame();frame();state.objective_location={X=1000,Y=200,Z=100};frame();healthy()
near(state.display.X,1200);near(state.display.Y,450)
assert(state.world.Y==0 and state.world.Z==0 and state.objective_location.Y==200)
state.active=false;frame();assert(state.restored and not state.component.warp and state.source.opacity==.7)
assert(state.objective_location.Y==200 and state.world.Y==0)
""", OBJECTIVE_SETUP)

run("objective rejects mismatched actor without stopping other adapters", """
frame();frame();healthy();assert(state.moves==0 and state.created==0 and state.source.opacity==.7)
assert(not state.component.warp)
""", OBJECTIVE_SETUP + ";state.wrong_actor=true")

run("mission text guide resolves actual actor class behind a generated instance name", """
frame();frame();healthy();assert(state.moves>0 and state.created==0)
state.aim=170;state.rotation={x=10,y=10,z=0};frame();healthy()
assert(state.display.X<1000 and state.display.Y>500 and state.source.label=='Refuel the pump')
feature.reset();assert(state.restored and state.source.opacity==.7)
""", "state.family='UI_Guide_C';state.owner_class='BP_TextGuide_FuelObjective_A_C';state.owner_name='ChildActor_GEN_VARIABLE_BP_TextGuide_C_CAT_822';state.source.label='Refuel the pump'")

PING = "state.family='UI_ObjectPing_C';state.owner_class='BP_ObjectPing_Default_C';state.nested_parent=true;state.component.relative={X=0,Y=0,Z=64}"

run("object ping preserves live icon/distance and height across aim and head motion", """
frame();frame();healthy();assert(state.created==0 and state.moves>0)
near(state.display.X,1000);near(state.display.Y,468)
state.source.label='Ping 12m';state.aim=175;frame();healthy()
near(state.display.X,1000);near(state.display.Y,468)
state.rotation={x=10,y=10,z=0};frame();healthy()
assert(state.display.X<1000 and state.display.Y>468 and state.source.label=='Ping 12m')
local x,y=state.display.X,state.display.Y
for i=1,120 do frame() end;healthy();near(state.display.X,x);near(state.display.Y,y)
assert(state.world.X==1000 and state.world.Y==0 and state.scene.parent==state.root)
feature.reset();assert(state.restored and state.source.opacity==.7 and state.component.relative.Z==64)
""", PING)

run("object ping follows moving tagged targets independently of stale distance data", """
frame();frame();state.parent_location={X=1000,Y=200,Z=100}
state.objective_location={X=950,Y=190,Z=99};frame();healthy()
near(state.display.X,1200);near(state.display.Y,418)
state.aim=-80;frame();healthy();near(state.display.X,1200);near(state.display.Y,418)
assert(state.objective_location.Y==190 and state.world.Y==0)
state.component.visible=false;frame();assert(state.source.opacity==0)
state.component.visible=true;frame();assert(state.source.opacity==.7)
feature.reset();assert(state.restored and state.objective_location.Y==190)
""", PING)

run("chicken and other object tags preserve rotated/scaled native attachment offsets", """
frame();frame();healthy()
near(state.display.X,1000+40000/970);near(state.display.Y,500-16000/970)
state.parent_location={X=1200,Y=100,Z=50};state.aim=170;frame();healthy()
near(state.display.X,1000+140000/1170);near(state.display.Y,500-41000/1170)
assert(state.created==0 and state.world.X==1000)
feature.reset();near(state.component.relative.X,20);near(state.component.relative.Y,10);near(state.component.relative.Z,64)
""", PING+";state.owner_class='BP_ObjectPing_Animal_Chicken_C';state.component.relative={X=20,Y=10,Z=64};state.parent_rotation=90;state.parent_scale={X=2,Y=3,Z=.5}")

run("object ping rejects a mismatched actor/component binding before writing", """
frame();healthy();assert(state.moves==0 and state.source.opacity==.7 and state.created==0)
""", PING+";state.wrong_component=true")

run("object ping stops moving when its verified scene attachment changes", """
frame();frame();healthy();local moves=state.moves
state.scene.parent=nil;frame();healthy()
assert(state.moves==moves and state.source.opacity==.7 and state.world.Y==0)
frame();healthy();assert(state.moves==moves)
""", PING)

run("hidden known marker is ready on its first visible frame", """
frame();healthy();assert(state.moves==0 and state.source.opacity==0)
state.component.visible=true;frame();healthy();assert(state.moves>0 and state.source.opacity==.7)
""", "state.family='UI_Guide_C';state.component.visible=false")

run("late widget instance binds without another full object-array pass", """
frame();healthy();assert(state.moves==0)
state.no_widget=false;frame();healthy();assert(state.moves>0)
""", "state.family='UI_Guide_C';state.no_widget=true")

run("newly allocated objects bypass the background scan cooldown", """
frame();frame();healthy()
state.objects[state.next]={get_short_name=function() state.saw_new=true;return 'unrelated' end}
state.next=state.next+1
frame();healthy();assert(state.saw_new)
""")

run("initial discovery yields at its time budget instead of blocking on the array", """
frame();healthy();assert(state.reads>=32 and state.reads<=96 and state.moves==0)
""", """
state.next=5000;state.reads=0;state.mock_clock=0
local array=uevr.api:get_uobject_array();local get=array.get_object
array.get_object=function(self,i) state.reads=state.reads+1;return get(self,i) end
os.clock=function() state.mock_clock=state.mock_clock+.001;return state.mock_clock end
""")


for owner in ['BP_Enemy_Cryptic_Nuker_C', 'BP_RadioactiveBarrel_C', 'BP_GasBomb_BossSpawner_C',
              'BP_CrypticTrain_Section_Cart_C', 'BP_CrypticTrain_Section_Loco_C', 'BP_Enemy_Cryptic_Saloon_Spirit_C']:
    run('health-bar family follows target with native height: '+owner, r'''
frame();frame();healthy();assert(state.moves>0 and state.created==0)
near(state.display.X,1000);near(state.display.Y,436)
state.parent_location={X=1200,Y=200,Z=50};state.aim=170;frame();healthy()
near(state.display.X,1000+200000/1200);near(state.display.Y,500-89000/1200)
state.component.visible=false;frame();healthy();assert(state.restored and state.source.opacity==.7)
feature.reset();near(state.component.relative.Z,128)
''', "state.family='UI_Lifebar_C';state.owner_class="+repr(owner)+";state.component.relative={X=0,Y=0,Z=128}")

run('health bar validates the attachment chain and keeps nested native offsets', r'''
frame();frame();healthy();near(state.display.Y,436)
state.scene.parent=nil;local moves=state.moves;frame();healthy();assert(state.moves==moves)
''', "state.family='UI_Lifebar_C';state.owner_class='BP_Enemy_Ordinary_C';state.nested_parent=true;state.component.relative={X=0,Y=0,Z=128}")

run('dropped Joker card preserves live text and follows its scene attachment', r'''
frame();frame();healthy();assert(state.moves>0 and state.created==0)
near(state.display.Y,504)
state.source.label='Rare Joker';state.parent_location={X=1000,Y=200,Z=0};state.aim=160
frame();healthy();near(state.display.X,1200);assert(state.source.label=='Rare Joker')
feature.reset();near(state.component.relative.Z,-8)
''', "state.family='UI_JokerCard_InGame_C';state.owner_class='BP_Pickable_Joker_C';state.nested_parent=true;state.component.relative={X=0,Y=0,Z=-8}")

run('socket-mounted or absolute-location bars are left native', r'''
frame();frame();healthy();assert(state.moves==0 and state.source.opacity==.7)
''', "state.family='UI_Lifebar_C';state.owner_class='BP_Enemy_Ordinary_C';state.socket='Head'")

run('native counts above the old probe limit do not disable marker helpers', '''
state.next=286344
frame();healthy()
''')
