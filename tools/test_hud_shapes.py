"""Shared immersive HUD proportions and ownership checks (lupa)."""
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
MOCK = r'''
state={objects={},next=1,roots={},logs={},aspect=1,active=true}
farfarwest_gameplay_ready=true
local offsets={RenderTransform=144,RenderTransformPivot=200,Image_Compass=1008,
 Overlay_Pings=944,TextBlock_Text=832,ProgressBar_Boss=840,Text_Title=816,TextBlock_Seconds=816}
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
