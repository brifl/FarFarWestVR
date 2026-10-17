-- Move the game's existing crosshair to the firing camera's traced target.
-- Object access is restricted to the source-built, guarded UE5.8 backend.
local vr, functions, api = uevr.params.vr, uevr.params.functions, uevr.api
local tag_ok, tag = pcall(functions.get_tag)
if not tag_ok or tag ~= "ffw-ue58-sdk-v1" then
    functions.log_info("[FarFarWest reticle] Waiting for the UE5.8 SDK backend; helper skipped.")
    return
end
local math_ok, geometry = pcall(require, "libs/reticle_projection")
if not math_ok then
    functions.log_warn("[FarFarWest reticle] Geometry helper unavailable; helper skipped.")
    return
end

local projection = UEVR_Matrix4x4f.new()
local array, image_class, user_widget_class, slate, layout, system
local image, image_index, image_address, owner, pawn, original
local calibration, viewport_width, viewport_height, local_width, local_height
local raw_camera, eye_camera, scan_index
local elapsed, next_scan, next_mode = 0, 0, 0
local enabled, written, stopped, reported = true, false, false, false

local function finite(n) return type(n)=="number" and n==n and math.abs(n)<1e12 end
local function vec(v) return {x=v.x, y=v.y, z=v.z} end
local function ue(v) return {X=v.x, Y=v.y, Z=v.z} end
local function info(message) functions.log_info("[FarFarWest reticle] "..message) end

local function active()
    return _G.farfarwest_gameplay_ready == true and vr.is_runtime_ready()
        and vr.is_hmd_active() and not functions.is_drawing_ui()
        and vr:get_mod_value("VR_2DScreenMode") == "false"
end

local function valid_image()
    if not image or not array then return false end
    local current = array:get_object(image_index)
    return current and current:get_address()==image_address
        and current:get_short_name()=="Crosshair_Top"
end

local function restore()
    if written and valid_image() then
        image:SetRenderTranslation({X=original.x, Y=original.y})
        image:SetRenderOpacity(original.opacity)
    end
    written = false
end

local function reset()
    restore()
    image, owner, pawn, original, calibration, scan_index = nil, nil, nil, nil, nil, nil
    raw_camera, eye_camera = nil, nil
end

local function guarded(fn)
    if stopped then return end
    local ok, err = pcall(fn)
    if not ok then
        pcall(restore)
        stopped = true
        functions.log_warn("[FarFarWest reticle] Stopped safely: "..tostring(err))
    end
end

local function function_checked(class, name, minimum, maximum)
    local fn = class:find_function(name)
    assert(fn, "Missing function "..name)
    local size = fn:get_properties_size()
    assert(size>=minimum and size<=maximum, "Unexpected parameter size for "..name)
    local field, count = fn:get_child_properties(), 0
    while field do
        count = count+1
        assert(count<=32, "Unexpected parameter chain for "..name)
        local property = fn:find_property(field:get_fname():to_string())
        assert(property, "Parameter metadata missing for "..name)
        local offset = property:get_offset()
        assert(offset>=0 and offset<size, "Invalid parameter offset for "..name)
        field = field:get_next()
    end
end

local function default_object(path)
    local class = api:find_uobject("Class "..path)
    assert(class, "Missing class "..path)
    local object = class:get_class_default_object()
    assert(object, "Missing default object "..path)
    return object, class
end

local function prepare_api()
    array = api:get_uobject_array()
    assert(array and array.get_objects_offset()==0 and array.get_item_distance()==24,
        "Compact object-array access is unavailable")
    image_class = api:find_uobject("Class /Script/UMG.Image")
    user_widget_class = api:find_uobject("Class /Script/UMG.UserWidget")
    assert(image_class and user_widget_class, "UMG classes unavailable")
    for name, offset in pairs({RenderTransform=0x90, RenderOpacity=0xe0, Slot=0x30}) do
        local property = image_class:find_property(name)
        assert(property and property:get_offset()==offset, "Widget layout mismatch: "..name)
    end
    function_checked(image_class, "SetRenderTranslation", 16, 16)
    function_checked(image_class, "SetRenderOpacity", 4, 4)
    function_checked(image_class, "GetCachedGeometry", 32, 256)
    function_checked(user_widget_class, "GetOwningPlayerPawn", 8, 8)
    local class
    slate, class = default_object("/Script/UMG.SlateBlueprintLibrary")
    function_checked(class, "GetLocalSize", 32, 512)
    function_checked(class, "LocalToViewport", 64, 512)
    layout, class = default_object("/Script/UMG.WidgetLayoutLibrary")
    function_checked(class, "GetViewportSize", 24, 24)
    system, class = default_object("/Script/Engine.KismetSystemLibrary")
    function_checked(class, "LineTraceSingle", 128, 1024)
    info("SDK widget layout and function parameters verified.")
end

