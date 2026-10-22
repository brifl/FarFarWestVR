return function()
local api,vr,log=uevr.api,uevr.params.vr,uevr.params.functions
local tuning=require('libs/tuning')
local safe=require('libs/hud_safe_area')
local shape=require('libs/ui_shape')
local retainer=require('libs/hud_retainer')
local projection=UEVR_Matrix4x4f.new()
local eye,projection_error
local query=require('libs/live_widgets')(
    'WidgetBlueprintGeneratedClass /Game/Interfaces/UI_Player.UI_Player_C',8,.25)
-- Disjoint groups only; moving a parent and one of its children would double-shift it.
local direct={HB_Spells=true,HB_JokerCooldown=true,HB_Moneys=true,
    VerticalBox_PlayerHealths=true,HorizontalBox_1=true,VerticalBox_0=true}
local nested={UI_Equipment_PlayerStats=true,VB_Lobby=true}
local priority={HorizontalBox_1=1,HB_Spells=2,HB_JokerCooldown=3,VerticalBox_0=4,
    UI_Equipment_PlayerStats=5,HB_Moneys=5,VerticalBox_PlayerHealths=6,VB_Lobby=7}
local elapsed,entries,slate,layout,failed,next_bind,next_apply=0,{},nil,nil,false,0,0
local rejected,retainers={},{}
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
    for _,binding in pairs(retainers) do pcall(retainer.restore,binding,query.valid) end
    entries,rejected,retainers={},{},{};query.reset()
end
local function tick(engine,delta)
    if failed then return end
    local ok,err=pcall(function()
        elapsed=elapsed+math.min(math.max(delta or 0,0),.1)
        if not vr.is_runtime_ready() or not vr.is_hmd_active() or _G.farfarwest_gameplay_ready~=true then
            restore_all();eye=nil;return
        end
        if elapsed<next_apply then return end
        next_apply=elapsed+.1
        local roots=query.get(engine,elapsed)
        if not slate then
            local c=assert(api:find_uobject('Class /Script/UMG.SlateBlueprintLibrary'))
            for name in pairs({GetLocalSize=true,LocalToViewport=true}) do assert(c:find_function(name),'Missing HUD geometry '..name) end
            slate=assert(c:get_class_default_object())
            local widget=assert(api:find_uobject('Class /Script/UMG.Widget'))
            for name,size in pairs({SetRenderTranslation=16,SetRenderScale=16,GetDesiredSize=16,GetParent=8}) do
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
                    local address=canvas:get_address()
                    if not retainers[address] and not rejected[address] then
                        local ok,binding=pcall(retainer.bind,canvas,query.track)
                        if ok and binding then binding.root=root;retainers[address]=binding
                        elseif not ok then
                            rejected[address]=true
                            log.log_warn('[FarFarWest HUD margins] Retainer skipped: '..tostring(binding))
                        end
                    end
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
        for address,binding in pairs(retainers) do
            if not query.valid(binding.root) or not retainer.valid(binding,query.valid) then
                pcall(retainer.restore,binding,query.valid);retainers[address]=nil
            else
                local ok,result=pcall(retainer.apply,binding)
                if not ok then
                    pcall(retainer.restore,binding,query.valid);retainers[address]=nil;rejected[address]=true
                    log.log_warn('[FarFarWest HUD margins] Retainer stopped: '..tostring(result))
                elseif result and not binding.reported then
                    binding.reported=true
                    log.log_info('[FarFarWest HUD margins] Curved retained HUD bypassed during gameplay; native widgets preserved.')
                end
            end
        end
        local margins={left=tuning.get('hud.left_margin'),right=tuning.get('hud.right_margin'),
            top=tuning.get('hud.top_margin'),bottom=tuning.get('hud.bottom_margin')}
        local multiplier=tuning.get('hud.scale_multiplier')
        local correct_aspect=tuning.get('hud.aspect_correction')==1
        if correct_aspect and not eye then return end
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
                local factor=1
                if correct_aspect then factor=shape.height_factor(eye,viewport.X,viewport.Y) end
                if not factor then return end -- Wait for a usable stereo projection.
                local visibility=entry.widget.object:get_property('Visibility')
                local applied,reason=true,nil
                if visibility~=1 and visibility~=2 then
                    applied,reason=pcall(safe.plan,entry,viewport,margins,multiplier,factor)
                end
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
            else
                local signature=string.format('%.3f:%.3f:%.3f:%.3f:%.3f:%.3f',
                    margins.left,margins.right,margins.top,margins.bottom,multiplier,plan.height_factor)
                if entry.reported~=signature then
                    entry.reported=signature
                    log.log_info(string.format('[FarFarWest HUD margins] %s inset L/R/T/B=%.2f/%.2f/%.2f/%.2f; scale %.2f; height factor %.5f.',
                        entry.widget.name,margins.left,margins.right,margins.top,margins.bottom,multiplier,
                        plan.height_factor))
                end
            end
        end
    end)
    if not ok then
        restore_all();failed=true
        log.log_warn('[FarFarWest HUD margins] Stopped safely: '..tostring(err))
    end
end
local function camera()
    if failed or not vr.is_runtime_ready() or not vr.is_hmd_active() or _G.farfarwest_gameplay_ready~=true then
        eye=nil;return
    end
    local ok,err=pcall(function()
        vr.get_ue_projection_matrix(-1,projection)
        eye={[0]={[0]=projection:get(0,0)},[1]={[1]=projection:get(1,1)}}
    end)
    if not ok then
        eye=nil
        if not projection_error then
            projection_error=true
            log.log_warn('[FarFarWest HUD margins] Waiting for eye projection: '..tostring(err))
        end
    end
end
return {tick=tick,camera=camera,reset=function() restore_all();eye=nil end}
end
