"""HUD geometry and common Interact key regressions (requires lupa)."""
from pathlib import Path
from lupa import LuaRuntime
ROOT = Path(__file__).resolve().parents[1]

GEOMETRY = r'''
state={objects={},writes=0,viewport={X=2560,Y=1440}}
function near(a,b) assert(math.abs(a-b)<.000001,tostring(a)..' differs from '..tostring(b)) end
local function object(index,name)
 local o={index=index,name=name}
 function o:get_address() return self.index*4096 end
 function o:read_dword(n) assert(n==12);return self.index end
 function o:get_short_name() assert(not self.dead);return self.name end
 state.objects[index]=o;return o
end
function track(o) return {object=o,index=o.index,address=o:get_address(),name=o.name} end
function valid(ref) return state.objects[ref.index]==ref.object end
local canvas=object(1,'MovingCanvas')
function canvas:GetCachedGeometry() return self end
local slot=object(2,'Slot')
function slot:get_class() return {get_short_name=function() return 'CanvasPanelSlot' end,
 find_property=function(_,name) assert(name=='LayoutData');return {get_offset=function() return 56 end} end} end
slot.layout={Anchors={Minimum={X=0,Y=1},Maximum={X=0,Y=1}},Offsets={Left=20,Top=-20},Alignment={X=0,Y=1}}
function slot:get_property(n) if n=='Parent' then return self.parent or canvas end;assert(n=='LayoutData');return self.layout end
local widget=object(3,'HB_Spells')
widget.translation={X=0,Y=0};widget.scale={X=1,Y=1};widget.size={X=160,Y=100}
function widget:get_property(n)
 assert(not self.dead)
 if n=='Slot' then return slot end
 if n=='RenderTransformPivot' then return {X=.5,Y=.5} end
 assert(n=='RenderTransform');return {Translation=self.translation,Scale=self.scale,Angle=0,Shear={X=0,Y=0}}
end
function widget:GetCachedGeometry() return self end
function widget:SetRenderTranslation(p) assert(not self.dead);state.writes=state.writes+1;self.translation={X=p.X,Y=p.Y} end
local slate={}
function slate:GetLocalSize(g) if g==canvas then return {X=1280,Y=720} end;assert(g==widget);return widget.size end
function slate:LocalToViewport(context,g,p,pixel)
 assert(context==canvas and g==canvas,'Corrected child origin must never feed back into placement')
 pixel.result={X=(state.parent_x or 0)+2*p.X,Y=(state.parent_y or 0)+2*p.Y}
end
safe=require('libs/hud_safe_area')
state.widget,state.slot,state.canvas=widget,slot,canvas
binding=safe.bind(widget,slate,track)
function apply(h,v) return safe.apply(binding,state.viewport,h or .2,v or .2) end
'''

KEY = r'''
state={refreshes=0}
local offsets={Key=856,gamepadKeys=864,Image_GamepadIcon=848,Text_Key=832,Text_Hold=840}
state.offsets=offsets
local function class(name)
 return {get_short_name=function() return name end,get_address=function() return name end,
 find_property=function(_,n) return {get_offset=function() return n=='isGamepad' and 0 or offsets[n] end} end,
 find_function=function() return {get_properties_size=function() return 1 end,
 find_property=function(_,n)
  if n==(state.modern_parameter and 'bIsGamepad' or 'isGamepad') then return {get_offset=function() return 0 end} end
 end} end}
end
local function widget(name,visibility)
 local o={visibility=visibility or 0}
 function o:get_class() return class(name) end
 function o:get_property(n) assert(n=='Visibility');return self.visibility end
 function o:SetVisibility(n) self.visibility=n end
 return o
end
local key=widget('UI_Key_C');local image=widget('Image',1);local text=widget('TextBlock');local hold=widget('TextBlock',3)
local action={get_short_name=function() return state.action or 'IA_Interact' end}
function key:get_property(n)
 if n=='Visibility' then return self.visibility end
 if n=='Key' then return action end
 if n=='gamepadKeys' then return state.override and {get_short_name=function() return state.override end} end
 if n=='Text_Hold' then return hold end
 if n=='Text_Key' then return text end
 assert(n=='Image_GamepadIcon');return image
end
function key:F_RefreshKey(gamepad)
 assert(gamepad);state.refreshes=state.refreshes+1;image.visibility=3;text.visibility=1;hold.visibility=1
end
hint=require('libs/interaction_key')
state.key,state.image,state.text,state.hold=key,image,text,hold
'''


def run(name, fixture, code):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().script_path = str(ROOT / 'scripts/?.lua')
    lua.execute("package.path=script_path..';'..package.path")
    lua.execute(fixture)
    lua.execute(code)
    print('PASS', name)


