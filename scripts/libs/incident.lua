-- Bounded ten-second flight recorder. Plain metadata only; no retained UObjects.
local M={}
local json=require('libs/ui_audit_catalog').json
local enabled,now=false,0
local started=os.time()
local buckets,definitions={},{}
local pending,writer,next_id=nil,nil,0
local max_bucket,max_definitions,max_file=256,2048,2097152
local skipped,definition_count,epoch=0,0,0
local gesture_status
local function bucket()
    local generation=math.floor(now*2)
    local slot=generation%21+1
    local b=buckets[slot]
    if not b or b.generation~=generation then
        if b then
            for key in pairs(b.samples) do
                local d=definitions[b.samples[key].definition]
                if d then d.refs=d.refs-1;if d.refs==0 then definitions[b.samples[key].definition]=nil;definition_count=definition_count-1 end end
            end
        end
        b={time=generation/2,generation=generation,samples={},logs={},count=0,ordinary=0};buckets[slot]=b
    end
    return b
end
function M.enabled() return enabled end
function M.gesture_status(value)
    if value~=nil then gesture_status=value end
    return gesture_status
end
function M.now() return now end
function M.configure(value)
    local next_enabled=value==true
    if enabled and not next_enabled then M.reset() end
    enabled=next_enabled
end
local function copy_fields(source,keys)
    local out={}
    for _,k in ipairs(keys) do if source[k]~=nil then out[k]=source[k] end end
    return out
end
local static={'class','root_class','path','parent','fields','owner_fields','component','space','owner_class','kind'}
local dynamic={'visible','context','action','mode','flag','coverage','x0','y0','x1','y1',
    'relative_x','relative_y','relative_z','attachment','component_is_actor_root','transform','target','owner_instance','component_instance','tracking','references'}
function M.observe(id,sample,instance)
    if not enabled or not sample.visible then return end
    local b=bucket()
    local definition=id..'|'..(sample.owner_class or '')
    local key=definition..'|'..tostring(instance or 0)..'|'..epoch
    local old=b.samples[key]
    local critical=sample.kind=='marker_tracking' or sample.kind=='shape_adapter' or sample.kind=='world_widget' or sample.fields~=nil
    if not old and (b.count>=max_bucket or (not critical and b.ordinary>=192)) then skipped=skipped+1;return end
    local d=definitions[definition]
    if not d then
        if definition_count>=max_definitions then skipped=skipped+1;return end
        d={type='definition',key=definition,id=id,metadata=copy_fields(sample,static),refs=0}
        definitions[definition]=d;definition_count=definition_count+1
    end
    local row=copy_fields(sample,dynamic)
    row.type='sample';row.definition=definition;row.instance=instance;row.time=now;row.epoch=epoch
    row.count=old and old.count+1 or 1
    if not old then b.count=b.count+1;d.refs=d.refs+1;if not critical then b.ordinary=b.ordinary+1 end end
    b.samples[key]=row
end
function M.count(key,example,source,severity,count,timestamp)
    if not enabled then return end
    local b=bucket();local bucket_key=key..'|'..epoch;local row=b.logs[bucket_key]
    if not row then
        local n=0;for _ in pairs(b.logs) do n=n+1 end
        if n>=128 then skipped=skipped+1;return end
        row={type='log_count',key=key,example=example,source=source,severity=severity,count=0,first=timestamp,last=timestamp,time=now,epoch=epoch}
        b.logs[bucket_key]=row
    end
    row.count=row.count+(count or 1);row.last=timestamp;row.time=now
