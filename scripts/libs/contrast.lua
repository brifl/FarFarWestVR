-- Preserve the accepted master-contrast increase on the game's weather grading.
return function()
local api,vr,functions=uevr.api,uevr.params.vr,uevr.params.functions
local array,class,scan_index
local entries,elapsed,next_scan={},0,0
local stopped,reported=false,false
local multiplier=1.10
local function finite(n) return type(n)=="number" and n==n and n>=0 and n<=10 end
local function near(a,b) return math.abs(a-b)<.000001 end
local function valid(entry)
    local object=array:get_object(entry.index)
    return object and object:get_address()==entry.address and object:get_short_name()==entry.name
end
local function restore(entry)
    if entry.written and valid(entry) then
        local contrast=entry.object:get_property("Settings").ColorContrast
        if near(contrast.W,entry.applied) then contrast.W=entry.original end
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
    class=api:find_uobject("Class /Script/Engine.PostProcessComponent")
    assert(class and class:find_property("Settings"),"Post-process settings unavailable")
end
local function discover()
    if elapsed<next_scan then return end
    local count=array:get_object_count()
    assert(count>0 and count<=250000,"Object count exceeds verified budget")
    if scan_index==nil or scan_index>=count then scan_index=count-1 end
    for _=1,512 do
        if scan_index<0 then scan_index=nil;next_scan=elapsed+1;return end
        local index=scan_index;local object=array:get_object(index);scan_index=index-1
        if object and object:get_short_name():lower()=="postprocess" and object:is_a(class)
            and not entries[object:get_address()] then
            local owner=object:get_outer()
            if owner and not owner:get_short_name():match("^Default__")
                and owner:get_class():get_short_name():match("^BP_BlendableAtmosphere_")
                and object:get_property("bEnabled") and object:get_property("bUnbound")
                and object:get_property("BlendWeight")>0 then
                local settings=object:get_property("Settings")
                if settings.bOverride_ColorContrast then
                    local c=settings.ColorContrast
                    assert(finite(c.X) and finite(c.Y) and finite(c.Z) and finite(c.W),"Invalid contrast values")
                    entries[object:get_address()]={object=object,index=index,address=object:get_address(),
                        name=object:get_short_name(),original=c.W,applied=c.W*multiplier,written=false}
                end
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
            count=count+1;assert(count<=16,"Unexpected number of weather post-process components")
            if not valid(entry) then entries[address]=nil
            else
                local settings=entry.object:get_property("Settings")
                local c=settings.ColorContrast
                assert(finite(c.W),"Invalid master contrast")
                -- Reapply a refreshed native baseline without multiplying our
                -- own value. Leave a different game-controlled master alone.
                if settings.bOverride_ColorContrast and near(c.W,entry.original) then
                    entry.written=true
                    c.W=entry.applied
                    assert(near(settings.ColorContrast.W,entry.applied),"Contrast write did not take effect")
                    if not reported then
                        reported=true
                        functions.log_info(string.format("[FarFarWest contrast] Master %.4f -> %.4f; accepted ten-percent increase active, RGB preserved.",entry.original,entry.applied))
                    end
                end
            end
        end
    end)
    if not ok then
        reset();stopped=true
        functions.log_warn("[FarFarWest contrast] Stopped safely: "..tostring(err))
    end
end
return {tick=tick,reset=reset}
end
