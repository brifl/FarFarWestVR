"""Tuning reload, grading ownership, fog scaling and HUD offset checks (requires lupa)."""
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
MOCK = r'''
state={source=ini,logs={},hmd=true}
io.open=function(name,mode)
    assert(name=='tuning.ini' and mode=='rb')
    if not state.source then return nil end
    return {read=function(_,n) return state.source:sub(1,n) end,close=function() end}
end
function near(a,b) assert(math.abs(a-b)<.000001,tostring(a)..' differs from '..tostring(b)) end
function reload(source)
    state.source=source
    for i=1,11 do tuning.tick(nil,.1) end
end
local function log(message) state.logs[#state.logs+1]=message end
local post_class={find_property=function(_,name)
    if name==(state.lowercase_settings and 'settings' or 'Settings') then return {} end
end}
local fog_class={find_property=function() return {get_offset=function() return 592 end} end}
function fog_class:find_function(name)
    assert(name=='SetFogDensity')
    local parameter={get_fname=function() return {to_string=function() return 'Value' end} end,
        get_next=function() return nil end}
    return {get_properties_size=function() return 4 end,get_child_properties=function() return parameter end,
        find_property=function() return {get_offset=function() return 0 end} end}
end
local owner={get_short_name=function() return 'BP_BlendableAtmosphere_Afternoon_Heat_C_1' end,
    get_class=function() return {get_short_name=function() return 'BP_BlendableAtmosphere_Afternoon_Heat_C' end} end}
local settings={ColorContrast={X=1.2,Y=1.2,Z=1.2,W=1},bOverride_ColorContrast=true,
    ColorSaturation={X=1.4,Y=.8,Z=1.2,W=1.3},bOverride_ColorSaturation=false}
local post={get_address=function() return 4096 end,get_short_name=function() return 'postprocess' end,
    is_a=function(_,c) return c==post_class end,get_outer=function() return owner end}
function post:get_property(name)
    if name==(state.lowercase_settings and 'settings' or 'Settings') then return settings elseif name=='BlendWeight' then return 1 end
    assert(name=='bEnabled' or name=='bUnbound');return true
end
local fog={density=.02,get_address=function() return 8192 end,
    get_short_name=function() return 'ExponentialHeightFog' end,
    is_a=function(_,c) return c==fog_class end,get_outer=function() return owner end}
function fog:get_property(name) assert(name=='FogDensity');return self.density end
function fog:SetFogDensity(n) self.density=n end
local sizes={SetRenderTranslation=16,GetCachedGeometry=80,GetLocalSize=96,
    LocalToViewport=128,GetViewportSize=24,GetChildrenCount=4,GetChildAt=16,F_RefreshKey=1}
local function widget_class(name)
    return {get_short_name=function() return name end,get_address=function() return name end,
        find_property=function(_,field) return {get_offset=function()
            local offsets={RenderTransform=144,TextBlock_Text=832,Text_Title=816,
                TextBlock_Seconds=816,ProgressBar_Boss=840,Image_Compass=1008,Overlay_Pings=944,
                HorizontalBox_NextKey=856,Key=856,gamepadKeys=864,Text_Hold=840,Image_GamepadIcon=848,Text_Key=832}
            return offsets[field] end} end,
        find_function=function(_,fn) return {get_properties_size=function() return sizes[fn] end,
            get_child_properties=function() return nil end,
            find_property=function(_,name) assert(name=='isGamepad');return {get_offset=function() return 0 end} end} end}
end
local widget_base=widget_class('Widget')
function make_hud(index,kind,name)
    local o={translation={X=7,Y=11},kind=kind,name=name or kind..'_1',index=index,children={}}
    function o:get_address() return self.index*4096 end
    function o:read_dword(offset) assert(offset==12);return self.index end
    function o:get_short_name() return self.name end
    function o:get_class() return widget_class(self.kind) end
    function o:is_a(c) return c==widget_base end
    function o:get_property(n)
        assert(not self.dead,'Accessed a collected widget')
        if n=='Visibility' then return self.visibility or 0 end
        if n=='HorizontalBox_NextKey' or n=='gamepadKeys' or n=='Text_Hold' then return self.children[n] end
        if self.children[n] then return self.children[n] end
        assert(n=='RenderTransform')
        return {Translation=self.translation,Scale={X=1,Y=1},Shear={X=0,Y=0},Angle=0}
    end
    function o:GetCachedGeometry() return self end
    function o:SetRenderTranslation(p) self.translation={X=p.X,Y=p.Y} end
    return o
end
local hud=make_hud(3,'UI_NpcTalk_C')
local slate={GetLocalSize=function() return {X=1280,Y=720} end}
function slate:LocalToViewport(_,_,p,pixel) pixel.result={X=123+2*p.X,Y=456+2*p.Y} end
local layout={GetViewportSize=function() return {X=2560,Y=1440} end}
local classes={['Class /Script/Engine.PostProcessComponent']=post_class,
    ['Class /Script/Engine.ExponentialHeightFogComponent']=fog_class,
    ['Class /Script/UMG.Widget']=widget_base}
for name,object in pairs({SlateBlueprintLibrary=slate,WidgetLayoutLibrary=layout}) do
    local c=widget_class(name);c.get_class_default_object=function() return object end
    classes['Class /Script/UMG.'..name]=c
end
local objects={[1]=post,[2]=fog,[3]=hud}
local array={get_objects_offset=function() return 0 end,get_item_distance=function() return 24 end,
    get_object_count=function() return state.object_count or 4 end,get_object=function(_,i) return objects[i] end}
uevr={api={get_uobject_array=function() return array end,find_uobject=function(_,name) return classes[name] end},
    params={vr={is_runtime_ready=function() return true end,is_hmd_active=function() return state.hmd end},
        functions={log_info=log,log_warn=log}}}
state.settings,state.fog,state.hud=settings,fog,hud
state.objects=objects
function install_dialogue_hint()
    local panel_class=classes['Class /Script/UMG.PanelWidget'] or widget_class('PanelWidget')
    classes['Class /Script/UMG.PanelWidget']=panel_class
    local panel=make_hud(4,'HorizontalBox','HorizontalBox_NextKey')
    function panel:is_a(c) return c==panel_class end
    local key=make_hud(5,'UI_Key_C','UI_Key')
    local image=make_hud(6,'Image','Image_GamepadIcon');image.visibility=1
    local text=make_hud(7,'TextBlock','Text_Key')
    local action=make_hud(8,'InputAction','IA_Interact')
    for _,o in ipairs({panel,key,image,text,action}) do objects[o.index]=o end
    state.object_count=9;state.refreshes=0
    key.children={Key=action,Image_GamepadIcon=image,Text_Key=text}
    function key:F_RefreshKey(gamepad)
        assert(not self.dead and gamepad==true)
        state.refreshes=state.refreshes+1
        self.children.Image_GamepadIcon.visibility=0;self.children.Text_Key.visibility=1
    end
    function panel:GetChildrenCount() return 1 end
    function panel:GetChildAt(i) assert(i==0);return key end
    hud.children.HorizontalBox_NextKey=panel
    state.hint_key,state.hint_image,state.hint_text=key,image,text
end
function healthy()
    for _,message in ipairs(state.logs) do assert(not message:lower():find('stopped safely',1,true),message) end
end
'''


