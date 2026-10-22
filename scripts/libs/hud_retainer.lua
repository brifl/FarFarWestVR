-- The game's curved retained HUD texture duplicates hints after VR repositioning.
-- Keep the same live widgets, but draw them directly during immersive gameplay.
local M={}
local material='MaterialInstanceConstant /Game/Interfaces/MI_CurvedUI.MI_CurvedUI'
local function address(o) return o and o:get_address() end
local function curved(o)
    local effect=o:get_property('EffectMaterial')
    return effect and effect:get_full_name()==material
end
function M.bind(canvas,track)
    local scaler=canvas:GetParent()
    if not scaler or scaler:get_short_name()~='DPIScalerBox_2' then return end
    local retainer=scaler:GetParent()
    if not retainer or retainer:get_short_name()~='RetainerBox_0' then return end
    local c=retainer:get_class()
    assert(c:get_short_name()=='RetainerBox','Unexpected HUD retainer class')
    for name,offset in pairs({bRetainRender=400,EffectMaterial=416}) do
        local p=c:find_property(name)
        assert(p and p:get_offset()==offset,'Unexpected HUD retainer field '..name)
    end
    local fn=c:find_function('SetRetainRendering')
    assert(fn and fn:get_properties_size()==1,'Unexpected HUD retainer setter')
    local p=fn:find_property('bInRetainRendering')
    assert(p and p:get_offset()==0,'Unexpected HUD retainer parameter')
    if not curved(retainer) then return end
    local original=retainer:get_property('bRetainRender')
    assert(type(original)=='boolean','Unexpected HUD retained-rendering flag')
    return {canvas=track(canvas),scaler=track(scaler),retainer=track(retainer),original=original}
end
function M.valid(b,valid)
    return valid(b.canvas) and valid(b.scaler) and valid(b.retainer)
        and address(b.canvas.object:GetParent())==b.scaler.address
        and address(b.scaler.object:GetParent())==b.retainer.address
        and curved(b.retainer.object)
end
function M.apply(b)
    if b.retainer.object:get_property('bRetainRender') then
        b.original=true -- Preserve a newer native decision when menus restore the renderer.
        b.written=true -- Cleanup owns a partially completed native setter.
        b.retainer.object:SetRetainRendering(false)
    end
    return b.written==true
end
function M.restore(b,valid)
    if b.written and valid(b.retainer) and b.retainer.object:get_property('bRetainRender')==false then
        b.retainer.object:SetRetainRendering(b.original)
    end
    b.written=false
end
return M
