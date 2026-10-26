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
local health={frames=0,ready_frames=0,left_trigger_frames=0,right_trigger_frames=0,
    both_trigger_frames=0,at_ears_frames=0,attempts=0,marked=0,reasons={}}
local both_was_down,announced=false,false
local attempt_outcome,next_attempt_note=nil,0
recorder.gesture_status(health)
local function state(reason)
    health.state=reason
    health.reasons[reason]=(health.reasons[reason] or 0)+1
end
local function mark(reason)
    if not digest_failed then pcall(digest.flush) end
    local saved,name=recorder.trigger(reason,{backend_tag=tag,tuning=tuning.snapshot()})
    if not saved then
        if name then log.log_warn('[FarFarWest report] Could not save marker: '..tostring(name)) end
        return false
    end
    log.log_info('[FarFarWest report] Marked '..name..'; saving recent UI/tracking context.')
    health.marked=health.marked+1
    for _,source in ipairs({vr.get_left_joystick_source(),vr.get_right_joystick_source()}) do
        pcall(vr.trigger_haptic_vibration,0,.10,120,.6,source)
        pcall(vr.trigger_haptic_vibration,.18,.10,120,.6,source)
    end
    return true
end
uevr.sdk.callbacks.on_pre_engine_tick(function(_,delta)
    if stopped then return end
    local success,err=pcall(function()
        local clock=os.clock()
        delta=math.max(delta or 0,clock-last_clock);last_clock=clock
        health.frames=health.frames+1
        recorder.configure(tuning.get('diagnostics.gesture_enabled')==1)
        if not recorder.enabled() then state('disabled');detector.reset();return end
        if not announced then
            announced=true
            log.log_info('[FarFarWest report] Gesture monitor active; recognition counters saved in the log digest.')
        end
        local blocked=not vr.is_runtime_ready() and 'runtime_unavailable'
            or not vr.is_hmd_active() and 'headset_inactive'
            or not vr.is_using_controllers() and 'controllers_inactive'
            or log.is_drawing_ui() and 'uevr_panel_open' or nil
        if blocked then state(blocked);both_was_down=false;detector.step(false,false,false,false,delta,.6,8);return end
        if not action then action=vr.get_action_handle('/actions/default/in/Trigger') end
        local indices={vr.get_hmd_index(),vr.get_left_controller_index(),vr.get_right_controller_index()}
        if indices[1]<0 or indices[1]>=64 or indices[2]<1 or indices[2]>=64 or indices[3]<1 or indices[3]>=64
            or indices[2]==indices[3] then state('invalid_device_indices');both_was_down=false;detector.reset();return end
        health.ready_frames=health.ready_frames+1
        for i=1,3 do vr.get_pose(indices[i],points[i],rotations[i]) end
        local left=vr.is_action_active(action,vr.get_left_joystick_source())
        local right=vr.is_action_active(action,vr.get_right_joystick_source())
        local near,metrics=gesture.at_ears(points[1],points[2],points[3],rotations[1],tuning.get('diagnostics.head_radius_m'),left and right)
        if left then health.left_trigger_frames=health.left_trigger_frames+1 end
        if right then health.right_trigger_frames=health.right_trigger_frames+1 end
        if near then health.at_ears_frames=health.at_ears_frames+1 end
        local before=left and right and detector.status()
        local fired=detector.step(true,near,left,right,delta,tuning.get('diagnostics.hold_seconds'),tuning.get('diagnostics.cooldown_seconds'))
        if left and right then
            health.both_trigger_frames=health.both_trigger_frames+1
            if not both_was_down then health.attempts=health.attempts+1;attempt_outcome=nil end
            local reason=before.cooldown_seconds>0 and 'cooldown' or before.release_required and 'release_both_triggers'
                or not near and metrics.reason or 'holding'
            if fired then attempt_outcome=mark('ears-and-both-triggers') and 'marked' or 'report_busy_or_write_failed' end
            reason=attempt_outcome or reason
            state(reason)
            health.last_attempt={unix_time=os.time(),reason=reason,pose=metrics,detector=detector.status()}
            if metrics.left and metrics.right then
                local distance=math.max(metrics.left.distance_m,metrics.right.distance_m)
                if not health.closest_attempt or distance<health.closest_attempt.distance_m then
                    health.closest_attempt={distance_m=distance,attempt=health.last_attempt}
                end
            end
        else
            if both_was_down and recorder.now()>=next_attempt_note then
                next_attempt_note=recorder.now()+15
                if health.last_attempt.reason=='holding' then health.last_attempt.reason='hold_too_short' end
                log.log_info('[FarFarWest report] Report chord released; last result: '..health.last_attempt.reason)
                if not digest_failed then pcall(digest.flush) end
            end
            state('waiting_for_chord')
        end
        both_was_down=left and right
    end)
    if not success then
        health.error=tostring(err);state('gesture_error')
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
