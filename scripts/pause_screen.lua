-- Follow the game's input mode, including Resume clicks and submenu navigation.
-- LogViewport is enabled by the menu-logging preset. No UObject/world lookup.
local vr = uevr.params.vr
local functions = uevr.params.functions
-- UEVR removes os.getenv and permits file access only within profile/data.
-- tools/prepare_menu_helper.py creates a native Windows link to the game log.
local log_path = "FarFarWest.log"
local log_position = nil
local partial_line = ""
local capture_seen = false
local menu_state = nil
local applied_state = nil
local poll_time = 0
local last_mode = nil
local ready_time = 0
local saved_rotation = nil

local function observe_line(line)
    if not line:find("LogViewport:", 1, true) then return end
    local capture = line:match("Viewport MouseCaptureMode Changed, .- %-> ([%w_:]+)")
    if capture then
        capture = capture:match("([^:]+)$")
        local menu
        if capture == "NoCapture" or capture == "CaptureDuringMouseDown"
            or capture == "CaptureDuringRightMouseDown" then
            menu = true
        elseif capture == "CapturePermanently" or capture == "CapturePermanently_IncludingInitialMouseDown" then
            menu = false
        end
        if menu ~= nil then
            capture_seen = true
            menu_state = menu
            functions.log_info("[FarFarWest] Game mouse capture: " .. capture)
        end
    elseif not capture_seen then
        -- Use cursor visibility only until an explicit input capture mode exists.
        local cursor = line:match("Player bShowMouseCursor Changed, .- %-> ([%w]+)")
        if cursor then
            cursor = cursor:lower()
            if cursor == "true" or cursor == "1" then menu_state = true end
            if cursor == "false" or cursor == "0" then menu_state = false end
        end
    end
end

local function poll_game_log()
    local file = io.open(log_path, "rb")
    if not file then return end
    local size = file:seek("end")
    if not size then file:close(); return end
    if log_position == nil or size < log_position then
        -- Read recent startup state as well as transitions after Lua loads.
        log_position = math.max(0, size - 65536)
        partial_line = ""
        capture_seen = false
        menu_state = nil
        applied_state = nil
    elseif size - log_position > 65536 then
        log_position = size - 65536
        partial_line = ""
    end
    file:seek("set", log_position)
    local data = file:read(size - log_position) or ""
    log_position = size
    file:close()
    local lines = partial_line .. data
    local start = 1
    while true do
        local finish = lines:find("\n", start, true)
        if not finish then break end
        observe_line(lines:sub(start, finish - 1))
        start = finish + 1
    end
    partial_line = lines:sub(start)
    if #partial_line > 65536 then partial_line = "" end
end

local function update_screen(screen)
    -- With Slate capture disabled, the OpenVR UI texture retains its last
    -- loading/menu frame. EnableGUI=false clears that overlay on the next
    -- renderer update; the game's HUD is already part of the world image.
    vr.set_mod_value("VR_EnableGUI", screen and "true" or "false")
    if screen then
        -- Restore the readable baseline; the installed distance drifted to 9m.
        vr.set_mod_value("UI_Distance", "3.000000")
        vr.set_mod_value("UI_Size", "1.800000")
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
    functions.log_info(screen and "[FarFarWest] Menu screen enabled."
        or "[FarFarWest] Immersive view restored; menu overlay disabled.")
end

-- JoyToKey sends Escape on B's first poll but leaks native X on held polls.
-- Remove that second action; leave its synthetic Escape and other inputs intact.
uevr.sdk.callbacks.on_xinput_get_state(function(_, _, state)
    if not vr.is_runtime_ready() then return end
    local action = vr.get_action_handle("/actions/default/in/BButtonRight")
    if vr.is_action_active(action, vr.get_right_joystick_source()) then
        state.Gamepad.wButtons = state.Gamepad.wButtons & (~0x4000)
    end
end)

uevr.sdk.callbacks.on_pre_engine_tick(function(_, delta)
    local elapsed = math.min(math.max(delta or 0, 0), 0.1)
    poll_time = poll_time + elapsed
    if poll_time >= 0.05 then
        poll_time = 0
        poll_game_log()
    end
    if not vr.is_runtime_ready() then
        last_mode = nil
        applied_state = nil
        ready_time = 0
        saved_rotation = nil
        return
    end
    if not vr.is_hmd_active() then
        return
    end

    ready_time = ready_time + elapsed
    if last_mode == nil and ready_time < 0.5 then
        return
    end

    -- A button press requests a game action; only its resulting input-mode
    -- transition changes presentation. F8 remains a manual fallback until the
    -- next observed transition. Missing logs never guess that a click is Resume.
    if menu_state ~= nil and menu_state ~= applied_state and not functions.is_drawing_ui() then
        vr.set_mod_value("VR_2DScreenMode", menu_state and "true" or "false")
        applied_state = menu_state
    end
    local screen = vr:get_mod_value("VR_2DScreenMode") == "true"
    if screen ~= last_mode then update_screen(screen) end
end)

functions.log_info("[FarFarWest] Game input-mode menu helper loaded; waiting for LogViewport transitions.")