run('20 percent margins move the whole cooldown group without stale-geometry drift', GEOMETRY, r'''
for i=1,1000 do assert(apply()) end
near(state.widget.translation.X,236);near(state.widget.translation.Y,-124)
-- Resulting group bounds are x=512..832, y=952..1152: inside a 20% inset.
assert(safe.valid(binding,valid))
''')
run('centered bottom health group moves up; zero margins restore native coordinates', GEOMETRY, r'''
local a=state.slot.layout.Anchors;a.Minimum.X=.5;a.Maximum.X=.5
state.slot.layout.Alignment={X=.5,Y=1};state.slot.layout.Offsets={Left=0,Top=-80}
state.widget.size={X=400,Y=40}
assert(apply());near(state.widget.translation.X,0);near(state.widget.translation.Y,-64)
assert(apply(0,0));near(state.widget.translation.Y,0)
''')
run('moving canvas and changing margins use native parent layout without feedback', GEOMETRY, r'''
assert(apply());state.parent_x=40;state.parent_y=20
assert(apply());near(state.widget.translation.X,216);near(state.widget.translation.Y,-134)
assert(apply(.1,.1));near(state.widget.translation.X,88);near(state.widget.translation.Y,-62)
''')
run('native transform changes and script reset restore the current game-owned baseline', GEOMETRY, r'''
assert(apply());state.widget.translation={X=7,Y=-11};assert(apply())
safe.restore(binding,valid);near(state.widget.translation.X,7);near(state.widget.translation.Y,-11)
''')
run('stretched replacement layout relinquishes the owned translation', GEOMETRY, r'''
assert(apply());state.slot.layout.Anchors.Maximum.X=1
assert(not apply());near(state.widget.translation.X,0);near(state.widget.translation.Y,0)
''')
run('stale widgets receive no cleanup writes and changed parent slots invalidate bindings', GEOMETRY, r'''
assert(apply());state.slot.parent={get_address=function() return 888 end}
assert(not safe.valid(binding,valid))
state.objects[3]=nil;state.widget.dead=true;local writes=state.writes
safe.restore(binding,valid);assert(state.writes==writes)
''')
run('oversized groups center without shrinking text', GEOMETRY, r'''
near(safe.shift(10,910,200,1000),40)
near(safe.shift(210,790,200,1000),0)
''')
run('nested lobby groups use their verified parent canvas without reparenting', GEOMETRY, r'''
state.canvas.name='CanvasPanel_86'
local nested=safe.bind(state.widget,binding.slate,track,'CanvasPanel_86')
assert(nested and safe.apply(nested,state.viewport,.2,.3))
near(state.widget.translation.X,236);near(state.widget.translation.Y,-196)
safe.restore(nested,valid);near(state.widget.translation.X,0);near(state.widget.translation.Y,0)
''')
run('measured HUD groups pack inside margins without ammo/cooldown overlap or drift', GEOMETRY, r'''
local function plan(name,priority,native,box)
 return {binding={widget={name=name}},priority=priority,group=1,native=native,
  left=box[1]*2560,top=box[2]*1440,right=box[3]*2560,bottom=box[4]*1440,
  min_x=512,max_x=2048,min_y=432,max_y=1008,width=2560,height=1440,
  dx=0,dy=0,enabled=true,horizontal=true,vertical=true}
end
local function rect(x,y,r,b) return {left=x*2560,top=y*1440,right=r*2560,bottom=b*1440} end
local function make()
 return {
  plan('health',1,rect(.35,.88,.581,.933),{.35,.648,.581,.7}),
  plan('spells',2,rect(.02,.835,.098,.93),{.2,.605,.278,.7}),
  plan('cooldowns',3,rect(.601,.883,.8,.934),{.601,.649,.8,.7}),
  plan('ammo',4,rect(.885,.808,.981,.939),{.704,.569,.8,.7}),
  plan('level',5,rect(.547,.058,.979,.085),{.368,.3,.8,.327}),
  plan('party',6,rect(.02,.06,.24,.33),{.2,.3,.42,.57}),
  plan('hints',7,rect(.812,.78,.971,.957),{.641,.523,.8,.7}),
 }
end
local previous
for step=1,100 do
 local plans=make();safe.avoid_overlaps(plans,4)
 local result={}
 for i,p in ipairs(plans) do
  assert(p.left>=p.min_x and p.right<=p.max_x+.001 and p.top>=p.min_y and p.bottom<=p.max_y+.001,p.binding.widget.name)
  for j=1,i-1 do local q=plans[j]
   assert(p.right<=q.left or p.left>=q.right or p.bottom<=q.top or p.top>=q.bottom,p.binding.widget.name..' overlaps '..q.binding.widget.name)
  end
  result[#result+1]=p.left..','..p.top
 end
 local signature=table.concat(result,';');assert(not previous or signature==previous);previous=signature
end
''')
run('world and dropped-item Interact hints keep X without changing hold presentation', KEY, r'''
assert(hint.update(state.key));assert(state.refreshes==1 and state.hold.visibility==3)
assert(not hint.update(state.key));assert(state.refreshes==1)
state.image.visibility=1;state.text.visibility=0
assert(hint.update(state.key));assert(state.refreshes==2 and state.hold.visibility==3)
''')
run('unrelated and explicitly overridden actions keep native labels', KEY, r'''
state.action='IA_SpellA';assert(not hint.update(state.key))
state.action='IA_Interact';state.override='IA_Other';assert(not hint.update(state.key))
state.override=nil;state.key.visibility=2;assert(not hint.update(state.key));assert(state.refreshes==0)
''')
run('0.3.0.0 key layout keeps X and native hold presentation', KEY, r'''
state.modern_parameter=true
for name,value in pairs(state.offsets) do state.offsets[name]=value-16 end
assert(hint.update(state.key));assert(state.refreshes==1 and state.hold.visibility==3)
''')
run('mixed unverified key layouts stop before changing hint presentation', KEY, r'''
state.offsets.Image_GamepadIcon=832
assert(not pcall(hint.update,state.key));assert(state.refreshes==0)
''')

