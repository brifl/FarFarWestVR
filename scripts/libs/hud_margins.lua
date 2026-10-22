return function()
local api,vr,log=uevr.api,uevr.params.vr,uevr.params.functions
local tuning=require('libs/tuning')
local safe=require('libs/hud_safe_area')
local query=require('libs/live_widgets')(
    'WidgetBlueprintGeneratedClass /Game/Interfaces/UI_Player.UI_Player_C',8,.25)
-- Disjoint groups only; moving a parent and one of its children would double-shift it.
local direct={HB_Spells=true,HB_JokerCooldown=true,HB_Moneys=true,
    VerticalBox_PlayerHealths=true,HorizontalBox_1=true,VerticalBox_0=true}
local elapsed,entries,slate,layout,failed,next_bind,next_apply=0,{},nil,nil,false,0,0
local rejected={}
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
                        if direct[name] and not entries[child:get_address()] and not rejected[child:get_address()] then
                            local bound,entry=pcall(safe.bind,child,slate,query.track)
                            if bound and entry then entry.root=root;entries[child:get_address()]=entry
                            elseif not bound then
                                rejected[child:get_address()]=true
                                log.log_warn('[FarFarWest HUD margins] Group skipped: '..name..': '..tostring(entry))
                            end
                        end
                    end
                end
            end
        end
        end
        local h,v=tuning.get('hud.horizontal_margin'),tuning.get('hud.vertical_margin')
        for address,entry in pairs(entries) do
            local canvas=query.valid(entry.root) and entry.root.object:get_property('MovingCanvas')
            if not canvas or canvas:get_address()~=entry.parent.address or not safe.valid(entry,query.valid) then
                pcall(safe.restore,entry,query.valid);entries[address]=nil
            else
                local viewport=layout:GetViewportSize(entry.root.object)
                assert(viewport and viewport.X>0 and viewport.Y>0,'Invalid HUD viewport')
                local applied,reason=pcall(safe.apply,entry,viewport,h,v)
                if not applied then
                    pcall(safe.restore,entry,query.valid);entries[address]=nil;rejected[address]=true
                    log.log_warn('[FarFarWest HUD margins] Group stopped: '..entry.widget.name..': '..tostring(reason))
                elseif reason and entry.reported~=h..':'..v then
                    entry.reported=h..':'..v
                    log.log_info(string.format('[FarFarWest HUD margins] %s inset H=%.2f V=%.2f.',entry.widget.name,h,v))
                end
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
