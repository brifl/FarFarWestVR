local object_count=require('libs/object_count')
-- Draw the game's cursor asset in the viewport when CommonUI hides its cursor layer.
-- Pointer movement/clicks remain entirely with the existing controller-ray helper.
return function()
local api,vr,log=uevr.api,uevr.params.vr,uevr.params.functions
local tuning=require('libs/tuning')
local shape=require('libs/ui_shape')
local projection=UEVR_Matrix4x4f.new()
local query=require('libs/live_widgets')
local cursor_queries={query('WidgetBlueprintGeneratedClass /Game/Interfaces/Cursors/UI_Cursor.UI_Cursor_C',64,.1),
    query('WidgetBlueprintGeneratedClass /Game/Interfaces/Cursors/UI_Cursor_Hand.UI_Cursor_Hand_C',64,.1)}
local hidden,elapsed={},0
local array,library,layout,viewport_class,cursor_class
local proxy,world,failed,reported=nil,nil,false,false
local path='WidgetBlueprintGeneratedClass /Game/Interfaces/Cursors/UI_Cursor.UI_Cursor_C'
local function finite(n) return type(n)=='number' and n==n and math.abs(n)<1e7 end
local function valid(ref)
    local o=ref and array and array:get_object(ref.index)
    return o and o:get_address()==ref.address and o:get_short_name()==ref.name
end
local function track(o)
    local index=o:read_dword(12);local count=object_count(array)
    assert(index>=0 and index<count,'Cursor object exceeds verified array')
    local ref={object=o,index=index,address=o:get_address(),name=o:get_short_name()}
    assert(valid(ref),'Cursor object identity mismatch');return ref
end
local function cleanup()
    if valid(proxy) then proxy.object:RemoveFromParent() end
    proxy,world=nil,nil
end
local function restore_hidden()
    for _,entry in pairs(hidden) do
        if entry.query.valid(entry.ref) and entry.ref.object:get_property('RenderOpacity')==0 then
            entry.ref.object:SetRenderOpacity(entry.opacity)
        end
    end
    hidden={}
end
local function suppress_originals(engine)
    for _,q in ipairs(cursor_queries) do
        for address,ref in pairs(q.get(engine,elapsed)) do
            if q.valid(ref) and (not proxy or address~=proxy.address) then
                local opacity=ref.object:get_property('RenderOpacity')
                assert(finite(opacity),'Invalid original cursor opacity')
                local entry=hidden[address]
                if not entry then entry={ref=ref,query=q,opacity=opacity};hidden[address]=entry end
                if opacity~=0 then entry.opacity=opacity;ref.object:SetRenderOpacity(0) end
            end
        end
    end
    for address,entry in pairs(hidden) do if not entry.query.valid(entry.ref) then hidden[address]=nil end end
end
local function method(class,name,minimum,maximum)
    local fn=class:find_function(name)
    assert(fn and fn:get_properties_size()>=minimum and fn:get_properties_size()<=(maximum or minimum),
        'Unexpected native cursor function '..name)
    return fn
end
local function field(class,name,offset)
    local p=class:find_property(name)
    assert(p and p:get_offset()==offset,'Unexpected native cursor field '..name)
end
local function prepare()
    array=api:get_uobject_array()
    assert(array and array.get_objects_offset()==0 and array.get_item_distance()==24,'Unexpected cursor object array')
    viewport_class=assert(api:find_uobject('Class /Script/Engine.GameViewportClient'))
    local c=assert(api:find_uobject('Class /Script/UMG.WidgetBlueprintLibrary'))
    local fn=method(c,'Create',32)
    for name,offset in pairs({WorldContextObject=0,WidgetType=8,OwningPlayer=16,ReturnValue=24}) do field(fn,name,offset) end
    library=assert(c:get_class_default_object())
    c=assert(api:find_uobject('Class /Script/UMG.WidgetLayoutLibrary'))
    method(c,'GetMousePositionOnViewport',24)
    method(c,'GetViewportSize',24)
    layout=assert(c:get_class_default_object())
    c=assert(api:find_uobject('Class /Script/UMG.UserWidget'))
    for name,size in pairs({AddToViewport=4,RemoveFromParent=0,SetDesiredSizeInViewport=16,
        SetAlignmentInViewport=16,ForceLayoutPrepass=0,GetDesiredSize=16,SetVisibility=1,SetRenderOpacity=4,
        SetRenderScale=16}) do
        method(c,name,size)
    end
    method(c,'SetPositionInViewport',17,32)
    field(c,'RenderOpacity',224)
