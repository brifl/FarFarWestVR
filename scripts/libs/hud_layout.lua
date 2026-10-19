-- Configurable offsets for live HUD panels; all text/state stays in the game widget.
return function()
local api,vr,functions=uevr.api,uevr.params.vr,uevr.params.functions
local tuning=require('libs/tuning')
local positioning=require('libs/screen_widget_projection')
local targets={
    UI_NpcTalk_C={key='hud.dialogue_offset_y',field='TextBlock_Text',offset=832},
    UI_Lifebar_Boss_C={key='hud.boss_health_offset_y',field='ProgressBar_Boss',offset=840},
    UI_Counter_C={key='hud.mission_info_offset_y',field='Text_Title',offset=816},
    UI_Timer_C={key='hud.mission_info_offset_y',field='TextBlock_Seconds',offset=816},
    UI_Player_C={children={
        {key='hud.compass_offset_y',field='Image_Compass',offset=1008},
        {key='hud.compass_offset_y',field='Overlay_Pings',offset=944},
    }},
}
local array,widget_class,slate,layout,scan_index
local entries,elapsed,next_scan={},0,0
local stopped=false
local function valid_ref(ref)
    local object=array:get_object(ref.index)
    return object and object:get_address()==ref.address and object:get_short_name()==ref.name
end
local function valid(entry)
    if not valid_ref(entry) then return false end
    if entry.root then
        if not valid_ref(entry.root) then return false end
        local child=entry.root.object:get_property(entry.kind.field)
        return child and child:get_address()==entry.address
    end
    return true
end
local function reset()
    for _,entry in pairs(entries) do
        if valid_ref(entry) then pcall(positioning.restore,entry.binding) end
    end
    entries,scan_index,next_scan={},nil,0
end
local function checked(class,method,minimum,maximum)
    local fn=class:find_function(method)
    assert(fn,'Missing function '..method)
    local size=fn:get_properties_size()
    assert(size>=minimum and size<=maximum,'Unexpected parameters: '..method)
    local field,count=fn:get_child_properties(),0
    while field do
        count=count+1;assert(count<=16,'Unexpected parameter chain: '..method)
        local property=fn:find_property(field:get_fname():to_string())
        assert(property and property:get_offset()>=0 and property:get_offset()<size,
            'Invalid parameter metadata: '..method)
        field=field:get_next()
    end
end
local function prepare()
    array=api:get_uobject_array()
    assert(array and array.get_objects_offset()==0 and array.get_item_distance()==24,
        'Compact object array unavailable')
    widget_class=api:find_uobject('Class /Script/UMG.Widget')
    local library=api:find_uobject('Class /Script/UMG.SlateBlueprintLibrary')
    local viewport=api:find_uobject('Class /Script/UMG.WidgetLayoutLibrary')
    assert(widget_class and library and viewport,'UMG classes unavailable')
    local transform=widget_class:find_property('RenderTransform')
    assert(transform and transform:get_offset()==144,'Unexpected widget layout')
    checked(widget_class,'SetRenderTranslation',16,16)
    checked(widget_class,'GetCachedGeometry',32,256)
    checked(library,'GetLocalSize',32,512)
    checked(library,'LocalToViewport',64,512)
    checked(viewport,'GetViewportSize',24,24)
    slate=library:get_class_default_object();layout=viewport:get_class_default_object()
    assert(slate and layout,'Widget geometry libraries unavailable')
end
local function check_field(object,kind)
    local field=object:get_class():find_property(kind.field)
    assert(field and field:get_offset()==kind.offset,'HUD panel layout mismatch: '..kind.key)
end
local function bind(object,index,kind,root)
    local address=object:get_address()
    if entries[address] then return end
    local current=array:get_object(index)
    assert(current and current:get_address()==address,'HUD object identity mismatch')
    entries[address]={object=object,index=index,address=address,name=object:get_short_name(),
        kind=kind,root=root,binding=positioning.bind(object,slate)}
end
local function discover()
    if elapsed<next_scan then return end
    local count=array:get_object_count()
    assert(count>0 and count<=250000,'Object count exceeds verified budget')
    if scan_index==nil or scan_index>=count then scan_index=count-1 end
    for _=1,512 do
        if scan_index<0 then scan_index=nil;next_scan=elapsed+1;return end
        local index=scan_index;local object=array:get_object(index);scan_index=index-1
        local name=object and object:get_short_name()
        if name and name:match('^UI_') and not entries[object:get_address()] then
            local kind=targets[object:get_class():get_short_name()]
            if kind and object:is_a(widget_class) then
                if kind.children then
                    local root={object=object,index=index,address=object:get_address(),name=name}
                    for _,child_kind in ipairs(kind.children) do
                        check_field(object,child_kind)
                        local child=object:get_property(child_kind.field)
                        if child and child:is_a(widget_class) then
                            bind(child,child:read_dword(12),child_kind,root)
                        end
                    end
                else
                    check_field(object,kind)
                    bind(object,index,kind)
                end
            end
        end
    end
end
local function tick(_,delta)
    if stopped then return end
    local ok,err=pcall(function()
        elapsed=elapsed+math.min(math.max(delta or 0,0),.1)
        if not vr.is_runtime_ready() or not vr.is_hmd_active() then reset();return end
        if not array then prepare() end
        discover()
        local count=0
        for address,entry in pairs(entries) do
            count=count+1;assert(count<=32,'Too many HUD panels')
            if not valid(entry) then
                if valid_ref(entry) then pcall(positioning.restore,entry.binding) end
                entries[address]=nil
            else
                local fraction=tuning.get(entry.kind.key)
                if fraction==0 then positioning.restore(entry.binding)
                else
                    local viewport=layout:GetViewportSize(entry.object)
                    if viewport and viewport.Y>0 and positioning.offset(entry.binding,0,viewport.Y*fraction)
                        and entry.reported~=fraction then
                        entry.reported=fraction
                        functions.log_info(string.format('[FarFarWest HUD] %s offset %.3f viewport heights.',entry.kind.key,fraction))
                    end
                end
            end
        end
    end)
    if not ok then
        pcall(reset);stopped=true
        functions.log_warn('[FarFarWest HUD] Stopped safely: '..tostring(err))
    end
end
return {tick=tick,reset=reset}
end
