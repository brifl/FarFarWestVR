-- The game's mission-loading card outlives the engine's loading-screen log.
-- Observe only that card; the menu helper owns presentation and cleanup.
return function()
local api,log=uevr.api,uevr.params.functions
local array,widget_class,scan,count_seen,recent,recent_min
local entries,elapsed,next_scan={},0,0
local failed,shown=false,false
local function prepare()
    array=api:get_uobject_array()
    assert(array and array.get_objects_offset()==0 and array.get_item_distance()==24,
        'Compact object array unavailable')
    widget_class=api:find_uobject('Class /Script/UMG.UserWidget')
    assert(widget_class,'UserWidget class unavailable')
    local fn=widget_class:find_function('IsInViewport')
    assert(fn and fn:get_properties_size()==1,'Unexpected IsInViewport parameters')
    local field=widget_class:find_property('Visibility')
    assert(field and field:get_offset()==221,'Unexpected widget visibility layout')
end
local function visible()
    local active=false
    for address,ref in pairs(entries) do
        local object=array:get_object(ref.index)
        if not object or object:get_address()~=address or object:get_short_name()~=ref.name then
            entries[address]=nil
        else
            local visibility=object:get_property('Visibility')
            if visibility~=1 and visibility~=2 and object:IsInViewport() then active=true end
        end
    end
    return active
end
local function discover()
    local count=array:get_object_count()
    assert(count>0 and count<=250000,'Object count outside the verified budget')
    if count_seen and count>count_seen then
        recent_min=recent_min and math.min(recent_min,count_seen) or count_seen
        recent=count-1
    elseif count_seen and count<count_seen then
        scan,recent,recent_min=nil,nil,nil;next_scan=0
    end
    count_seen=count
    if elapsed<next_scan and not recent then return end
    if scan==nil or scan>=count then scan=count-1 end
    local deadline=os.clock()+.001
    for _=1,8192 do
        if recent and recent<recent_min then recent,recent_min=nil,nil end
        if not recent and scan<0 then scan=nil;next_scan=elapsed+.25;return end
        local index=recent or scan
        if recent then recent=recent-1 else scan=scan-1 end
        local object=array:get_object(index)
        local name=object and object:get_short_name()
        if name and name:match('^UI_LoadingScreen_C_%d+$')
            and not entries[object:get_address()]
            and object:get_class():get_short_name()=='UI_LoadingScreen_C'
            and object:is_a(widget_class) then
            entries[object:get_address()]={index=index,name=name}
            if object:IsInViewport() then return end
        end
        if os.clock()>=deadline then return end
    end
end
local function tick(_,delta)
    if failed then return false end
    local ok,active=pcall(function()
        elapsed=elapsed+math.min(math.max(delta or 0,0),.1)
        if not array then prepare() end
        if visible() then return true end
        discover()
        return visible()
    end)
    if not ok then
        failed=true
        log.log_warn('[FarFarWest preview] Detection stopped safely: '..tostring(active))
        return false
    end
    if active~=shown then
        shown=active
        log.log_info(active and '[FarFarWest preview] Mission card visible; retaining menu presentation.'
            or '[FarFarWest preview] Mission card removed; following normal input mode.')
    end
    return active
end
return {tick=tick}
end
