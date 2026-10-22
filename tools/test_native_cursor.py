"""Native cursor hotspot and viewport/widget ownership regressions (lupa)."""
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
MOCK = r'''
state={objects={},next=1,created=0,removed=0,logs={},screen=true,active=true}
local methods={Create=32,GetMousePositionOnViewport=24,AddToViewport=4,RemoveFromParent=0,
 SetDesiredSizeInViewport=16,SetAlignmentInViewport=16,ForceLayoutPrepass=0,GetDesiredSize=16,
 SetVisibility=1,SetRenderOpacity=4,SetPositionInViewport=24}
local offsets={WorldContextObject=0,WidgetType=8,OwningPlayer=16,ReturnValue=24,GameViewport=3448}
local function class(name,default)
 return {get_class_default_object=function() return default end,
  find_property=function(_,n) return {get_offset=function() return state.bad_layout and 0 or offsets[n] end} end,
  find_function=function(_,n) return {get_properties_size=function() return assert(methods[n],n) end,
   find_property=function(_,p) return {get_offset=function() return state.bad_layout and 0 or offsets[p] end} end} end}
end
local function object(name)
 local o={index=state.next,name=name};state.next=state.next+1;state.objects[o.index]=o
 function o:get_address() return self.index*256 end
 function o:read_dword(n) assert(n==12 and not self.dead);return self.index end
 function o:get_short_name() assert(not self.dead);return self.name end
 return o
end
local viewport_class={}
function make_viewport()
 local o=object('GameViewport');function o:is_a(c) return c==viewport_class end;return o
end
state.viewport=make_viewport()
state.cursor_class=object('UI_Cursor_C')
state.engine={get_class=function() return class('Engine') end,
 get_property=function(_,n) assert(n=='GameViewport');return state.viewport end}
local library={}
function library:Create(viewport,c,player)
 assert(viewport==state.viewport and c==state.cursor_class and player==nil)
 state.created=state.created+1;local o=object('OwnedCursor');state.cursor=o
 function o:RemoveFromParent() assert(not self.dead);state.removed=state.removed+1;self.removed=true end
 function o:SetVisibility(v) assert(v==3);self.visibility=v end
 function o:SetRenderOpacity(v) assert(v==1) end
 function o:AddToViewport(z) assert(z==10000);if state.fail_attach then error('attach failed') end end
 function o:ForceLayoutPrepass() end
 function o:GetDesiredSize() return {_typed=true,X=0,Y=0} end
 function o:SetAlignmentInViewport(v) self.align=v end
 function o:SetDesiredSizeInViewport(v) assert(v._typed);self.size=v end
 function o:SetPositionInViewport(p,remove_dpi)
  assert(not self.dead and not remove_dpi);self.position=p
 end
 return o
end
local layout={GetMousePositionOnViewport=function(_,v) assert(v==state.viewport);return {X=777.25,Y=455.5} end}
local array={get_objects_offset=function() return 0 end,get_item_distance=function() return 24 end,
 get_object_count=function() return state.next end,get_object=function(_,i) return state.objects[i] end}
local function log(s) state.logs[#state.logs+1]=s end
uevr={api={get_uobject_array=function() return array end,find_uobject=function(_,path)
 local name=path:match('%.([^%.]+)$')
 if name=='GameViewportClient' then return viewport_class end
 if name=='UI_Cursor_C' then return not state.missing_asset and state.cursor_class or nil end
 return class(name,({WidgetBlueprintLibrary=library,WidgetLayoutLibrary=layout})[name])
end},params={vr={is_runtime_ready=function() return true end,is_hmd_active=function() return state.active end,
 get_mod_value=function(_,n) assert(n=='VR_2DScreenMode');return state.screen and 'true' or 'false' end},
 functions={is_drawing_ui=function() return state.panel end,log_info=log,log_warn=log}}}
function tick() feature.tick(state.engine,.016) end
function healthy() for _,s in ipairs(state.logs) do assert(not s:find('Stopped safely',1,true),s) end end
'''


def run(name, test):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().script_path = str(ROOT / 'scripts/?.lua')
    lua.execute("package.path=script_path..';'..package.path")
    lua.execute(MOCK)
    lua.execute("feature=require('libs/native_cursor')()")
    lua.execute(test)
    print('PASS', name)


run('centered native hotspot follows local coordinates without applying DPI twice', '''
tick();healthy();local o=state.cursor
assert(o.align.X==.5 and o.align.Y==.5 and o.size.X==66 and o.size.Y==66)
assert(o.position.X==777.25 and o.position.Y==455.5)
for i=1,100 do tick() end
healthy();assert(state.created==1 and state.removed==0)
''')
run('menus, UEVR panel, inactive HMD and reset remove only the owned cursor', '''
tick();state.screen=false;tick();assert(state.removed==1)
state.screen=true;tick();state.panel=true;tick();assert(state.removed==2)
state.panel=false;tick();state.active=false;tick();assert(state.removed==3)
state.active=true;tick();feature.reset();feature.reset();healthy();assert(state.removed==4)
''')
run('viewport replacement and stale widgets never reuse destroyed objects', '''
tick();local old=state.cursor;state.viewport=make_viewport();tick()
assert(old.removed and state.created==2)
local old=state.cursor;state.objects[old.index]=nil;old.dead=true;tick()
healthy();assert(state.created==3 and state.removed==1)
feature.reset();assert(state.removed==2)
''')
run('missing asset retries and partial attachment failure cleans up once', '''
state.missing_asset=true;tick();healthy();assert(state.created==0)
state.missing_asset=false;state.fail_attach=true;tick()
assert(state.created==1 and state.removed==1)
tick();feature.reset();assert(state.created==1 and state.removed==1)
''')
run('unknown metadata stops before creating a native widget', '''
state.bad_layout=true;tick();assert(state.created==0)
state.bad_layout=false;tick();assert(state.created==0)
''')
