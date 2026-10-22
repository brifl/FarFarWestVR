local log=uevr.params.functions
local ok,tag=pcall(log.get_tag)
if not ok or tag~='ffw-ue58-sdk-v1' then return end
local loaded,feature=pcall(function() return require('libs/carry_drop')() end)
if not loaded then log.log_warn('[FarFarWest carry] Cannot load: '..tostring(feature));return end
uevr.sdk.callbacks.on_pre_engine_tick(feature.tick)
uevr.sdk.callbacks.on_script_reset(feature.reset)
