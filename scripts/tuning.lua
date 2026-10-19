local functions=uevr.params.functions
local ok,tag=pcall(functions.get_tag)
if not ok or tag~='ffw-ue58-sdk-v1' then return end
local tuning=require('libs/tuning')
uevr.sdk.callbacks.on_pre_engine_tick(tuning.tick)
