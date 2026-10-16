-- Keep the existing Quest B -> Escape mapping, and make its pause menu readable.
-- Use only UEVR runtime APIs: world/player lookups remain incompatible here.
local vr = uevr.params.vr
local functions = uevr.params.functions
local was_down = false

uevr.sdk.callbacks.on_pre_engine_tick(function()
    if not vr.is_runtime_ready() then
        was_down = false
        return
    end

    local action = vr.get_action_handle("/actions/default/in/BButtonRight")
    local down = vr.is_action_active(action, vr.get_right_joystick_source())
    if down and not was_down and not functions.is_drawing_ui() then
        if vr:get_mod_value("VR_2DScreenMode") ~= "true" then
            vr.set_mod_value("VR_2DScreenMode", "true")
            print("[FarFarWest] Pause screen enabled; F8 returns to immersive VR.")
        end
    end
    was_down = down
end)

print("[FarFarWest] Quest B pause-screen helper loaded.")
