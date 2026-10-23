-- Correct disjoint HUD overlays that are outside the fixed edge-group adapter.
-- Native content, position offsets and animated scale baselines stay owned by the game.
return function()
local api,vr,log=uevr.api,uevr.params.vr,uevr.params.functions
local tuning=require('libs/tuning')
local shape=require('libs/ui_shape')
local query=require('libs/live_widgets')
local specs={
 {path='/Game/Interfaces/UI_Player.UI_Player_C',children={Image_Compass=1008,Overlay_Pings=944}},
 {path='/Game/Interfaces/UI_NpcTalk.UI_NpcTalk_C',field='TextBlock_Text',offset=832},
 {path='/Game/Interfaces/Boss/UI_Lifebar_Boss.UI_Lifebar_Boss_C',field='ProgressBar_Boss',offset=840,
  scale_key='hud.boss_health_scale_multiplier',anchor={X=.5,Y=0}},
 {path='/Game/Interfaces/UI_Counter.UI_Counter_C',field='Text_Title',offset=816},
 {path='/Game/Interfaces/UI_Timer.UI_Timer_C',field='TextBlock_Seconds',offset=816},
 {path='/Game/Interfaces/UI_LowAmmo.UI_LowAmmo_C',field='Appear',offset=816,
  scale_key='hud.scale_multiplier',anchor={X=.5,Y=.5}},
}
for _,s in ipairs(specs) do s.query=query('WidgetBlueprintGeneratedClass '..s.path,16,.5,true) end
local projection=UEVR_Matrix4x4f.new()
local eye,layout,elapsed,entries,failed=nil,nil,0,{},false
local rejected={}
local function active()
 return _G.farfarwest_gameplay_ready==true and vr.is_runtime_ready() and vr.is_hmd_active()
  and not log.is_drawing_ui() and vr:get_mod_value('VR_2DScreenMode')=='false'
end
local function restore(entry)
 if entry.query.valid(entry.ref) then shape.restore(entry.binding) end
end
local function reset()
 for _,entry in pairs(entries) do pcall(restore,entry) end
 entries={};rejected={};eye=nil
 for _,s in ipairs(specs) do s.query.reset() end
end
local function field(c,n,offset)
 local p=c:find_property(n);assert(p and p:get_offset()==offset,'Unexpected HUD shape field '..n)
end
local function bind(o,root,s,name)
 local address=o:get_address();if entries[address] then return end
 local t=o:get_property('RenderTransform')
 assert(math.abs(t.Angle)<.001 and math.abs(t.Shear.X)<.001 and math.abs(t.Shear.Y)<.001,
  'Rotated/sheared overlay requires its own calibration')
 entries[address]={ref=s.query.track(o),root=root,query=s.query,field=name,
  scale_key=s.scale_key,binding=shape.bind(o,s.anchor)}
end
local function tick(engine,delta)
 if failed then return end
 local ok,err=pcall(function()
  elapsed=elapsed+math.min(math.max(delta or 0,0),.1)
  if not engine or not active() then reset();return end
  if not layout then
   local c=assert(api:find_uobject('Class /Script/UMG.WidgetLayoutLibrary'))
   local fn=c:find_function('GetViewportSize');assert(fn and fn:get_properties_size()==24,'Unexpected HUD viewport function')
   layout=assert(c:get_class_default_object())
   c=assert(api:find_uobject('Class /Script/UMG.Widget'))
   for n,size in pairs({GetDesiredSize=16,SetRenderScale=16,SetRenderTransformPivot=16,GetParent=8}) do
    fn=c:find_function(n);assert(fn and fn:get_properties_size()==size,'Unexpected HUD shape method '..n)
   end
   field(c,'RenderTransform',144);field(c,'RenderTransformPivot',200)
  end
  local present={}
  for _,s in ipairs(specs) do
   for _,root in pairs(s.query.get(engine,elapsed)) do
    if s.query.valid(root) and not rejected[root.address] then
     present[root.address]=true
     local bound,reason=pcall(function()
      local o=root.object
      if s.children then
       for name,offset in pairs(s.children) do
        field(o:get_class(),name,offset)
        local child=o:get_property(name)
        if child then bind(child,root,s,name) end
       end
      elseif not o:GetParent() then
       -- Nested HUD groups already inherit their parent's aspect correction.
       field(o:get_class(),s.field,s.offset);bind(o,root,s)
      end
     end)
     if not bound then
      rejected[root.address]=true
      for address,entry in pairs(entries) do
       if entry.root.address==root.address then pcall(restore,entry);entries[address]=nil end
      end
      log.log_warn('[FarFarWest HUD shape] Skipped '..root.name..': '..tostring(reason))
     end
    end
   end
  end
  for address,entry in pairs(entries) do
   local valid=present[entry.root.address] and entry.query.valid(entry.ref) and entry.query.valid(entry.root)
   if valid and entry.field then
    local child=entry.root.object:get_property(entry.field)
    valid=child and child:get_address()==address
   elseif valid then valid=not entry.ref.object:GetParent() end
   if not valid then pcall(restore,entry);entries[address]=nil
   elseif tuning.get('hud.aspect_correction')==0 then
    shape.apply(entry.binding,1,entry.scale_key and tuning.get(entry.scale_key) or 1)
   elseif eye then
    local viewport=layout:GetViewportSize(entry.root.object)
    local factor=viewport and shape.height_factor(eye,viewport.X,viewport.Y)
    if shape.apply(entry.binding,factor,entry.scale_key and tuning.get(entry.scale_key) or 1) and not entry.reported then
     entry.reported=true;log.log_info('[FarFarWest HUD shape] Corrected '..entry.ref.name..' while preserving native placement.')
    end
   end
  end
 end)
 if not ok then pcall(reset);failed=true;log.log_warn('[FarFarWest HUD shape] Stopped safely: '..tostring(err)) end
end
local function camera()
 if failed or not active() then eye=nil;return end
 local ok=pcall(function()
  vr.get_ue_projection_matrix(-1,projection)
  eye={[0]={[0]=projection:get(0,0)},[1]={[1]=projection:get(1,1)}}
 end)
 if not ok then eye=nil end
end
return {tick=tick,camera=camera,reset=reset}
end
