-- Follow the game's level and input mode, including Resume and submenus.
-- LogViewport is enabled by the menu-logging preset. No engine-world lookup.
local vr = uevr.params.vr
local functions = uevr.params.functions
-- UEVR removes os.getenv and permits file access only within profile/data.
-- tools/prepare_menu_helper.py creates a native Windows link to the game log.
local log_path = "FarFarWest.log"
local log_position = nil
local partial_line = ""
local capture_seen = false
local menu_state = nil
local playable_map = false
local loading = true
local applied_state = nil
local poll_time = 0
local last_mode = nil
local ready_time = 0
local saved_rotation = nil
-- Autorun scripts share Lua globals. Aiming must wait for a known game level,
-- rather than trusting the immersive/screen mode saved by the previous run.
_G.farfarwest_gameplay_ready = false
-- This custom card remains visible after the generic loading-screen log ends.
-- Native access is optional and restricted to the guarded backend.
local preview
local tag_ok,tag=pcall(functions.get_tag)
if tag_ok and tag=='ffw-ue58-sdk-v1' then
    local ok,helper=pcall(function() return require('libs/mission_preview')() end)
    if ok then preview=helper
    else functions.log_warn('[FarFarWest preview] Helper unavailable: '..tostring(helper)) end
end

local function observe_line(line)
    local map = line:match("LogLoad: LoadMap: ([^?%s]+)")
    if map then
        playable_map = map:match("^/Game/Levels/") ~= nil
            and map ~= "/Game/Levels/L_OpeningCredits"
            and map ~= "/Game/Levels/L_Map_TitleScreen"
        loading = true
        capture_seen = false
        menu_state = true
        _G.farfarwest_gameplay_ready = false
        functions.log_info("[FarFarWest] Loaded level: " .. map)
        return
    end
    if line:find("LogLoadingScreen: Showing loading screen", 1, true) then
        loading = true
    elseif line:find("LogLoadingScreen: Hiding loading screen", 1, true) then
        loading = false
        -- Default LogLoad messages still distinguish the title from gameplay
        -- when the optional verbose input-mode logging is absent.
        if playable_map and not capture_seen then menu_state = false end
    end
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
        playable_map = false
        loading = true
        _G.farfarwest_gameplay_ready = false
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
    -- The game's projected crosshair handles gameplay aiming. Keep UEVR's
    -- forced mouse cursor for menus; its own panel draws a cursor separately.
    vr.set_mod_value("FrameworkConfig_AlwaysShowCursor", screen and "true" or "false")
    -- With Slate capture disabled, the OpenVR UI texture retains its last
    -- loading/menu frame. EnableGUI=false clears that overlay on the next
    -- renderer update; the game's HUD is already part of the world image.
    vr.set_mod_value("VR_EnableGUI", screen and "true" or "false")
    -- The game camera pitch follows the aiming hand. Applying it to the menu
    -- overlay raises/lowers the whole screen with the controller; use the
    -- headset's recentered, level orientation instead. Keep gameplay unchanged.
    vr.set_mod_value("VR_DecoupledPitchUIAdjust", screen and "false" or "true")
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

uevr.sdk.callbacks.on_pre_engine_tick(function(engine, delta)
    local elapsed = math.min(math.max(delta or 0, 0), 0.1)
    poll_time = poll_time + elapsed
    if poll_time >= 0.05 then
        poll_time = 0
        poll_game_log()
    end
    if not vr.is_runtime_ready() then
        _G.farfarwest_gameplay_ready = false
        last_mode = nil
        applied_state = nil
        ready_time = 0
        saved_rotation = nil
        return
    end
    if not vr.is_hmd_active() then
        _G.farfarwest_gameplay_ready = false
        return
    end

    ready_time = ready_time + elapsed
    if last_mode == nil and ready_time < 0.5 then
        return
    end

    -- Follow input-mode transitions and the actual mission card, rather than
    -- guessing from button presses. F8 remains a manual fallback until the
    -- next observed transition. Missing logs never guess that a click is Resume.
    local desired_menu = menu_state
    local preview_visible = preview and preview.tick(engine,delta)
    if not playable_map or loading or preview_visible then desired_menu = true end
    if desired_menu ~= nil and desired_menu ~= applied_state and not functions.is_drawing_ui() then
        vr.set_mod_value("VR_2DScreenMode", desired_menu and "true" or "false")
        applied_state = desired_menu
    end
    local screen = vr:get_mod_value("VR_2DScreenMode") == "true"
    _G.farfarwest_gameplay_ready = playable_map and not loading
        and desired_menu == false and not screen
    if screen ~= last_mode then update_screen(screen) end
end)

uevr.sdk.callbacks.on_script_reset(function()
    vr.set_mod_value("FrameworkConfig_AlwaysShowCursor", "true")
end)

functions.log_info("[FarFarWest] Menu helper loaded; following level and input-mode logs.")
