-- Stable callbacks let the marker helper be inspected/reloaded without relaunching.
local functions = uevr.params.functions
local tag_ok, tag = pcall(functions.get_tag)
if not tag_ok or tag ~= "ffw-ue58-sdk-v1" then return end
local feature, last_source, poll_time = nil, nil, .5

local function install(factory)
    assert(type(factory)=="function", "Marker implementation must return a factory")
    local candidate = factory()
    assert(type(candidate)=="table" and type(candidate.tick)=="function"
        and type(candidate.camera)=="function" and type(candidate.reset)=="function",
        "Marker implementation has invalid callbacks")
    if feature then feature.reset() end
    feature = candidate
end
local ok, err = pcall(function() install(require("libs/world_marker_impl")) end)
if not ok then functions.log_warn("[FarFarWest markers] Cannot load helper: "..tostring(err)) end

local function poll_override(delta)
    poll_time = poll_time+math.min(math.max(delta or 0,0),.1)
    if poll_time<.5 then return end
    poll_time=0
    -- Optional developer file in profile/data. Normal play needs no override.
    local file=io.open("world_markers_dev.lua","rb")
    if not file then return end
    local source=file:read(65537); file:close()
    if not source or source==last_source then return end
    last_source=source
    local success, reason=pcall(function()
        assert(#source<=65536,"Marker development file exceeds 64 KB")
        local chunk, failure=load(source,"@world_markers_dev.lua","t")
        assert(chunk,failure)
        install(chunk())
    end)
    if success then functions.log_info("[FarFarWest markers] Development helper reloaded.")
    else functions.log_warn("[FarFarWest markers] Development reload rejected: "..tostring(reason)) end
end

local function invoke(name,...)
    if not feature then return end
    local success,reason=pcall(feature[name],...)
    if not success then
        pcall(feature.reset); feature=nil
        functions.log_warn("[FarFarWest markers] Helper callback stopped: "..tostring(reason))
    end
end

uevr.sdk.callbacks.on_post_calculate_stereo_view_offset(function(...)
    invoke("camera",...)
end)
uevr.sdk.callbacks.on_post_engine_tick(function(engine,delta)
    poll_override(delta)
    invoke("tick",engine,delta)
end)
uevr.sdk.callbacks.on_script_reset(function()
    invoke("reset")
end)
