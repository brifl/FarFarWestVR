-- Swap only the tracked crosshair's brush resource; keep native geometry/tint.
local source=package.searchpath('libs/reticle_style',package.path)
local root=source and source:gsub('\\','/'):match('^(.*)/scripts/libs/reticle_style%.lua$')
local tuning=require('libs/tuning')
local object_count=require('libs/object_count')
return function(asset_path)
local api,log=uevr.api,uevr.params.functions
local path=asset_path or (root and root..'/assets/aiming_reticle.png')
local array,rendering,texture,binding
local failed,reported=false,false
local function valid(ref)
    if not ref or not array then return false end
    local o=array:get_object(ref.index)
    return o and o:get_address()==ref.address and o:get_short_name()==ref.name
end
local function track(o)
    local index=o:read_dword(12)
    assert(index>=0 and index<object_count(array),'Unexpected reticle resource index')
    local ref={object=o,index=index,address=o:get_address(),name=o:get_short_name()}
    assert(valid(ref),'Reticle resource identity changed');return ref
end
local function method(c,name,size,fields)
    local fn=c:find_function(name)
    assert(fn and fn:get_properties_size()==size,'Unexpected reticle style function '..name)
    for key,offset in pairs(fields or {}) do
        local p=fn:find_property(key)
        assert(p and p:get_offset()==offset,'Unexpected reticle style parameter '..name..'.'..key)
    end
end
local function prepare()
    assert(path,'Cannot locate aiming_reticle.png beside the profile scripts')
    array=api:get_uobject_array()
    assert(array and array.get_objects_offset()==0 and array.get_item_distance()==24,'Unexpected reticle object array')
    local c=assert(api:find_uobject('Class /Script/UMG.Image'))
    method(c,'SetBrushResourceObject',8,{ResourceObject=0})
    c=assert(api:find_uobject('Class /Script/Engine.KismetRenderingLibrary'))
    method(c,'ImportFileAsTexture2D',32,{WorldContextObject=0,Filename=8,ReturnValue=24})
    rendering=assert(c:get_class_default_object())
end
local function address(o) return o and o:get_address() end
local function restore()
    local b=binding;binding=nil
    if not b or not valid(b.image) then return end
    local image=b.image.object
    local current=image:get_property('Brush').ResourceObject
    -- A game-driven brush change belongs to the game; do not overwrite it.
    if address(current)~=b.applied then return end
    if b.original and not valid(b.original) then
        log.log_warn('[FarFarWest reticle style] Original resource expired; leaving the live brush unchanged.')
        return
    end
    image:SetBrushResourceObject(b.original and b.original.object or nil)
end
local function apply(image,context)
    if failed then return end
    local ok,err=pcall(function()
        if tuning.get('aim.halo_reticle')==0 then restore();return end
        if not array then prepare() end
        if binding and (not valid(binding.image) or binding.image.address~=image:get_address()) then restore() end
        local current=image:get_property('Brush').ResourceObject
        if not valid(texture) then
            local loaded=rendering:ImportFileAsTexture2D(context,path)
            assert(loaded and loaded:get_class():get_short_name()=='Texture2D','Cannot import '..path)
            texture=track(loaded)
        end
        if address(current)==texture.address then return end
        -- Snapshot the resource identity, not a live FSlateBrush struct view.
        -- This also follows legitimate brush changes when weapons/spells change.
        local original
        if binding and address(current)==binding.applied then original=binding.original
        elseif current then original=track(current) end
        binding={image=track(image),original=original,applied=texture.address}
        image:SetBrushResourceObject(texture.object)
        if not reported then
            reported=true;log.log_info('[FarFarWest reticle style] Black-halo reticle active; native brush dimensions/tint retained.')
        end
    end)
    if not ok then
        pcall(restore);failed=true
        log.log_warn('[FarFarWest reticle style] Halo unavailable; aim tracking continues: '..tostring(err))
    end
end
return {apply=apply,scale_multiplier=function()
    return binding and not failed and tuning.get('aim.halo_reticle')==1
        and tuning.get('aim.halo_reticle_scale') or 1
end,restore=function()
    local ok,err=pcall(restore)
    if not ok and not failed then
        failed=true
        log.log_warn('[FarFarWest reticle style] Cannot restore halo resource; aim tracking continues: '..tostring(err))
    end
end}
end
