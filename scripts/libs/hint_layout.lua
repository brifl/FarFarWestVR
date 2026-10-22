-- Only the complete key/slot layouts measured in supported game builds are accepted.
local schemas={
    UI_Key_C={
        {Key=856,gamepadKeys=864,Image_GamepadIcon=848,Text_Key=832,Text_Hold=840},
        {Key=840,gamepadKeys=848,Image_GamepadIcon=832,Text_Key=816,Text_Hold=824},
    },
    UI_Spell_CardSlot_C={
        {ID=888,actionKey=944,HorizontalBox_Keys=856},
        {ID=896,actionKey=952,HorizontalBox_Keys=856},
    },
}
return function(class)
    local name=class:get_short_name()
    for _,schema in ipairs(schemas[name] or {}) do
        local matched=true
        for field,offset in pairs(schema) do
            local p=class:find_property(field)
            if not p or p:get_offset()~=offset then matched=false;break end
        end
        if matched then return end
    end
    error('Unverified hint widget layout: '..name)
end
