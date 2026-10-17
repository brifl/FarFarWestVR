-- Deferred experiment. Outside scripts/ so it does not run in the profile.
-- One-variable comfort test: replace temporal AA with FXAA while UEVR runs.
-- Use the console-variable interface on the engine thread, not cvar-data scans
-- or UObject/world discovery. UE 5.8 ECVF_SetByConsole is 0x10000000:
-- https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Core/EConsoleVariableFlags
local vr = uevr.params.vr
local functions = uevr.params.functions
local variable = nil
local timer = 0
local attempts = 0
local stopped = false
local verified = false

local function stop(message)
    stopped = true
    functions.log_warn("[FarFarWest AA test] " .. message)
end

local function check_aa()
    if variable == nil then
        local manager = uevr.api:get_console_manager()
        if manager ~= nil then
            variable = manager:find_variable("r.AntiAliasingMethod")
        end
        if variable == nil then
            attempts = attempts + 1
            if attempts >= 10 then stop("Console variable unavailable; test not applied.") end
            return
        end
    end

    local before = variable:get_int()
    -- Check both documented getters before calling the native setter.
    if variable:get_float() ~= before or before < 0 or before > 4 then
        stop("Unexpected console-variable readback; test not applied.")
        return
    end
    if before == 0 or before == 3 then
        stop("AA is already non-temporal (" .. before .. "); leaving it unchanged.")
        return
    end
    if before ~= 1 then
        variable:set_ex("1", 0x10000000)
        local after = variable:get_int()
        functions.log_info("[FarFarWest AA test] r.AntiAliasingMethod " .. before .. " -> " .. after)
        if after ~= 1 then stop("FXAA request did not take effect; stopping test."); return end
        verified = true
    elseif not verified then
        functions.log_info("[FarFarWest AA test] r.AntiAliasingMethod already 1 (FXAA).")
        verified = true
    end
end

uevr.sdk.callbacks.on_pre_engine_tick(function(_, delta)
    if stopped or not vr.is_runtime_ready() or not vr.is_hmd_active() then return end
    timer = timer + math.min(math.max(delta or 0, 0), 0.1)
    if timer < 1 then return end
    timer = 0
    -- A missing Lua binding should leave the working menu helper running.
    local ok, err = pcall(check_aa)
    if not ok then stop("Lua/API error: " .. tostring(err)) end
end)

functions.log_info("[FarFarWest AA test] Loaded; FXAA readback will be logged after runtime startup.")