end
function M.bursting() return pending and now<pending.until_time or false end
function M.trigger(reason,context)
    if not enabled or pending or writer then return false end
    next_id=next_id+1
    local stamp=os.date('!%Y%m%dT%H%M%SZ')
    local name
    for _=1,100 do
        name=string.format('issue-%s-%04d.jsonl',stamp,next_id)
        local existing=io.open(name,'rb')
        if not existing then break end
        existing:close();next_id=next_id+1;name=nil
    end
    if not name then return false end
    local output,err=io.open(name,'wb')
    if not output then return false,err end
    local timestamp=os.time()
    local header={type='issue',version=1,file=name,reason=reason or 'gesture',utc=os.date('!%Y-%m-%dT%H:%M:%SZ',timestamp),
        local_time=os.date('%Y-%m-%dT%H:%M:%S',timestamp),unix_time=timestamp,pre_seconds=10,post_seconds=5,
        time=now,sample_epoch=epoch,context=context,skipped_samples=skipped,map=_G.farfarwest_current_map,gameplay=_G.farfarwest_gameplay_ready==true,
        screenshots='Manual Virtual Desktop/SteamVR screenshots; this helper takes no screenshots.'}
    local line=json(header)..'\n'
    local ok=output:write(line)
    if not ok then output:close();return false,'Cannot write report header' end
    output:flush()
    pending={file=name,header=header,until_time=now+5,rows={},definitions={},definition_keys={}}
    for _,b in pairs(buckets) do
        if b.time+.5>=now-10 then
            for _,row in pairs(b.samples) do
                if row.time>=now-10 then pending.rows[#pending.rows+1]=row end
                if not pending.definition_keys[row.definition] then
                    local d=definitions[row.definition]
                    if d then pending.definitions[#pending.definitions+1]=d end
                    pending.definition_keys[row.definition]=true
                end
            end
            for _,row in pairs(b.logs) do if row.time>=now-10 then pending.rows[#pending.rows+1]=row end end
        end
    end
    epoch=epoch+1 -- Freeze pre-marker counts, including the current half-second bucket.
    writer={output=output,bytes=#line,index=1,file=name}
    local status=io.open('issue_capture_status.json','wb')
    if status then status:write(json(header)..'\n');status:close() end
    return true,name
end
function M.tick(delta)
    now=math.max(now+math.min(math.max(delta or 0,0),.25),os.time()-started)
    if enabled then bucket() end
    if not pending or not writer then return end
    if not writer.rows then
        writer.rows={}
        for _,d in ipairs(pending.definitions) do
            writer.rows[#writer.rows+1]={type='definition',key=d.key,id=d.id,metadata=d.metadata}
        end
        table.sort(pending.rows,function(a,b) return a.time<b.time end)
        for _,row in ipairs(pending.rows) do writer.rows[#writer.rows+1]=row end
    end
    if writer.index>#writer.rows and not writer.post_added then
        if now<pending.until_time then return end
        writer.post_added=true
        -- Add the most recent post-marker observations. Definitions are immutable
        -- plain tables so bucket expiry cannot invalidate a queued report.
        for _,b in pairs(buckets) do
            if b.time+.5>=pending.header.time then
                for _,row in pairs(b.samples) do
                    if row.epoch>pending.header.sample_epoch and row.time<=pending.until_time then
                    if not pending.definition_keys[row.definition] then
                        local d=definitions[row.definition]
                        if d then writer.rows[#writer.rows+1]={type='definition',key=d.key,id=d.id,metadata=d.metadata} end
                        pending.definition_keys[row.definition]=true
                    end
                    writer.rows[#writer.rows+1]=row
                    end
                end
                for _,row in pairs(b.logs) do
                    if row.epoch>pending.header.sample_epoch and row.time<=pending.until_time then writer.rows[#writer.rows+1]=row end
                end
            end
        end
    end
    local deadline=os.clock()+.0005
    for _=1,32 do
        local row=writer.rows[writer.index]
        if not row then
            if not writer.post_added then break end
            writer.output:write(json({type='end',truncated=writer.truncated or false,skipped_samples=skipped})..'\n')
            writer.output:flush();writer.output:close();writer=nil;pending=nil;return
        end
        local line=json(row)..'\n'
        if writer.bytes+#line>max_file-256 then
            writer.truncated=true;writer.index=#writer.rows+1;break
        end
        assert(writer.output:write(line),'Incident write failed')
        writer.bytes=writer.bytes+#line;writer.index=writer.index+1
        if os.clock()>=deadline then break end
    end
    writer.output:flush()
end
function M.reset()
    if writer then pcall(writer.output.flush,writer.output);pcall(writer.output.close,writer.output) end
    buckets,definitions={},{};definition_count=0;pending,writer=nil,nil
end
return M
