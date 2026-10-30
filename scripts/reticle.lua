local object_count=require('libs/object_count')
-- Move the game's existing crosshair to the firing camera's traced target.
-- Object access is restricted to the source-built, guarded UE5.8 backend.
local vr, functions, api = uevr.params.vr, uevr.params.functions, uevr.api
local tag_ok, tag = pcall(functions.get_tag)
if not tag_ok or tag ~= "ffw-ue58-sdk-v1" then
    functions.log_info("[FarFarWest reticle] Waiting for the UE5.8 SDK backend; helper skipped.")
    return
end
local math_ok, geometry = pcall(require, "libs/reticle_projection")
local shape_ok, ui_shape = pcall(require, "libs/ui_shape")
if not math_ok or not shape_ok then
    functions.log_warn("[FarFarWest reticle] Projection/shape helper unavailable; helper skipped.")
    return
end

local projection = UEVR_Matrix4x4f.new()
local array, image_class, user_widget_class, slate, layout, system
local image, image_index, image_address, owner, owner_ref, original
local shape
local style=require('libs/reticle_style')()
local calibration, viewport_width, viewport_height, local_width, local_height
local raw_camera, eye_camera, scan_index
local elapsed, next_scan, next_mode = 0, 0, 0
local enabled, written, stopped, reported = true, false, false, false
local suspended=false
local stage = "startup"

local function finite(n) return type(n)=="number" and n==n and math.abs(n)<1e12 end
local function vec(v) return {x=v.x, y=v.y, z=v.z} end
local function ue(v) return {X=v.x, Y=v.y, Z=v.z} end
local function info(message) functions.log_info("[FarFarWest reticle] "..message) end

local function active()
    return _G.farfarwest_gameplay_ready == true and vr.is_runtime_ready()
        and vr.is_hmd_active() and not functions.is_drawing_ui()
        and vr:get_mod_value("VR_2DScreenMode") == "false"
end

local function track(object)
    local index = object:read_dword(12) -- Verified UObject index in the guarded backend.
    if index >= array:get_object_count() then return nil end
    local current = array:get_object(index)
    if not current or current:get_address()~=object:get_address() then return nil end
    return {index=index, address=current:get_address(), name=current:get_short_name()}
end

local function valid_owner()
    if not owner_ref then return false end
    local current = array:get_object(owner_ref.index)
    return current and current:get_address()==owner_ref.address
        and current:get_short_name()==owner_ref.name
end

local function valid_image()
    if not image or not array then return false end
    local current = array:get_object(image_index)
    return current and current:get_address()==image_address
        and current:get_short_name()=="Crosshair_Top"
end

local function restore()
    style.restore()
    if shape and valid_image() then ui_shape.restore(shape) end
    if written and valid_image() then
        image:SetRenderTranslation({X=original.x, Y=original.y})
        image:SetRenderOpacity(original.opacity)
    end
    written = false
end

local function reset()
    restore()
    image, owner, owner_ref, original, calibration, scan_index = nil, nil, nil, nil, nil, nil
    shape=nil
    raw_camera, eye_camera = nil, nil
end

local function guarded(fn)
    if stopped then return end
    local ok, err = pcall(fn)
    if not ok then
        pcall(restore)
        stopped = true
        functions.log_warn("[FarFarWest reticle] Stopped safely during "..stage..": "..tostring(err))
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
    function_checked(image_class, "SetRenderScale", 16, 16)
    function_checked(image_class, "SetRenderTransformPivot", 16, 16)
    function_checked(image_class, "GetDesiredSize", 16, 16)
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
    local count=object_count(array)
    if scan_index==nil or scan_index>=count then scan_index=count-1 end
    for _=1,256 do
        if scan_index<0 then scan_index=nil; next_scan=elapsed+1; return end
        local index = scan_index
        scan_index = scan_index-1
        local object = array:get_object(index)
        if object and object:get_short_name()=="Crosshair_Top" and object:is_a(image_class) then
            local tree = object:get_outer()
            local candidate_owner = tree and tree:get_outer()
            local candidate_ref = candidate_owner and track(candidate_owner)
            if candidate_ref and candidate_owner:is_a(user_widget_class)
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
                    owner, owner_ref, calibration = candidate_owner, candidate_ref, nil
                    shape=ui_shape.bind(image,{X=.5,Y=.5})
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
        stage = "read firing camera"
        if not active() then return end
        assert(is_double, "Expected UE5 double camera values")
        raw_camera = {position=vec(position), rotation=vec(rotation), time=elapsed}
    end)
