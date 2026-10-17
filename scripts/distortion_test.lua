-- Single-variable heat/refraction test. cvars_data.txt only loads UEVR's
-- predefined entries, which do not include r.DisableDistortion in this build.
-- Console-manager access avoids the incompatible UObject/world discovery.
local vr = uevr.params.vr
local functions = uevr.params.functions
local variable = nil
local timer = 0
local attempts = 0
local stopped = false
local verified = false

local function stop(message)
    stopped = true
    functions.log_warn("[FarFarWest distortion] " .. message)
end

local function apply_distortion_test()
    if variable == nil then
        local manager = uevr.api:get_console_manager()
        if manager ~= nil then variable = manager:find_variable("r.DisableDistortion") end
        if variable == nil then
            attempts = attempts + 1
            if attempts >= 10 then stop("Console variable unavailable; test not applied.") end
            return
        end
    end
    local before = variable:get_int()
    if (before ~= 0 and before ~= 1) or variable:get_float() ~= before then
        stop("Unexpected console-variable readback; test not applied.")
        return
    end
    if before ~= 1 then
        -- UE 5.8 ECVF_SetByConsole; read back the actual value after the request.
        variable:set_ex("1", 0x10000000)
        local after = variable:get_int()
        functions.log_info("[FarFarWest distortion] r.DisableDistortion " .. before .. " -> " .. after)
        if after ~= 1 then stop("Request did not take effect; stopping test."); return end
        verified = true
    elseif not verified then
        functions.log_info("[FarFarWest distortion] Verified r.DisableDistortion=1.")
        verified = true
    end
end

uevr.sdk.callbacks.on_pre_engine_tick(function(_, delta)
    if stopped or not vr.is_runtime_ready() or not vr.is_hmd_active() then return end
    timer = timer + math.min(math.max(delta or 0, 0), 0.1)
    if timer < 1 then return end
    timer = 0
    local ok, err = pcall(apply_distortion_test)
    if not ok then stop("Lua/API error: " .. tostring(err)) end
end)

functions.log_info("[FarFarWest distortion] Loaded; waiting to apply and verify r.DisableDistortion=1.")
