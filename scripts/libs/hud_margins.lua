return function()
local api,vr,log=uevr.api,uevr.params.vr,uevr.params.functions
local tuning=require('libs/tuning')
local safe=require('libs/hud_safe_area')
local query=require('libs/live_widgets')(
    'WidgetBlueprintGeneratedClass /Game/Interfaces/UI_Player.UI_Player_C',8,.25)
-- Disjoint groups only; moving a parent and one of its children would double-shift it.
local direct={HB_Spells=true,HB_JokerCooldown=true,HB_Moneys=true,
    VerticalBox_PlayerHealths=true,HorizontalBox_1=true,VerticalBox_0=true}
local nested={UI_Equipment_PlayerStats=true,VB_Lobby=true}
local priority={HorizontalBox_1=1,HB_Spells=2,HB_JokerCooldown=3,VerticalBox_0=4,
    UI_Equipment_PlayerStats=5,HB_Moneys=5,VerticalBox_PlayerHealths=6,VB_Lobby=7}
local elapsed,entries,slate,layout,failed,next_bind,next_apply=0,{},nil,nil,false,0,0
local rejected={}
local function bind(child,root,canvas,ancestors)
    local address=child:get_address()
    if entries[address] or rejected[address] then return end
    local ok,entry=pcall(safe.bind,child,slate,query.track,canvas:get_short_name())
    if ok and entry then
        entry.root,entry.ancestors=root,ancestors
        entry.canvas=query.track(root.object:get_property('MovingCanvas'))
        entries[address]=entry
    elseif not ok then
        rejected[address]=true
        log.log_warn('[FarFarWest HUD margins] Group skipped: '..child:get_short_name()..': '..tostring(entry))
    end
end
local function restore_all()
    for _,entry in pairs(entries) do pcall(safe.restore,entry,query.valid) end
    entries,rejected={},{};query.reset()
end
local function tick(engine,delta)
    if failed then return end
    local ok,err=pcall(function()
        elapsed=elapsed+math.min(math.max(delta or 0,0),.1)
        if not vr.is_runtime_ready() or not vr.is_hmd_active() or _G.farfarwest_gameplay_ready~=true then
            restore_all();return
        end
        if elapsed<next_apply then return end
        next_apply=elapsed+.1
        local roots=query.get(engine,elapsed)
        if not slate then
            local c=assert(api:find_uobject('Class /Script/UMG.SlateBlueprintLibrary'))
            for name in pairs({GetLocalSize=true,LocalToViewport=true}) do assert(c:find_function(name),'Missing HUD geometry '..name) end
            slate=assert(c:get_class_default_object())
            local widget=assert(api:find_uobject('Class /Script/UMG.Widget'))
            for name,size in pairs({SetRenderTranslation=16,GetParent=8}) do
                local fn=widget:find_function(name);assert(fn and fn:get_properties_size()==size,'Unexpected HUD method '..name)
            end
            local viewport=assert(api:find_uobject('Class /Script/UMG.WidgetLayoutLibrary'))
            local fn=viewport:find_function('GetViewportSize');assert(fn and fn:get_properties_size()==24,'Unexpected viewport size function')
            layout=assert(viewport:get_class_default_object())
        end
        if elapsed>=next_bind then
        next_bind=elapsed+.25
        for _,root in pairs(roots) do
            if query.valid(root) then
                local c=root.object:get_class();local field=c:find_property('MovingCanvas')
                assert(field and field:get_offset()==960,'Unexpected HUD canvas field')
                local canvas=root.object:get_property('MovingCanvas')
                if canvas then
                    local n=canvas:GetChildrenCount();assert(n>=0 and n<=64,'Too many direct HUD groups')
                    for i=0,n-1 do
                        local child=canvas:GetChildAt(i);local name=child and child:get_short_name()
                        if direct[name] then bind(child,root,canvas) end
                        if name=='NamedSlot_216' then
                            local panel=child:GetChildAt(0)
                            if panel and panel:get_short_name()=='CanvasPanel_86' then
                                local count=panel:GetChildrenCount();assert(count<=16,'Unexpected lobby HUD groups')
                                for j=0,count-1 do
                                    local group=panel:GetChildAt(j)
                                    if group and nested[group:get_short_name()] then
                                        bind(group,root,panel,{query.track(panel),query.track(child),query.track(canvas)})
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end
        end
        local h,v=tuning.get('hud.horizontal_margin'),tuning.get('hud.vertical_margin')
        local plans={}
        for address,entry in pairs(entries) do
            local canvas=query.valid(entry.root) and entry.root.object:get_property('MovingCanvas')
            local valid=canvas and canvas:get_address()==entry.canvas.address and safe.valid(entry,query.valid)
            if valid and entry.ancestors then
                for i=1,#entry.ancestors-1 do
                    local ref,next_ref=entry.ancestors[i],entry.ancestors[i+1]
                    if not query.valid(ref) or not query.valid(next_ref) then valid=false;break end
                    local parent=ref.object:GetParent()
                    if not parent or parent:get_address()~=next_ref.address then valid=false;break end
                end
            end
            if not valid then
                pcall(safe.restore,entry,query.valid);entries[address]=nil
            else
                local viewport=layout:GetViewportSize(entry.root.object)
                assert(viewport and viewport.X>0 and viewport.Y>0,'Invalid HUD viewport')
                local visibility=entry.widget.object:get_property('Visibility')
                local applied,reason=true,nil
                if visibility~=1 and visibility~=2 then applied,reason=pcall(safe.plan,entry,viewport,h,v) end
                if not applied then
                    pcall(safe.restore,entry,query.valid);entries[address]=nil;rejected[address]=true
                    log.log_warn('[FarFarWest HUD margins] Group stopped: '..entry.widget.name..': '..tostring(reason))
                elseif reason then
                    reason.group=entry.root.address;reason.priority=priority[entry.widget.name] or 8
                    plans[#plans+1]=reason
                end
            end
        end
        safe.avoid_overlaps(plans,4)
        for _,plan in ipairs(plans) do
            local entry=plan.binding
            local ok,err=pcall(safe.commit,plan)
            if not ok then
                pcall(safe.restore,entry,query.valid);entries[entry.widget.address]=nil;rejected[entry.widget.address]=true
                log.log_warn('[FarFarWest HUD margins] Group stopped: '..entry.widget.name..': '..tostring(err))
            elseif entry.reported~=h..':'..v then
                entry.reported=h..':'..v
                log.log_info(string.format('[FarFarWest HUD margins] %s inset H=%.2f V=%.2f.',entry.widget.name,h,v))
            end
        end
    end)
    if not ok then
        restore_all();failed=true
        log.log_warn('[FarFarWest HUD margins] Stopped safely: '..tostring(err))
    end
end
return {tick=tick,reset=restore_all}
end
