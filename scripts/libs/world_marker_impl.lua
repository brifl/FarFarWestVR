local object_count=require('libs/object_count')
return function()
-- Reproject screen-space world markers through the rendered eye.
-- Preserve live labels, distances and interaction state in their original widgets.
local vr, functions, api = uevr.params.vr, uevr.params.functions, uevr.api
local ok, tag = pcall(functions.get_tag)
if not ok or tag ~= "ffw-ue58-sdk-v1" then return end
local loaded, geometry = pcall(require, "libs/reticle_projection")
if not loaded then functions.log_warn("[FarFarWest markers] Projection helper unavailable."); return end

local matrix = UEVR_Matrix4x4f.new()
local array, component_class, widget_class, factory, layout, slate, math_library
local entries, camera, entry_count = {}, nil, 0
local elapsed, next_scan, scan_index = 0, 0, nil
local candidates,candidate_count={},0
local first_scan,observed_count,recent_index,recent_min=true,nil,nil,nil
local clock=os and os.clock
local stage = "startup"
local stopped, reported, shape_reported = false, false, false
local kinds = {
    UI_WorldIcon_C={owner="^BP_WorldIcon_C_", image="Image_Icon", offset=808},
    UI_Guide_C={owner="^BP_LobbyGuide_C_", image="Image_Aura", offset=824, world_label=true},
    UI_Interact_C={owner="^BP_Player.*_C_", field="UI_Key",offset=816,screen=true},
    UI_PlayerInfos_C={owner_class="^BP_PlayerNameWidget_C$",field="PlayerNameText",offset=840,
        screen=true,screen_root=true,component_offset=680,additional_fields={PlayerState=872},
        shape_content=true,label="teammate marker"},
    UI_Damages_C={owner_class='^BP_UiDamages_C$',field='TextBlock_Damages',offset=808,
        screen=true,screen_root=true,component_offset=688,shape_field='TextBlock_Damages',
        transient=true,label='damage number'},
    UI_PingObjective_C={owner_class="^BP_ObjectivePing.*_C$",field="OwningActor",offset=912,
        world_label=true,actor_field="OwningActor",target_field="Location",target_offset=872,label="objective marker"},
    UI_ObjectPing_C={owner_class="^BP_ObjectPing.*_C$",field="Image_Logo",offset=824,
        world_label=true,target_field="Location",target_offset=864,label="object ping",
        parent_field="Scene",parent_offset=696,component_field="Widget",component_offset=688},
}
kinds.UI_Lifebar_C={field='ProgressBar_Boss',offset=808,world_label=true,attached=true,label='health bar',
    owners={'^BP_Enemy_.*_C$','^BP_CrypticTrain_Section_.*_C$','^BP_RadioactiveBarrel_C$','^BP_GasBomb_BossSpawner_C$'}}
kinds.UI_JokerCard_InGame_C={field='Overlay_Transform',offset=840,world_label=true,attached=true,
    label='dropped Joker card',owner_class='^BP_Pickable_Joker_C$'}
kinds.UI_NpcInGame_C={field='InteractTextHolder',offset=816,world_label=true,attached=true,
    label='NPC name label',owner_class='^BP_NPC_.*_C$'}
local mission_guide={owner_class="^BP_TextGuide.*_C$",field="InteractTextHolder",offset=816,
    world_label=true,label="mission guide"}
local screen_projection=require('libs/screen_widget_projection')
local ui_shape=require('libs/ui_shape')
local audit_registry=require('libs/ui_audit_registry')
local incident=require('libs/incident')
local rejected={}
local fast_discovery
local discovery_factory=require('libs/marker_discovery')
local function info(s) functions.log_info("[FarFarWest markers] "..s) end
local function finite(n) return type(n)=="number" and n==n and math.abs(n)<1e12 end
local function active()
    return _G.farfarwest_gameplay_ready == true and vr.is_runtime_ready()
        and vr.is_hmd_active() and not functions.is_drawing_ui()
        and vr:get_mod_value("VR_2DScreenMode") == "false"
end

local function track(object)
    local index = object:read_dword(12) -- Verified UObject internal index in this guarded build.
    assert(index<array:get_object_count(), "Object index outside the verified array")
    local ref = {object=object, index=index, address=object:get_address(), name=object:get_short_name()}
    assert(array:get_object(index):get_address()==ref.address, "Object identity mismatch")
    return ref
