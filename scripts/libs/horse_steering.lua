-- Shape only mounted left-stick steering. Resolve possession on the game thread;
-- the XInput callback consumes a Boolean snapshot, never a cached native pawn.
return function(tuning)
tuning=tuning or require('libs/tuning')
local api,vr,log=uevr.api,uevr.params.vr,uevr.params.functions
local array,statics,viewport_class,mount_class
local mounted,failed,reported,exponent=false,false,false,1
local elapsed,next_class=0,0
local function field(c,n,offset)
 local p=c:find_property(n);assert(p and p:get_offset()==offset,'Unexpected horse field '..n)
end
local function valid(r)
 local o=r and array:get_object(r.index)
 return o and o:get_address()==r.address and o:get_short_name()==r.name
end
local function ready()
 return _G.farfarwest_gameplay_ready==true and vr.is_runtime_ready() and vr.is_hmd_active()
  and vr.is_using_controllers() and not log.is_drawing_ui()
  and vr:get_mod_value('VR_2DScreenMode')=='false'
end
local function prepare()
 array=api:get_uobject_array()
 assert(array and array.get_objects_offset()==0 and array.get_item_distance()==24,'Unexpected horse object array')
 local c=assert(api:find_uobject('Class /Script/Engine.GameplayStatics'))
 local fn=assert(c:find_function('GetPlayerController'))
 assert(fn:get_properties_size()==24,'Unexpected horse controller query')
 for n,o in pairs({WorldContextObject=0,PlayerIndex=8,ReturnValue=16}) do field(fn,n,o) end
 statics=assert(c:get_class_default_object())
 viewport_class=assert(api:find_uobject('Class /Script/Engine.GameViewportClient'))
end
local function stop(err)
 mounted=false;failed=true
 log.log_warn('[FarFarWest horse] Steering curve stopped safely: '..tostring(err))
end
local function tick(engine,delta)
 mounted=false
 if failed then return end
 local ok,err=pcall(function()
  elapsed=elapsed+math.min(math.max(delta or 0,0),.1)
  if not engine or not ready() then return end
  exponent=tuning.get('horse.steering_exponent')
  if exponent==1 then return end
  if not statics then prepare() end
  if not valid(mount_class) and elapsed>=next_class then
   next_class=elapsed+1
   local c=api:find_uobject('BlueprintGeneratedClass /Game/Mounts/BP_Mount.BP_Mount_C')
   if c then
    local index=c:read_dword(12)
    assert(index>=0 and index<array:get_object_count(),'Invalid horse class index')
    mount_class={object=c,index=index,address=c:get_address(),name=c:get_short_name()}
    assert(valid(mount_class),'Horse class identity mismatch')
    field(c,'isLocallyMounted',2016);field(c,'Controller',728)
   end
  end
  if not valid(mount_class) then return end
  field(engine:get_class(),'GameViewport',3448)
  local viewport=engine:get_property('GameViewport');if not viewport then return end
  assert(viewport:is_a(viewport_class),'Unexpected horse world context')
  local pc=statics:GetPlayerController(viewport,0);if not pc then return end
  field(pc:get_class(),'Pawn',744)
  local pawn=pc:get_property('Pawn')
  if not pawn or not pawn:is_a(mount_class.object) then return end
  local owner=pawn:get_property('Controller')
  mounted=owner and owner:get_address()==pc:get_address() and pawn:get_property('isLocallyMounted')==true or false
  if mounted and not reported then
   reported=true;log.log_info('[FarFarWest horse] Mounted left-stick steering curve active; other axes unchanged.')
  end
 end)
 if not ok then stop(err) end
end
local function input(_,user_index,state)
 if failed or not mounted or exponent==1 then return end
 local ok,err=pcall(function()
  if user_index~=vr.get_lowest_xinput_index() or not ready() then return end
  local pad=state.Gamepad;local x=pad.sThumbLX
  if x==0 then return end
  -- Signed power curve: more precision near center, same full-lock endpoints.
  local maximum=x<0 and 32768 or 32767
  local magnitude=math.min(math.abs(x)/maximum,1)^exponent
  pad.sThumbLX=(x<0 and -1 or 1)*math.floor(magnitude*maximum+.5)
 end)
 if not ok then stop(err) end
end
return {tick=tick,input=input,reset=function() mounted=false end}
end
