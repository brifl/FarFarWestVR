"""Exercise bounded hint discovery against current UI trees, not retained widgets."""
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
MOCK = r'''
state={objects={},next=1,queries=0,inspections=0,loaded=true,lookups=0,logs={}}
local function object(kind,name,props)
 local o={kind=kind,name=name,props=props or {},index=state.next,children={}}
 state.next=state.next+1;state.objects[o.index]=o
 function o:get_address() return self.index*256 end
 function o:read_dword(n) assert(n==12);return self.index end
 function o:get_short_name() return self.name end
 function o:get_class() return state.engine_class end
 function o:get_property(n)
  if n=='Visibility' then state.inspections=state.inspections+1;return self.props[n] or 0 end
  return self.props[n]
 end
 function o:is_a(c)
  return c==state.viewport_class and self.kind=='viewport'
   or c==state.key_class and self.kind=='key'
   or c==state.user_class and (self.kind=='root' or self.kind=='key')
   or c==state.panel_class and self.kind=='panel'
 end
 function o:GetChildrenCount() return #self.children end
 function o:GetChildAt(i) return self.children[i+1] end
 function o:find_property(n)
  local offsets={WidgetTree=704,RootWidget=72,Visibility=221,GameViewport=3448,
   WorldContextObject=0,FoundWidgets=8,WidgetClass=24,TopLevelOnly=32}
  if offsets[n] then return {get_offset=function() return offsets[n] end} end
 end
 function o:find_function(n)
  local sizes={GetAllWidgetsOfClass=40,GetChildrenCount=4,GetChildAt=16}
  return {get_properties_size=function() return assert(sizes[n]) end,find_property=self.find_property}
 end
 return o
end
state.object=object
state.user_class=object('class','UserWidget');state.key_class=object('class','UI_Key_C')
state.panel_class=object('class','PanelWidget');state.viewport_class=object('class','GameViewportClient')
state.tree_class=object('class','WidgetTree');state.widget_class=object('class','Widget')
state.engine_class=object('class','Engine')
state.library_class=object('class','WidgetBlueprintLibrary')
function state.library_class:get_class_default_object() return {GetAllWidgetsOfClass=function(_,v,found,c,top)
 assert(c==state.user_class and top==true,'must query viewport roots, never all retained UI_Key instances')
 assert(v==state.viewport);state.queries=state.queries+1
 for _,root in ipairs(state.roots) do found[#found+1]=root end
end} end
state.viewport=object('viewport','Viewport');state.engine=object('engine','Engine',{GameViewport=state.viewport})
state.key=object('key','UI_Key_1');state.panel=object('panel','Panel');state.panel.children={state.key}
state.tree=object('tree','Tree',{RootWidget=state.panel})
state.root=object('root','HUD',{WidgetTree=state.tree});state.roots={state.root}
local array={get_objects_offset=function() return 0 end,get_item_distance=function() return 24 end,
 get_object_count=function() return state.next end,get_object=function(_,i) return state.objects[i] end}
uevr={api={get_uobject_array=function() return array end,find_uobject=function(_,path)
 local classes={UserWidget=state.user_class,PanelWidget=state.panel_class,Widget=state.widget_class,
  WidgetTree=state.tree_class,GameViewportClient=state.viewport_class,WidgetBlueprintLibrary=state.library_class}
 if path=='WidgetBlueprintGeneratedClass /Test/UI_Key.UI_Key_C' then
  state.lookups=state.lookups+1;return state.loaded and state.key_class or nil
 end
 return assert(classes[path:match('%.([^%.]+)$')],path)
end},params={functions={log_warn=function(s) state.logs[#state.logs+1]=s end}}}
os.clock=function() return 0 end
query=require('libs/active_widgets')('WidgetBlueprintGeneratedClass /Test/UI_Key.UI_Key_C',256,.25)
function ref(o) return {object=o,index=o.index,address=o:get_address(),name=o.name} end
function has(o,time) return query.get(state.engine,time)[o:get_address()]~=nil end
'''


def run(name, body):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().script_path = str(ROOT/'scripts/?.lua')
    lua.execute("package.path=script_path..';'..package.path")
    lua.execute(MOCK)
    lua.execute(body)
    print('PASS', name)


run('hundreds of retained keys do not enter the active query or stop hint updates', r'''
for i=1,600 do state.object('key','Retained_'..i) end
assert(has(state.key,0));assert(state.inspections==3 and state.queries==1)
assert(has(state.key,.1));assert(state.queries==1 and #state.logs==0)
''')
run('registered world-widget hints join viewport keys and leave after component destruction', r'''
local key=state.object('key','WorldKey');local panel=state.object('panel','WorldPanel');panel.children={key}
local tree=state.object('tree','WorldTree',{RootWidget=panel})
local root=state.object('root','WorldPrompt',{WidgetTree=tree});local component=state.object('component','Widget')
require('libs/ui_audit_registry').set(ref(component),ref(root),nil,'prompt')
assert(has(key,0) and has(state.key,.1))
state.objects[component.index]=nil;assert(not has(key,.3))
''')
run('hidden branches and tree cycles are skipped without losing visible hints', r'''
local hidden=state.object('panel','Hidden',{Visibility=2});hidden.children={state.object('key','HiddenKey')}
state.panel.children={hidden,state.root,state.key}
assert(has(state.key,0));assert(not has(hidden.children[1],.1));assert(state.inspections==4)
''')
run('traversal yields between frames and picks up newly shown keys on refresh', r'''
state.panel.children={}
for i=1,500 do state.panel.children[i]=state.object('widget','Child_'..i) end
state.panel.children[500]=state.key
assert(not has(state.key,0));assert(state.inspections==128)
for i=1,4 do has(state.key,i*.016) end
assert(has(state.key,.1))
state.key.props.Visibility=2;assert(not has(state.key,.3))
for i=1,4 do has(state.key,.3+i*.016) end
assert(not has(state.key,.4))
''')
run('late class lookup is throttled and viewport replacement clears old hints', r'''
state.loaded=false;assert(not has(state.key,0));assert(not has(state.key,.1));assert(state.lookups==1)
state.loaded=true;assert(has(state.key,1.1));assert(state.lookups==2)
local old=state.key;state.key=state.object('key','NewKey');state.panel.children={state.key}
state.viewport=state.object('viewport','NewViewport');state.engine.props.GameViewport=state.viewport
assert(has(state.key,1.11));assert(not has(old,1.12))
''')
run('active-result limit preserves partial results and recovers on a smaller next screen', r'''
state.panel.children={}
for i=1,300 do state.panel.children[i]=state.object('key','Key_'..i) end
for i=0,4 do query.get(state.engine,i*.016) end
local n=0;for _ in pairs(query.get(state.engine,.1)) do n=n+1 end
assert(n==256 and #state.logs==1)
state.panel.children={state.key};assert(has(state.key,.3))
''')