end
local function valid(ref)
    if not ref then return false end
    local object = array:get_object(ref.index)
    return object and object:get_address()==ref.address and object:get_short_name()==ref.name
end
local function free_attachment(component)
    local socket=component:get_property('AttachSocketName')
    local name=socket and (type(socket)=='string' and socket or socket:to_string())
    return (not name or name=='' or name=='None') and not component:get_property('bAbsoluteLocation')
end
local function component_valid(entry)
    if not valid(entry.component) or not valid(entry.source) or not valid(entry.owner) then return false end
    local widget = entry.component.object:get_property("Widget")
    if not widget or widget:get_address()~=entry.source.address then return false end
    if entry.shape_ref then
        if not valid(entry.shape_ref) then return false end
        local tree=not entry.kind.shape_field and entry.source.object:get_property('WidgetTree')
        local root=entry.kind.shape_field and entry.source.object:get_property(entry.kind.shape_field)
            or tree and tree:get_property('RootWidget')
        if not root or root:get_address()~=entry.shape_ref.address then return false end
    end
    if entry.kind.screen_root then
        local root=entry.owner.object:get_property('RootComponent')
        local bound=entry.owner.object:get_property('Widget')
        return root and root:get_address()==entry.component.address
            and bound and bound:get_address()==entry.component.address
    end
    if entry.parent then
        if not valid(entry.parent) or not valid(entry.root) then return false end
        local parent=entry.component.object:get_property("AttachParent")
        local root=entry.parent.object:get_property("AttachParent")
        local owner_root=entry.owner.object:get_property("RootComponent")
        if entry.kind.attached then
            if not free_attachment(entry.component.object) then return false end
            if not parent or parent:get_address()~=entry.parent.address
                or not owner_root or owner_root:get_address()~=entry.root.address then return false end
            for i,ref in ipairs(entry.chain) do
                if not valid(ref) then return false end
                local next_ref=entry.chain[i+1] or entry.root
                local next_parent=ref.object:get_property('AttachParent')
                if not next_parent or next_parent:get_address()~=next_ref.address then return false end
            end
            return true
        end
        local owner_widget=entry.owner.object:get_property(entry.kind.component_field)
        local owner_parent=entry.owner.object:get_property(entry.kind.parent_field)
        return parent and parent:get_address()==entry.parent.address
            and root and root:get_address()==entry.root.address
            and owner_root and owner_root:get_address()==entry.root.address
            and owner_widget and owner_widget:get_address()==entry.component.address
            and owner_parent and owner_parent:get_address()==entry.parent.address
    end
    return true
end
local function restore(entry)
    audit_registry.remove(entry.component.address)
    local display=entry.proxy or entry.source
    if entry.shape and valid(entry.shape_ref or display) then ui_shape.restore(entry.shape) end
    if valid(entry.proxy) then entry.proxy.object:RemoveFromParent() end
    if entry.screen and valid(entry.source) then screen_projection.restore(entry.screen) end
    if entry.moved and component_valid(entry) then
        entry.component.object:K2_SetRelativeLocation(entry.relative,false,{},true)
        entry.moved=false
    end
    if entry.hidden and valid(entry.source) then
        entry.source.object:SetRenderOpacity(entry.opacity)
    end
    entry.hidden = false
end
local function reset()
    for _, entry in pairs(entries) do pcall(restore, entry) end
    entries, camera, next_scan, scan_index, entry_count = {}, nil, 0, nil, 0
    candidates,candidate_count={},0
    first_scan,observed_count,recent_index,recent_min=true,nil,nil,nil
    rejected={}
end
local function guarded(fn)
    if stopped then return end
    local success, err = pcall(fn)
    if not success then
        reset(); stopped=true
        functions.log_warn("[FarFarWest markers] Stopped safely during "..stage..": "..tostring(err))
    end
end

local function checked(class, name, minimum, maximum)
    local fn = class:find_function(name)
    assert(fn, "Missing function "..name)
    local size = fn:get_properties_size()
    assert(size>=minimum and size<=maximum, "Unexpected parameter size: "..name)
    local field, count = fn:get_child_properties(), 0
    while field do
        count=count+1; assert(count<=32, "Unexpected parameter chain: "..name)
        local property=fn:find_property(field:get_fname():to_string())
        assert(property and property:get_offset()>=0 and property:get_offset()<size,
            "Invalid function metadata: "..name)
        field=field:get_next()
    end
