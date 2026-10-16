-- Quest B keeps its Escape binding and toggles screen mode in BOTH directions.
-- F8 remains an optional fallback. No world/player lookups are used here.
local vr = uevr.params.vr
local functions = uevr.params.functions
local was_down = false
local last_mode = nil
local ready_time = 0
local saved_rotation = nil

local function update_screen(screen)
    if screen then
        if last_mode == false then
            saved_rotation = UEVR_Quaternionf.new()
            vr.get_rotation_offset(saved_rotation)
        end
        vr.recenter_view()
    elseif saved_rotation ~= nil then
        vr.set_rotation_offset(saved_rotation)
        saved_rotation = nil
    end
    last_mode = screen
    functions.log_info(screen and "[FarFarWest] Screen view enabled. B returns to immersive VR."
        or "[FarFarWest] Immersive view restored.")
end

uevr.sdk.callbacks.on_pre_engine_tick(function(_, delta)
    if not vr.is_runtime_ready() then
        was_down = false
        last_mode = nil
        ready_time = 0
        saved_rotation = nil
        return
    end
    if not vr.is_hmd_active() then
        return
    end

    -- Let the first tracked poses settle before centering the startup screen.
    ready_time = ready_time + math.min(math.max(delta or 0, 0), 0.1)
    if last_mode == nil and ready_time < 0.5 then
        return
    end

    local screen = vr:get_mod_value("VR_2DScreenMode") == "true"
    if screen ~= last_mode then
        update_screen(screen)
    end
    local action = vr.get_action_handle("/actions/default/in/BButtonRight")
    local down = vr.is_action_active(action, vr.get_right_joystick_source())
    if down and not was_down and not functions.is_drawing_ui() then
        vr.set_mod_value("VR_2DScreenMode", screen and "false" or "true")
        update_screen(not screen)
    end
    was_down = down
end)

functions.log_info("[FarFarWest] Two-way Quest B screen helper loaded.")
