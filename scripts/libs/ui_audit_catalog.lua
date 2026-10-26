-- Bounded, append-only catalog. No UObject references or gameplay writes here.
local M={}
local function quote(s)
    return '"'..s:gsub('[%z\1-\31\\"]',function(c)
        return string.format('\\u%04x',c:byte())
    end)..'"'
end
function M.json(v)
    local kind=type(v)
    if kind=='string' then return quote(v) end
    if kind=='number' then return v==v and math.abs(v)<1e100 and tostring(v) or 'null' end
    if kind=='boolean' then return tostring(v) end
    if kind~='table' then return 'null' end
    local keys,out={},{}
    for k in pairs(v) do keys[#keys+1]=k end
    table.sort(keys,function(a,b) return tostring(a)<tostring(b) end)
    for _,k in ipairs(keys) do out[#out+1]=quote(tostring(k))..':'..M.json(v[k]) end
    return '{'..table.concat(out,',')..'}'
end
function M.normalize(name)
    -- Preserve designer names such as Text_Key_1. Only strip generated instance IDs.
    return (name:gsub('_C_%d+$','_C'):gsub('_%d%d%d%d%d%d%d%d%d+$',''))
end
function M.new(write,options)
    options=options or {}
    local records,count,bytes,dropped,sequence={},0,0,0,0
    local dirty,dirty_head={},1
    local max_records,max_bytes=options.records or 4096,options.bytes or 16777216
    local reserved=math.max(0,math.min(options.reserved_records or 0,max_records))
    local ordinary=0
    local full=false
    local C={}
    local function emit(value)
        local line=M.json(value)..'\n'
        if bytes+#line>max_bytes then full=true;return false end
        local ok,err=write(line);assert(ok~=nil and ok~=false,err or 'Audit write failed')
        bytes=bytes+#line;return true
    end
    function C.event(value) return emit(value) end
    function C.observe(id,sample,time)
        local r=records[id]
        local changed=false
        if not r then
            if count>=max_records or (not sample.priority and ordinary>=max_records-reserved) then
                dropped=dropped+1;return
            end
            if not sample.priority then ordinary=ordinary+1 end
            count=count+1
            r={type='widget',id=id,first=time,seen=0,visible=0,edge_samples=0,
                contexts={},modes={},owners={},coverage={},flags={}}
            records[id]=r;changed=true
        end
        r.last=time;r.seen=r.seen+1
        for _,key in ipairs({'class','root_class','path','fields','kind','action','component','space','parent','owner_fields','attachment','relative_x','relative_y','relative_z','component_is_actor_root'}) do
            if sample[key]~=nil then
                if r[key]~=sample[key] and (not key:match('^relative_') or r[key]==nil) then changed=true end
                r[key]=sample[key]
            end
        end
        local function remember(set,key,limit)
            if not key or key=='' or set[key] then return end
            local n=0;for _ in pairs(set) do n=n+1 end
            if n<limit then set[key]=true;changed=true end
        end
        remember(r.contexts,sample.context,24);remember(r.modes,sample.mode,8)
        remember(r.owners,sample.owner_class,32);remember(r.coverage,sample.coverage,8)
        remember(r.flags,sample.flag,16)
        if sample.visible then
            if r.visible==0 then changed=true end
            r.visible=r.visible+1
            if sample.edge then
                if r.edge_samples==0 then changed=true end
                r.edge_samples=r.edge_samples+1
            end
            if sample.x0 then
                for _,key in ipairs({'x0','y0','x1','y1'}) do
                    local n=sample[key]
                    for suffix,choose in pairs({_min=math.min,_max=math.max}) do
                        local old=r[key..suffix];local next_value=choose(old or n,n)
                        if old==nil or math.floor(old*50)~=math.floor(next_value*50) then changed=true end
                        r[key..suffix]=next_value
                    end
                    r[key]=n
                end
            end
        end
        if changed and not r.dirty then r.dirty=true;dirty[#dirty+1]=r end
        return r
    end
    function C.flush_all()
        for _,r in pairs(records) do
            if not r.dirty then r.dirty=true;dirty[#dirty+1]=r end
        end
        return C.flush()
    end
    function C.flush(limit)
        local n=0
        if dirty_head>4096 then
            local pending={}
            for i=dirty_head,#dirty do pending[#pending+1]=dirty[i] end
            dirty,dirty_head=pending,1
        end
        while dirty_head<=#dirty do
            local r=dirty[dirty_head];dirty_head=dirty_head+1
            r.dirty=nil;sequence=sequence+1;r.revision=sequence
            if not emit(r) then return false,0 end
            n=n+1
            if limit and n>=limit then return true,#dirty-dirty_head+1 end
        end
        dirty,dirty_head={},1
        return true,0
    end
    function C.stats() return {records=count,bytes=bytes,dropped=dropped,full=full} end
    function C.contains(id) return records[id]~=nil end
    return C
end
return M
