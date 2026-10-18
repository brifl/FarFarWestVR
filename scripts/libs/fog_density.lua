-- The tested ambient haze control. Keep other fog systems and scene settings.
return function()
local api,vr,functions=uevr.api,uevr.params.vr,uevr.params.functions
local array,class,scan_index
local entries,elapsed,next_scan={},0,0
local stopped,reported=false,false
local function finite(n) return type(n)=="number" and n==n and n>=0 and n<=10 end
local function valid(entry)
    local object=array:get_object(entry.index)
    return object and object:get_address()==entry.address
        and object:get_short_name()=="ExponentialHeightFog"
end
local function restore(entry)
    if entry.written and valid(entry) and entry.object:get_property("FogDensity")==0 then
        entry.object:SetFogDensity(entry.original)
    end
end
local function reset()
    for _,entry in pairs(entries) do pcall(restore,entry) end
    entries,scan_index,next_scan={},nil,0
end
local function prepare()
    array=api:get_uobject_array()
    assert(array and array.get_objects_offset()==0 and array.get_item_distance()==24,
        "Compact object array unavailable")
    class=api:find_uobject("Class /Script/Engine.ExponentialHeightFogComponent")
    assert(class,"Fog class unavailable")
    local density=class:find_property("FogDensity")
    assert(density and density:get_offset()==592,"Unexpected fog component layout")
    local fn=class:find_function("SetFogDensity")
    assert(fn and fn:get_properties_size()==4,"Unexpected fog setter parameters")
    local field=fn:get_child_properties()
    local parameter=field and fn:find_property(field:get_fname():to_string())
    assert(parameter and parameter:get_offset()==0 and not field:get_next(),
        "Unexpected fog setter metadata")
end
local function discover()
    if elapsed<next_scan then return end
    local count=array:get_object_count()
    assert(count>0 and count<=250000,"Object count exceeds verified budget")
    if scan_index==nil or scan_index>=count then scan_index=count-1 end
    for _=1,512 do
        if scan_index<0 then scan_index=nil;next_scan=elapsed+1;return end
        local index=scan_index;local object=array:get_object(index);scan_index=index-1
        if object and object:get_short_name()=="ExponentialHeightFog" and object:is_a(class)
            and not entries[object:get_address()] then
            -- Limit this to the game's ambient weather actors, excluding
            -- unrelated fog effects and class-default/template objects.
            local owner=object:get_outer()
            if owner and not owner:get_short_name():match("^Default__")
                and owner:get_class():get_short_name():match("^BP_BlendableAtmosphere_") then
                local density=object:get_property("FogDensity")
                assert(finite(density),"Invalid ambient fog density")
                entries[object:get_address()]={object=object,index=index,address=object:get_address(),
                    original=density,written=false}
            end
        end
    end
end
local function tick(_,delta)
    if stopped then return end
    local ok,err=pcall(function()
        elapsed=elapsed+math.min(math.max(delta or 0,0),.1)
        if not vr.is_runtime_ready() or not vr.is_hmd_active() then return end
        if not array then prepare() end
        discover()
        local count=0
        for address,entry in pairs(entries) do
            count=count+1;assert(count<=16,"Unexpected number of ambient fog components")
            if not valid(entry) then entries[address]=nil
            else
                local current=entry.object:get_property("FogDensity")
                assert(finite(current),"Invalid ambient fog density")
                if current~=0 then
                    -- Remember a new native/weather value before suppressing it;
                    -- never multiply our own value again on subsequent frames.
                    entry.original=current;entry.written=true
                    entry.object:SetFogDensity(0)
                    assert(entry.object:get_property("FogDensity")==0,"Fog density setter did not take effect")
                    if not reported then
                        reported=true
                        functions.log_info(string.format("[FarFarWest fog] Ambient weather fog density %.6f -> 0; tested clear-distance setting active.",current))
                    end
                end
            end
        end
    end)
    if not ok then
        reset();stopped=true
        functions.log_warn("[FarFarWest fog] Stopped safely: "..tostring(err))
    end
end
return {tick=tick,reset=reset}
end