end
local function tick(engine,delta)
    if failed then return end
    elapsed=elapsed+math.min(math.max(delta or 0,0),.1)
    local ok,err=pcall(function()
        if not engine or not vr.is_runtime_ready() or not vr.is_hmd_active()
            or log.is_drawing_ui() then cleanup();restore_hidden();return end
        if not library then prepare() end
        if vr:get_mod_value('VR_2DScreenMode')~='true' then
            cleanup()
            if _G.farfarwest_gameplay_ready==true then suppress_originals(engine) else restore_hidden() end
            return
        end
        field(engine:get_class(),'GameViewport',3448)
        local viewport=engine:get_property('GameViewport')
        if not viewport then cleanup();return end
        assert(viewport:is_a(viewport_class),'Unexpected cursor world context')
        if not valid(world) or world.address~=viewport:get_address() then cleanup();world=track(viewport) end
        if not valid(cursor_class) then
            local c=api:find_uobject(path)
            if not c then cleanup();return end -- The older game has no native cursor asset.
            cursor_class=track(c)
        end
        if not valid(proxy) then
            local o=assert(library:Create(viewport,cursor_class.object,nil),'Native cursor creation failed')
            proxy=track(o) -- Own partially completed creation so an error can remove it.
            o:SetVisibility(3);o:SetRenderOpacity(1);o:AddToViewport(10000)
            o:ForceLayoutPrepass()
            local size=o:GetDesiredSize()
            -- The native software cursor measures 66 square; its first prepass can return zero.
            if size.X<=0 or size.Y<=0 then size.X,size.Y=66,66 end
            assert(finite(size.X) and finite(size.Y) and size.X>0 and size.Y>0 and size.X<=128 and size.Y<=128,
                'Unexpected native cursor size')
            -- Its canvas already translates the graphic by 32 pixels, expecting a centered hotspot.
            o:SetAlignmentInViewport({X=.5,Y=.5});o:SetDesiredSizeInViewport(size)
            if not reported then
                reported=true;log.log_info('[FarFarWest native cursor] Game cursor active with centered hotspot.')
            end
        end
        local position=layout:GetMousePositionOnViewport(viewport)
        assert(position and finite(position.X) and finite(position.Y),'Invalid menu pointer position')
        -- These are viewport-local coordinates; applying DPI removal again misaligns the cursor.
        proxy.object:SetPositionInViewport(position,false)
        local size=tuning.get('cursor.scale_multiplier')
        local factor=1
        if tuning.get('cursor.aspect_correction')==1 then
            vr.get_ue_projection_matrix(0,projection)
            local viewport_size=layout:GetViewportSize(viewport)
            factor=shape.height_factor({[0]={[0]=projection:get(0,0)},[1]={[1]=projection:get(1,1)}},viewport_size.X,viewport_size.Y)
        end
        if factor then
            local scale=proxy.object:GetDesiredSize();scale.X,scale.Y=size,size*factor
            proxy.object:SetRenderScale(scale)
        end
        -- Suppress the game's software copies in both modes, including their click flashes.
        -- Our corrected copy is the only menu arrow; gameplay keeps the firing reticle.
        suppress_originals(engine)
    end)
    if not ok then
        pcall(cleanup);pcall(restore_hidden);failed=true
        log.log_warn('[FarFarWest native cursor] Stopped safely: '..tostring(err))
    end
end
return {tick=tick,reset=function() cleanup();restore_hidden() end}
end
