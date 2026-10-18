-- Correct a live screen-space world widget without moving its world target.
-- Reusable for interaction prompts and other marker families with live text.
local geometry=require('libs/reticle_projection')
local M={}
local function finite(n) return type(n)=='number' and n==n and math.abs(n)<1e12 end

function M.bind(widget,slate)
    local transform=widget:get_property('RenderTransform')
    assert(finite(transform.Translation.X) and finite(transform.Translation.Y),'Invalid widget translation')
    return {widget=widget,slate=slate,original={X=transform.Translation.X,Y=transform.Translation.Y},written=false}
end

function M.restore(binding)
    if binding.written then
        binding.widget:SetRenderTranslation(binding.original)
        binding.written=false
    end
end

function M.place(binding,native_pixel,eye_pixel)
    local widget,slate=binding.widget,binding.slate
    local cached=widget:GetCachedGeometry()
    local size=slate:GetLocalSize(cached)
    if not size or not finite(size.X) or not finite(size.Y) or size.X<=0 or size.Y<=0 then return false end
    local transform=widget:get_property('RenderTransform')
    assert(math.abs(transform.Angle)<.001 and math.abs(transform.Shear.X)<.001
        and math.abs(transform.Shear.Y)<.001,'Rotated/sheared world widget needs separate calibration')
    local function at(x,y)
        local pixel,viewport={},{}
        slate:LocalToViewport(widget,cached,{X=x,Y=y},pixel,viewport)
        assert(pixel.result,'Widget viewport geometry unavailable')
        return {x=pixel.result.X,y=pixel.result.Y}
    end
    local basis=geometry.calibrate(at(0,0),at(1,0),at(0,1),transform.Scale.X,transform.Scale.Y)
    assert(basis and finite(native_pixel.X) and finite(native_pixel.Y),'Invalid world-widget projection')
    -- Only the inherited pixel basis comes from cached geometry. Its position
    -- includes our previous correction and may be a render frame old. Using the
    -- game's fresh native projection as the origin prevents accumulated drift.
    basis.x,basis.y=native_pixel.X,native_pixel.Y
    local position=geometry.translation(basis,eye_pixel,binding.original.X,binding.original.Y)
    assert(position,'Invalid corrected widget translation')
    binding.written=true -- Cleanup also owns a partially failed native write.
    widget:SetRenderTranslation(position)
    return true
end

return M
