-- A square viewport glyph needs different pixel extents on the two eye axes.
-- Keep its attachment point fixed while compensating that difference.
local M={}
local function finite(n) return type(n)=='number' and n==n and math.abs(n)<1e12 end
local function near(a,b) return math.abs(a-b)<1e-5 end
local function same(a,b) return near(a.X,b.X) and near(a.Y,b.Y) end
local function copy(v) return {X=v.X,Y=v.Y} end
function M.height_factor(projection,width,height)
    local fx=projection and projection[0] and projection[0][0]
    local fy=projection and projection[1] and projection[1][1]
    if not finite(fx) or not finite(fy) or not finite(width) or not finite(height)
        or math.abs(fx)<1e-6 or math.abs(fy)<1e-6 or width<=0 or height<=0 then return nil end
    local factor=math.abs(fy)*height/(math.abs(fx)*width)
    if not finite(factor) or factor<.1 or factor>10 then return nil end
    return factor
end
local function vector(widget,x,y)
    -- A reflected getter supplies a typed temporary, avoiding a live property
    -- view or a named Lua table when calling native FVector2D setters.
    local value=widget:GetDesiredSize();value.X,value.Y=x,y;return value
end
local function scale(widget,value) widget:SetRenderScale(vector(widget,value.X,value.Y)) end
local function pivot(widget,value) widget:SetRenderTransformPivot(vector(widget,value.X,value.Y)) end
local function safe_anchor(binding)
    -- Changing the pivot must not move the original visual. All measured game
    -- roots have unit scale; matching pivots also support non-unit originals.
    return near((binding.scale.X-1)*(binding.anchor.X-binding.pivot.X),0)
        and near((binding.scale.Y-1)*(binding.anchor.Y-binding.pivot.Y),0)
end
function M.bind(widget,anchor)
    local transform=widget:get_property('RenderTransform')
    local original_pivot=widget:get_property('RenderTransformPivot')
    anchor=anchor or original_pivot
    for _,v in ipairs({transform.Scale,original_pivot,anchor}) do
        assert(finite(v.X) and finite(v.Y),'Invalid glyph transform')
    end
    local binding={widget=widget,scale=copy(transform.Scale),pivot=copy(original_pivot),anchor=copy(anchor)}
    binding.disabled=not safe_anchor(binding)
    return binding
end
function M.restore(binding)
    if not binding or not binding.written then return end
    local widget=binding.widget
    if same(widget:get_property('RenderTransform').Scale,binding.applied) then scale(widget,binding.scale) end
    if same(widget:get_property('RenderTransformPivot'),binding.anchor)
        and not same(binding.pivot,binding.anchor) then pivot(widget,binding.pivot) end
    binding.written=false
end
function M.apply(binding,factor)
    if not binding or binding.disabled then return false end
    if not finite(factor) or factor<.1 or factor>10 then M.restore(binding);return false end
    local widget=binding.widget
    local current=widget:get_property('RenderTransform').Scale
    local current_pivot=widget:get_property('RenderTransformPivot')
    if not binding.written or not same(current,binding.applied) then binding.scale=copy(current) end
    local expected_pivot=binding.written and binding.anchor or binding.pivot
    if not same(current_pivot,expected_pivot) or not safe_anchor(binding) then
        -- Respect game-driven transform changes instead of moving its attachment.
        M.restore(binding);binding.disabled=true;return false
    end
    if near(factor,1) then M.restore(binding);return true end
    local target={X=binding.scale.X,Y=binding.scale.Y*factor}
    binding.applied=target;binding.written=true -- Cleanup owns partial setter failure.
    if not same(current_pivot,binding.anchor) then pivot(widget,binding.anchor) end
    if not same(current,target) then scale(widget,target) end
    return true
end
return M
