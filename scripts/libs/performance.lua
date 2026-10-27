-- Bounded performance history. Five-second read-only native polls; no actor scans.
local M={}
local windows,events={},{}
local window,latest,peak={}, {},{}
local total_frames,next_poll,next_window,next_event,discarded=0,0,0,0,0
local flush_pending=false
local capture_enabled=true
local function reset_window() window={frames=0,delta_sum=0,max_delta_ms=0,over_50ms=0,over_250ms=0,over_500ms=0,audit_peak_ms=0,lua_peak_ms=0} end
reset_window()
local function bounded_push(list,row,limit)
    if #list>=limit then table.remove(list,1);discarded=discarded+1 end
    list[#list+1]=row
end
local function copy(source) local out={};for k,v in pairs(source) do out[k]=v end;return out end
function M.parse(text)
    if type(text)~='string' or not text:match('^v=1;') then return nil end
    local out={}
    for key,value in text:gmatch('([%w_]+)=([%-%.%d]+)') do
        local n=tonumber(value);if n and n==n and math.abs(n)<1e15 then out[key]=n end
    end
    if out.ws==nil or out.commit==nil or out.li==nil then return nil end
    return out
end
function M.frame(delta)
    local now=os.time();total_frames=total_frames+1
    local ms=math.max(0,delta or 0)*1000
    window.frames=window.frames+1;window.delta_sum=window.delta_sum+ms
    window.max_delta_ms=math.max(window.max_delta_ms,ms)
    peak.engine_delta_ms=math.max(peak.engine_delta_ms or 0,ms)
    if ms>=50 then window.over_50ms=window.over_50ms+1 end
    if ms>=250 then window.over_250ms=window.over_250ms+1 end
    if ms>=500 then window.over_500ms=window.over_500ms+1 end
    if now>=next_poll then
        next_poll=now+5
        local ok,text=pcall(function() return uevr.params.vr:get_mod_value('FFW_DiagnosticStats') end)
        local native=ok and M.parse(text)
        if native then
            latest=native;latest.unix_time=now
            local cost=math.max(native.lp or 0,native.lq or 0,native.ls or 0,native.li or 0)
            window.lua_peak_ms=math.max(window.lua_peak_ms,cost);peak.lua_callback_ms=math.max(peak.lua_callback_ms or 0,cost)
        end
        local heap_ok,kb=pcall(collectgarbage,'count')
        if heap_ok then latest.lua_heap_kb=kb;peak.lua_heap_kb=math.max(peak.lua_heap_kb or 0,kb) end
        local slots_ok,slots=pcall(function() return uevr.api:get_uobject_array():get_object_count() end)
        if slots_ok and type(slots)=='number' and slots>=0 and slots<=0x7fffffff then latest.object_slots=slots end
        latest.map=_G.farfarwest_current_map;latest.gameplay=_G.farfarwest_gameplay_ready==true
        latest.capture_enabled=capture_enabled
    end
    if ms>=250 and now>=next_event then
        next_event=now+10;flush_pending=true
        local row=copy(latest);row.unix_time=now;row.engine_delta_ms=ms
        bounded_push(events,row,64)
        local log=uevr.params.functions
        log.log_info(string.format('[FarFarWest performance] Engine interval %.1f ms; latest Lua peak %.2f ms; private memory %s MiB.',
            ms,peak.lua_callback_ms or 0,tostring(latest.commit or 'unavailable')))
    end
    if next_window==0 then next_window=now+30 end
    if now>=next_window then
        local row=copy(latest);row.window=copy(window);row.unix_time=now
        bounded_push(windows,row,512);reset_window();next_window=now+30
    end
end
function M.set_capture_enabled(value) capture_enabled=value==true end
function M.audit(ms)
    window.audit_peak_ms=math.max(window.audit_peak_ms,ms)
    peak.audit_ms=math.max(peak.audit_ms or 0,ms)
end
function M.needs_flush() local needed=flush_pending;flush_pending=false;return needed end
function M.context() return {latest=copy(latest),peak=copy(peak),window=copy(window)} end
function M.snapshot() return {version=1,frames=total_frames,latest=latest,peak=peak,window=window,windows=windows,events=events,discarded_history=discarded} end
return M