def run(name, code):
    lua = LuaRuntime(unpack_returned_tuples=True)
    # User-editable tuning.ini must not determine the test fixture.
    lua.globals().ini = '[graphics]\nsaturation_multiplier=.95\nfog_density_multiplier=0\n'
    lua.globals().script_path = str(ROOT / 'scripts/?.lua')
    lua.execute("package.path=script_path..';'..package.path")
    lua.execute(MOCK)
    lua.execute("tuning=require('libs/tuning')")
    lua.execute(code)
    print('PASS', name)


run('INI reload, comments, defaults and invalid-file preservation', r'''
near(tuning.get('graphics.saturation_multiplier'),.95)
near(tuning.get('hud.dialogue_offset_y'),-.10)
near(tuning.get('audit.auto_start'),0)
near(tuning.get('audit.horizontal_margin'),.10)
near(tuning.get('audit.vertical_margin'),.15)
reload('[graphics]\nsaturation_multiplier = 0.9 ; comment\n[hud]\nboss_health_offset_y=0.12\n[audit]\nauto_start=1\nhorizontal_margin=.12\nvertical_margin=.18\n')
near(tuning.get('audit.auto_start'),1)
near(tuning.get('audit.horizontal_margin'),.12)
near(tuning.get('audit.vertical_margin'),.18)
near(tuning.get('graphics.saturation_multiplier'),.9)
near(tuning.get('graphics.contrast_multiplier'),1.1)
near(tuning.get('hud.boss_health_offset_y'),.12)
reload(string.char(239,187,191)..'[graphics]\nsaturation_multiplier=.9')
near(tuning.get('graphics.saturation_multiplier'),.9)
for _,bad in ipairs({'[graphics]\nsaturation_multiplier=5','[graphics]\nsaturation_multiplier=1e999',
    '[audit]\nauto_start=.5','[audit]\nauto_start=2','[hud]\nboss_heath_offset_y=.2','[oops]\nvalue=1',string.rep('x',8193)}) do
    reload(bad);near(tuning.get('graphics.saturation_multiplier'),.9)
end
''')

