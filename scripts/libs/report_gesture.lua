-- Deliberate, read-only report chord in OpenVR/OpenXR tracking space (metres).
local M={}
local function finite(n) return type(n)=='number' and n==n and math.abs(n)<10000 end
local function vector(p) return p and finite(p.x) and finite(p.y) and finite(p.z) end
function M.at_ears(head,left,right,rotation,radius)
    if not vector(head) or not vector(left) or not vector(right) or not rotation then return false end
    local x,y,z,w=rotation.x,rotation.y,rotation.z,rotation.w
    if not finite(x) or not finite(y) or not finite(z) or not finite(w) then return false end
    local norm=x*x+y*y+z*z+w*w
    if norm<.5 or norm>1.5 then return false end
    local rx,ry,rz=1-2*(y*y+z*z)/norm,2*(x*y+w*z)/norm,2*(x*z-w*y)/norm
    local fx,fy,fz=-2*(x*z+w*y)/norm,2*(w*x-y*z)/norm,2*(x*x+y*y)/norm-1
    local function near(p,side)
        local dx,dy,dz=p.x-head.x,p.y-head.y,p.z-head.z
        return dx*dx+dy*dy+dz*dz<=radius*radius and (dx*rx+dy*ry+dz*rz)*side>.10
            and math.abs(dx*fx+dy*fy+dz*fz)<.22
    end
    return near(left,-1) and near(right,1)
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
    }
end
return M
