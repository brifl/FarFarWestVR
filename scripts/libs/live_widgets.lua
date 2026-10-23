-- Guarded native discovery in the callback engine's current world.
return function(path,limit,interval,top_only)
local api=uevr.api
local array,library,viewport_class,class
local entries,next_query,world={},0,nil
local function count()
    local n=array:get_object_count()
    assert(n>0 and n<=250000,'Widget query object count exceeds verified budget')
    return n
end
local function field(c,name,offset)
    local p=c:find_property(name);assert(p and p:get_offset()==offset,'Unexpected widget query field '..name)
end
local function track(o)
    local index=o:read_dword(12)
    local current=index>=0 and index<count() and array:get_object(index)
    assert(current and current:get_address()==o:get_address(),'Widget query identity mismatch')
    return {object=o,index=index,address=o:get_address(),name=o:get_short_name()}
end
local function valid(ref)
    local o=ref and array and array:get_object(ref.index)
    return o and o:get_address()==ref.address and o:get_short_name()==ref.name
end
local function get(engine,time)
    if not engine then return entries end
    if not array then
        array=api:get_uobject_array()
        assert(array and array.get_objects_offset()==0 and array.get_item_distance()==24,'Unexpected compact array')
        local c=assert(api:find_uobject('Class /Script/UMG.WidgetBlueprintLibrary'))
        local fn=c:find_function('GetAllWidgetsOfClass')
        assert(fn and fn:get_properties_size()==40,'Unexpected widget query function')
        for n,o in pairs({WorldContextObject=0,FoundWidgets=8,WidgetClass=24,TopLevelOnly=32}) do field(fn,n,o) end
        library=assert(c:get_class_default_object())
        viewport_class=assert(api:find_uobject('Class /Script/Engine.GameViewportClient'))
    end
    field(engine:get_class(),'GameViewport',3448)
    local viewport=engine:get_property('GameViewport')
    if not viewport then entries={};world=nil;return entries end
    assert(viewport:is_a(viewport_class),'Unexpected widget world context')
    if world~=viewport:get_address() then entries={};next_query=0;world=viewport:get_address() end
    if time<next_query then return entries end
    next_query=time+(interval or .25)
    if not valid(class) then
        local c=api:find_uobject(path)
        if not c then return entries end
        class=track(c)
    end
    local found={};library:GetAllWidgetsOfClass(viewport,found,class.object,top_only==true)
    assert(#found<=limit,'Native widget query exceeds its budget')
    local next_entries={}
    for _,o in ipairs(found) do
        assert(o:is_a(class.object),'Unexpected widget query result')
        local ref=track(o);next_entries[ref.address]=ref
    end
    entries=next_entries
    return entries
end
return {get=get,valid=valid,track=track,reset=function() entries,next_query,world={},0,nil end}
end
