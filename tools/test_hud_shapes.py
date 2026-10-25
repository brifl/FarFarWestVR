"""Shared immersive HUD proportions and ownership checks (lupa)."""
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
MOCK = r'''
state={objects={},next=1,roots={},logs={},aspect=1,active=true}
farfarwest_gameplay_ready=true
local offsets={RenderTransform=144,RenderTransformPivot=200,Image_Compass=1008,
 Overlay_Pings=944,TextBlock_Text=832,ProgressBar_Boss=840,Text_Title=816,TextBlock_Seconds=816,Appear=816,
 VerticalBox_Holder=808,Border_0=824,Border_Color=832,TextDeath=824,ProgressBar=824}
function make(name,sx,sy)
 local o={name=name,index=state.next,scale={X=sx or 1,Y=sy or 1},pivot={X=.5,Y=.5},translation={X=3,Y=4},props={}}
 state.next=state.next+1;state.objects[o.index]=o
 function o:get_address() return self.index*256 end
 function o:get_short_name() assert(not self.dead);return self.name end
 function o:get_class() return {find_property=function(_,n)
  return {get_offset=function() return (state.bad or state.bad_field==n) and 0 or offsets[n] end}
 end} end
 function o:get_property(n)
  assert(not self.dead)
  if n=='RenderTransform' then return {Scale=self.scale,Translation=self.translation,Angle=0,Shear={X=0,Y=0}} end
  if n=='RenderTransformPivot' then return self.pivot end
  return self.props[n]
 end
 function o:GetParent() assert(not self.dead);return self.parent end
 function o:GetDesiredSize() return {typed=true,X=100,Y=40} end
 function o:SetRenderScale(v) assert(not self.dead and v.typed);self.scale={X=v.X,Y=v.Y} end
 function o:SetRenderTransformPivot(v) assert(not self.dead and v.typed);self.pivot={X=v.X,Y=v.Y} end
 return o
end
local function ref(o) return {object=o,index=o.index,address=o:get_address(),name=o.name} end
local function valid(r) return r and state.objects[r.index]==r.object end
package.loaded['libs/live_widgets']=function(path,limit,interval,top)
 assert(top==true,'HUD shapes must query viewport roots, not retained widget instances')
 return {get=function() local out={};for _,o in ipairs(state.roots[path] or {}) do out[#out+1]=ref(o) end;return out end,
 valid=valid,track=ref,reset=function() end}
end
package.loaded['libs/tuning']={get=function(n)
 if n=='hud.boss_health_scale_multiplier' then return state.boss_scale or .85 end
 if n=='hud.scale_multiplier' then return state.hud_scale or .85 end
 assert(n=='hud.aspect_correction');return state.aspect
end}
state.player=make('UI_Player_C');state.image=make('Image_Compass',.8,.8);state.pings=make('Overlay_Pings')
state.player.props.Image_Compass=state.image;state.player.props.Overlay_Pings=state.pings
state.roots['WidgetBlueprintGeneratedClass /Game/Interfaces/UI_Player.UI_Player_C']={state.player}
state.panels={}
for _,path in ipairs({'/Game/Interfaces/UI_NpcTalk.UI_NpcTalk_C','/Game/Interfaces/Boss/UI_Lifebar_Boss.UI_Lifebar_Boss_C',
 '/Game/Interfaces/UI_Counter.UI_Counter_C','/Game/Interfaces/UI_Timer.UI_Timer_C'}) do
 local o=make(path,1.2,1.2);state.panels[#state.panels+1]=o
 state.roots['WidgetBlueprintGeneratedClass '..path]={o}
end
state.panels[2].scale={X=1,Y=1}
state.warning=make('UI_LowAmmo_C')
state.roots['WidgetBlueprintGeneratedClass /Game/Interfaces/UI_LowAmmo.UI_LowAmmo_C']={state.warning}
state.drop=make('UI_DropItem_C');state.drop_holder=make('VerticalBox_Holder')
state.drop.props.VerticalBox_Holder=state.drop_holder
state.roots['WidgetBlueprintGeneratedClass /Game/Interfaces/UI_DropItem.UI_DropItem_C']={state.drop}
UEVR_Matrix4x4f={new=function() return {get=function(_,c) return c==0 and 1 or 1.15 end} end}
local function log(s) state.logs[#state.logs+1]=s end
local methods={GetDesiredSize=16,SetRenderScale=16,SetRenderTransformPivot=16,GetParent=8,GetViewportSize=24}
uevr={api={find_uobject=function(_,path) return {
 get_class_default_object=function() return {GetViewportSize=function() return {X=2560,Y=1440} end} end,
 find_function=function(_,n) return {get_properties_size=function() return methods[n] end} end,
 find_property=function(_,n) return {get_offset=function() return state.bad and 0 or offsets[n] end} end}
end},params={vr={is_runtime_ready=function() return true end,is_hmd_active=function() return state.active end,
 get_mod_value=function() return state.menu and 'true' or 'false' end,get_ue_projection_matrix=function() end},
 functions={is_drawing_ui=function() return state.panel end,log_info=log,log_warn=log}}}
feature=require('libs/hud_shapes')()
function frame() feature.camera();feature.tick({},.016) end
function near(a,b) assert(math.abs(a-b)<.00001,tostring(a)..' differs from '..tostring(b)) end
function healthy() for _,s in ipairs(state.logs) do assert(not s:find('Stopped safely',1,true),s) end end
function overlay(name,field,parents)
 local root=make(name);local leaf=make(field);local group=leaf
 root.props[field]=leaf
 for _,parent in ipairs(parents or {}) do local next_group=make(parent);group.parent=next_group;group=next_group end
 state.roots['WidgetBlueprintGeneratedClass /Game/Interfaces/'..name:gsub('_C$','')..'.'..name]={root}
 return root,group,leaf
end
'''


