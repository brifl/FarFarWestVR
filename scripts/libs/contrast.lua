local object_count=require('libs/object_count')
-- Configurable weather grading; preserve native RGB balance and restore our writes.
return function()
local api,vr,functions=uevr.api,uevr.params.vr,uevr.params.functions
local tuning=require('libs/tuning')
local array,class,scan_index,settings_field
local entries,elapsed,next_scan={},0,0
local stopped=false
local specs={
    {name='contrast',field='ColorContrast',flag='bOverride_ColorContrast',enable=false},
    {name='saturation',field='ColorSaturation',flag='bOverride_ColorSaturation',enable=true},
}
local function finite(n) return type(n)=='number' and n==n and n>=0 and n<=10 end
local function near(a,b) return math.abs(a-b)<.000001 end
local function snapshot(v)
    assert(v and finite(v.X) and finite(v.Y) and finite(v.Z) and finite(v.W),'Invalid grading vector')
    return {X=v.X,Y=v.Y,Z=v.Z,W=v.W}
end
local function same(v,expected)
    return near(v.X,expected.X) and near(v.Y,expected.Y) and near(v.Z,expected.Z) and near(v.W,expected.W)
end
local function write(v,value)
    v.X=value.X;v.Y=value.Y;v.Z=value.Z;v.W=value.W
end
local function valid(entry)
    local object=array:get_object(entry.index)
    return object and object:get_address()==entry.address and object:get_short_name()==entry.name
end
local function restore_channel(settings,c)
    if not c.applied then return end
    local value=settings[c.spec.field]
    if c.writing or (same(value,c.applied) and settings[c.spec.flag]==true) then
        write(value,c.original);settings[c.spec.flag]=c.override
    end
    c.applied=nil;c.writing=false
end
local function restore(entry)
    if not valid(entry) then return end
    local settings=entry.object:get_property(settings_field)
    for _,c in ipairs(entry.channels) do restore_channel(settings,c) end
end
local function reset()
    for _,entry in pairs(entries) do pcall(restore,entry) end
    entries,scan_index,next_scan={},nil,0
end
local function prepare()
    array=api:get_uobject_array()
    assert(array and array.get_objects_offset()==0 and array.get_item_distance()==24,
        'Compact object array unavailable')
    class=api:find_uobject('Class /Script/Engine.PostProcessComponent')
    assert(class,'Post-process component unavailable')
    -- The 0.3.0.0 reflection name is lowercase; vector/flag checks still gate writes.
    settings_field=class:find_property('Settings') and 'Settings'
        or class:find_property('settings') and 'settings'
    assert(settings_field,'Post-process settings unavailable')
end
local function discover()
    if elapsed<next_scan then return end
    local count=object_count(array)
    if scan_index==nil or scan_index>=count then scan_index=count-1 end
    for _=1,512 do
        if scan_index<0 then scan_index=nil;next_scan=elapsed+1;return end
        local index=scan_index;local object=array:get_object(index);scan_index=index-1
        if object and object:get_short_name():lower()=='postprocess' and object:is_a(class)
            and not entries[object:get_address()] then
            local owner=object:get_outer()
            if owner and not owner:get_short_name():match('^Default__')
                and owner:get_class():get_short_name():match('^BP_BlendableAtmosphere_')
                and object:get_property('bEnabled') and object:get_property('bUnbound')
                and object:get_property('BlendWeight')>0 then
                local settings=object:get_property(settings_field)
                local entry={object=object,index=index,address=object:get_address(),
                    name=object:get_short_name(),channels={}}
                for _,spec in ipairs(specs) do
                    local override=settings[spec.flag]
                    assert(type(override)=='boolean','Missing grading flag: '..spec.flag)
                    entry.channels[#entry.channels+1]={spec=spec,original=snapshot(settings[spec.field]),override=override}
                end
                entries[entry.address]=entry
            end
        end
    end
end
local function apply(settings,c)
    local value=settings[c.spec.field]
    local native=same(value,c.original) and settings[c.spec.flag]==c.override
    local ours=c.applied and same(value,c.applied) and settings[c.spec.flag]==true
    if not native and not ours then return end -- Preserve a different game-controlled grade.
    local multiplier=tuning.get('graphics.'..c.spec.name..'_multiplier')
    if multiplier==1 then restore_channel(settings,c);return end
    if not c.override and not c.spec.enable then return end
    -- An inactive native override has neutral effective values. Do not enable
    -- unused RGB tint values when introducing a saturation multiplier.
    local baseline=c.override and c.original or {X=1,Y=1,Z=1,W=1}
    local target={X=baseline.X,Y=baseline.Y,Z=baseline.Z,W=baseline.W*multiplier}
    if ours and same(value,target) then return end
    c.applied=target;c.writing=true
    write(value,target);settings[c.spec.flag]=true
    assert(same(settings[c.spec.field],target) and settings[c.spec.flag]==true,'Grading write did not take effect')
    c.writing=false
    functions.log_info(string.format('[FarFarWest grading] %s multiplier %.3f; master %.4f -> %.4f.',
        c.spec.name,multiplier,baseline.W,target.W))
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
            count=count+1;assert(count<=16,'Unexpected number of weather post-process components')
            if not valid(entry) then entries[address]=nil
            else
                local settings=entry.object:get_property(settings_field)
                for _,c in ipairs(entry.channels) do apply(settings,c) end
            end
        end
    end)
    if not ok then
        reset();stopped=true
        functions.log_warn('[FarFarWest grading] Stopped safely: '..tostring(err))
    end
end
return {tick=tick,reset=reset}
end