end
local function default_object(path)
    local class=api:find_uobject("Class "..path)
    assert(class, "Missing class "..path)
    local object=class:get_class_default_object()
    assert(object, "Missing default object "..path)
    return object,class
end
local function prepare()
    array=api:get_uobject_array()
    assert(array and array.get_objects_offset()==0 and array.get_item_distance()==24,
        "Compact object array unavailable")
    component_class=api:find_uobject("Class /Script/UMG.WidgetComponent")
    widget_class=api:find_uobject("Class /Script/UMG.UserWidget")
    local image_class=api:find_uobject("Class /Script/UMG.Image")
    assert(component_class and widget_class and image_class, "UMG classes unavailable")
    for name,offset in pairs({Space=1512,WidgetClass=1520,Pivot=1568,Widget=1800}) do
        local p=component_class:find_property(name)
        assert(p and p:get_offset()==offset,"WidgetComponent layout mismatch: "..name)
    end
    checked(component_class,"K2_GetComponentLocation",24,24)
    checked(component_class,"GetOwner",8,8)
    checked(widget_class,"GetOwningPlayer",8,8)
    checked(widget_class,"GetOwningPlayerPawn",8,8)
    checked(widget_class,"GetDesiredSize",16,16)
    checked(widget_class,"ForceLayoutPrepass",0,0)
    checked(widget_class,"AddToViewport",4,4)
    checked(widget_class,"RemoveFromParent",0,0)
    checked(widget_class,"SetAlignmentInViewport",16,16)
    checked(widget_class,"SetDesiredSizeInViewport",16,16)
    checked(widget_class,"SetPositionInViewport",17,32)
    checked(widget_class,"SetRenderOpacity",4,4)
    checked(widget_class,"SetVisibility",1,1)
    checked(widget_class,"SetRenderScale",16,16)
    checked(widget_class,"SetRenderTransformPivot",16,16)
    checked(image_class,"SetBrush",64,512)
    checked(image_class,"SetColorAndOpacity",16,16)
    local class
    factory,class=default_object("/Script/UMG.WidgetBlueprintLibrary")
    checked(class,"Create",32,32)
    layout,class=default_object("/Script/UMG.WidgetLayoutLibrary")
    checked(class,"GetViewportSize",24,24)
    info("WidgetComponent layout and viewport functions verified.")
end