def run(name, code):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().script_path = str(ROOT / 'scripts/?.lua')
    lua.execute("package.path=script_path..';'..package.path")
    lua.execute(MOCK)
    lua.execute(code)
    print('PASS', name)


run('compass background and ping glyphs share aspect correction without changing offsets', '''
frame();healthy();near(state.image.scale.X,.8);near(state.image.scale.Y,.8*.646875)
near(state.pings.scale.Y,.646875);near(state.player.scale.Y,1)
assert(state.image.translation.Y==4 and state.pings.translation.Y==4)
''')
run('dialogue, boss, counters and timers share shape correction; nested HUD groups are excluded', '''
state.panels[4].parent=state.player;frame();healthy()
near(state.panels[1].scale.Y,1.2*.646875);near(state.panels[2].scale.Y,.85*.646875)
near(state.panels[3].scale.Y,1.2*.646875)
near(state.panels[4].scale.Y,1.2)
''')
run('game-driven scale baselines remain animated and never compound', '''
frame();state.image.scale={X=1.05,Y=1.05};frame();healthy()
for i=1,100 do frame() end
near(state.image.scale.X,1.05);near(state.image.scale.Y,1.05*.646875)
feature.reset();near(state.image.scale.Y,1.05)
''')
run('aspect toggle, menus, UEVR panel and inactive headset restore native proportions', '''
frame();state.aspect=0;frame();near(state.image.scale.Y,.8)
state.aspect=1;frame();state.menu=true;frame();near(state.image.scale.Y,.8)
state.menu=false;frame();state.panel=true;frame();near(state.image.scale.Y,.8)
state.panel=false;frame();state.active=false;frame();near(state.image.scale.Y,.8);healthy()
''')
run('rebuilt compass children restore detached widgets and avoid stale native access', '''
frame();local old=state.image
state.image=make('Image_Compass_New',.7,.7);state.player.props.Image_Compass=state.image
frame();healthy();near(old.scale.Y,.8);near(state.image.scale.Y,.7*.646875)
state.objects[state.image.index]=nil;state.image.dead=true;feature.reset();healthy()
''')
run('unknown layout stops before any scale write', '''
state.bad=true;frame();near(state.image.scale.Y,.8);near(state.pings.scale.Y,1)
state.bad=false;frame();near(state.image.scale.Y,.8)
''')
run('one unsupported panel does not disable compass or other verified HUD families', '''
state.bad_field='ProgressBar_Boss';frame();healthy()
near(state.panels[2].scale.Y,1);near(state.panels[1].scale.Y,1.2*.646875)
near(state.pings.scale.Y,.646875)
''')
run('boss canvas scales about top center without adding a screen-center displacement', '''
local boss=state.panels[2]
frame();healthy();near(boss.pivot.X,.5);near(boss.pivot.Y,0)
near(boss.scale.X,.85);near(boss.scale.Y,.85*.646875)
local height=1440;local bar_y=.13*height
-- The existing offset helper adds 15% once. Scaling must add no pivot displacement.
local function displayed() return (bar_y-boss.pivot.Y*height)*boss.scale.Y+boss.pivot.Y*height+.15*height end
near(displayed(),(.13*.85*.646875+.15)*height)
assert(displayed()<height*.25)
for i=1,100 do frame() end;healthy();assert(displayed()<height*.25)
state.boss_scale=.7;frame();near(boss.scale.X,.7);near(boss.scale.Y,.7*.646875)
state.aspect=0;frame();near(boss.scale.Y,.7)
state.boss_scale=1;frame();near(boss.scale.Y,1);near(boss.pivot.Y,.5)
feature.reset();near(boss.scale.X,1);near(boss.pivot.Y,.5)
''')
run('removed viewport panels release owned shapes without waiting for a world change', '''
frame();local boss=state.panels[2]
state.roots['WidgetBlueprintGeneratedClass /Game/Interfaces/Boss/UI_Lifebar_Boss.UI_Lifebar_Boss_C']={}
frame();healthy();near(boss.scale.X,1);near(boss.pivot.Y,.5)
''')

