return function()
local query=require('libs/active_widgets')(
    'WidgetBlueprintGeneratedClass /Game/Interfaces/UI_Key.UI_Key_C',256,.25)
local key_hint=require('libs/interaction_key')
local elapsed,failed,reported=0,false,false
local log=uevr.params.functions
local function tick(engine,delta)
    if failed then return end
    local ok,err=pcall(function()
        elapsed=elapsed+math.min(math.max(delta or 0,0),.1)
        for _,ref in pairs(query.get(engine,elapsed)) do
            if query.valid(ref) and key_hint.update(ref.object) and not reported then
                reported=true
                log.log_info('[FarFarWest hints] Native Interact hints retain Quest X across menus and world widgets.')
            end
        end
    end)
    if not ok then
        failed=true;query.reset()
        log.log_warn('[FarFarWest hints] Interact hints stopped safely: '..tostring(err))
    end
end
return {tick=tick,reset=query.reset}
end
