-- Read-only UI census. Each script load can start its own bounded capture.
return function()
local api,vr,log=uevr.api,uevr.params.vr,uevr.params.functions
local catalog=require('libs/ui_audit_catalog')
local registry=require('libs/ui_audit_registry')
local tuning=require('libs/tuning')
local array,classes,library,slate,layout
local prepared=false
local active,file,output,elapsed,duration,store
local clock=os.clock
local poll,next_query,next_flush,next_status,scan_index,next_scan=0,0,0,0,0,0
local queue,head,visited,links,schemas={},1,{},{},{}
local link_count,schema_count=0,0
local errors,scans,max_tick_ms,queue_dropped=0,0,0,0
local last_command
local auto_pending=true
local next_ledger=300
local function field(class,name,offset)
    local p=class:find_property(name)
    assert(p and p:get_offset()==offset,'Unexpected audit field: '..name)
end
local function method(class,name,minimum,maximum)
    local f=class:find_function(name)
    assert(f and f:get_properties_size()>=minimum and f:get_properties_size()<=(maximum or minimum),
        'Unexpected audit function: '..name)
end
local function track(o)
    if not o then return end
    local index=o:read_dword(12)
    local current=index>=0 and index<array:get_object_count() and array:get_object(index)
    if not current or current:get_address()~=o:get_address() then return end
    return {object=o,index=index,address=o:get_address(),name=o:get_short_name()}
end
local function valid(r)
    local o=r and array:get_object(r.index)
    return o and o:get_address()==r.address and o:get_short_name()==r.name
end
local function prepare()
    array=api:get_uobject_array()
    assert(array and array.get_objects_offset()==0 and array.get_item_distance()==24,'Unexpected audit object array')
    classes={}
    for _,name in ipairs({'Widget','UserWidget','WidgetTree','PanelWidget','WidgetComponent',
        'WidgetBlueprintLibrary','SlateBlueprintLibrary','WidgetLayoutLibrary'}) do
        classes[name]=assert(api:find_uobject('Class /Script/UMG.'..name),'Missing audit class '..name)
    end
    classes.Viewport=assert(api:find_uobject('Class /Script/Engine.GameViewportClient'))
    field(classes.Widget,'Slot',48);field(classes.UserWidget,'WidgetTree',704)
    field(classes.WidgetComponent,'Widget',1800);field(classes.WidgetComponent,'Space',1512)
    method(classes.Widget,'GetParent',8);method(classes.Widget,'GetCachedGeometry',32,256)
    method(classes.PanelWidget,'GetChildrenCount',4);method(classes.PanelWidget,'GetChildAt',16)
    method(classes.UserWidget,'IsInViewport',1)
    method(classes.WidgetBlueprintLibrary,'GetAllWidgetsOfClass',40)
    method(classes.SlateBlueprintLibrary,'GetLocalSize',32,512)
    method(classes.SlateBlueprintLibrary,'LocalToViewport',64,512)
    method(classes.WidgetLayoutLibrary,'GetViewportSize',24)
    library=assert(classes.WidgetBlueprintLibrary:get_class_default_object())
    slate=assert(classes.SlateBlueprintLibrary:get_class_default_object())
    layout=assert(classes.WidgetLayoutLibrary:get_class_default_object())
    prepared=true
end
local function command(text)
    local f=assert(io.open('ui_audit_command.txt','wb'))
    assert(f:write(text..'\n'));assert(f:close());last_command=text
end
local function status(reason)
    local stats=store.stats()
    stats.file=output;stats.elapsed=elapsed;stats.duration=duration;stats.state=reason
    stats.links=link_count;stats.schemas=schema_count
    stats.errors=errors;stats.sweeps=scans;stats.max_tick_ms=max_tick_ms;stats.queue_dropped=queue_dropped
    local f=assert(io.open('ui_audit_status.json','wb'))
    assert(f:write(catalog.json(stats)..'\n'));assert(f:close())
end
local function session_note(event)
    local stats=store.stats()
    local note=assert(io.open('ui_audit_sessions.md','ab'))
    if note:seek('end')==0 then
        assert(note:write('# Gameplay UI capture sessions\n\n'..
            'Each capture has its own JSONL file. An unfinished entry retains its last checkpoint.\n\n'..
            '| Capture | Event | Engine seconds | IDs | Errors | Dropped | Bytes |\n'..
            '| --- | --- | ---: | ---: | ---: | ---: | ---: |\n'))
    end
    assert(note:write(string.format('| %s | %s | %.1f | %d | %d | %d | %d |\n',
        output,event,elapsed,stats.records,errors,stats.dropped,stats.bytes)))
    assert(note:close())
