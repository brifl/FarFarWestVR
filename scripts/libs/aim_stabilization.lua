-- Time-based angular smoothing: steadier at rest, faster during deliberate sweeps.
-- Filter hand orientation before the world/snap anchor so snap turns stay immediate.
return function()
local yaw,pitch,raw_yaw,raw_pitch,speed
local function wrap(n) return (n+180)%360-180 end
local function reset() yaw,pitch,raw_yaw,raw_pitch,speed=nil,nil,nil,nil,0 end
local function step(y,p,dt,strength)
    if not yaw or strength==0 or dt>.25 then
        yaw,pitch,raw_yaw,raw_pitch,speed=y,p,y,p,0
        return y,p
    end
    if dt<=0 then return yaw,pitch end
    local dy,dp=wrap(y-raw_yaw),p-raw_pitch
    local rate=math.sqrt(dy*dy+dp*dp)/dt
    speed=speed+(rate-speed)*(1-math.exp(-dt/.05))
    local tau=(.006+.120*strength*strength)/(1+speed/90)
    local alpha=1-math.exp(-dt/tau)
    yaw=wrap(yaw+wrap(y-yaw)*alpha);pitch=pitch+(p-pitch)*alpha
    raw_yaw,raw_pitch=y,p
    return yaw,pitch
end
reset()
return {step=step,reset=reset}
end
