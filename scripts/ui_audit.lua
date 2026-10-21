-- Capture on launch when enabled, or on a one-shot request in profile/data.
local functions=uevr.params.functions
local ok,tag=pcall(functions.get_tag)
if not ok or tag~='ffw-ue58-sdk-v1' then return end
local loaded,helper=pcall(function() return require('libs/ui_audit')() end)
if not loaded then functions.log_warn('[FarFarWest audit] Cannot load: '..tostring(helper));return end
uevr.sdk.callbacks.on_post_engine_tick(helper.tick)
uevr.sdk.callbacks.on_script_reset(function() pcall(helper.reset) end)