end
local function finish(reason)
    if not active then return end
    active=false
    store.flush_all()
    store.event({type='end',reason=reason,elapsed=elapsed,errors=errors,sweeps=scans})
    assert(file:flush());assert(file:close());file=nil
    status(reason);session_note(reason);command('done '..output)
    queue,visited,links,schemas={}, {}, {}, {}
    log.log_info('[FarFarWest audit] '..reason..': data/'..output)
end
local function start(seconds)
    if active then finish('replaced') end
    if not prepared then prepare() end
    local counter=io.open('ui_audit_counter.txt','rb')
    local n=counter and tonumber(counter:read(32)) or 0
    if counter then counter:close() end
    n=math.floor(math.max(0,math.min(n or 0,999999)))
    for _=1,100 do
        n=n+1;output=string.format('ui-audit-%06d.jsonl',n)
        local existing=io.open(output,'rb')
        if not existing then break end
        existing:close();output=nil
    end
    assert(output,'Cannot allocate a new audit filename')
    counter=assert(io.open('ui_audit_counter.txt','wb'));assert(counter:write(tostring(n)));assert(counter:close())
    file=assert(io.open(output,'wb'))
    store=catalog.new(function(line) return file:write(line) end)
    active=true;elapsed=0;duration=seconds;next_ledger=300
    queue,head,visited,links,schemas={},1,{},{},{}
    link_count,schema_count=0,0
    poll,next_query,next_flush,next_status,scan_index,next_scan=0,0,30,10,0,0
    errors,scans,max_tick_ms,queue_dropped=0,0,0,0
    store.event({type='start',version=1,duration=duration,
        horizontal_margin=tuning.get('audit.horizontal_margin'),vertical_margin=tuning.get('audit.vertical_margin'),
        text_access='Action bindings and key-widget modes; arbitrary FText strings unavailable',
        bounds='Normalized viewport bounds; these are diagnostic margins, not a headset visibility measurement'})
    assert(file:flush());command('active '..output);status('active');session_note('started')
    log.log_info('[FarFarWest audit] Read-only capture started: data/'..output)
end
local function parent(o)
    local p=o:GetParent()
    if p then return p end
    local outer=o:get_outer()
    if outer and outer:is_a(classes.WidgetTree) then return outer:get_outer() end
end
local function ancestry(o)
    local path,seen={},{}
    local visible,top,root,owner=true,nil,nil,nil
    for _=1,32 do
        local ref=track(o);if not ref or seen[ref.address] then break end
        seen[ref.address]=true
        if not o:is_a(classes.Widget) then break end
        local v=o:get_property('Visibility')
        if v==1 or v==2 or o:get_property('RenderOpacity')<=0 then visible=false end
        table.insert(path,1,catalog.normalize(ref.name))
        top=o
        if o:is_a(classes.UserWidget) then root=o:get_class():get_full_name();owner=o end
        o=parent(o);if not o then break end
    end
    local placed=top and top:is_a(classes.UserWidget) and top:IsInViewport() or false
    return table.concat(path,'/'),root or '',visible,placed,owner
