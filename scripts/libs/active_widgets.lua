-- Find nested widgets through current viewport roots and corrected world widgets.
-- Avoid enumerating every retained UI_Key in a long multiplayer session.
return function(path,limit,interval)
local api=uevr.api
local roots=require('libs/live_widgets')('Class /Script/UMG.UserWidget',256,interval,true)
local registry=require('libs/ui_audit_registry')
local classes,target,world
local entries,queue,head,visited={}, {},1,{}
local elapsed_next,next_class_query,total,reported=0,0,0,false
local clock=os.clock
local function reset()
    roots.reset();entries,queue,head,visited={}, {},1,{};elapsed_next=0;next_class_query=0;world=nil
end
local function prepare()
    classes={}
    for _,name in ipairs({'UserWidget','WidgetTree','PanelWidget','Widget'}) do
        classes[name]=assert(api:find_uobject('Class /Script/UMG.'..name),'Missing active widget class '..name)
    end
    local p=classes.UserWidget:find_property('WidgetTree')
    assert(p and p:get_offset()==704,'Unexpected active widget tree')
    assert(classes.WidgetTree:find_property('RootWidget'),'Missing active widget root')
    for name,size in pairs({GetChildrenCount=4,GetChildAt=16}) do
        local f=classes.PanelWidget:find_function(name)
        assert(f and f:get_properties_size()==size,'Unexpected active widget method '..name)
    end
    p=classes.Widget:find_property('Visibility')
    assert(p and p:get_offset()==221,'Unexpected active widget visibility')
end
local function budget()
    if reported then return end
    reported=true
    uevr.params.functions.log_warn('[FarFarWest hints] Active widget traversal reached its budget; keeping partial results.')
end
local function enqueue(o)
    if not o then return end
    local address=o:get_address()
    if visited[address] then return end
    if #queue>=4096 then budget();return end
    visited[address]=true;queue[#queue+1]=roots.track(o)
end
local function get(engine,time)
    if not engine then return entries end
    local found=roots.get(engine,time)
    local viewport=engine:get_property('GameViewport')
    local address=viewport and viewport:get_address()
    if world~=address then
        entries,queue,head,visited={}, {},1,{};elapsed_next=0;next_class_query=0;world=address
    end
    if not viewport then return entries end
    if not classes then prepare() end
    if not roots.valid(target) then
        entries={}
        if time<next_class_query then return entries end
        next_class_query=time+1
        local c=api:find_uobject(path)
        if not c then return entries end
        target=roots.track(c);entries,queue,head={}, {},1;elapsed_next=0
    end
    if head>#queue then
        if time<elapsed_next then return entries end
        elapsed_next=time+(interval or .25)
        entries,queue,head,visited,total={}, {},1,{},0
        for _,ref in pairs(found) do if roots.valid(ref) then enqueue(ref.object) end end
        registry.visit_sources(roots.valid,enqueue)
    end
    local deadline=clock()+.0005
    for i=1,128 do
        if head>#queue then break end
        local ref=queue[head];head=head+1
        if roots.valid(ref) then
            local o=ref.object
            local visibility=o:get_property('Visibility')
            if visibility~=1 and visibility~=2 then
                if o:is_a(target.object) then
                    if total>=limit then budget();head=#queue+1;break end
                    entries[ref.address]=ref;total=total+1
                end
                if o:is_a(classes.UserWidget) then
                    local tree=o:get_property('WidgetTree')
                    enqueue(tree and tree:get_property('RootWidget'))
                end
                if o:is_a(classes.PanelWidget) then
                    local n=o:GetChildrenCount()
                    assert(type(n)=='number' and n>=0 and n<=512 and n%1==0,'Unexpected active widget child count')
                    for index=0,n-1 do enqueue(o:GetChildAt(index)) end
                end
            end
        end
        if i%16==0 and clock()>=deadline then break end
    end
    return entries
end
return {get=get,valid=roots.valid,track=roots.track,reset=reset}
end
