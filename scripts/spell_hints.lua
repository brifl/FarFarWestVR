local functions=uevr.params.functions
local tag_ok,tag=pcall(functions.get_tag)
if not tag_ok or tag~='ffw-ue58-sdk-v1' then return end
local ok,helper=pcall(function() return require('libs/spell_slot_hints')() end)
if not ok then
    functions.log_warn('[FarFarWest hints] Cannot load spell hints: '..tostring(helper))
    return
end
uevr.sdk.callbacks.on_post_engine_tick(helper.tick)
uevr.sdk.callbacks.on_script_reset(helper.reset)