QUERY = r'''
state={objects={},count=0,queries=0,loaded=true}
local function obj(name,properties)
 state.count=state.count+1
 local o={index=state.count,name=name,props=properties or {}}
 function o:get_address() return self.index*4096 end
 function o:read_dword(n) assert(n==12);return self.index end
 function o:get_short_name() return self.name end
 function o:get_property(n) return self.props[n] end
 function o:is_a(class) return class==state.viewport_class or class==state.target end
 function o:get_class() return self end
 function o:find_property(n)
  assert(n=='GameViewport');return {get_offset=function() return 3448 end}
 end
 state.objects[o.index]=o;return o
end
state.target=obj('UI_Key_C');state.viewport_class={}
state.viewport=obj('Viewport');state.engine=obj('Engine',{GameViewport=state.viewport})
state.key=obj('UI_Key_1')
local lib={GetAllWidgetsOfClass=function(_,world,found,class,top)
 assert(world==state.engine.props.GameViewport and class==state.target and top==false)
 state.queries=state.queries+1
 if state.objects[state.key.index] then found[1]=state.key end
end}
local query_class={find_function=function(_,name)
 assert(name=='GetAllWidgetsOfClass')
 return {get_properties_size=function() return 40 end,find_property=function(_,n)
  local offsets={WorldContextObject=0,FoundWidgets=8,WidgetClass=24,TopLevelOnly=32}
  return {get_offset=function() return offsets[n] end}
 end}
end,get_class_default_object=function() return lib end}
local array={get_objects_offset=function() return 0 end,get_item_distance=function() return 24 end,
 get_object_count=function() return state.count+1 end,get_object=function(_,i) return state.objects[i] end}
uevr={api={get_uobject_array=function() return array end,find_uobject=function(_,path)
 if path=='Class /Script/UMG.WidgetBlueprintLibrary' then return query_class end
 if path=='Class /Script/Engine.GameViewportClient' then return state.viewport_class end
 assert(path=='WidgetBlueprintGeneratedClass /Test/UI_Key.UI_Key_C');return state.loaded and state.target or nil
end}}
query=require('libs/live_widgets')('WidgetBlueprintGeneratedClass /Test/UI_Key.UI_Key_C',8,.25)
state.obj=obj
'''
run('native query validates lifetimes and refreshes immediately when the viewport changes', QUERY, r'''
local found=query.get(state.engine,0);local ref=found[state.key:get_address()]
assert(ref and query.valid(ref) and state.queries==1)
query.get(state.engine,.1);assert(state.queries==1)
state.engine.props.GameViewport=state.obj('NewViewport');query.get(state.engine,.1);assert(state.queries==2)
state.objects[state.key.index]=nil;assert(not query.valid(ref))
query.get(state.engine,.5);assert(next(query.get(state.engine,.6))==nil)
''')
run('native query waits for a late-loaded class without enabling UObjectHook', QUERY, r'''
state.loaded=false;assert(next(query.get(state.engine,0))==nil)
state.loaded=true;assert(next(query.get(state.engine,.3)))
assert(state.queries==1)
''')
