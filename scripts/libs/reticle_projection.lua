-- Pure geometry for projecting the firing target into the rendered eye.
local M = {}

local function finite(n)
    return type(n) == "number" and n == n and math.abs(n) < 1e12
end

local function vector(v)
    return v and finite(v.x) and finite(v.y) and finite(v.z)
end

function M.basis(pitch, yaw, roll)
    if not finite(pitch) or not finite(yaw) or not finite(roll) then return nil end
    local p, y, r = math.rad(pitch), math.rad(yaw), math.rad(roll)
    local cp, sp, cy, sy, cr, sr = math.cos(p), math.sin(p), math.cos(y), math.sin(y), math.cos(r), math.sin(r)
    return {x=cp*cy, y=cp*sy, z=sp},
        {x=sr*sp*cy-cr*sy, y=sr*sp*sy+cr*cy, z=-sr*cp},
        {x=-cr*sp*cy-sr*sy, y=sr*cy-cr*sp*sy, z=cr*cp}
end

function M.ray_end(origin, rotation, distance)
    if not vector(origin) or not vector(rotation) or not finite(distance) or distance <= 0 then return nil end
    local forward = M.basis(rotation.x, rotation.y, rotation.z)
    if not forward then return nil end
    return {x=origin.x+forward.x*distance, y=origin.y+forward.y*distance, z=origin.z+forward.z*distance}
end

function M.project(point, eye, rotation, projection, width, height)
    if not vector(point) or not vector(eye) or not vector(rotation) or not finite(width) or not finite(height)
        or width <= 0 or height <= 0 then return nil end
    local forward, right, up = M.basis(rotation.x, rotation.y, rotation.z)
    if not forward then return nil end
    local dx, dy, dz = point.x-eye.x, point.y-eye.y, point.z-eye.z
    local coordinates = {
        [0]=dx*right.x+dy*right.y+dz*right.z,
        dx*up.x+dy*up.y+dz*up.z,
        dx*forward.x+dy*forward.y+dz*forward.z,
        1,
    }
    local clip = {}
    for row=0,3 do
        local value = 0
        for column=0,3 do
            local n = projection[column] and projection[column][row]
            if not finite(n) then return nil end
            value = value + coordinates[column]*n
        end
        if not finite(value) then return nil end
        clip[row] = value
    end
    if clip[3] <= 0.001 then return nil end
    local x, y = clip[0]/clip[3], clip[1]/clip[3]
    return {x=(x+1)*width/2, y=(1-y)*height/2, inside=math.abs(x)<=1 and math.abs(y)<=1}
end

-- LocalToViewport samples include the image's own scale. Translation is applied
-- after that scale, so remove it before inverting the inherited pixel transform.
function M.calibrate(center, along_x, along_y, scale_x, scale_y)
    if not center or not along_x or not along_y then return nil end
    if not finite(center.x) or not finite(center.y) or not finite(along_x.x)
        or not finite(along_x.y) or not finite(along_y.x) or not finite(along_y.y) then return nil end
    if not finite(scale_x) or not finite(scale_y) or math.abs(scale_x)<1e-5 or math.abs(scale_y)<1e-5 then return nil end
    local a, b = (along_x.x-center.x)/scale_x, (along_y.x-center.x)/scale_y
    local c, d = (along_x.y-center.y)/scale_x, (along_y.y-center.y)/scale_y
    local determinant = a*d-b*c
    if not finite(determinant) or math.abs(determinant)<1e-6 then return nil end
    return {x=center.x, y=center.y, a=d/determinant, b=-b/determinant, c=-c/determinant, d=a/determinant}
end

function M.translation(calibration, pixel, original_x, original_y)
    local x, y = pixel.x-calibration.x, pixel.y-calibration.y
    local tx = original_x+calibration.a*x+calibration.b*y
    local ty = original_y+calibration.c*x+calibration.d*y
    if not finite(tx) or not finite(ty) then return nil end
    return {X=tx, Y=ty}
end

return M
