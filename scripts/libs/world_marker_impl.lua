return function()
-- Reproject the saloon's screen-space world markers through the rendered eye.
-- Keep the originals attached to their actors; use viewport copies while in VR.
local vr, functions, api = uevr.params.vr, uevr.params.functions, uevr.api
local ok, tag = pcall(functions.get_tag)
if not ok or tag ~= "ffw-ue58-sdk-v1" then return end
local loaded, geometry = pcall(require, "libs/reticle_projection")
if not loaded then functions.log_warn("[FarFarWest markers] Projection helper unavailable."); return end

local matrix = UEVR_Matrix4x4f.new()
local array, component_class, widget_class, factory, layout
local entries, camera, entry_count = {}, nil, 0
local elapsed, next_scan, scan_index = 0, 0, nil
local stage = "startup"
local stopped, reported = false, false
local kinds = {
    UI_WorldIcon_C={owner="^BP_WorldIcon_C_", image="Image_Icon", offset=808},
    UI_Guide_C={owner="^BP_LobbyGuide_C_", image="Image_Aura", offset=824, guide=true},
}
local function info(s) functions.log_info("[FarFarWest markers] "..s) end
local function finite(n) return type(n)=="number" and n==n and math.abs(n)<1e12 end
local function active()
    return _G.farfarwest_gameplay_ready == true and vr.is_runtime_ready()
        and vr.is_hmd_active() and not functions.is_drawing_ui()
        and vr:get_mod_value("VR_2DScreenMode") == "false"
end

local function track(object)
    local index = object:read_dword(12) -- Verified UObject internal index in this guarded build.
    assert(index<array:get_object_count(), "Object index outside the verified array")
    local ref = {object=object, index=index, address=object:get_address(), name=object:get_short_name()}
    assert(array:get_object(index):get_address()==ref.address, "Object identity mismatch")
    return ref
end
local function valid(ref)
    if not ref then return false end
    local object = array:get_object(ref.index)
    return object and object:get_address()==ref.address and object:get_short_name()==ref.name
end
local function component_valid(entry)
    if not valid(entry.component) or not valid(entry.source) or not valid(entry.owner) then return false end
    local widget = entry.component.object:get_property("Widget")
    return widget and widget:get_address()==entry.source.address
end
local function restore(entry)
    if valid(entry.proxy) then entry.proxy.object:RemoveFromParent() end
    if entry.hidden and valid(entry.source) then
        entry.source.object:SetRenderOpacity(entry.opacity)
    end
    entry.hidden = false
end
local function reset()
    for _, entry in pairs(entries) do pcall(restore, entry) end
    entries, camera, next_scan, scan_index, entry_count = {}, nil, 0, nil, 0
end
local function guarded(fn)
    if stopped then return end
    local success, err = pcall(fn)
    if not success then
        reset(); stopped=true
        functions.log_warn("[FarFarWest markers] Stopped safely during "..stage..": "..tostring(err))
    end
end

local function checked(class, name, minimum, maximum)
    local fn = class:find_function(name)
    assert(fn, "Missing function "..name)
    local size = fn:get_properties_size()
    assert(size>=minimum and size<=maximum, "Unexpected parameter size: "..name)
    local field, count = fn:get_child_properties(), 0
    while field do
        count=count+1; assert(count<=32, "Unexpected parameter chain: "..name)
        local property=fn:find_property(field:get_fname():to_string())
        assert(property and property:get_offset()>=0 and property:get_offset()<size,
            "Invalid function metadata: "..name)
        field=field:get_next()
    end
end
local function default_object(path)
    local class=api:find_uobject("Class "..path)
    assert(class, "Missing class "..path)
    local object=class:get_class_default_object()
    assert(object, "Missing default object "..path)
    return object,class