local function bind_world_label(component,source,kind)
    stage="verify live "..(kind.label or "lobby guide").." projection"
    local owner=component:GetOwner()
    local parent=component:GetAttachParent()
    local root=owner and owner:get_property("RootComponent")
    -- Only reposition this visual child. Its separate actor remains the target.
    -- Construction/reparenting may leave an attached bar outside the owner root
    -- temporarily. Leave it native and retry, rather than rejecting its identity.
    if kind.attached and (not parent or not root or root:get_address()==component:get_address()) then
        return 'attachment pending'
    end
    assert(parent and root and root:get_address()~=component:get_address(),
        "World label must be a child of its actor root")
    local chain
    if kind.attached then
        assert(free_attachment(component),'Socket/absolute marker attachment needs a separate adapter')
        chain={};local node=parent
        while node:get_address()~=root:get_address() do
            assert(#chain<8,'Marker attachment chain exceeds verified budget')
            chain[#chain+1]=track(node)
            local field=node:get_class():find_property('AttachParent')
            assert(field and field:get_offset()==208,'Marker parent layout differs')
            node=node:get_property('AttachParent')
            if not node then return 'attachment pending' end
        end
    elseif kind.parent_field then
        for field,offset in pairs({[kind.parent_field]=kind.parent_offset,[kind.component_field]=kind.component_offset}) do
            local p=owner:get_class():find_property(field)
            assert(p and p:get_offset()==offset,"Ping actor layout differs: "..field)
        end
        local bound_parent=owner:get_property(kind.parent_field)
        local bound_widget=owner:get_property(kind.component_field)
        local attach=parent:get_class():find_property("AttachParent")
        assert(attach and attach:get_offset()==208,"Ping scene attachment layout differs")
        local parent_root=parent:get_property("AttachParent")
        assert(bound_parent and bound_parent:get_address()==parent:get_address()
            and bound_widget and bound_widget:get_address()==component:get_address()
            and parent_root and parent_root:get_address()==root:get_address(),"Ping attachment binding differs")
        checked(parent:get_class(),"K2_GetComponentToWorld",96,96)
        if not math_library then
            local class
            math_library,class=default_object("/Script/Engine.KismetMathLibrary")
            checked(class,"TransformLocation",144,144)
        end
    else
        assert(root:get_address()==parent:get_address(),"World label must be a child of its actor root")
    end
    local relative=component:get_property("RelativeLocation")
    assert(finite(relative.X) and finite(relative.Y) and finite(relative.Z),"Invalid world-label attachment offset")
    if not kind.parent_field and not kind.attached then
        assert(math.abs(relative.X)<.001 and math.abs(relative.Y)<.001
            and math.abs(relative.Z)<.001,"Unexpected world-label attachment offset")
    end
    if kind.actor_field then
        local target=source:get_property(kind.actor_field)
        assert(target and target:get_address()==owner:get_address(),"Objective widget/actor binding differs")
    end
    if kind.target_field then
        local field=source:get_class():find_property(kind.target_field)
        assert(field and field:get_offset()==kind.target_offset,"World-label target layout differs")
    end
    if kind.attached then
        checked(parent:get_class(),'K2_GetComponentToWorld',96,96)
        if not math_library then
            local class
            math_library,class=default_object('/Script/Engine.KismetMathLibrary')
            checked(class,'TransformLocation',144,144)
        end
    end
    local player=source:GetOwningPlayer()
    assert(player,"World-label player unavailable")
    checked(component_class,"K2_SetWorldLocation",296,296)
    checked(component_class,"K2_SetRelativeLocation",296,296)
    checked(owner:get_class(),"K2_GetActorLocation",24,24)
    checked(player:get_class(),"DeprojectScreenPositionToWorld",64,64)
    local opacity=source:get_float_property("RenderOpacity")
    assert(finite(opacity),"Invalid lobby-guide opacity")
    entries[component:get_address()]={component=track(component),source=track(source),
        owner=track(owner),player=track(player),kind=kind,opacity=opacity,hidden=true,
        parent=(kind.parent_field or kind.attached) and track(parent) or nil,
        root=(kind.parent_field or kind.attached) and track(root) or nil,chain=chain,
        relative={X=relative.X,Y=relative.Y,Z=relative.Z},moved=false}
    entry_count=entry_count+1
    info("Tracking live "..(kind.label or "lobby guide").."; original text retained, actor unchanged.")
end

local function bind_screen(component,source,kind)
    local label=kind.label or 'interaction prompt'
    stage="verify live "..label
    local player=source:GetOwningPlayer()
    local owner=component:GetOwner()
    assert(player and owner,'Screen marker owner/player unavailable')
    if kind.screen_root then
        local p=owner:get_class():find_property('Widget')
        assert(p and p:get_offset()==kind.component_offset,'Screen marker component layout differs')
        local root,bound=owner:get_property('RootComponent'),owner:get_property('Widget')
        assert(root and root:get_address()==component:get_address()
            and bound and bound:get_address()==component:get_address(),'Screen widget must be its actor root')
    else
        checked(widget_class,"GetOwningPlayerPawn",8,8)
        local pawn=source:GetOwningPlayerPawn()
        assert(pawn and pawn:get_address()==owner:get_address(),"Prompt must belong to the local player")
    end
    checked(player:get_class(),"ProjectWorldLocationToScreen",48,48)
    checked(widget_class,"SetRenderTranslation",16,16)
    checked(widget_class,"GetCachedGeometry",32,256)
    if not slate then
        local class
        slate,class=default_object("/Script/UMG.SlateBlueprintLibrary")
        checked(class,"GetLocalSize",32,512)
        checked(class,"LocalToViewport",64,512)
    end
    local opacity=source:get_float_property("RenderOpacity")
    assert(finite(opacity),"Invalid prompt opacity")
    entries[component:get_address()]={component=track(component),source=track(source),
        owner=track(owner),player=track(player),kind=kind,opacity=opacity,hidden=true,
        screen=screen_projection.bind(source,slate)}
    entry_count=entry_count+1
    info("Tracking live "..label.."; text, progress and world target retained.")
end

local function inspect_component(component)
    stage="read marker component owner"
    local outer=component:get_outer()
    if not outer then return end
    local owner_name=outer:get_short_name()
    stage="read marker widget property"
    local source=component:get_property("Widget")
    stage="read marker widget class"
    if not source then return end
    local widget_name=source:get_class():get_short_name()
    local kind=kinds[widget_name]
    if not kind then return end
    local owner_class=outer:get_class():get_short_name()
    if widget_name=="UI_Guide_C" and owner_class:match(mission_guide.owner_class) then kind=mission_guide end
    if kind.owners then
        local supported=false
        for _,pattern in ipairs(kind.owners) do if owner_class:match(pattern) then supported=true;break end end
        if not supported then return end
    elseif kind.owner_class then
        if not owner_class:match(kind.owner_class) then return end
    elseif not owner_name:match(kind.owner) then return end
    if kind.screen and not kind.screen_root then
        -- Remote prompts are ineligible; a local possession gap may resolve later.
        -- Neither condition is a bad layout or a permanently rejected component.
        local pawn,owner=source:GetOwningPlayerPawn(),component:GetOwner()
        if not pawn or not owner or pawn:get_address()~=owner:get_address() then return end
    end
    if kind.attached or kind.transient then
        local visibility=source:get_property('Visibility')
        local owner=component:GetOwner()
        if not owner or not component:get_property('bVisible') or owner:get_property('bHidden')
            or visibility==1 or visibility==2 then return end
        local count=0
        for _,entry in pairs(entries) do
            if (kind.attached and entry.kind.attached) or (kind.transient and entry.kind.transient) then count=count+1 end
        end
        if count>=(kind.transient and 16 or 32) then return end -- Reserve capacity for established guides/prompts/pings.
    end
    stage="read marker component visibility"
    -- The typed bool getter throws on this backend; reflected reads work for
    -- both the component's bVisible and the actor's bHidden bitfields.
    if source
        and component:read_byte(1512)==1
        and not entries[component:get_address()] then
        stage="validate world-icon widget"
        assert(entry_count<64,"Too many world icons")
        local p=source:get_class():find_property(kind.field or kind.image)
        assert(p and p:get_offset()==kind.offset,"World-marker image layout mismatch")
        for name,offset in pairs(kind.additional_fields or {}) do
            p=source:get_class():find_property(name)
            assert(p and p:get_offset()==offset,'Screen marker layout differs: '..name)
        end
        if kind.screen then
            bind_screen(component,source,kind)
            return
        end
        if kind.world_label then
            return bind_world_label(component,source,kind)
        end
        local size=source:GetDesiredSize()
        if not size or size.X<=0 or size.Y<=0 then
            source:ForceLayoutPrepass() -- Also size icons outside the gun camera's view.
            size=source:GetDesiredSize()
        end
        if size and finite(size.X) and finite(size.Y) and size.X>0 and size.Y>0 then
            local owner=component:GetOwner()
            assert(owner and owner:get_class():find_property("bHidden"),"World-icon owner unavailable")
            local opacity=source:get_float_property("RenderOpacity")
            assert(finite(opacity),"Invalid world-icon opacity")
            local entry={component=track(component),source=track(source),owner=track(owner),opacity=opacity,hidden=false,kind=kind}
            entries[component:get_address()]=entry -- Cleanup owns every subsequent mutation.
            entry_count=entry_count+1
            stage="create viewport icon"
            local proxy=factory:Create(source,source:get_class(),source:GetOwningPlayer())
            assert(proxy and proxy:is_a(widget_class),"Cannot create world-icon viewport copy")
            entry.proxy=track(proxy)
            entry.icon=proxy:get_property(kind.image)
            assert(entry.icon,"World-icon image is missing")
            stage="attach viewport icon"
            proxy:SetRenderOpacity(0)
            proxy:AddToViewport(component:get_int_property("LayerZOrder"))
            local pivot=component:get_property("Pivot")
            proxy:SetAlignmentInViewport({X=pivot.X,Y=pivot.Y})
            proxy:SetDesiredSizeInViewport({X=size.X,Y=size.Y})
            proxy:SetVisibility(3) -- HitTestInvisible: markers never intercept input.
            entry.hidden=true
            source:SetRenderOpacity(0)
            entry.style_time=0
            info("Tracking world icon at "..tostring(component:get_address()).." ("..source:get_class():get_short_name().."); native icon hidden.")
        end
    end
end

local function place_screen(entry,point,pixel)
    assert(valid(entry.player),"Prompt player became invalid")
    local screen={}
    if not entry.player.object:ProjectWorldLocationToScreen(point,screen,false)
        or not screen.result or not screen_projection.place(entry.screen,screen.result,pixel) then
        entry.source.object:SetRenderOpacity(0)
        entry.hidden=true
        return
    end
    entry.source.object:SetRenderOpacity(entry.opacity)
    entry.hidden=true
    if not entry.reported then
        entry.reported=true
        info("Live "..(entry.kind.label or 'interaction prompt').." now uses headset projection; no text copy or target movement.")
    end
end

local function place_world_label(entry,pixel)
    assert(valid(entry.player),"World-label player became invalid")
    local origin,direction={},{}
    if not entry.player.object:DeprojectScreenPositionToWorld(pixel.x,pixel.y,origin,direction) then
        entry.source.object:SetRenderOpacity(0)
        return
    end
    local p,d=origin.result,direction.result
    assert(p and d and finite(p.X) and finite(p.Y) and finite(p.Z)
        and finite(d.X) and finite(d.Y) and finite(d.Z),"Invalid world-label projection ray")
    -- The engine's screen-widget layer uses the game camera. Invert that same
    -- projection to place this visual child at the headset-projected pixel.
    -- Never use its warped component location as the real marker target.
    entry.moved=true -- Cleanup owns a failed/partial move too.
    entry.component.object:K2_SetWorldLocation({X=p.X+d.X*1000,Y=p.Y+d.Y*1000,Z=p.Z+d.Z*1000},false,{},true)
    entry.source.object:SetRenderOpacity(entry.opacity)
    if not entry.reported then
        entry.reported=true
        info("Live "..(entry.kind.label or "mission label").." now uses headset projection; no default-label copy.")
    end
end

local function marker_context(component,source)
    local ok,context=pcall(function()
        local owner=component:GetOwner()
        return ' ['..source:get_class():get_short_name()..' on '..
            (owner and owner:get_class():get_short_name() or 'no owner')..
            ', '..component:get_short_name()..']'
    end)
    return ok and context or ''
end
local function reject(component,source,message)
    rejected[component.address]={component=component,source=source}
    functions.log_warn('[FarFarWest markers] '..message..
        marker_context(component.object,source and source.object))
end

local function consider(object)
    local address=object:get_address()
    if entries[address] then return end
    local ref=candidates[address]
    if ref and not valid(ref) then
        candidates[address]=nil;candidate_count=candidate_count-1;rejected[address]=nil;ref=nil
    end
    local rejection=rejected[address]
    if rejection then
        local source=object:get_property('Widget')
        if valid(rejection.component) and valid(rejection.source) and source
            and source:get_address()==rejection.source.address then return end
        rejected[address]=nil -- A reused component address or rebuilt widget is a new binding.
    end
    if ref and elapsed<(ref.retry_at or 0) then return end
    if not candidates[address] then
        -- SetWidget can supply a live instance without setting WidgetClass.
        local source=object:get_property('Widget')
        local class=source and source:get_class() or object:get_property('WidgetClass')
        if not class or not kinds[class:get_short_name()] then return end
        if candidate_count<128 then candidates[address]=track(object);candidate_count=candidate_count+1 end
    end
    local success,err=pcall(inspect_component,object)
    if not success then
        if entries[address] then
            pcall(restore,entries[address]);entries[address]=nil;entry_count=entry_count-1
        end
        local source=object:get_property('Widget')
        reject(candidates[address] or track(object),source and track(source),
            'Marker skipped during '..stage..': '..tostring(err))
    elseif err=='attachment pending' and candidates[address] then
        local pending=candidates[address]
        pending.retry_at=elapsed+.1
        if not pending.attachment_reported then
            pending.attachment_reported=true
            info('Waiting for marker attachment beneath its owner root; retrying'..
                marker_context(object,object:get_property('Widget')))
        end
    end
end

local function discover()
    -- Widget instances and visibility often arrive after their components.
    -- Revisit recognized components without waiting for another array pass.
    for address,ref in pairs(candidates) do
        if not valid(ref) then
            candidates[address]=nil;candidate_count=candidate_count-1;rejected[address]=nil
        elseif not entries[address] then
            consider(ref.object)
        end
    end
    stage='scan object array'
    local count=object_count(array)
    if observed_count and count>observed_count then
        recent_min=recent_min and math.min(recent_min,observed_count) or observed_count
        recent_index=count-1
    elseif observed_count and count<observed_count then
        recent_index,recent_min=nil,nil
        first_scan,scan_index,next_scan=true,nil,0
    end
    observed_count=count
    if elapsed<next_scan and not recent_index then return end
    if scan_index==nil or scan_index>=count then scan_index=count-1 end
    -- get_objects_matching activates UObjectHook; use the proven reticle path.
    -- Front-load initial/new objects, capped at 2 ms rather than a blocking sweep.
    local deadline=(first_scan or recent_index) and clock and clock()+.002
    for i=1,deadline and 8192 or 512 do
        if recent_index and recent_index<recent_min then recent_index,recent_min=nil,nil end
        if not recent_index and elapsed<next_scan then return end
        if not recent_index and scan_index<0 then
            scan_index=nil;next_scan=elapsed+1;first_scan=false;return
        end
        local index=recent_index or scan_index
        local object=array:get_object(index)
        if recent_index then recent_index=recent_index-1 else scan_index=scan_index-1 end
        -- Blueprint-created components need not have one of the old fixed names.
        if object and object:is_a(component_class) then
            consider(object)
        end
        if deadline and i%32==0 and clock()>=deadline then return end
    end
end

local callbacks = {}
callbacks.camera = function(_,_,_,position,rotation,is_double)
    guarded(function()
        if not active() then return end
        stage="read eye camera"
        assert(is_double,"Expected UE5 double camera values")
        vr.get_ue_projection_matrix(-1,matrix)
        local projection={}
        for col=0,3 do
            projection[col]={}
            for row=0,3 do projection[col][row]=matrix:get(col,row) end
        end
        camera={position={x=position.x,y=position.y,z=position.z},
            rotation={x=rotation.x,y=rotation.y,z=rotation.z},matrix=projection,time=elapsed}
    end)
end

callbacks.tick = function(engine,delta)
    guarded(function()
        elapsed=elapsed+math.min(math.max(delta or 0,0),.1)
        if not active() then reset(); return end
        if not array then stage="verify widget API"; prepare() end
        if not fast_discovery then fast_discovery=discovery_factory(component_class,consider) end
        fast_discovery.tick(engine,delta)
        discover()
        for address,entry in pairs(entries) do
            stage="validate tracked icon"
            if not component_valid(entry) or (entry.proxy and not valid(entry.proxy))
                or ((entry.kind.attached or entry.kind.transient) and (not entry.component.object:get_property('bVisible')
                    or entry.owner.object:get_property('bHidden'))) then
                restore(entry); entries[address]=nil; entry_count=entry_count-1
            else
                if not entry.audit_registered then
                    audit_registry.set(entry.component,entry.source,entry.proxy,
                        entry.kind.label or entry.source.object:get_class():get_short_name())
                    entry.audit_registered=true
                end
                local proxy=entry.proxy and entry.proxy.object
                local display=proxy or entry.source.object
                local viewport=layout:GetViewportSize(display)
                local ready=camera and elapsed-camera.time<=.2
                    and viewport and viewport.X>0 and viewport.Y>0
                    and entry.component.object:get_property("bVisible")
                    and not entry.owner.object:get_property("bHidden")
                local visibility=entry.source.object:get_property("Visibility")
                ready=ready and visibility~=1 and visibility~=2 -- Collapsed/Hidden.
                local opacity=entry.source.object:get_float_property("RenderOpacity")
                if opacity~=0 then
                    assert(finite(opacity),"Invalid world-icon opacity")
                    entry.opacity=opacity
                    entry.source.object:SetRenderOpacity(0)
                end
                if not ready then display:SetRenderOpacity(0)
                else
                    local point
                    if entry.parent then
                        -- The untouched parent follows tagged objects. Transform
                        -- the native local offset, never our warped visual child.
                        point=math_library:TransformLocation(entry.parent.object:K2_GetComponentToWorld(),entry.relative)
                    elseif entry.kind.target_field then point=entry.source.object:get_property(entry.kind.target_field)
                    elseif entry.kind.world_label then point=entry.owner.object:K2_GetActorLocation()
                    else point=entry.component.object:K2_GetComponentLocation() end
                    local pixel=geometry.project({x=point.X,y=point.Y,z=point.Z},camera.position,
                        camera.rotation,camera.matrix,viewport.X,viewport.Y)
                    if incident.enabled() and not entry.diagnostic_failed and elapsed>=(entry.next_diagnostic or 0) then
                        entry.next_diagnostic=elapsed+.25
                        local diagnostic_ok,diagnostic_error=pcall(function()
                        local owner_origin
                        if entry.kind.world_label then
                            local p=entry.owner.object:K2_GetActorLocation()
                            owner_origin={x=p.X,y=p.Y,z=p.Z}
                        end
                        local class=entry.source.object:get_class():get_full_name()
                        incident.observe('tracking|'..class..'|'..(entry.kind.label or 'marker'),{
                            visible=true,kind='marker_tracking',class=class,path=entry.kind.label or 'marker',
                            owner_class=entry.owner.object:get_class():get_full_name(),owner_instance=entry.owner.name,
                            component_instance=entry.component.name,coverage=entry.kind.label or 'marker',
                            target={x=point.X,y=point.Y,z=point.Z},tracking={owner_origin=owner_origin,
                                eye_position=camera.position,eye_rotation=camera.rotation,
                                projected=pixel and {x=pixel.x,y=pixel.y,inside=pixel.inside} or nil,
                                native_offset=entry.relative}},entry.component.address)
                        end)
                        if not diagnostic_ok then
                            entry.diagnostic_failed=true
                            incident.count('marker-diagnostics',tostring(diagnostic_error),'markers','warning')
                        end
                    end
                    if pixel and pixel.inside then
                        if entry.screen then
                            stage="reproject live "..(entry.kind.label or 'interaction prompt')
                            local success,err=pcall(place_screen,entry,point,pixel)
                            if not success then
                                pcall(restore,entry); entries[address]=nil; entry_count=entry_count-1
                                reject(entry.component,entry.source,
                                    (entry.kind.label or 'Interaction prompt')..' stopped safely: '..tostring(err))
                            end
                        elseif entry.kind.world_label then
                            stage="reproject live mission label"
                            local success,err=pcall(place_world_label,entry,pixel)
                            if not success then
                                pcall(restore,entry);entries[address]=nil;entry_count=entry_count-1
                                reject(entry.component,entry.source,'Live label stopped safely: '..tostring(err))
                            end
                        else
                            if elapsed>=entry.style_time then
                                local source_icon=entry.source.object:get_property(entry.kind.image)
                                assert(source_icon,"Original world-icon image is missing")
                                stage="copy icon appearance"
                                entry.icon:SetBrush(source_icon:get_property("Brush"))
                                entry.icon:SetColorAndOpacity(source_icon:get_property("ColorAndOpacity"))
                                entry.style_time=elapsed+.25
                            end
                            stage="position viewport icon"
                            proxy:SetPositionInViewport({X=pixel.x,Y=pixel.y},true)
                            proxy:SetRenderOpacity(entry.opacity)
                        end
                        if entries[address] then
                            stage='normalize marker shape'
                            if not entry.shape then
                                local target=display
                                if entry.kind.shape_field then
                                    target=display:get_property(entry.kind.shape_field)
                                    if target then entry.shape_ref=track(target) end
                                elseif entry.kind.shape_content then
                                    -- The nameplate's outer scale is animated by the game.
                                    -- Correct its unit-scale content around the same bottom anchor.
                                    local p=display:get_class():find_property('WidgetTree')
                                    assert(p and p:get_offset()==704,'Unexpected marker widget tree')
                                    local tree=display:get_property('WidgetTree')
                                    target=tree and tree:get_property('RootWidget')
                                    if target and target:get_short_name()=='VerticalBox_0'
                                        and target:get_class():get_short_name()=='VerticalBox' then entry.shape_ref=track(target)
                                    else target=nil end -- Widget construction can finish after discovery.
                                end
                                if target then entry.shape=ui_shape.bind(target,entry.component.object:get_property('Pivot')) end
                            end
                            local factor=ui_shape.height_factor(camera.matrix,viewport.X,viewport.Y)
                            if ui_shape.apply(entry.shape,factor) and not shape_reported then
                                shape_reported=true
                                info('Marker shapes use eye aspect compensation; height factor '..tostring(factor))
                            end
                        end
                        if not reported then
                            reported=true
                            info("World icons now use headset projection on both axes, independently of aiming.")
                        end
                    else display:SetRenderOpacity(0) end
                end
            end
        end
    end)
end
callbacks.reset = reset
info("Helper loaded; vendors, guides, objectives, pings, health bars, dropped cards, teammate/NPC labels, damage numbers and interaction prompts use headset projection.")

return callbacks
end