run('grading changes do not compound; inactive saturation stays neutral; reset restores', r'''
local feature=require('libs/contrast')()
for i=1,120 do feature.tick(nil,.016) end;healthy()
local settings=state.settings
near(settings.ColorContrast.W,1.1);near(settings.ColorContrast.X,1.2)
near(settings.ColorSaturation.W,.95);near(settings.ColorSaturation.X,1)
assert(settings.bOverride_ColorSaturation)
reload('[graphics]\nsaturation_multiplier=.9\ncontrast_multiplier=1.2')
feature.tick(nil,.016);healthy();near(settings.ColorContrast.W,1.2);near(settings.ColorSaturation.W,.9)
reload('[graphics]\nsaturation_multiplier=1\ncontrast_multiplier=1')
feature.tick(nil,.016);healthy();near(settings.ColorContrast.W,1)
assert(not settings.bOverride_ColorSaturation)
near(settings.ColorSaturation.X,1.4);near(settings.ColorSaturation.W,1.3)
feature.reset();near(settings.ColorContrast.W,1)
''')

run('active saturation preserves RGB; externally changed grade survives reset', r'''
local settings=state.settings;settings.bOverride_ColorSaturation=true
local feature=require('libs/contrast')();feature.tick(nil,.016);healthy()
near(settings.ColorSaturation.X,1.4);near(settings.ColorSaturation.W,1.3*.95)
settings.ColorContrast.W=.66
reload('[graphics]\ncontrast_multiplier=1.3')
feature.tick(nil,.016);healthy();near(settings.ColorContrast.W,.66)
feature.reset();near(settings.ColorContrast.W,.66)
near(settings.ColorSaturation.W,1.3)
''')

run('fog scaling tracks native baseline and avoids feedback across tuning changes', r'''
local feature=require('libs/fog_density')();feature.tick(nil,.016);healthy();near(state.fog.density,0)
reload('[graphics]\nfog_density_multiplier=.5')
for i=1,60 do feature.tick(nil,.016) end;healthy();near(state.fog.density,.01)
reload('[graphics]\nfog_density_multiplier=.25')
feature.tick(nil,.016);near(state.fog.density,.005)
state.fog.density=.04;feature.tick(nil,.016);near(state.fog.density,.01)
feature.reset();near(state.fog.density,.04)
''')

run('HUD uses full viewport fraction, reloads offsets without drift and restores', r'''
local feature=require('libs/hud_layout')()
for i=1,60 do feature.tick(nil,.016) end;healthy()
near(state.hud.translation.X,7);near(state.hud.translation.Y,11-144/2)
reload('[hud]\ndialogue_offset_y=-.2')
for i=1,60 do feature.tick(nil,.016) end;healthy();near(state.hud.translation.Y,11-288/2)
reload('[hud]\ndialogue_offset_y=0');feature.tick(nil,.016);near(state.hud.translation.Y,11)
reload('[hud]\ndialogue_offset_y=.1');feature.tick(nil,.016);near(state.hud.translation.Y,11+144/2)
state.hmd=false;feature.tick(nil,.016);near(state.hud.translation.Y,11)
''')

run('dialogue keeps X across synthetic keyboard events without continuous refresh', r'''
install_dialogue_hint();state.hud.dialogue='Talk to vendor';state.hud.progress=.6
local feature=require('libs/hud_layout')()
for i=1,120 do feature.tick(nil,.016) end;healthy();assert(state.refreshes==1)
state.hint_image.visibility=2;state.hint_text.visibility=3
feature.tick(nil,.016);healthy();assert(state.refreshes==2)
assert(state.hud.dialogue=='Talk to vendor' and state.hud.progress==.6)
near(state.hud.translation.Y,11-144/2)
''')

