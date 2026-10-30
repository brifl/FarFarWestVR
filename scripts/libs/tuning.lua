-- Numeric INI settings, confined to UEVR's profile/data filesystem sandbox.
local M={}
local rules={
    ['graphics.saturation_multiplier']={.95,0,2},
    ['graphics.contrast_multiplier']={1.10,.5,2},
    ['graphics.fog_density_multiplier']={0,0,1},
    ['hud.dialogue_offset_y']={-.10,-.5,.5},
    ['hud.boss_health_offset_y']={.08,-.5,.5},
    ['hud.boss_health_scale_multiplier']={.85,.25,1.5},
    ['hud.mission_info_offset_y']={.10,-.5,.5},
    ['hud.compass_offset_y']={.10,-.5,.5},
    ['audit.auto_start']={0,0,1},
    ['audit.auto_seconds']={3600,10,10800},
    ['diagnostics.gesture_enabled']={1,0,1},
    ['diagnostics.capture_enabled']={1,0,1},
    ['diagnostics.head_radius_m']={.40,.2,.6},
    ['diagnostics.hold_seconds']={.6,.25,2},
    ['diagnostics.cooldown_seconds']={8,3,60},
    ['hud.left_margin']={.10,0,.4},
    ['hud.right_margin']={.10,0,.4},
    ['hud.top_margin']={.15,0,.4},
    ['hud.bottom_margin']={.15,0,.4},
    ['hud.scale_multiplier']={.80,.25,1.5},
    ['hud.aspect_correction']={1,0,1},
    ['aim.stabilization']={.35,0,1},
    ['aim.halo_reticle']={1,0,1},
    ['aim.halo_reticle_scale']={.25,.05,2},
    ['cursor.scale_multiplier']={1,.25,1.5},
    ['cursor.aspect_correction']={0,0,1},
    ['horse.steering_exponent']={2,1,4},
}
-- Explicit edges beat HUD axis pairs, which beat the older audit axis pairs.
local aliases={
    ['audit.horizontal_margin']={1,'hud.left_margin','hud.right_margin'},
    ['audit.vertical_margin']={1,'hud.top_margin','hud.bottom_margin'},
    ['hud.horizontal_margin']={2,'hud.left_margin','hud.right_margin'},
    ['hud.vertical_margin']={2,'hud.top_margin','hud.bottom_margin'},
}
local values,last_source,poll={},nil,0
for key,rule in pairs(rules) do values[key]=rule[1] end
local function log(level,message)
    uevr.params.functions[level]('[FarFarWest tuning] '..message)
end
local function parse(source)
    source=source:gsub('^\239\187\191','') -- Accept UTF-8 BOMs from Windows editors.
    local candidate={}
    for key,rule in pairs(rules) do candidate[key]=rule[1] end
    local section=''
    local priorities={}
    for raw in (source..'\n'):gmatch('(.-)\n') do
        local line=raw:gsub('[;#].*$',''):match('^%s*(.-)%s*$')
        if line~='' then
            local header=line:match('^%[([%w_]+)%]$')
            if header then
                assert(header=='graphics' or header=='hud' or header=='audit' or header=='aim'
                    or header=='cursor' or header=='horse' or header=='diagnostics','Unknown section: '..header)
                section=header
            else
                local name,text=line:match('^([%w_]+)%s*=%s*(.-)%s*$')
                assert(name,'Expected setting=value: '..line)
                local raw_key=section..'.'..name
                local targets=aliases[raw_key] or {3,raw_key}
                local n=tonumber(text)
                for i=2,#targets do
                    local key=targets[i];local rule=rules[key]
                    assert(rule,'Unknown setting: '..key)
                    assert(n and n==n and n>=rule[2] and n<=rule[3],
                        key..' must be between '..tostring(rule[2])..' and '..tostring(rule[3]))
                    assert((key~='audit.auto_start' and key~='diagnostics.gesture_enabled' and key~='diagnostics.capture_enabled' and key~='aim.halo_reticle' and not key:match('%.aspect_correction$')) or n==0 or n==1,
                        key..' must be 0 or 1')
                    if targets[1]>=(priorities[key] or 0) then
                        candidate[key]=n;priorities[key]=targets[1]
                    end
                end
            end
        end
    end
    return candidate
end
local function reload()
    local file=io.open('tuning.ini','rb')
    if not file then return end
    local source=file:read(8193);file:close()
    if source==last_source then return end
    last_source=source
    local ok,result=pcall(function()
        assert(source and #source<=8192,'tuning.ini exceeds 8 KB')
        return parse(source)
    end)
    if not ok then log('log_warn','Keeping previous values: '..tostring(result));return end
    values=result
    log('log_info','Reloaded data/tuning.ini.')
end
function M.get(key)
    assert(rules[key],'Unknown tuning key: '..tostring(key))
    return values[key]
end
function M.snapshot()
    local out={};for key,value in pairs(values) do out[key]=value end;return out
end
function M.tick(_,delta)
    poll=poll+math.min(math.max(delta or 0,0),.1)
    if poll<1 then return end
    poll=0;reload()
end
reload()
return M
