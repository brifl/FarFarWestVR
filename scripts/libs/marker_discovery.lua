-- Native actor queries find markers allocated into reused UObject slots promptly.
-- The bounded array scan remains the fallback for other marker families.
return function(component_class,consider)
local api,log=uevr.api,uevr.params.functions
local paths={
 'BlueprintGeneratedClass /Game/Interfaces/Pings/BP_ObjectPing.BP_ObjectPing_C',
 'BlueprintGeneratedClass /Game/Levels/Assets/Lobby/BP_WorldIcon.BP_WorldIcon_C',
 'BlueprintGeneratedClass /Game/GPE/Tools/BP_TextGuide.BP_TextGuide_C',
 'BlueprintGeneratedClass /Game/Player/BP_Player.BP_Player_C',
 'BlueprintGeneratedClass /Game/Player/BP_PlayerNameWidget.BP_PlayerNameWidget_C',
 'BlueprintGeneratedClass /Game/Interfaces/BP_UiDamages.BP_UiDamages_C',
}
local array,library,viewport_class,classes,retry=nil,nil,nil,{},{}
local elapsed,next_query,failed=0,0,false
local function valid(r)
 local o=r and array:get_object(r.index)
 return o and o:get_address()==r.address and o:get_short_name()==r.name
end
local function field(c,n,offset)
 local p=c:find_property(n);assert(p and p:get_offset()==offset,'Unexpected marker query field '..n)
end
local function method(c,n,size,fields)
 local f=c:find_function(n);assert(f and f:get_properties_size()==size,'Unexpected marker query function '..n)
 for p,o in pairs(fields) do field(f,p,o) end
end
local function prepare()
 array=api:get_uobject_array()
 assert(array and array.get_objects_offset()==0 and array.get_item_distance()==24,'Unexpected marker query array')
 local c=assert(api:find_uobject('Class /Script/Engine.GameplayStatics'))
 method(c,'GetAllActorsOfClass',32,{WorldContextObject=0,ActorClass=8,OutActors=16})
 library=assert(c:get_class_default_object())
 c=assert(api:find_uobject('Class /Script/Engine.Actor'))
 method(c,'K2_GetComponentsByClass',24,{ComponentClass=0,ReturnValue=8})
 viewport_class=assert(api:find_uobject('Class /Script/Engine.GameViewportClient'))
end
local function tick(engine,delta)
 elapsed=elapsed+math.min(math.max(delta or 0,0),.1)
 if failed or not engine or elapsed<next_query then return end
 next_query=elapsed+.05
 local ok,err=pcall(function()
  if not library then prepare() end
  field(engine:get_class(),'GameViewport',3448)
  local viewport=engine:get_property('GameViewport');if not viewport then return end
  assert(viewport:is_a(viewport_class),'Unexpected marker query world context')
  for _,path in ipairs(paths) do
   if not valid(classes[path]) and elapsed>=(retry[path] or 0) then
    retry[path]=elapsed+1
    local c=api:find_uobject(path)
    if c then
     local index=c:read_dword(12)
     classes[path]={object=c,index=index,address=c:get_address(),name=c:get_short_name()}
     assert(valid(classes[path]),'Marker query class identity mismatch')
    end
   end
   local ref=classes[path]
   if valid(ref) then
    local actors={};library:GetAllActorsOfClass(viewport,ref.object,actors)
    assert(#actors<=128,'Marker actor query budget exceeded')
    for _,actor in ipairs(actors) do
     assert(actor:is_a(ref.object),'Unexpected marker actor query result')
     local components=actor:K2_GetComponentsByClass(component_class)
     assert(#components<=16,'Marker component query budget exceeded')
     for _,c in ipairs(components) do
      assert(c:is_a(component_class),'Unexpected marker component query result')
      consider(c)
     end
    end
   end
  end
 end)
 if not ok then
  failed=true;log.log_warn('[FarFarWest markers] Fast discovery unavailable; retaining array scan: '..tostring(err))
 end
end
return {tick=tick}
end
