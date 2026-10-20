"""Check vendor hint replacement, native row rebuilds and texture lifetimes (lupa)."""
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
MOCK = r'''
state={objects={},next=1,slots={},logs={},imports=0,writes=0}
local offsets={ID=888,actionKey=944,HorizontalBox_Keys=856,Image_GamepadIcon=848,Text_Key=832,
    Visibility=221,GameViewport=3448}
local methods={GetAllWidgetsOfClass={40,{WorldContextObject=0,FoundWidgets=8,WidgetClass=24,TopLevelOnly=32}},
    ImportFileAsTexture2D={32,{WorldContextObject=0,Filename=8,ReturnValue=24}},
    SetBrushFromTexture={16,{Texture=0,bMatchSize=8}},SetDesiredSizeOverride={16,{DesiredSize=0}},
    GetDesiredSize={16,{}},SetVisibility={1,{}},GetChildrenCount={4,{}},GetChildAt={16,{}}}
local function field(offset) return {get_offset=function() return offset end} end
local function class(name,default)
    return {get_short_name=function() return name end,get_class_default_object=function() return default end,
        find_property=function(_,n) return field(state.bad_layout and 0 or offsets[n]) end,
        find_function=function(_,n)
            local spec=assert(methods[n],n)
            return {get_properties_size=function() return spec[1] end,
                find_property=function(_,p) return field(spec[2][p]) end}
        end}
end
local function object(kind,name)
    local o={index=state.next,kind=kind,name=name or kind,visibility=0,props={}}
    state.next=state.next+1;state.objects[o.index]=o
    function o:get_address() return self.index*256 end
    function o:read_dword(n) assert(n==12 and not self.dead);return self.index end
    function o:get_short_name() assert(not self.dead);return self.name end
    function o:get_class() assert(not self.dead);return class(self.kind) end
    function o:get_property(n)
        assert(not self.dead)
        if n=='Visibility' then return self.visibility end
        if n=='Brush' then return self.brush end
        return self.props[n]
    end
    function o:get_int_property(n) assert(n=='ID' and not self.dead);return self.id end
    function o:SetVisibility(v) assert(not self.dead);state.writes=state.writes+1;self.visibility=v end
    return o
end
function make_key()
    local key=object('UI_Key_C');local image=object('Image');local text=object('TextBlock')
    image.visibility=1;image.brush={ImageSize={X=35,Y=35}}
    function image:SetBrushFromTexture(texture,match)
        assert(not self.dead and not match and not texture.dead)
        state.writes=state.writes+1;self.brush.ResourceObject=texture
    end
    function image:GetDesiredSize() return {_typed=true,X=35,Y=35} end
    function image:SetDesiredSizeOverride(size)
        assert(not self.dead and size._typed);self.size=size;state.writes=state.writes+1
    end
    key.props.Image_GamepadIcon=image;key.props.Text_Key=text
    return key
end
function make_slot(id)
    local slot=object('UI_Spell_CardSlot_C');slot.id=id
    slot.props.actionKey=object('InputAction',({'IA_SpellA','IA_SpellB','IA_SpellC'})[id+1])
    local panel=object('HorizontalBox');panel.children={make_key()}
    if id==2 then panel.children[2]=make_key() end
    function panel:GetChildrenCount() assert(not self.dead);return #self.children end
    function panel:GetChildAt(i) assert(not self.dead);return self.children[i+1] end
    slot.props.HorizontalBox_Keys=panel;state.slots[id+1]=slot;return slot
end
local slot_class=object('WidgetBlueprintGeneratedClass','UI_Spell_CardSlot_C')
function slot_class:find_property(n) return field(state.bad_layout and 0 or offsets[n]) end
local viewport_class={};state.viewport={is_a=function(_,c) return c==viewport_class end}
state.engine={get_class=function() return class('Engine') end,
    get_property=function(_,n) assert(n=='GameViewport');return state.viewport end}
local library={GetAllWidgetsOfClass=function(_,viewport,found,c,top)
    assert(viewport==state.viewport and c==slot_class and top==false)
    for _,slot in ipairs(state.slots) do found[#found+1]=slot end
end}
local rendering={ImportFileAsTexture2D=function(_,viewport,path)
    assert(viewport==state.viewport and path:find('/assets/control_hints/',1,true))
    state.imports=state.imports+1
    if state.missing_asset then return nil end
    local texture=object('Texture2D');texture.path=path;return texture
end}
local array={get_objects_offset=function() return 0 end,get_item_distance=function() return 24 end,
    get_object_count=function() return state.next end,get_object=function(_,i) return state.objects[i] end}
local function log(s) table.insert(state.logs,s) end
uevr={api={get_uobject_array=function() return array end,find_uobject=function(_,path)
    local name=path:match('%.([^%.]+)$')
    if name=='UI_Spell_CardSlot_C' then
        assert(path=='WidgetBlueprintGeneratedClass /Game/Interfaces/Spells/UI_Spell_CardSlot.UI_Spell_CardSlot_C')
        return slot_class
    end
    if name=='GameViewportClient' then return viewport_class end
    return class(name,({WidgetBlueprintLibrary=library,KismetRenderingLibrary=rendering})[name])
end},params={functions={log_info=log,log_warn=log}}}
for id=0,2 do make_slot(id) end
function frames(n) for i=1,n or 1 do feature.tick(state.engine,.016) end end
function healthy() for _,s in ipairs(state.logs) do assert(not s:find('stopped safely',1,true),s) end end
'''


