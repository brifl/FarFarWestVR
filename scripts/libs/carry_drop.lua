-- The 0.3 carry prompt uses IA_Drop instead of the previous Interact action.
-- Dispatch its native input event on a fresh Quest X press, only for its owning item.
return function()
local api,vr,log=uevr.api,uevr.params.vr,uevr.params.functions
local query=require('libs/live_widgets')(
    'WidgetBlueprintGeneratedClass /Game/Interfaces/UI_Key.UI_Key_C',256,.1)
local key_hint=require('libs/interaction_key')
local array,statics,value_library,interact,button
local elapsed,latched,failed,hint=0,true,false,nil
local event='InpActEvt_IA_Drop_K2Node_EnhancedInputActionEvent_14'
local function field(c,n,offset)
    local p=c:find_property(n);assert(p and p:get_offset()==offset,'Unexpected carry field '..n)
end
local function method(c,n,size,fields)
    local f=c:find_function(n);assert(f and f:get_properties_size()==size,'Unexpected carry function '..n)
    for p,o in pairs(fields or {}) do field(f,p,o) end
    return f
end
local function address(o) return o and o:get_address() end
local function prepare()
    array=api:get_uobject_array()
    assert(array and array.get_objects_offset()==0 and array.get_item_distance()==24,'Unexpected carry array')
    local c=assert(api:find_uobject('Class /Script/Engine.GameplayStatics'))
    method(c,'GetPlayerController',24,{WorldContextObject=0,PlayerIndex=8,ReturnValue=16})
    statics=assert(c:get_class_default_object())
    c=assert(api:find_uobject('Class /Script/EnhancedInput.EnhancedInputLibrary'))
    method(c,'MakeInputActionValueOfType',64,{X=0,Y=8,Z=16,ValueType=24,ReturnValue=32})
    value_library=assert(c:get_class_default_object())
    c=assert(api:find_uobject('Class /Script/UMG.Widget'));method(c,'GetParent',8)
    button=vr.get_action_handle('/actions/default/in/AButtonLeft') -- Quest X.
end
local function belongs(key,context)
    local node=key
    for _=1,16 do
        if not node then return false end
        if address(node)==address(context) then return true end
        local parent=node:GetParent()
        if not parent then
            local outer=node:get_outer()
            if outer and outer:get_class():get_short_name()=='WidgetTree' then parent=outer:get_outer() end
        end
        node=parent
    end
    return false
end
local function refresh(key)
    local hold=key:get_property('Text_Hold');local visibility=hold and hold:get_property('Visibility')
    key:F_RefreshKey(true)
    hold=key:get_property('Text_Hold')
    if hold and visibility~=nil and hold:get_property('Visibility')~=visibility then hold:SetVisibility(visibility) end
end
local function restore_hint()
    if hint and query.valid(hint.ref) then
        local key=hint.ref.object
        if address(key:get_property('gamepadKeys'))==hint.interact.address then
            local original=hint.original and query.valid(hint.original) and hint.original.object or nil
            key:set_property('gamepadKeys',original);refresh(key)
        end
    end
    hint=nil
end
local function tick(engine,delta)
    if failed then return end
    local ok,err=pcall(function()
        elapsed=elapsed+math.min(math.max(delta or 0,0),.1)
        if not engine or not vr.is_runtime_ready() or not vr.is_hmd_active() or log.is_drawing_ui()
            or _G.farfarwest_gameplay_ready~=true or vr:get_mod_value('VR_2DScreenMode')~='false' then
            restore_hint();latched=true;return
        end
        if not statics then prepare() end
        local down=vr.is_action_active(button,vr.get_left_joystick_source())
        local pressed=down and not latched;latched=down
        field(engine:get_class(),'GameViewport',3448)
        local viewport=engine:get_property('GameViewport');if not viewport then restore_hint();return end
        local pc=statics:GetPlayerController(viewport,0)
        if not pc then restore_hint();return end
        field(pc:get_class(),'Pawn',744)
        local pawn=pc:get_property('Pawn');if not pawn then restore_hint();return end
        local ac_field=pawn:get_class():find_property('AC_PlayerItems')
        if not ac_field then restore_hint();return end
        assert(ac_field:get_offset()==1768,'Unexpected carry items field')
        local items=pawn:get_property('AC_PlayerItems');if not items then restore_hint();return end
        field(items:get_class(),'equipedItem',208)
        local item=items:get_property('equipedItem');if not item then restore_hint();return end
        field(item:get_class(),'UI_ItemContext',1120)
        local context=item:get_property('UI_ItemContext')
        if not context or context:get_class():get_short_name()~='UI_DropItem_C' then restore_hint();return end
        local visibility=context:get_property('Visibility')
        if visibility==1 or visibility==2 then restore_hint();return end
        field(item:get_class(),'OwningPlayer',736)
        if address(item:get_property('OwningPlayer'))~=address(pawn) then restore_hint();return end
        local found=query.get(engine,elapsed)
        if hint and (not query.valid(hint.ref) or hint.context~=address(context)) then restore_hint() end
        if not hint then
            if not query.valid(interact) then
                local action=api:find_uobject('InputAction /Game/Player/Inputs/IA_Interact.IA_Interact')
                if not action then return end
                interact=query.track(action)
            end
            for _,ref in pairs(found) do
                if query.valid(ref) then
                    local key=ref.object;local action=key:get_property('Key')
                    if action and action:get_full_name()=='InputAction /Game/Player/Inputs/IA_Drop.IA_Drop'
                        and belongs(key,context) then
                        key_hint.validate(key:get_class())
                        local override=key:get_property('gamepadKeys')
                        if override and override:get_short_name()~='IA_Drop' then return end
                        method(pawn:get_class(),event,48,{ActionValue=0,ElapsedTime=32,TriggeredTime=36,SourceAction=40})
                        hint={ref=ref,context=address(context),interact=interact,
                            original=override and query.track(override),action=query.track(action)}
                        key:set_property('gamepadKeys',interact.object);refresh(key)
                        log.log_info('[FarFarWest carry] Held-item Drop is available on Quest X.')
                        break
                    end
                end
            end
        end
        if hint and query.valid(hint.ref) and query.valid(hint.action) then
            local key=hint.ref.object;local v=key:get_property('Visibility')
            if v==1 or v==2 then return end
            local image,text=key:get_property('Image_GamepadIcon'),key:get_property('Text_Key')
            if image and text and (image:get_property('Visibility')==1 or image:get_property('Visibility')==2
                or (text:get_property('Visibility')~=1 and text:get_property('Visibility')~=2)) then refresh(key) end
            if pressed then
                -- Use the game's input entry, retaining its drop permission/replication logic.
                local fn=method(pawn:get_class(),event,48,{ActionValue=0,ElapsedTime=32,TriggeredTime=36,SourceAction=40})
                local value=value_library:MakeInputActionValueOfType(1,0,0,0) -- Boolean action value.
                fn(pawn,value,0,0,hint.action.object)
                log.log_info('[FarFarWest carry] Dispatched native Drop input on Quest X.')
            end
        end
    end)
    if not ok then
        pcall(restore_hint);failed=true
        log.log_warn('[FarFarWest carry] Stopped safely: '..tostring(err))
    end
end
return {tick=tick,reset=function() restore_hint();latched=true end}
end
