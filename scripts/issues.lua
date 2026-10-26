-- Both controllers at the ears + both triggers: timestamp a local issue report.
-- Screenshot capture is intentionally left to Virtual Desktop / SteamVR.
local log,vr=uevr.params.functions,uevr.params.vr
local ok,tag=pcall(log.get_tag)
if not ok or tag~='ffw-ue58-sdk-v1' then return end
local tuning=require('libs/tuning')
local recorder=require('libs/incident')
local gesture=require('libs/report_gesture')
local detector=gesture.new()
local digest=require('libs/log_digest').new(recorder)
local points,rotations={},{}
for i=1,3 do points[i]=UEVR_Vector3f.new();rotations[i]=UEVR_Quaternionf.new() end
local action,stopped,digest_failed,poll,next_command=nil,false,false,0,0
local last_clock=os.clock()
local function mark(reason)
    if not digest_failed then pcall(digest.flush) end
    local saved,name=recorder.trigger(reason,{backend_tag=tag,tuning=tuning.snapshot()})
    if not saved then
        if name then log.log_warn('[FarFarWest report] Could not save marker: '..tostring(name)) end
        return
    end
    log.log_info('[FarFarWest report] Marked '..name..'; saving recent UI/tracking context.')
    for _,source in ipairs({vr.get_left_joystick_source(),vr.get_right_joystick_source()}) do
        pcall(vr.trigger_haptic_vibration,0,.10,120,.6,source)
        pcall(vr.trigger_haptic_vibration,.18,.10,120,.6,source)
    end
end
uevr.sdk.callbacks.on_pre_engine_tick(function(_,delta)
    if stopped then return end
    local success,err=pcall(function()
        local clock=os.clock()
        delta=math.max(delta or 0,clock-last_clock);last_clock=clock
        recorder.configure(tuning.get('diagnostics.gesture_enabled')==1)
        if not recorder.enabled() then detector.reset();return end
        local ready=vr.is_runtime_ready() and vr.is_hmd_active() and vr.is_using_controllers() and not log.is_drawing_ui()
        if not ready then detector.step(false,false,false,false,delta,.6,8);return end
        if not action then action=vr.get_action_handle('/actions/default/in/Trigger') end
        local indices={vr.get_hmd_index(),vr.get_left_controller_index(),vr.get_right_controller_index()}
        if indices[1]<0 or indices[1]>=64 or indices[2]<1 or indices[2]>=64 or indices[3]<1 or indices[3]>=64
            or indices[2]==indices[3] then detector.reset();return end
        for i=1,3 do vr.get_pose(indices[i],points[i],rotations[i]) end
        local near=gesture.at_ears(points[1],points[2],points[3],rotations[1],tuning.get('diagnostics.head_radius_m'))
        local left=vr.is_action_active(action,vr.get_left_joystick_source())
        local right=vr.is_action_active(action,vr.get_right_joystick_source())
        if detector.step(true,near,left,right,delta,tuning.get('diagnostics.hold_seconds'),tuning.get('diagnostics.cooldown_seconds')) then mark('ears-and-both-triggers') end
    end)
    if not success then
        stopped=true;recorder.configure(false)
        log.log_warn('[FarFarWest report] Gesture stopped safely: '..tostring(err))
    end
end)
uevr.sdk.callbacks.on_post_engine_tick(function(_,delta)
    if stopped then return end
    local success,err=pcall(function()
        if not digest_failed then
            local good,reason=pcall(digest.tick,delta)
            if not good then digest_failed=true;log.log_warn('[FarFarWest report] Log digest unavailable: '..tostring(reason)) end
        end
        recorder.tick(delta)
        poll=poll+math.min(math.max(delta or 0,0),.25)
        if poll>=next_command then
            next_command=poll+.5
            local file=io.open('issue_capture_command.txt','rb')
            local command=file and file:read(32);if file then file:close() end
            if command and command:match('^%s*mark%s*$') then
                local output=io.open('issue_capture_command.txt','wb')
                if output then output:write('done\n');output:close() end
                mark('manual-command')
            end
        end
    end)
    if not success then
        stopped=true;recorder.configure(false);recorder.reset()
        log.log_warn('[FarFarWest report] Recorder stopped safely: '..tostring(err))
    end
end)
uevr.sdk.callbacks.on_script_reset(function() pcall(digest.flush);recorder.reset() end)
