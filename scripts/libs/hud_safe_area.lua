-- Clamp fixed canvas groups using native layout, never our previous rendered position.
local M={}
local function finite(n) return type(n)=='number' and n==n and math.abs(n)<1e8 end
function M.shift(low,high,margin,extent)
    if high-low>extent-2*margin then return extent/2-(low+high)/2 end
    if low<margin then return margin-low end
    if high>extent-margin then return extent-margin-high end
    return 0
end
function M.bind(widget,slate,track)
    local slot=widget:get_property('Slot')
    if not slot or slot:get_class():get_short_name()~='CanvasPanelSlot' then return end
    local p=slot:get_class():find_property('LayoutData')
    assert(p and p:get_offset()==56,'Unexpected canvas-slot layout')
    local parent=slot:get_property('Parent')
    if not parent or parent:get_short_name()~='MovingCanvas' then return end
    local transform=widget:get_property('RenderTransform')
    return {widget=track(widget),slot=track(slot),parent=track(parent),slate=slate,
        original={X=transform.Translation.X,Y=transform.Translation.Y}}
end
function M.valid(b,valid)
    if not valid(b.widget) or not valid(b.slot) or not valid(b.parent) then return false end
    local slot=b.widget.object:get_property('Slot');local parent=b.slot.object:get_property('Parent')
    return slot and slot:get_address()==b.slot.address and parent and parent:get_address()==b.parent.address
end
function M.restore(b,valid)
    if b.last and valid(b.widget) then
        local o=b.widget.object;local t=o:get_property('RenderTransform').Translation
        if math.abs(t.X-b.last.X)<.001 and math.abs(t.Y-b.last.Y)<.001 then o:SetRenderTranslation(b.original) end
        b.last=nil
    end
end
function M.apply(b,viewport,horizontal,vertical)
    local widget,parent,slate=b.widget.object,b.parent.object,b.slate
    local transform=widget:get_property('RenderTransform')
    assert(math.abs(transform.Angle)<.001 and math.abs(transform.Shear.X)<.001 and math.abs(transform.Shear.Y)<.001,
        'Rotated/sheared HUD group requires separate layout')
    local t=transform.Translation
    if not b.last or math.abs(t.X-b.last.X)>.001 or math.abs(t.Y-b.last.Y)>.001 then
        b.original={X=t.X,Y=t.Y} -- Respect a new game-owned animation/offset baseline.
    end
    local layout=b.slot.object:get_property('LayoutData')
    local a=layout.Anchors
    if math.abs(a.Minimum.X-a.Maximum.X)>.00001 or math.abs(a.Minimum.Y-a.Maximum.Y)>.00001 then
        if b.last then widget:SetRenderTranslation(b.original);b.last=nil end
        return false
    end
    local geometry=parent:GetCachedGeometry()
    local size=slate:GetLocalSize(widget:GetCachedGeometry());local parent_size=slate:GetLocalSize(geometry)
    if not size or not parent_size or size.X<=0 or size.Y<=0 or parent_size.X<=0 or parent_size.Y<=0 then return false end
    local function at(x,y)
        local pixel,screen={},{};slate:LocalToViewport(parent,geometry,{X=x,Y=y},pixel,screen)
        assert(pixel.result,'HUD parent viewport basis unavailable');return pixel.result
    end
    local p0,px,py=at(0,0),at(1,0),at(0,1)
    local xx,xy,yx,yy=px.X-p0.X,py.X-p0.X,px.Y-p0.Y,py.Y-p0.Y
    local determinant=xx*yy-xy*yx
    if not finite(determinant) or math.abs(determinant)<.000001 then return false end
    local pivot=widget:get_property('RenderTransformPivot')
    local x=parent_size.X*a.Minimum.X+layout.Offsets.Left-layout.Alignment.X*size.X+b.original.X
    local y=parent_size.Y*a.Minimum.Y+layout.Offsets.Top-layout.Alignment.Y*size.Y+b.original.Y
    local left,top,right,bottom=math.huge,math.huge,-math.huge,-math.huge
    for _,point in ipairs({{0,0},{size.X,0},{0,size.Y},{size.X,size.Y}}) do
        local lx=x+pivot.X*size.X+(point[1]-pivot.X*size.X)*transform.Scale.X
        local ly=y+pivot.Y*size.Y+(point[2]-pivot.Y*size.Y)*transform.Scale.Y
        local sx,sy=p0.X+xx*lx+xy*ly,p0.Y+yx*lx+yy*ly
        assert(finite(sx) and finite(sy),'Invalid HUD layout bounds')
        left,top,right,bottom=math.min(left,sx),math.min(top,sy),math.max(right,sx),math.max(bottom,sy)
    end
    local dx=horizontal==0 and 0 or M.shift(left,right,horizontal*viewport.X,viewport.X)
    local dy=vertical==0 and 0 or M.shift(top,bottom,vertical*viewport.Y,viewport.Y)
    local target={X=b.original.X+(yy*dx-xy*dy)/determinant,Y=b.original.Y+(-yx*dx+xx*dy)/determinant}
    assert(finite(target.X) and finite(target.Y),'Invalid HUD margin translation')
    if not b.last or math.abs(target.X-t.X)>.001 or math.abs(target.Y-t.Y)>.001 then
        widget:SetRenderTranslation(target)
    end
    b.last=target
    return true
end
return M
