-- Controller orientation aiming, with stick feedback for older backends.
-- Camera yaw feedback keeps head direction independent of the aiming hand.
-- The projected firing reticle and world markers use separate helpers.
local vr = uevr.params.vr
local functions = uevr.params.functions
local marker = io.open("controller_aim_backend.txt", "rb")
local supported = marker and marker:read("*a") == "ue5-camera-aim-pose-v1\n"
if marker then marker:close() end
if not supported then
    functions.log_warn("[FarFarWest aim] Backend bridge is not prepared; aiming helper skipped.")
    return
end

local position = UEVR_Vector3f.new()
local hand_rotation = UEVR_Quaternionf.new()
local offset_rotation = UEVR_Quaternionf.new()
local stick = UEVR_Vector2f.new()
local anchor = nil
local camera_yaw, camera_pitch = nil, nil
local camera_time = -1
local elapsed = 0
local logged = false
local stopped = false
local snap_latched = true
local tag_ok,tag = pcall(functions.get_tag)
local native_supported = tag_ok and tag == "ffw-ue58-sdk-v1"
local native_failed,native_reported = false,false
local statics,controller_class,viewport_class

local function wrap(angle) return (angle + 180) % 360 - 180 end
local function finite(value) return value == value and math.abs(value) < 1e8 end

-- SteamVR -Z forward, converted to UE yaw-right / pitch-up degrees.
local function angles(q)
    local norm = q.x*q.x + q.y*q.y + q.z*q.z + q.w*q.w
    if not finite(norm) or norm < 0.5 or norm > 1.5 then return nil end
    local x = -2 * (q.x*q.z + q.w*q.y) / norm
    local y = 2 * (q.w*q.x - q.y*q.z) / norm
    local z = 2 * (q.x*q.x + q.y*q.y) / norm - 1
    return math.deg(math.atan(x, -z)), math.deg(math.atan(y, math.sqrt(x*x + z*z)))
end

local function checked(class,name,size,fields)
    local fn=class:find_function(name)
    assert(fn and fn:get_properties_size()==size,"Unexpected function "..name)
    for field,offset in pairs(fields or {}) do
        local property=fn:find_property(field)
        assert(property and property:get_offset()==offset,"Unexpected parameter "..name.."."..field)
    end
end

local function apply_native(engine,yaw,pitch)
    if not native_supported or native_failed or not engine then return end
    local ok,err=pcall(function()
        if not statics then
            local class=uevr.api:find_uobject("Class /Script/Engine.GameplayStatics")
            controller_class=uevr.api:find_uobject("Class /Script/Engine.Controller")
            viewport_class=uevr.api:find_uobject("Class /Script/Engine.GameViewportClient")
            assert(class and controller_class and viewport_class,"Native aiming classes unavailable")
            checked(class,"GetPlayerController",24,{WorldContextObject=0,PlayerIndex=8,ReturnValue=16})
            checked(controller_class,"GetControlRotation",24,{ReturnValue=0})
            checked(controller_class,"SetControlRotation",24,{NewRotation=0})
            checked(controller_class,"IsLookInputIgnored",1)
            local pawn=controller_class:find_property("Pawn")
            assert(pawn and pawn:get_offset()==744,"Unexpected controller pawn layout")
            statics=class:get_class_default_object();assert(statics,"Gameplay library unavailable")
        end
        local field=engine:get_class():find_property("GameViewport")
        assert(field and field:get_offset()==3448,"Unexpected engine viewport layout")
        local viewport=engine:get_property("GameViewport")
        if not viewport then return end
        assert(viewport:is_a(viewport_class),"Unexpected native viewport context")
        -- Resolve the current controller through the game's native function.
        -- Do not cache a pawn or use the unsupported SDK engine/world lookup.
        local controller=statics:GetPlayerController(viewport,0)
        if not controller then return end
        assert(controller:is_a(controller_class),"Unexpected player controller")
        if not controller:get_property("Pawn") or controller:IsLookInputIgnored() then return end
        -- The typed double rotator round-trip is verified in this backend.
        -- A named Lua table did not preserve the same rotation in the live test.
        local target=controller:GetControlRotation()
        target.Pitch,target.Yaw,target.Roll=pitch,yaw,0
        controller:SetControlRotation(target)
        if not native_reported then
            native_reported=true
            functions.log_info("[FarFarWest aim] Right-controller pose now drives native control rotation.")
        end
    end)
    if not ok then
        native_failed=true
        functions.log_warn("[FarFarWest aim] Native rotation unavailable; using stick feedback: "..tostring(err))
    end
