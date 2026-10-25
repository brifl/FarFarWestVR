-- Metadata only: lets the optional audit distinguish corrected marker instances.
local M={}
local entries,sources={},{}
function M.remove(address)
    local entry=entries[address]
    if not entry then return end
    if sources[entry.source.address]==entry then sources[entry.source.address]=nil end
    if entry.proxy and sources[entry.proxy.address]==entry then sources[entry.proxy.address]=nil end
    entries[address]=nil
end
function M.set(component,source,proxy,label)
    local old=entries[component.address]
    if old and old.component==component and old.source==source and old.proxy==proxy then return end
    M.remove(component.address)
    local entry={component=component,source=source,proxy=proxy,label=label}
    entries[component.address]=entry;sources[source.address]=entry
    if proxy then sources[proxy.address]=entry end
end
function M.find(address,valid)
    local entry=sources[address]
    if entry and valid(entry.component) and valid(entry.source) then
        if entry.source.address==address then return entry.label,'source' end
        if entry.proxy and valid(entry.proxy) and entry.proxy.address==address then return entry.label,'proxy' end
    end
end
function M.visit_sources(valid,visit)
    for _,entry in pairs(entries) do
        if valid(entry.component) and valid(entry.source) then visit(entry.source.object) end
    end
end
return M
