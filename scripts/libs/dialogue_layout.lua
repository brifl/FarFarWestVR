-- Keep the game's live conversation panel, raised within its existing HUD.
return function()
local api,vr,functions=uevr.api,uevr.params.vr,uevr.params.functions
local array,widget_class,slate,widget,index,address,name,original
local scan_index,next_scan,elapsed= nil,0,0
local written,stopped,reported=false,false,false
local height_fraction=.10
local function finite(n) return type(n)=="number" and n==n and math.abs(n)<1e12 end
local function valid()
    if not widget or not array then return false end
    local current=array:get_object(index)
    return current and current:get_address()==address and current:get_short_name()==name
end
local function reset()
    if written and valid() then widget:SetRenderTranslation(original) end
    widget,index,address,name,original=nil,nil,nil,nil,nil
    written,scan_index,next_scan=false,nil,0
end
local function checked(class,method,minimum,maximum)
    local fn=class:find_function(method)
    assert(fn,"Missing function "..method)
    local size=fn:get_properties_size()
    assert(size>=minimum and size<=maximum,"Unexpected parameters: "..method)
    local field,count=fn:get_child_properties(),0
    while field do
        count=count+1;assert(count<=16,"Unexpected parameter chain: "..method)
        local property=fn:find_property(field:get_fname():to_string())
        assert(property and property:get_offset()>=0 and property:get_offset()<size,
            "Invalid parameter metadata: "..method)
        field=field:get_next()
    end
end
local function prepare()
    array=api:get_uobject_array()
    assert(array and array.get_objects_offset()==0 and array.get_item_distance()==24,
        "Compact object array unavailable")
    widget_class=api:find_uobject("Class /Script/UMG.UserWidget")
    local library=api:find_uobject("Class /Script/UMG.SlateBlueprintLibrary")
    assert(widget_class and library,"UMG classes unavailable")
    local transform=widget_class:find_property("RenderTransform")
    assert(transform and transform:get_offset()==144,"Unexpected widget layout")
    checked(widget_class,"SetRenderTranslation",16,16)
    checked(widget_class,"GetCachedGeometry",32,256)
    checked(library,"GetLocalSize",32,512)
    slate=library:get_class_default_object()
    assert(slate,"Slate library unavailable")
end
local function discover()
    if elapsed<next_scan then return end
    local count=array:get_object_count()
    assert(count>0 and count<=250000,"Object count exceeds verified budget")
    if scan_index==nil or scan_index>=count then scan_index=count-1 end
    for _=1,512 do
        if scan_index<0 then scan_index=nil;next_scan=elapsed+1;return end
        local slot=scan_index;local object=array:get_object(slot);scan_index=slot-1
        if object and object:get_short_name():match("^UI_NpcTalk_C_") and object:is_a(widget_class)
            and object:get_class():get_short_name()=="UI_NpcTalk_C" then
            local field=object:get_class():find_property("TextBlock_Text")
            assert(field and field:get_offset()==832,"Unexpected conversation panel layout")
            local transform=object:get_property("RenderTransform")
            assert(finite(transform.Translation.X) and finite(transform.Translation.Y),"Invalid dialogue position")
            widget,index,address,name=object,slot,object:get_address(),object:get_short_name()
            original={X=transform.Translation.X,Y=transform.Translation.Y}
            return
        end
    end
end
local function tick(_,delta)
    if stopped then return end
    local ok,err=pcall(function()
        elapsed=elapsed+math.min(math.max(delta or 0,0),.1)
        if not vr.is_runtime_ready() or not vr.is_hmd_active() then reset();return end
        if not array then prepare() end
        if widget and not valid() then reset() end
        if not widget then discover() end
        if not widget then return end
        -- This panel fills the viewport. Local geometry accounts for DPI, so a
        -- tenth of its height remains the same screen fraction at any resolution.
        local size=slate:GetLocalSize(widget:GetCachedGeometry())
        if not size or not finite(size.Y) or size.Y<=0 then return end
        local target=original.Y-size.Y*height_fraction
        local current=widget:get_property("RenderTransform").Translation
        if not written or math.abs(current.Y-target)>.1 or math.abs(current.X-original.X)>.1 then
            written=true -- Restore even if the native call partially fails.
            widget:SetRenderTranslation({X=original.X,Y=target})
        end
        if not reported then
            reported=true
            functions.log_info(string.format("[FarFarWest dialogue] Live conversation panel raised %.1f local units (one tenth of its height).",size.Y*height_fraction))
        end
    end)
    if not ok then
        pcall(reset);stopped=true
        functions.log_warn("[FarFarWest dialogue] Stopped safely: "..tostring(err))
    end
end
return {tick=tick,reset=reset}
end