run('hidden dialogue and unrelated action hints retain native presentation', r'''
install_dialogue_hint();state.hud.visibility=2
local feature=require('libs/hud_layout')();feature.tick(nil,.016);healthy();assert(state.refreshes==0)
state.hud.visibility=0;state.hint_key.children.Key.name='IA_CallMount'
feature.tick(nil,.016);healthy();assert(state.refreshes==0)
state.hint_key.children.Key.name='IA_Interact';feature.tick(nil,.016);healthy();assert(state.refreshes==1)
''')

run('rebuilt dialogue children are rebound before accessing discarded objects', r'''
install_dialogue_hint();local feature=require('libs/hud_layout')();feature.tick(nil,.016);healthy()
for i=4,8 do state.objects[i].dead=true;state.objects[i]=nil end
state.hud.children.HorizontalBox_NextKey=nil
feature.tick(nil,.016) -- Hidden/teardown gaps must not read the stale cached children.
install_dialogue_hint();feature.tick(nil,.016);healthy();assert(state.refreshes==1)
''')

run('boss/counter/timer use independent configured HUD offsets', r'''
state.hud.kind='UI_Lifebar_Boss_C';state.hud.name='UI_Lifebar_Boss_C_1'
state.objects[4]=make_hud(4,'UI_Counter_C');state.objects[5]=make_hud(5,'UI_Timer_C');state.object_count=6
local feature=require('libs/hud_layout')();feature.tick(nil,.016);healthy()
near(state.hud.translation.Y,11+1440*.08/2)
reload('[hud]\nboss_health_offset_y=.12\nmission_info_offset_y=.06')
for i=1,60 do feature.tick(nil,.016) end;healthy()
near(state.hud.translation.Y,11+1440*.12/2)
near(state.objects[4].translation.Y,11+1440*.06/2)
near(state.objects[5].translation.Y,11+1440*.06/2)
feature.reset();near(state.hud.translation.Y,11);near(state.objects[4].translation.Y,11)
''')

run('compass background and marker overlay move together; root and aim stay fixed', r'''
state.hud.kind='UI_Player_C';state.hud.name='UI_Player_C_1'
local image=make_hud(4,'Image','Image_Compass');local overlay=make_hud(5,'Overlay','Overlay_Pings')
state.objects[4]=image;state.objects[5]=overlay;state.object_count=6
state.hud.children.Image_Compass=image;state.hud.children.Overlay_Pings=overlay
local feature=require('libs/hud_layout')()
for i=1,60 do feature.tick(nil,.016) end;healthy()
near(image.translation.Y,11+1440*.10/2);near(overlay.translation.Y,image.translation.Y)
near(state.hud.translation.Y,11)
reload('[hud]\ncompass_offset_y=.15');feature.tick(nil,.016);healthy()
near(image.translation.Y,11+1440*.15/2);near(overlay.translation.Y,image.translation.Y)
feature.reset();near(image.translation.Y,11);near(overlay.translation.Y,11)
''')

run('real HUD margins accept legacy audit keys but canonical values win regardless of section order', r'''
reload('[audit]\nhorizontal_margin=.2\nvertical_margin=.2')
near(tuning.get('hud.horizontal_margin'),.2);near(tuning.get('audit.vertical_margin'),.2)
reload('[hud]\nhorizontal_margin=.25\n[audit]\nhorizontal_margin=.2')
near(tuning.get('hud.horizontal_margin'),.25)
reload('[audit]\nhorizontal_margin=.2\n[hud]\nhorizontal_margin=.3')
near(tuning.get('audit.horizontal_margin'),.3)
''')
run('0.3.0.0 lowercase weather settings preserve grading and reset ownership', r'''
state.lowercase_settings=true
local feature=require('libs/contrast')()
for i=1,120 do feature.tick(nil,.016) end;healthy()
near(state.settings.ColorContrast.W,1.1);near(state.settings.ColorSaturation.W,.95)
feature.reset();near(state.settings.ColorContrast.W,1)
assert(not state.settings.bOverride_ColorSaturation)
''')
