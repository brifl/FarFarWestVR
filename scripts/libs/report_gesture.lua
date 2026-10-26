-- Deliberate, read-only report chord in OpenVR/OpenXR tracking space (metres).
local M={}
local function finite(n) return type(n)=='number' and n==n and math.abs(n)<10000 end
local function vector(p) return p and finite(p.x) and finite(p.y) and finite(p.z) end
function M.at_ears(head,left,right,rotation,radius,detailed)
    local function invalid(reason) return false,detailed~=false and {reason=reason} or nil end
    if not vector(head) or not vector(left) or not vector(right) or not rotation then return invalid('invalid_pose') end
    local x,y,z,w=rotation.x,rotation.y,rotation.z,rotation.w
    if not finite(x) or not finite(y) or not finite(z) or not finite(w) then return invalid('invalid_rotation') end
    local norm=x*x+y*y+z*z+w*w
    if norm<.5 or norm>1.5 then return invalid('invalid_rotation') end
    local rx,ry,rz=1-2*(y*y+z*z)/norm,2*(x*y+w*z)/norm,2*(x*z-w*y)/norm
    local fx,fy,fz=-2*(x*z+w*y)/norm,2*(w*x-y*z)/norm,2*(x*x+y*y)/norm-1
    local metrics=detailed~=false and {radius_m=radius} or nil
    local function near(p,side,name)
        local dx,dy,dz=p.x-head.x,p.y-head.y,p.z-head.z
        local distance=math.sqrt(dx*dx+dy*dy+dz*dz)
        local lateral=(dx*rx+dy*ry+dz*rz)*side
        local depth=math.abs(dx*fx+dy*fy+dz*fz)
        if metrics then metrics[name]={distance_m=distance,side_m=lateral,depth_m=depth} end
        local reason=distance>radius and 'too_far' or lateral<=.10 and 'wrong_side'
            or depth>=.22 and 'too_far_forward_back' or nil
        if metrics and reason and not metrics.reason then metrics.reason=name..'_'..reason end
        return reason==nil
    end
    local l,r=near(left,-1,'left'),near(right,1,'right')
    if metrics then metrics.reason=metrics.reason or 'at_ears' end
    return l and r,metrics
end
function M.new()
    local held,latched,cooldown=0,true,0
    return {
        step=function(ready,near,left_trigger,right_trigger,dt,hold,delay)
            dt=math.min(math.max(dt or 0,0),.1)
            cooldown=math.max(0,cooldown-dt)
            if not ready then held=0;latched=true;return false end
            if not left_trigger and not right_trigger then latched=false end
            if cooldown>0 then
                if left_trigger and right_trigger then latched=true end
                held=0;return false
            end
            if not near or not left_trigger or not right_trigger or latched then held=0;return false end
            held=held+dt
            if held+1e-8<hold then return false end
            held=0;latched=true;cooldown=delay;return true
        end,
        reset=function() held=0;latched=true end,
        status=function() return {held_seconds=held,release_required=latched,cooldown_seconds=cooldown} end,
    }
end
return M
