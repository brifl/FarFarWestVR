local object_count=require('libs/object_count')
-- Replace only the vendor's spell-slot key row with Quest grip labels.
-- Native slot selection, action mappings, spell cards and cooldown HUD stay intact.
local source=package.searchpath('libs/spell_slot_hints',package.path)
local root=source and source:gsub('\\','/'):match('^(.*)/scripts/libs/spell_slot_hints%.lua$')
local check_layout=require('libs/hint_layout')
return function(asset_directory)
local api,log=uevr.api,uevr.params.functions
local assets=asset_directory or (root and root..'/assets/control_hints/')
local array,library,rendering,slot_class,viewport_class
local entries,textures={},{}
local elapsed,next_query,failed=0,0,false
local kinds={
    [0]={action='IA_SpellA',file='left_grip.png',aspect=127/96,label='LG'},
    [1]={action='IA_SpellB',file='right_grip.png',aspect=137/96,label='RG'},
    [2]={action='IA_SpellC',file='both_grips.png',aspect=302/96,label='LG+RG'},
}
local function field(class,name,offset)
    local p=class:find_property(name)
    assert(p and p:get_offset()==offset,'Unexpected spell hint field: '..name)
end
local function method(class,name,size,fields)
    local fn=class:find_function(name)
    assert(fn and fn:get_properties_size()==size,'Unexpected spell hint function: '..name)
    for name,offset in pairs(fields or {}) do field(fn,name,offset) end
end
local function track(object)
    local count=object_count(array)
    local index=object:read_dword(12)
    assert(index<count,'Invalid spell hint object index')
    local current=array:get_object(index)
    assert(current and current:get_address()==object:get_address(),'Spell hint identity mismatch')
    return {object=object,index=index,address=object:get_address(),name=object:get_short_name()}
end
local function valid(ref)
    local object=ref and array:get_object(ref.index)
    return object and object:get_address()==ref.address and object:get_short_name()==ref.name
end
local function hidden(object)
    local v=object:get_property('Visibility');return v==1 or v==2
end
local function prepare()
    assert(assets,'Cannot locate spell hint assets beside the profile scripts')
    array=api:get_uobject_array()
    assert(array and array.get_objects_offset()==0 and array.get_item_distance()==24,'Unexpected object array')
    local class=api:find_uobject('Class /Script/UMG.WidgetBlueprintLibrary')
    assert(class,'Widget library missing')
    method(class,'GetAllWidgetsOfClass',40,{WorldContextObject=0,FoundWidgets=8,WidgetClass=24,TopLevelOnly=32})
    library=class:get_class_default_object()
    class=api:find_uobject('Class /Script/Engine.KismetRenderingLibrary')
    assert(class,'Texture library missing')
    method(class,'ImportFileAsTexture2D',32,{WorldContextObject=0,Filename=8,ReturnValue=24})
    rendering=class:get_class_default_object()
    class=api:find_uobject('Class /Script/UMG.Image');assert(class,'Image class missing')
    method(class,'SetBrushFromTexture',16,{Texture=0,bMatchSize=8})
    method(class,'SetDesiredSizeOverride',16,{DesiredSize=0})
    method(class,'GetDesiredSize',16)
    method(class,'SetVisibility',1)
    field(class,'Visibility',221)
    class=api:find_uobject('Class /Script/UMG.PanelWidget');assert(class,'Panel class missing')
    method(class,'GetChildrenCount',4);method(class,'GetChildAt',16)
    viewport_class=api:find_uobject('Class /Script/Engine.GameViewportClient')
    assert(library and rendering and viewport_class,'Native hint libraries unavailable')
end
local function texture(kind,viewport)
    local ref=textures[kind.file]
    if not valid(ref) then
        local object=rendering:ImportFileAsTexture2D(viewport,assets..kind.file)
        assert(object and object:get_class():get_short_name()=='Texture2D','Cannot load spell hint: '..kind.file)
        ref=track(object);textures[kind.file]=ref
    end
    return ref.object
