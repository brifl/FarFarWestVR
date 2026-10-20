-- Quest X sends F. Keep the dialogue's native X icon when that synthetic key
-- makes the game select a keyboard hint; action bindings and dialogue stay native.
return function(valid)
local api,log=uevr.api,uevr.params.functions
local panel_class,binding,failed,reported
local function field(class,name,offset)
    local property=class:find_property(name)
    assert(property and property:get_offset()==offset,'Unexpected dialogue hint field: '..name)
end
local function track(object)
    local ref={object=object,index=object:read_dword(12),address=object:get_address(),name=object:get_short_name()}
    assert(valid(ref),'Dialogue hint identity mismatch')
    return ref
end
local function hidden(widget)
    local visibility=widget:get_property('Visibility')
    return visibility==1 or visibility==2
end
local function bind(source,panel)
    if not panel_class then
        panel_class=api:find_uobject('Class /Script/UMG.PanelWidget')
        assert(panel_class,'PanelWidget unavailable')
        for name,size in pairs({GetChildrenCount=4,GetChildAt=16}) do
            local fn=panel_class:find_function(name)
            assert(fn and fn:get_properties_size()==size,'Unexpected panel function: '..name)
        end
    end
    assert(panel:is_a(panel_class),'Unexpected dialogue hint panel')
    local count=panel:GetChildrenCount()
    assert(count>=0 and count<=8,'Unexpected dialogue hint child count')
    for i=0,count-1 do
        local key=panel:GetChildAt(i)
        if key and key:get_class():get_short_name()=='UI_Key_C' then
            local class=key:get_class()
            for name,offset in pairs({Key=856,Image_GamepadIcon=848,Text_Key=832}) do field(class,name,offset) end
            local fn=class:find_function('F_RefreshKey')
            assert(fn and fn:get_properties_size()==1,'Unexpected hint refresh function')
            field(fn,'isGamepad',0)
            local image,text=key:get_property('Image_GamepadIcon'),key:get_property('Text_Key')
            if not image or not text then return end -- Widget construction can lag its parent.
            assert(image:get_class():get_short_name()=='Image' and text:get_class():get_short_name()=='TextBlock',
                'Unexpected dialogue hint children')
            return {source=source:get_address(),panel=track(panel),key=track(key),image=track(image),text=track(text)}
        end
    end
end
local function update(source)
    if failed then return end
    local ok,err=pcall(function()
        if hidden(source) then return end
        if binding and (binding.source~=source:get_address() or not valid(binding.panel)
            or not valid(binding.key) or not valid(binding.image) or not valid(binding.text)) then binding=nil end
        if not binding then
            local class=source:get_class()
            assert(class:get_short_name()=='UI_NpcTalk_C','Unexpected dialogue class')
            field(class,'HorizontalBox_NextKey',856)
        end
        local panel=source:get_property('HorizontalBox_NextKey')
        if not panel or hidden(panel) then return end
        if binding and panel:get_address()~=binding.panel.address then binding=nil end
        if not binding then binding=bind(source,panel) end
        if not binding then return end
        local key=binding.key.object
        local action=key:get_property('Key')
        if not action or action:get_short_name()~='IA_Interact' then return end
        if hidden(binding.image.object) or not hidden(binding.text.object) then
            key:F_RefreshKey(true)
            if not reported then
                reported=true
                log.log_info('[FarFarWest hints] Dialogue Next hint retains the Quest X icon.')
            end
        end
    end)
    if not ok then
        binding=nil;failed=true
        log.log_warn('[FarFarWest hints] Dialogue hint stopped safely: '..tostring(err))
    end
end
return {update=update,reset=function() binding=nil end}
end