end
local function schema(class)
    local name=class:get_full_name()
    if schemas[name] then return schemas[name] end
    if schema_count>=512 then return 'schema capacity reached' end
    schema_count=schema_count+1
    local out={};local current=class;local total=0
    for _=1,6 do
        if not current or current:get_short_name()=='UserWidget' then break end
        local p=current:get_child_properties()
        while p and total<96 do
            total=total+1
            local key=p:get_fname():to_string()
            local property=current:find_property(key)
            if property then out[#out+1]=key..':'..p:get_class():get_name()..'@'..property:get_offset() end
            p=p:get_next()
        end
        current=current:get_super_struct()
    end
    local text=table.concat(out,';')
    if #text>6000 then text=text:sub(1,6000) end
    schemas[name]=text;return text
end
local function enqueue(o)
    local ref=track(o)
    if not ref or visited[ref.address] then return end
    visited[ref.address]=true
    if #queue>=8192 then queue_dropped=queue_dropped+1;return end
    queue[#queue+1]=ref
end
local function discover(viewport)
    local found={}
    library:GetAllWidgetsOfClass(viewport,found,classes.UserWidget,false)
    assert(#found<=1024,'Audit user-widget query exceeds budget')
    queue,head,visited={},1,{}
    for _,o in ipairs(found) do
        local ref=track(o)
        if ref then enqueue(o) end
    end
    scans=scans+1;next_query=elapsed+3
end
local function components(deadline)
    local count=array:get_object_count()
    assert(count>0 and count<=250000,'Audit object count exceeds verified budget')
    if elapsed<next_scan then return end
    for i=1,256 do
        if scan_index>=count then
            scan_index=0;next_scan=elapsed+5
            for address,link in pairs(links) do
                if not valid(link.component) or not valid(link.source) or not valid(link.owner) then
                    links[address]=nil;link_count=link_count-1
                end
            end
            return
        end
        local o=array:get_object(scan_index);scan_index=scan_index+1
        if o and o:is_a(classes.WidgetComponent) then
            local source=o:get_property('Widget')
            local owner=o:get_outer()
            if source and owner then
                local c,s,a=track(o),track(source),track(owner)
                if c and s and a and (links[s.address] or link_count<2048) then
                    if not links[s.address] then link_count=link_count+1 end
                    links[s.address]={component=c,source=s,owner=a}
                end
            end
        end
        if i%16==0 and clock()>=deadline then return end
    end
end
local function bounds(o,viewport)
    local geometry=o:GetCachedGeometry()
    local size=slate:GetLocalSize(geometry)
    if not size or size.X<=0 or size.Y<=0 or size.X>100000 or size.Y>100000 then return end
    local minx,miny,maxx,maxy=math.huge,math.huge,-math.huge,-math.huge
    for _,point in ipairs({{X=0,Y=0},{X=size.X,Y=0},{X=0,Y=size.Y},{X=size.X,Y=size.Y}}) do
        local pixel,screen={},{}
        slate:LocalToViewport(o,geometry,point,pixel,screen)
        if not pixel.result then return end
        local x,y=pixel.result.X/viewport.X,pixel.result.Y/viewport.Y
        if x~=x or y~=y or math.abs(x)>100 or math.abs(y)>100 then return end
        minx,miny,maxx,maxy=math.min(minx,x),math.min(miny,y),math.max(maxx,x),math.max(maxy,y)
    end
    return minx,miny,maxx,maxy
end
local function sample(ref,viewport)
    if not valid(ref) then return end
    local o=ref.object
    if o:is_a(classes.UserWidget) then
        local tree=o:get_property('WidgetTree');local root=tree and tree:get_property('RootWidget')
        if root then enqueue(root) end
    end
    local panel=o:is_a(classes.PanelWidget)
    if panel then
        local count=o:GetChildrenCount();assert(count>=0 and count<=512,'Audit panel child count exceeds budget')
        for i=0,count-1 do enqueue(o:GetChildAt(i)) end
    end
    local path,root,visible,placed,root_widget=ancestry(o)
    local class=o:get_class();local class_name=class:get_short_name()
    local data={class=class:get_full_name(),root_class=root,path=path,visible=false,
        kind=panel and 'panel' or 'widget',parent=path:match('^(.*)/') or '',
        context=(_G.farfarwest_current_map or 'unknown')..(_G.farfarwest_gameplay_ready and ':gameplay' or ':menu/loading')}
    if o:is_a(classes.UserWidget) then data.fields=schema(class) end
    local address=root_widget and root_widget:get_address() or ref.address
    local coverage,role=registry.find(address,valid)
    if coverage then data.coverage=coverage..':'..role end
    local link=links[address]
    if link and valid(link.component) and valid(link.source) and valid(link.owner) then
        local c,owner=link.component.object,link.owner.object
        local current=c:get_property('Widget')
        if not current or current:get_address()~=link.source.address then
            links[address]=nil;link_count=link_count-1;link=nil
        end
    end
    if link and valid(link.component) and valid(link.source) and valid(link.owner) then
        local c,owner=link.component.object,link.owner.object
        data.kind='world_widget';data.owner_class=owner:get_class():get_full_name()
        if o:get_address()==address then
            data.owner_fields=schema(owner:get_class())
            local attach=c:get_property('AttachParent')
            data.attachment=attach and (attach:get_class():get_full_name()..':'..catalog.normalize(attach:get_short_name())) or ''
            local actor_root=owner:get_property('RootComponent')
            data.component_is_actor_root=actor_root and actor_root:get_address()==c:get_address() or false
            local relative=c:get_property('RelativeLocation')
            if relative then data.relative_x,data.relative_y,data.relative_z=relative.X,relative.Y,relative.Z end
        end
        data.component=catalog.normalize(link.component.name);data.space=c:read_byte(1512)==1 and 'screen' or 'world'
        placed=c:get_property('bVisible') and not owner:get_property('bHidden')
    end
    if class_name=='UI_Key_C' then
        for name,offset in pairs({Key=856,gamepadKeys=864,Image_GamepadIcon=848,Text_Key=832}) do field(class,name,offset) end
        local action=o:get_property('Key');local override=o:get_property('gamepadKeys')
        data.action=action and action:get_short_name() or ''
        local text,image=o:get_property('Text_Key'),o:get_property('Image_GamepadIcon')
        local function shown(w) local v=w and w:get_property('Visibility');return w and v~=1 and v~=2 end
        data.mode=(shown(text) and 'keyboard' or '')..(shown(image) and '+gamepad' or '')
        if override then data.fields=(data.fields or '')..';gamepadKeys='..override:get_short_name() end
        data.kind='key_hint'
    end
    data.visible=visible and placed==true
    if data.visible then
        if data.space=='screen' and not coverage then data.flag='unhandled_screen_marker_candidate' end
        if data.action=='IA_Interact' and data.mode and data.mode:find('keyboard',1,true) then
            data.flag='interact_keyboard_hint'
        end
        data.x0,data.y0,data.x1,data.y1=bounds(o,viewport)
        if data.x0 then
            local h,v=tuning.get('audit.horizontal_margin'),tuning.get('audit.vertical_margin')
            data.edge=data.x0<h or data.x1>1-h or data.y0<v or data.y1>1-v
            local area=(data.x1-data.x0)*(data.y1-data.y0)
            if data.edge and area<.4 and not panel and not coverage then data.flag=data.flag or 'edge_hud_candidate' end
        end
    end
    -- Root class + structural path survives process addresses, maps and engine instance IDs.
    local id=data.class..'|'..path
    store.observe(id,data,elapsed)
end
local function tick(engine,delta)
    local begin=clock()
    local ok,err=pcall(function()
        local dt=math.min(math.max(delta or 0,0),.25)
        poll=poll+dt
        if poll>=1 then
            poll=0
            local f=io.open('ui_audit_command.txt','rb')
            local text=f and f:read(129) or '';if f then f:close() end
            text=text:match('^%s*(.-)%s*$')
            if text~=last_command then
                last_command=text
                local seconds=text:match('^start%s+(%d+)$')
                if text=='start' then seconds='3600' end
                if seconds then
                    auto_pending=false;start(math.max(10,math.min(tonumber(seconds),3600)))
                elseif text=='stop' then auto_pending=false;finish('stopped') end
            end
            if auto_pending then
                auto_pending=false
                if tuning.get('audit.auto_start')==1 then start(3600) end
            end
        end
        if not active then return end
        elapsed=elapsed+dt
        if elapsed>=duration then finish('completed');return end
        if store.stats().full then finish('size limit');return end
        if elapsed>=next_flush then
            local _,pending=store.flush(16)
            if pending==0 then file:flush();next_flush=elapsed+30 end
        end
        if elapsed>=next_status then status('active');next_status=elapsed+10 end
        if elapsed>=next_ledger then session_note('checkpoint');next_ledger=elapsed+300 end
        if not engine or not vr.is_runtime_ready() then return end
        field(engine:get_class(),'GameViewport',3448)
        local viewport=engine:get_property('GameViewport')
        if not viewport then return end
        assert(viewport:is_a(classes.Viewport),'Unexpected audit viewport')
        local size=layout:GetViewportSize(viewport)
        if not size or size.X<=0 or size.Y<=0 then return end
        local deadline=begin+.00075
        components(begin+.00025)
        if head>#queue and elapsed>=next_query then discover(viewport) end
        local n=0
        while head<=#queue and n<16 and clock()<deadline do
            local ref=queue[head];head=head+1;n=n+1
            local sampled,reason=pcall(sample,ref,size)
            if not sampled then
                errors=errors+1
                if errors<=8 then store.event({type='error',message=tostring(reason),widget=ref.name}) end
                if errors>=64 then finish('error limit');break end
            end
        end
        max_tick_ms=math.max(max_tick_ms,(clock()-begin)*1000)
    end)
    if not ok then
        log.log_warn('[FarFarWest audit] Stopped safely: '..tostring(err))
        active=false
        if file then pcall(file.flush,file);pcall(file.close,file);file=nil end
        pcall(function() if store then status('error') end;command('error') end)
        queue,visited,links,schemas={}, {}, {}, {}
    end
end
return {tick=tick,reset=function() if active then finish('script reset') end end}
end