end

local function target_angles()
    local index=vr.get_right_controller_index()
    if index<1 or index>=64 then return nil end
    vr.get_pose(index,position,hand_rotation)
    local yaw,pitch=angles(hand_rotation)
    if yaw==nil then return nil end
    return wrap(anchor+yaw),math.max(-85,math.min(85,pitch))
end

local function gameplay()
    return _G.farfarwest_gameplay_ready == true
        and not stopped and vr.is_runtime_ready() and vr.is_hmd_active()
        and vr.is_using_controllers() and not functions.is_drawing_ui()
        and vr:get_mod_value("VR_2DScreenMode") == "false"
end

local function reset()
    anchor = nil
    camera_yaw, camera_pitch = nil, nil
    camera_time = -1
end

uevr.sdk.callbacks.on_pre_engine_tick(function(engine, delta)
    elapsed = elapsed + math.min(math.max(delta or 0, 0), 0.1)
    if not gameplay() then reset(); snap_latched = true; return end
    vr.get_joystick_axis(vr.get_right_joystick_source(), stick)
    if math.abs(stick.x) < 0.25 then
        snap_latched = false
    elseif math.abs(stick.x) > 0.65 and not snap_latched and anchor ~= nil then
        anchor = wrap(anchor + (stick.x > 0 and 45 or -45))
        snap_latched = true
    end
    if native_supported and not native_failed and anchor~=nil and camera_yaw~=nil and elapsed-camera_time<=.2 then
        local yaw,pitch=target_angles()
        if yaw~=nil then apply_native(engine,yaw,pitch) end
    end
end)

uevr.sdk.callbacks.on_early_calculate_stereo_view_offset(function(_, _, _, _, rotation, is_double)
    if not gameplay() then reset(); return end
    if not is_double then
        stopped = true
        reset()
        functions.log_warn("[FarFarWest aim] Expected UE5 double camera values; aiming stopped.")
        return
    end
    local pitch, yaw = rotation.x, rotation.y
    if not finite(pitch) or not finite(yaw) then return end
    camera_pitch, camera_yaw, camera_time = pitch, yaw, elapsed
    if anchor == nil then
        vr.get_rotation_offset(offset_rotation)
        local offset_yaw = angles(offset_rotation)
        if offset_yaw == nil then return end
        anchor = wrap(yaw + offset_yaw)
    end
    -- Compensate actual camera yaw, including while the game's look input
    -- catches up, so moving the aiming wrist does not turn the headset view.
    local radians = math.rad(-wrap(anchor - yaw)) * 0.5
    offset_rotation.x, offset_rotation.z = 0, 0
    offset_rotation.y, offset_rotation.w = math.sin(radians), math.cos(radians)
    vr.set_rotation_offset(offset_rotation)
end)

local function axis(error)
    if math.abs(error) < 0.25 then return 0 end
    -- Overcome the game's stick dead zone, then taper the turn toward target.
    local magnitude = 0.26 + 0.74 * math.min(math.abs(error) / 35, 1)
    return math.floor((error < 0 and -1 or 1) * 32767 * magnitude)
end

uevr.sdk.callbacks.on_xinput_get_state(function(_, user_index, state)
    if user_index ~= vr.get_lowest_xinput_index() or not gameplay()
        or anchor == nil or camera_yaw == nil or elapsed - camera_time > 0.2 then return end
    if native_supported and not native_failed then
        -- Native rotation already uses the controller pose. Suppress the
        -- synthetic look correction and leave all buttons/other axes intact.
        state.Gamepad.sThumbRX,state.Gamepad.sThumbRY=0,0
        return
    end
    local target_yaw,target_pitch=target_angles()
    if target_yaw==nil then return end
    state.Gamepad.sThumbRX = axis(wrap(target_yaw - camera_yaw))
    state.Gamepad.sThumbRY = axis(target_pitch - camera_pitch)
    if not logged then
        logged = true
        functions.log_info("[FarFarWest aim] Right-controller orientation now drives gamepad aiming.")
    end
end)

functions.log_info("[FarFarWest aim] Controller aiming helper loaded; waiting for immersive gameplay.")