def run(name, test):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().script_path = str(ROOT / 'scripts/?.lua')
    lua.execute("package.path=script_path..';'..package.path")
    lua.execute(MOCK)
    lua.execute("feature=require('libs/spell_slot_hints')()")
    lua.execute(test)
    print('PASS', name)


run('correct grip labels and native height; no repeated texture imports or writes', '''
frames();healthy();assert(state.imports==3)
for i,filename in ipairs({'left_grip.png','right_grip.png','both_grips.png'}) do
 local slot=state.slots[i];local key=slot.props.HorizontalBox_Keys.children[1]
 assert(key.props.Image_GamepadIcon.brush.ResourceObject.path:find(filename,1,true))
 assert(key.props.Image_GamepadIcon.size.Y==35 and key.props.Text_Key.visibility==1)
 assert(slot.id==i-1 and slot.props.actionKey.name==({'IA_SpellA','IA_SpellB','IA_SpellC'})[i])
end
assert(state.slots[3].props.HorizontalBox_Keys.children[2].visibility==1)
local writes=state.writes;frames(120);healthy();assert(state.imports==3 and state.writes==writes)
''')
run('native input-mode rebuilds replace children without stale UObject access', '''
frames();local panel=state.slots[3].props.HorizontalBox_Keys
for _,key in ipairs(panel.children) do key.dead=true;state.objects[key.index]=nil end
panel.children={make_key(),make_key()};frames();healthy()
assert(panel.children[1].props.Image_GamepadIcon.size.X>100 and panel.children[2].visibility==1)
assert(state.imports==3)
''')
run('hidden vendor slots do not load assets or alter their hints', '''
for _,slot in ipairs(state.slots) do slot.visibility=2 end
frames(40);healthy();assert(state.imports==0 and state.writes==0)
state.slots[1].visibility=0;frames();healthy();assert(state.imports==1)
''')
run('closed menus and collected label textures are rebuilt safely', '''
frames()
for _,slot in ipairs(state.slots) do slot.dead=true;state.objects[slot.index]=nil end
state.slots={};frames(40)
for i,o in pairs(state.objects) do if o.kind=='Texture2D' then o.dead=true;state.objects[i]=nil end end
for id=0,2 do make_slot(id) end
frames(40);healthy();assert(state.imports==6)
''')
run('missing texture fails once before changing the first hint', '''
state.missing_asset=true;frames(40)
assert(state.imports==1 and state.writes==0 and #state.logs==1)
assert(state.logs[1]:find('stopped safely',1,true))
''')
run('unexpected native layouts stop before writing UI', '''
state.bad_layout=true;frames(40)
assert(state.imports==0 and state.writes==0 and #state.logs==1)
assert(state.logs[1]:find('stopped safely',1,true))
''')