end)

uevr.sdk.callbacks.on_post_calculate_stereo_view_offset(function(_, _, _, position, rotation, is_double)
    guarded(function()
        stage = "read eye camera and projection"
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
        stage = "check gameplay state"
        elapsed = elapsed+math.min(math.max(delta or 0,0),0.1)
        if elapsed>=next_mode then
            local file = io.open("reticle_mode.txt", "rb")
            local mode = file and file:read("*a") or "enabled"
            if file then file:close() end
            enabled = not mode:match("^probe")
            next_mode = elapsed+0.5
        end
        if not active() then
            -- Modal screens often leave this HUD alive. Retain its validated
            -- identity so Resume does not start another whole-array search.
            if not suspended then
                restore();calibration=nil;raw_camera,eye_camera=nil,nil;suspended=true
            end
            return
        end
        suspended=false
        stage = "prepare widget API"
        if not array then prepare_api() end
        stage = "validate or discover crosshair"
        if image and (not valid_image() or not valid_owner()) then reset() end
        if not image then bind_image(); return end
        -- Mounting/dismounting replaces the possessed pawn while the HUD can
        -- survive. Never retain the old pawn across ticks or trace with it
        -- after garbage collection. Cinematics may temporarily leave no pawn.
        stage = "read current owning pawn"
        local pawn = owner:GetOwningPlayerPawn()
        if not pawn then
            image:SetRenderOpacity(0)
            written = true
            raw_camera, eye_camera = nil, nil
            return
        end
        stage = "read crosshair viewport"
        local viewport = layout:GetViewportSize(owner)
        if not viewport or viewport.X<=0 or viewport.Y<=0 then return end
        if viewport_width~=viewport.X or viewport_height~=viewport.Y then
            restore(); calibration=nil
            viewport_width, viewport_height = viewport.X, viewport.Y
            return -- Allow cached geometry to reflect the restored translation.
        end
        stage = "read crosshair geometry"
        local cached = image:GetCachedGeometry()
        local size = slate:GetLocalSize(cached)
        if not size or size.X<=0 or size.Y<=0 then return end
        if calibration and (size.X~=local_width or size.Y~=local_height) then
            restore(); calibration=nil; return
        end
        if not calibration then calibrate(cached,size); return end
        if not enabled then restore(); reported=false; return end
        style.apply(image,owner)
        if not raw_camera or not eye_camera or elapsed-raw_camera.time>0.2 or elapsed-eye_camera.time>0.2 then
            image:SetRenderOpacity(0)
            written = true
            return
        end
        local endpoint = geometry.ray_end(raw_camera.position, raw_camera.rotation, 100000)
        assert(endpoint, "Invalid firing camera")
        local hit = {}
        stage = "trace firing target using current pawn"
        local blocked = system:LineTraceSingle(pawn, ue(raw_camera.position), ue(endpoint), 0,
            false, {pawn}, 0, hit, true, {R=0,G=0,B=0,A=0}, {R=0,G=0,B=0,A=0}, 0)
        local point = endpoint
        if blocked then
            assert(hit.result, "Trace result was not returned")
            local impact = hit.result.ImpactPoint
            point = {x=impact.X, y=impact.Y, z=impact.Z}
        end
        stage = "project and position crosshair"
        local pixel = geometry.project(point, eye_camera.position, eye_camera.rotation,
            eye_camera.matrix, viewport_width, viewport_height)
        if not pixel or not pixel.inside then
            image:SetRenderOpacity(0)
            written = true
            return
        end
        local translation = geometry.translation(calibration,pixel,original.x,original.y)
        assert(translation, "Invalid reticle projection")
        written = true -- Cleanup owns partial translation/shape setter failures.
        image:SetRenderTranslation(translation)
        image:SetRenderOpacity(original.opacity)
        stage='normalize crosshair shape'
        ui_shape.apply(shape,ui_shape.height_factor(eye_camera.matrix,viewport_width,viewport_height))
        if not reported then
            info("Original crosshair now follows the traced firing-camera target in each eye.")
            reported = true
        end
    end)
end)

uevr.sdk.callbacks.on_script_reset(function() pcall(restore) end)
info("Helper loaded; validates HUD access and reads the current owning pawn each tick.")