end
local function discover(viewport)
    if elapsed<next_query then return end
    next_query=elapsed+.25
    if not valid(slot_class) then
        local class=api:find_uobject('WidgetBlueprintGeneratedClass /Game/Interfaces/Spells/UI_Spell_CardSlot.UI_Spell_CardSlot_C')
        if not class then return end
        assert(class:get_short_name()=='UI_Spell_CardSlot_C','Unexpected spell-slot class')
        check_layout(class)
        slot_class=track(class)
    end
    local found={}
    library:GetAllWidgetsOfClass(viewport,found,slot_class.object,false)
    assert(#found<=16,'Too many spell-slot widgets')
    local next_entries={}
    for _,object in ipairs(found) do
        assert(object:get_class():get_short_name()=='UI_Spell_CardSlot_C','Unexpected spell-slot result')
        local address=object:get_address()
        local ref=track(object)
        local old=entries[address]
        ref.reported=old and old.index==ref.index and old.reported
        next_entries[address]=ref
    end
    entries=next_entries
end
local function update(entry,viewport)
    local slot=entry.object
    if hidden(slot) then return end
    local kind=kinds[slot:get_int_property('ID')]
    local action=slot:get_property('actionKey')
    if not kind or not action or action:get_short_name()~=kind.action then return end
    local panel=slot:get_property('HorizontalBox_Keys')
    if not panel or hidden(panel) then return end
    local count=panel:GetChildrenCount();assert(count>=0 and count<=8,'Unexpected spell hint row')
    local first=true
    for i=0,count-1 do
        local key=panel:GetChildAt(i)
        if key and key:get_class():get_short_name()=='UI_Key_C' then
            if first then
                first=false
                local class=key:get_class()
                check_layout(class)
                local image,text=key:get_property('Image_GamepadIcon'),key:get_property('Text_Key')
                if not image or not text then return end
                assert(image:get_class():get_short_name()=='Image' and text:get_class():get_short_name()=='TextBlock',
                    'Unexpected spell hint children')
                local asset=texture(kind,viewport)
                local brush=image:get_property('Brush')
                local resource=brush.ResourceObject
                if not resource or resource:get_address()~=asset:get_address() then
                    local height=brush.ImageSize.Y
                    assert(height>0 and height<=128,'Unexpected spell hint height')
                    image:SetBrushFromTexture(asset,false)
                    local size=image:GetDesiredSize() -- Preserve the native typed FVector2D.
                    size.X,size.Y=height*kind.aspect,height
                    image:SetDesiredSizeOverride(size)
                end
                if hidden(key) then key:SetVisibility(3) end
                if hidden(image) then image:SetVisibility(3) end
                if not hidden(text) then text:SetVisibility(1) end
                if not entry.reported then
                    entry.reported=true
                    log.log_info('[FarFarWest hints] Vendor spell slot '..kind.action..' uses '..kind.label..'.')
                end
            elseif not hidden(key) then key:SetVisibility(1) end
        end
    end
end
local function tick(engine,delta)
    if failed then return end
    local ok,err=pcall(function()
        elapsed=elapsed+math.min(math.max(delta or 0,0),.1)
        if not engine then return end
        if not array then prepare() end
        field(engine:get_class(),'GameViewport',3448)
        local viewport=engine:get_property('GameViewport')
        if not viewport then return end
        assert(viewport:is_a(viewport_class),'Unexpected native viewport')
        discover(viewport)
        for address,entry in pairs(entries) do
            if valid(entry) then update(entry,viewport) else entries[address]=nil;next_query=0 end
        end
    end)
    if not ok then
        failed=true;entries={}
        log.log_warn('[FarFarWest hints] Spell hints stopped safely: '..tostring(err))
    end
end
return {tick=tick,reset=function() entries,textures,next_query={},{},0 end}
end
