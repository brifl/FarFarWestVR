-- Change presentation only: Quest X emits the native F/Interact action.
local M={}
local check_layout=require('libs/hint_layout')
local checked={}
local function field(class,name,offset)
    local p=class:find_property(name)
    assert(p and p:get_offset()==offset,'Unexpected interaction key field '..name)
end
local function hidden(widget)
    local v=widget:get_property('Visibility');return v==1 or v==2
end
function M.update(key)
    local class=key:get_class()
    assert(class:get_short_name()=='UI_Key_C','Unexpected interaction key class')
    if hidden(key) then return false end
    local address=class:get_address()
    if not checked[address] then
        check_layout(class)
        local fn=class:find_function('F_RefreshKey')
        assert(fn and fn:get_properties_size()==1,'Unexpected interaction refresh parameters')
        field(fn,'isGamepad',0);checked[address]=true
    end
    local action,override=key:get_property('Key'),key:get_property('gamepadKeys')
    if not action or action:get_short_name()~='IA_Interact' then return false end
    if override and override:get_short_name()~='IA_Interact' then return false end
    local image,text,hold=key:get_property('Image_GamepadIcon'),key:get_property('Text_Key'),key:get_property('Text_Hold')
    if not image or not text then return false end
    assert(image:get_class():get_short_name()=='Image' and text:get_class():get_short_name()=='TextBlock',
        'Unexpected interaction presentation widgets')
    if hidden(image) or not hidden(text) then
        local hold_visibility=hold and hold:get_property('Visibility')
        key:F_RefreshKey(true)
        -- Synthetic F still uses native keyboard hold rules; only the icon changes.
        local current_hold=key:get_property('Text_Hold')
        if current_hold and hold_visibility~=nil and current_hold:get_property('Visibility')~=hold_visibility then
            current_hold:SetVisibility(hold_visibility)
        end
        return true
    end
    return false
end
return M
