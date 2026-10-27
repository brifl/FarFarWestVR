-- Native priority is optional; old backends retain the original report cue.
local M={}
function M.new(vr)
    local native=false
    local ok,value=pcall(function() return vr:get_mod_value('FFW_ReportHaptics') end)
    native=ok and value=='1'
    local next_buzz,buzzing,silence_until=0,false,0
    local function send(duration,amplitude,source)
        return pcall(vr.trigger_haptic_vibration,0,duration,1,amplitude,source)
    end
    return {
        priority=function() return native end,
        confirm=function(now)
            silence_until=now+.65
            if native then
                vr:set_mod_value('FFW_ReportHaptics','1')
            else
                for _,source in ipairs({vr.get_left_joystick_source(),vr.get_right_joystick_source()}) do
                    pcall(vr.trigger_haptic_vibration,0,.10,1,5,source)
                    pcall(vr.trigger_haptic_vibration,.28,.10,1,5,source)
                end
            end
        end,
        tick=function(near,now)
            if now<silence_until then return end
            if near and now>=next_buzz then
                send(.1,5,vr.get_right_joystick_source());next_buzz=now+.05;buzzing=true
            elseif not near and buzzing then
                send(.02,0,vr.get_right_joystick_source());buzzing=false
            end
        end,
    }
end
return M