local function bind_image()
    if elapsed<next_scan then return end
    local count = array:get_object_count()
    assert(count>0 and count<=250000, "Object count outside the probe budget")
    if scan_index==nil or scan_index>=count then scan_index=count-1 end
    for _=1,256 do
        if scan_index<0 then scan_index=nil; next_scan=elapsed+1; return end
        local index = scan_index
        scan_index = scan_index-1
        local object = array:get_object(index)
        if object and object:get_short_name()=="Crosshair_Top" and object:is_a(image_class) then
            local tree = object:get_outer()
            local candidate_owner = tree and tree:get_outer()
            if candidate_owner and candidate_owner:is_a(user_widget_class)
                and not candidate_owner:get_short_name():find("Default__", 1, true) then
                local candidate_pawn = candidate_owner:GetOwningPlayerPawn()
                if candidate_pawn then
                    local transform = object:get_property("RenderTransform")
                    assert(math.abs(transform.Angle)<0.001 and math.abs(transform.Shear.X)<0.001
                        and math.abs(transform.Shear.Y)<0.001, "Rotated/sheared crosshair needs separate calibration")
                    original = {x=transform.Translation.X, y=transform.Translation.Y,
                        opacity=object:get_float_property("RenderOpacity")}
                    assert(finite(original.x) and finite(original.y) and finite(original.opacity), "Invalid crosshair defaults")
                    image, image_index, image_address = object, index, object:get_address()
                    owner, pawn, calibration = candidate_owner, candidate_pawn, nil
                    info("Found live Crosshair_Top; calibrating its viewport geometry.")
                    return
                end
            end
        end
    end
end

local function pixel_at(cached, x, y)
    local pixel, viewport = {}, {}
    slate:LocalToViewport(owner, cached, {X=x, Y=y}, pixel, viewport)
    assert(pixel.result and finite(pixel.result.X) and finite(pixel.result.Y), "Invalid viewport geometry")
    return {x=pixel.result.X, y=pixel.result.Y}
end

local function calibrate(cached, size)
    local transform = image:get_property("RenderTransform")
    local x, y = size.X/2, size.Y/2
    calibration = geometry.calibrate(pixel_at(cached,x,y), pixel_at(cached,x+1,y),
        pixel_at(cached,x,y+1), transform.Scale.X, transform.Scale.Y)
    assert(calibration, "Degenerate crosshair geometry")
    local_width, local_height = size.X, size.Y
    info(string.format("Viewport %.0fx%.0f; crosshair center %.1f, %.1f; geometry verified.",
        viewport_width, viewport_height, calibration.x, calibration.y))
end

uevr.sdk.callbacks.on_early_calculate_stereo_view_offset(function(_, _, _, position, rotation, is_double)
    guarded(function()
        if not active() then return end
        assert(is_double, "Expected UE5 double camera values")
        raw_camera = {position=vec(position), rotation=vec(rotation), time=elapsed}
    end)
end)

uevr.sdk.callbacks.on_post_calculate_stereo_view_offset(function(_, _, _, position, rotation, is_double)
    guarded(function()
        if not active() then return end
        assert(is_double, "Expected UE5 double camera values")
        -- Source backend extension: -1 selects this frame's actual stereo eye.
        vr.get_ue_projection_matrix(-1, projection)
        local matrix = {}
        for column=0,3 do
            matrix[column] = {}
            for row=0,3 do matrix[column][row]=projection:get(column,row) end
        end
        eye_camera = {position=vec(position), rotation=vec(rotation), matrix=matrix, time=elapsed}
    end)
end)

uevr.sdk.callbacks.on_post_engine_tick(function(_, delta)
    guarded(function()
        elapsed = elapsed+math.min(math.max(delta or 0,0),0.1)
        if elapsed>=next_mode then
            local file = io.open("reticle_mode.txt", "rb")
            local mode = file and file:read("*a") or "enabled"
            if file then file:close() end
            enabled = not mode:match("^probe")
            next_mode = elapsed+0.5
        end
        if not active() then reset(); return end
        if not array then prepare_api() end
        if image and not valid_image() then reset() end
        if not image then bind_image(); return end
        local viewport = layout:GetViewportSize(owner)
        if not viewport or viewport.X<=0 or viewport.Y<=0 then return end
        if viewport_width~=viewport.X or viewport_height~=viewport.Y then
            restore(); calibration=nil
            viewport_width, viewport_height = viewport.X, viewport.Y
            return -- Allow cached geometry to reflect the restored translation.
        end
        local cached = image:GetCachedGeometry()
        local size = slate:GetLocalSize(cached)
        if not size or size.X<=0 or size.Y<=0 then return end
        if calibration and (size.X~=local_width or size.Y~=local_height) then
            restore(); calibration=nil; return
        end
        if not calibration then calibrate(cached,size); return end
        if not enabled then restore(); reported=false; return end
        if not raw_camera or not eye_camera or elapsed-raw_camera.time>0.2 or elapsed-eye_camera.time>0.2 then
            image:SetRenderOpacity(0)
            written = true
            return
        end
        local endpoint = geometry.ray_end(raw_camera.position, raw_camera.rotation, 100000)
        assert(endpoint, "Invalid firing camera")
        local hit = {}
        local blocked = system:LineTraceSingle(pawn, ue(raw_camera.position), ue(endpoint), 0,
            false, {pawn}, 0, hit, true, {R=0,G=0,B=0,A=0}, {R=0,G=0,B=0,A=0}, 0)
        local point = endpoint
        if blocked then
            assert(hit.result, "Trace result was not returned")
            local impact = hit.result.ImpactPoint
            point = {x=impact.X, y=impact.Y, z=impact.Z}
        end
        local pixel = geometry.project(point, eye_camera.position, eye_camera.rotation,
            eye_camera.matrix, viewport_width, viewport_height)
        if not pixel or not pixel.inside then
            image:SetRenderOpacity(0)
            written = true
            return
        end
        local translation = geometry.translation(calibration,pixel,original.x,original.y)
        assert(translation, "Invalid reticle projection")
        image:SetRenderTranslation(translation)
        image:SetRenderOpacity(original.opacity)
        written = true
        if not reported then
            info("Original crosshair now follows the traced firing-camera target in each eye.")
            reported = true
        end
    end)
end)

uevr.sdk.callbacks.on_script_reset(function() pcall(restore) end)
info("Helper loaded; validates HUD access and geometry before moving the crosshair.")
