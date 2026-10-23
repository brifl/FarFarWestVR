local object_count=require('libs/object_count')
-- The game's mission-loading card outlives the engine's loading-screen log.
-- Query that card directly; the menu helper owns presentation and cleanup.
return function()
local api,log=uevr.api,uevr.params.functions
local array,widget_class,viewport_class,library,card_class
local entries,elapsed,next_query={},0,0
local failed,shown=false,false
local class_path='WidgetBlueprintGeneratedClass /Game/Interfaces/UI_LoadingScreen.UI_LoadingScreen_C'
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
    viewport_class=api:find_uobject('Class /Script/Engine.GameViewportClient')
    local class=api:find_uobject('Class /Script/UMG.WidgetBlueprintLibrary')
    assert(viewport_class and class,'Native widget query unavailable')
    fn=class:find_function('GetAllWidgetsOfClass')
    assert(fn and fn:get_properties_size()==40,'Unexpected widget query parameters')
    for name,offset in pairs({WorldContextObject=0,FoundWidgets=8,WidgetClass=24,TopLevelOnly=32}) do
        field=fn:find_property(name)
        assert(field and field:get_offset()==offset,'Widget query layout mismatch: '..name)
    end
    library=class:get_class_default_object();assert(library,'Widget query library unavailable')
end
local function track(object)
    local count=object_count(array)
    local index=object:read_dword(12)
    assert(index<count,'Widget query returned an invalid index')
    local current=array:get_object(index)
    assert(current and current:get_address()==object:get_address(),'Widget query identity mismatch')
    return {index=index,address=object:get_address(),name=object:get_short_name(),object=object}
end
local function valid(ref)
    local object=array:get_object(ref.index)
    return object and object:get_address()==ref.address and object:get_short_name()==ref.name
end
local function visible()
    local active=false
    for address,ref in pairs(entries) do
        if not valid(ref) then entries[address]=nil
        else
            local visibility=ref.object:get_property('Visibility')
            if visibility~=1 and visibility~=2 and ref.object:IsInViewport() then active=true end
        end
    end
    return active
end
local function discover(engine)
    if elapsed<next_query or not engine then return end
    next_query=elapsed+.05
    if card_class and not valid(card_class) then card_class=nil end
    if not card_class then
        local class=api:find_uobject(class_path)
        if not class then next_query=elapsed+.25;return end
        assert(class:get_short_name()=='UI_LoadingScreen_C'
            and class:get_class():get_short_name()=='WidgetBlueprintGeneratedClass','Unexpected mission-card class')
        card_class=track(class)
    end
    -- Use the callback's live engine and its viewport as the native world
    -- context. Do not call the unsupported SDK UEngine::get_world lookup.
    local field=engine:get_class():find_property('GameViewport')
    assert(field and field:get_offset()==3448,'Unexpected engine viewport layout')
    local viewport=engine:get_property('GameViewport')
    if not viewport then return end
    assert(viewport:is_a(viewport_class),'Unexpected native viewport context')
    local found={}
    library:GetAllWidgetsOfClass(viewport,found,card_class.object,true)
    assert(#found<=16,'Too many mission cards')
    entries={}
    for _,object in ipairs(found) do
        assert(object:is_a(widget_class) and object:get_class():get_short_name()=='UI_LoadingScreen_C',
            'Unexpected widget query result')
        local ref=track(object);entries[ref.address]=ref
    end
end
local function tick(engine,delta)
    if failed then return false end
    local ok,active=pcall(function()
        elapsed=elapsed+math.min(math.max(delta or 0,0),.1)
        if not array then prepare() end
        if visible() then return true end
        discover(engine)
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