end
local function prepare()
    array=api:get_uobject_array()
    assert(array and array.get_objects_offset()==0 and array.get_item_distance()==24,
        "Compact object array unavailable")
    component_class=api:find_uobject("Class /Script/UMG.WidgetComponent")
    widget_class=api:find_uobject("Class /Script/UMG.UserWidget")
    local image_class=api:find_uobject("Class /Script/UMG.Image")
    assert(component_class and widget_class and image_class, "UMG classes unavailable")
    for name,offset in pairs({Space=1512,WidgetClass=1520,Pivot=1568,Widget=1800}) do
        local p=component_class:find_property(name)
        assert(p and p:get_offset()==offset,"WidgetComponent layout mismatch: "..name)
    end
    checked(component_class,"K2_GetComponentLocation",24,24)
    checked(component_class,"GetOwner",8,8)
    checked(widget_class,"GetOwningPlayer",8,8)
    checked(widget_class,"GetDesiredSize",16,16)
    checked(widget_class,"ForceLayoutPrepass",0,0)
    checked(widget_class,"AddToViewport",4,4)
    checked(widget_class,"RemoveFromParent",0,0)
    checked(widget_class,"SetAlignmentInViewport",16,16)
    checked(widget_class,"SetDesiredSizeInViewport",16,16)
    checked(widget_class,"SetPositionInViewport",17,32)
    checked(widget_class,"SetRenderOpacity",4,4)
    checked(widget_class,"SetVisibility",1,1)
    checked(image_class,"SetBrush",64,512)
    checked(image_class,"SetColorAndOpacity",16,16)
    local class
    factory,class=default_object("/Script/UMG.WidgetBlueprintLibrary")
    checked(class,"Create",32,32)
    layout,class=default_object("/Script/UMG.WidgetLayoutLibrary")
    checked(class,"GetViewportSize",24,24)
    info("WidgetComponent layout and viewport functions verified.")
end

local function inspect_component(component)
    stage="read marker component owner"
    local outer=component:get_outer()
    if not outer then return end
    local owner_name=outer:get_short_name()
    if not owner_name:match("^BP_WorldIcon_C_") and not owner_name:match("^BP_LobbyGuide_C_") then return end
    stage="read marker widget property"
    local source=component:get_property("Widget")
    stage="read marker widget class"
    if not source then return end
    local kind=kinds[source:get_class():get_short_name()]
    if not kind or not owner_name:match(kind.owner) then return end
    stage="read marker component visibility"
    -- The typed bool getter throws on this backend; reflected reads work for
    -- both the component's bVisible and the actor's bHidden bitfields.
    if source
        and component:read_byte(1512)==1 and component:get_property("bVisible")
        and not entries[component:get_address()] then
        stage="validate world-icon widget"
        assert(entry_count<64,"Too many world icons")
        local p=source:get_class():find_property(kind.image)
        assert(p and p:get_offset()==kind.offset,"World-marker image layout mismatch")
        if kind.guide then
            local text=source:get_class():find_property("InteractText")
            assert(text and text:get_offset()==840,"Lobby-guide text layout mismatch")
            -- Create runs the guide's Construct with its class-default label.
            -- Leave customized variants untouched: Lua cannot safely copy FText.
            local default=source:get_class():get_class_default_object()
            if source:read_qword(840)~=default:read_qword(840)
                or source:read_qword(848)~=default:read_qword(848) then return end
        end
        local size=source:GetDesiredSize()
        if not size or size.X<=0 or size.Y<=0 then
            source:ForceLayoutPrepass() -- Also size icons outside the gun camera's view.
            size=source:GetDesiredSize()
        end
        if size and finite(size.X) and finite(size.Y) and size.X>0 and size.Y>0 then
            local owner=component:GetOwner()
            assert(owner and owner:get_class():find_property("bHidden"),"World-icon owner unavailable")
            local opacity=source:get_float_property("RenderOpacity")
            assert(finite(opacity),"Invalid world-icon opacity")
            local entry={component=track(component),source=track(source),owner=track(owner),opacity=opacity,hidden=false,kind=kind}
            entries[component:get_address()]=entry -- Cleanup owns every subsequent mutation.
            entry_count=entry_count+1
            stage="create viewport icon"
            local proxy=factory:Create(source,source:get_class(),source:GetOwningPlayer())
            assert(proxy and proxy:is_a(widget_class),"Cannot create world-icon viewport copy")
            entry.proxy=track(proxy)
            entry.icon=proxy:get_property(kind.image)
            assert(entry.icon,"World-icon image is missing")
            stage="attach viewport icon"
            proxy:SetRenderOpacity(0)
            proxy:AddToViewport(component:get_int_property("LayerZOrder"))
            local pivot=component:get_property("Pivot")
            proxy:SetAlignmentInViewport({X=pivot.X,Y=pivot.Y})
            proxy:SetDesiredSizeInViewport({X=size.X,Y=size.Y})
            proxy:SetVisibility(3) -- HitTestInvisible: markers never intercept input.
            entry.hidden=true
            source:SetRenderOpacity(0)
            entry.style_time=0
            info("Tracking world icon at "..tostring(component:get_address()).." ("..source:get_class():get_short_name().."); native icon hidden.")
        end
    end