run('low-ammo warning follows HUD size, restores on dismissal and rebinds its next instance', '''
local path='WidgetBlueprintGeneratedClass /Game/Interfaces/UI_LowAmmo.UI_LowAmmo_C'
local warning=state.warning
frame();healthy();near(warning.scale.X,.85);near(warning.scale.Y,.85*.646875)
state.hud_scale=.7;frame();near(warning.scale.X,.7);near(warning.scale.Y,.7*.646875)
state.aspect=0;frame();near(warning.scale.Y,.7)
state.roots[path]={};frame();near(warning.scale.X,1);near(warning.scale.Y,1)
state.objects[warning.index]=nil;warning.dead=true
local next_warning=make('UI_LowAmmo_C_2');state.roots[path]={next_warning}
state.aspect=1;frame();healthy();near(next_warning.scale.Y,.7*.646875)
state.menu=true;frame();near(next_warning.scale.X,1);near(next_warning.scale.Y,1)
''')

run('carried-item rows inherit one correction and a rebuilt holder restores the detached group', '''
local rows={make('Drop'),make('Shoot'),make('Aim')}
for _,row in ipairs(rows) do row.parent=state.drop_holder end
local holder=state.drop_holder
frame();healthy();near(holder.scale.X,1);near(holder.scale.Y,.646875)
near(state.drop.scale.Y,1)
for _,row in ipairs(rows) do near(row.scale.Y,1) end
local replacement=make('VerticalBox_Holder_2');state.drop.props.VerticalBox_Holder=replacement
frame();healthy();near(holder.scale.Y,1);near(replacement.scale.Y,.646875)
state.aspect=0;frame();near(replacement.scale.Y,1)
state.aspect=1;frame();state.menu=true;frame();near(replacement.scale.Y,1)
''')

run('captured notices correct the shared content once without moving the fullscreen root or text', '''
local notices={
 {overlay('UI_ShortMessage_C','Border_0')},
 {overlay('UI_DisturbanceIncrease_C','Border_Color')},
 {overlay('UI_DeadAlly_C','TextDeath',{'VerticalBox_0'})},
 {overlay('UI_CrypticSnake_C','ProgressBar',{'SizeBox_0','Border_0','VerticalBox_0'})},
}
frame();healthy()
for _,n in ipairs(notices) do
 local root,group,leaf=n[1],n[2],n[3]
 near(root.scale.Y,1);near(group.scale.Y,.646875);near(group.translation.Y,4)
 if leaf~=group then near(leaf.scale.Y,1) end
end
for i=1,100 do frame() end;healthy()
for _,n in ipairs(notices) do near(n[2].scale.Y,.646875) end
state.aspect=0;frame();for _,n in ipairs(notices) do near(n[2].scale.Y,1) end
state.aspect=1;frame();feature.reset();for _,n in ipairs(notices) do near(n[2].scale.Y,1) end
''')

run('rebuilt notice parent groups restore their old binding and respect a changed hierarchy', '''
local root,group,leaf=overlay('UI_DeadAlly_C','TextDeath',{'VerticalBox_0'})
frame();healthy();near(group.scale.Y,.646875)
local replacement=make('VerticalBox_0');leaf.parent=replacement
frame();healthy();near(group.scale.Y,1);near(replacement.scale.Y,.646875)
leaf.parent=make('UnknownUpdatedLayout');frame();healthy();near(replacement.scale.Y,1)
near(leaf.parent.scale.Y,1);near(state.image.scale.Y,.8*.646875)
''')

run('new notice families stay native if nested in another HUD and release on dismissal', '''
local root,group=overlay('UI_CrypticSnake_C','ProgressBar',{'SizeBox_0','Border_0','VerticalBox_0'})
root.parent=state.player;frame();healthy();near(group.scale.Y,1)
root.parent=nil;frame();healthy();near(group.scale.Y,.646875)
root.parent=state.player;frame();healthy();near(group.scale.Y,1)
root.parent=nil;frame();near(group.scale.Y,.646875)
state.roots['WidgetBlueprintGeneratedClass /Game/Interfaces/UI_CrypticSnake.UI_CrypticSnake_C']={}
frame();healthy();near(group.scale.Y,1)
''')
