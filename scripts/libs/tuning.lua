-- Numeric INI settings, confined to UEVR's profile/data filesystem sandbox.
local M={}
local rules={
    ['graphics.saturation_multiplier']={.95,0,2},
    ['graphics.contrast_multiplier']={1.10,.5,2},
    ['graphics.fog_density_multiplier']={0,0,1},
    ['hud.dialogue_offset_y']={-.10,-.5,.5},
    ['hud.boss_health_offset_y']={.08,-.5,.5},
    ['hud.mission_info_offset_y']={.10,-.5,.5},
    ['hud.compass_offset_y']={.10,-.5,.5},
    ['audit.horizontal_margin']={.10,0,.4},
    ['audit.vertical_margin']={.15,0,.4},
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
    for raw in (source..'\n'):gmatch('(.-)\n') do
        local line=raw:gsub('[;#].*$',''):match('^%s*(.-)%s*$')
        if line~='' then
            local header=line:match('^%[([%w_]+)%]$')
            if header then
                assert(header=='graphics' or header=='hud' or header=='audit','Unknown section: '..header)
                section=header
            else
                local name,text=line:match('^([%w_]+)%s*=%s*(.-)%s*$')
                assert(name,'Expected setting=value: '..line)
                local key=section..'.'..name
                local rule=rules[key]
                assert(rule,'Unknown setting: '..key)
                local n=tonumber(text)
                assert(n and n==n and n>=rule[2] and n<=rule[3],
                    key..' must be between '..tostring(rule[2])..' and '..tostring(rule[3]))
                candidate[key]=n
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
function M.tick(_,delta)
    poll=poll+math.min(math.max(delta or 0,0),.1)
    if poll<1 then return end
    poll=0;reload()
end
reload()
return M