end

local function discover()
    if elapsed<next_scan then return end
    stage="scan object array"
    local count=array:get_object_count()
    assert(count>0 and count<=250000,"Object count outside the verified budget")
    if scan_index==nil or scan_index>=count then scan_index=count-1 end
    -- get_objects_matching activates UObjectHook; use the proven reticle path.
    for _=1,512 do
        if scan_index<0 then scan_index=nil; next_scan=elapsed+1; return end
        local object=array:get_object(scan_index)
        scan_index=scan_index-1
        if object and object:get_short_name()=="Widget" and object:is_a(component_class) then
            inspect_component(object)
        end
    end
end

local callbacks = {}
callbacks.camera = function(_,_,_,position,rotation,is_double)
    guarded(function()
        if not active() then return end
        stage="read eye camera"
        assert(is_double,"Expected UE5 double camera values")
        vr.get_ue_projection_matrix(-1,matrix)
        local projection={}
        for col=0,3 do
            projection[col]={}
            for row=0,3 do projection[col][row]=matrix:get(col,row) end
        end
        camera={position={x=position.x,y=position.y,z=position.z},
            rotation={x=rotation.x,y=rotation.y,z=rotation.z},matrix=projection,time=elapsed}
    end)
end

callbacks.tick = function(_,delta)
    guarded(function()
        elapsed=elapsed+math.min(math.max(delta or 0,0),.1)
        if not active() then reset(); return end
        if not array then stage="verify widget API"; prepare() end
        discover()
        for address,entry in pairs(entries) do
            stage="validate tracked icon"
            if not component_valid(entry) or not valid(entry.proxy) then
                restore(entry); entries[address]=nil; entry_count=entry_count-1
            else
                local proxy=entry.proxy.object
                local viewport=layout:GetViewportSize(proxy)
                local ready=camera and elapsed-camera.time<=.2
                    and viewport and viewport.X>0 and viewport.Y>0
                    and entry.component.object:get_property("bVisible")
                    and not entry.owner.object:get_property("bHidden")
                local visibility=entry.source.object:get_property("Visibility")
                ready=ready and visibility~=1 and visibility~=2 -- Collapsed/Hidden.
                local opacity=entry.source.object:get_float_property("RenderOpacity")
                if opacity~=0 then
                    assert(finite(opacity),"Invalid world-icon opacity")
                    entry.opacity=opacity
                    entry.source.object:SetRenderOpacity(0)
                end
                if not ready then proxy:SetRenderOpacity(0)
                else
                    local point=entry.component.object:K2_GetComponentLocation()
                    local pixel=geometry.project({x=point.X,y=point.Y,z=point.Z},camera.position,
                        camera.rotation,camera.matrix,viewport.X,viewport.Y)
                    if pixel and pixel.inside then
                        if elapsed>=entry.style_time then
                            local source_icon=entry.source.object:get_property(entry.kind.image)
                            assert(source_icon,"Original world-icon image is missing")
                            stage="copy icon appearance"
                            entry.icon:SetBrush(source_icon:get_property("Brush"))
                            entry.icon:SetColorAndOpacity(source_icon:get_property("ColorAndOpacity"))
                            entry.style_time=elapsed+.25
                        end
                        stage="position viewport icon"
                        proxy:SetPositionInViewport({X=pixel.x,Y=pixel.y},true)
                        proxy:SetRenderOpacity(entry.opacity)
                        if not reported then
                            reported=true
                            info("World icons now use headset projection on both axes, independently of aiming.")
                        end
                    else proxy:SetRenderOpacity(0) end
                end
            end
        end
    end)
end
callbacks.reset = reset
info("Helper loaded; vendor icons and default lobby guides are replaced during immersive play.")

return callbacks
end
