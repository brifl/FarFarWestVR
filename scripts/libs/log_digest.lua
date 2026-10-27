-- Tail only relevant messages; keep one dictionary entry/counter per message.
local M={}
local performance=require('libs/performance')
function M.classify(line,source)
    if line:find('The shift value seems to be invalid ',1,true) then
        local value=line:match('shift value seems to be invalid (%-?%d+)') or '?'
        return 'remap.invalid_shift.'..value,'RemapControls: invalid shift '..value,'error',true
    end
    local severity=(line:find('[error]',1,true) or line:find('Error:',1,true) or line:find('Fatal error',1,true)) and 'error'
        or (line:find('[warning]',1,true) or line:find('Warning:',1,true)) and 'warning'
    if not severity then return end
    local message=line:match('%[Plugin%]%s*(.*)')
    if not message then
        message=line:gsub('^%[[^%]]*%]%s*','')
        -- Unreal prefixes every line with a changing frame number after its timestamp.
        if source=='game' then message=message:gsub('^%[%s*%d+%]%s*','') end
    end
    message=message:gsub('%s+$',''):gsub('_C_%d+','_C_*'):gsub('0x%x+','0x*'):sub(1,600)
    local documented=message:find('Skipping unsupported pawn BP_LoadingScreen_C',1,true)~=nil
        or (message:find('Skipped UI_DisturbanceIncrease_C',1,true)~=nil
            and message:find('Rotated/sheared overlay',1,true)~=nil)
    return source..':'..message,message,severity,documented
end
function M.new(recorder)
    local json=require('libs/ui_audit_catalog').json
    local elapsed,next_poll,next_save=0,0,0
    local streams={{name='UEVR.log',source='uevr'},{name='FarFarWest.log',source='game'}}
    local counts,count,ordinary,overflow={},0,0,0
    local output='log-digest-'..os.date('!%Y%m%dT%H%M%SZ')..'.json'
    for n=1,100 do
        local old=io.open(output,'rb')
        if not old then break end
        old:close();output='log-digest-'..os.date('!%Y%m%dT%H%M%SZ')..'-'..n..'.json'
    end
    local function save()
        local file=io.open(output,'wb');if not file then return end
        file:write(json({version=1,utc=os.date('!%Y-%m-%dT%H:%M:%SZ'),messages=counts,
            overflow=overflow,gesture=recorder.gesture_status(),performance=performance.snapshot(),uevr_log_available=streams[1].available or false,
            skipped_uevr_bytes=streams[1].skipped_bytes or 0,skipped_game_bytes=streams[2].skipped_bytes or 0,
            note='Counts since this script load. Original engine/plugin log files are not modified.'})..'\n')
        file:close()
    end
    local function observe(line,source)
        local key,message,severity,documented=M.classify(line,source)
        if not key then return end
        local timestamp=line:match('^%[([^%]]+)%]') or os.date('!%Y-%m-%dT%H:%M:%SZ')
        local row=counts[key]
        if not row then
            -- Reserve dictionary capacity for errors after a noisy game warning stream.
            if count>=256 or (severity~='error' and ordinary>=192) then overflow=overflow+1;return end
            count=count+1
            if severity~='error' then ordinary=ordinary+1 end
            row={message=message,source=source,severity=severity,documented=documented,count=0,first=timestamp}
            counts[key]=row
        end
        row.count=row.count+1;row.last=timestamp
        recorder.count(key,message,source,severity,1,timestamp)
    end
    local function poll()
        for _,stream in ipairs(streams) do
            local file=io.open(stream.name,'rb')
            stream.available=file~=nil
            if file then
                local size=file:seek('end')
                if size then
                    local position=stream.position
                    if not position or size<position then position=math.max(0,size-16384);stream.partial='' end
                    if size-position>16384 then
                        stream.skipped_bytes=(stream.skipped_bytes or 0)+(size-position-16384)
                        position=size-16384;stream.partial=''
                    end
                    file:seek('set',position)
                    local data=(stream.partial or '')..(file:read(math.min(size-position,16384)) or '')
                    stream.position=size
                    local begin=1
                    while true do
                        local last=data:find('\n',begin,true);if not last then break end
                        observe(data:sub(begin,last-1),stream.source);begin=last+1
                    end
                    stream.partial=data:sub(begin):sub(-2048)
                end
                file:close()
            end
        end
    end
    return {
        tick=function(delta)
            if not recorder.enabled() then return end
            elapsed=elapsed+math.min(math.max(delta or 0,0),.25)
            if elapsed>=next_poll then next_poll=elapsed+.5;poll() end
            if elapsed>=next_save then next_save=elapsed+60;save() end
        end,
        flush=function() if recorder.enabled() then poll();save() end end,
        output=function() return output end,
    }
end
return M
