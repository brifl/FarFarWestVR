"""Contextual Quest X drop: native input dispatch, hint ownership and possession (lupa)."""
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
MOCK = r'''
state={objects={},next=1,down=false,ready=true,drops=0,logs={},refreshes=0}
farfarwest_gameplay_ready=true
local offsets={GameViewport=3448,Pawn=744,AC_PlayerItems=1768,equipedItem=208,UI_ItemContext=1120,OwningPlayer=736,
 Key=840,gamepadKeys=848,Image_GamepadIcon=832,Text_Key=816,Text_Hold=824,bIsGamepad=0}
local event='InpActEvt_IA_Drop_K2Node_EnhancedInputActionEvent_14'
local methods={GetPlayerController={24,{WorldContextObject=0,PlayerIndex=8,ReturnValue=16}},
 MakeInputActionValueOfType={64,{X=0,Y=8,Z=16,ValueType=24,ReturnValue=32}},
 GetParent={8,{}},F_RefreshKey={1,{bIsGamepad=0}}}
methods[event]={48,{ActionValue=0,ElapsedTime=32,TriggeredTime=36,SourceAction=40}}
local function field(n) return {get_offset=function() return offsets[n] end} end
local function class(name,default)
 return {get_short_name=function() return name end,get_class_default_object=function() return default end,
 find_property=function(_,n)
  if n=='AC_PlayerItems' then
   if state.unsupported_pawn then return nil end
   if state.alternate_layout then return {get_offset=function() return 1904 end} end
  end
  return field(n)
 end,
 find_function=function(_,n)
  local spec=assert(methods[n],n)
  local fn={get_properties_size=function() return state.bad_event and n==event and 12 or spec[1] end,
   find_property=function(_,p) if spec[2][p]~=nil then return {get_offset=function() return spec[2][p] end} end end}
  if n==event then setmetatable(fn,{__call=function(_,pawn,value,elapsed,triggered,action)
   assert(pawn==state.pc.props.Pawn and value.typed and value.X==1 and value.ValueType==0
    and elapsed==0 and triggered==0 and action==state.drop)
   state.drops=state.drops+1
  end}) end
  return fn
 end}
end
local function object(name)
 local o={index=state.next,name=name,props={Visibility=3},class=class(name)}
 state.next=state.next+1;state.objects[o.index]=o
 function o:get_address() return self.index*256 end
 function o:read_dword(n) assert(n==12 and not self.dead);return self.index end
 function o:get_short_name() assert(not self.dead);return self.name end
 function o:get_full_name() return self.full_name or self.name end
 function o:get_class() assert(not self.dead);return self.class end
 function o:get_property(n) assert(not self.dead);return self.props[n] end
 function o:set_property(n,v) assert(not self.dead);self.props[n]=v end
 function o:SetVisibility(n) assert(not self.dead);self.props.Visibility=n end
 function o:GetParent() assert(not self.dead);return self.parent end
 function o:get_outer() return nil end
 return o
end
state.interact=object('IA_Interact');state.interact.full_name='InputAction /Game/Player/Inputs/IA_Interact.IA_Interact'
state.drop=object('IA_Drop');state.drop.full_name='InputAction /Game/Player/Inputs/IA_Drop.IA_Drop'
state.context=object('UI_DropItem_C')
state.key=object('UI_Key_C');state.key.parent=state.context
state.key.props.Key=state.drop
state.image=object('Image');state.image.props.Visibility=1
state.text=object('TextBlock');state.hold=object('TextBlock');state.hold.props.Visibility=4
state.key.props.Image_GamepadIcon=state.image;state.key.props.Text_Key=state.text;state.key.props.Text_Hold=state.hold
function state.key:F_RefreshKey(v)
 assert(v);state.refreshes=state.refreshes+1
 self.props.Image_GamepadIcon.props.Visibility=3;self.props.Text_Key.props.Visibility=1
 self.props.Text_Hold.props.Visibility=1
end
state.pawn=object('BP_Player_C');state.pc=object('Controller');state.pc.props.Pawn=state.pawn
state.items=object('AC_PlayerItems_C');state.item=object('BP_Item_Pet_Pig_C')
state.pawn.props.AC_PlayerItems=state.items;state.items.props.equipedItem=state.item
state.item.props.UI_ItemContext=state.context;state.item.props.OwningPlayer=state.pawn
state.viewport=object('Viewport');state.engine=object('Engine');state.engine.props.GameViewport=state.viewport
local statics={GetPlayerController=function(_,v,i) assert(v==state.viewport and i==0);return state.pc end}
local input={MakeInputActionValueOfType=function(_,x,y,z,t) return {typed=true,X=x,Y=y,Z=z,ValueType=t} end}
local array={get_objects_offset=function() return 0 end,get_item_distance=function() return 24 end,
 get_object=function(_,i) return state.objects[i] end}
local initialized=false
local function ref(o) assert(initialized);return {object=o,index=o.index,address=o:get_address(),name=o.name} end
local function valid(r) assert(initialized);return r and state.objects[r.index]==r.object end
package.loaded['libs/active_widgets']=function()
 return {get=function() initialized=true;return state.objects[state.key.index] and {ref(state.key)} or {} end,
 valid=valid,track=ref}
end
local function log(s) state.logs[#state.logs+1]=s end
uevr={api={get_uobject_array=function() return array end,find_uobject=function(_,path)
 if path==state.interact.full_name then return state.interact end
 local name=path:match('%.([^%.]+)$')
 return class(name,({GameplayStatics=statics,EnhancedInputLibrary=input})[name])
end},params={vr={is_runtime_ready=function() return state.ready end,is_hmd_active=function() return true end,
 get_mod_value=function() return state.menu and 'true' or 'false' end,
 get_action_handle=function(path) assert(path=='/actions/default/in/AButtonLeft');return 123 end,
 get_left_joystick_source=function() return 1 end,
 is_action_active=function(h,source) assert(h==123 and source==1);return state.down end},
 functions={is_drawing_ui=function() return false end,log_info=log,log_warn=log}}}
function tick() feature.tick(state.engine,.016) end
function healthy() for _,s in ipairs(state.logs) do assert(not s:find('Stopped safely',1,true),s) end end
'''


def run(name, code):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().script_path = str(ROOT / 'scripts/?.lua')
    lua.execute("package.path=script_path..';'..package.path")
    lua.execute(MOCK)
    lua.execute("feature=require('libs/carry_drop')()")
    lua.execute(code)
    print('PASS', name)


run('fresh X dispatches native Drop once and its X hint preserves hold presentation', '''
tick();healthy();assert(state.key.props.gamepadKeys==state.interact and state.hold.props.Visibility==4)
state.down=true;for i=1,100 do tick() end;healthy();assert(state.drops==1)
state.down=false;tick();state.down=true;tick();assert(state.drops==2)
assert(state.key.props.Key==state.drop)
feature.reset();assert(state.key.props.gamepadKeys==nil)
''')
run('guns, hidden prompts and unsupported pawns never receive Drop', '''
tick();state.item.props.UI_ItemContext=nil;state.down=true;tick();healthy();assert(state.drops==0)
assert(state.key.props.gamepadKeys==nil)
state.item.props.UI_ItemContext=state.context;state.context.props.Visibility=1
state.down=false;tick();state.down=true;tick();healthy();assert(state.drops==0)
state.unsupported_pawn=true;state.context.props.Visibility=3;tick();healthy();assert(state.drops==0)
''')
run('menus require release before rearming and a replaced pawn uses its current item', '''
tick();state.menu=true;state.down=true;tick();state.menu=false;tick();healthy();assert(state.drops==0)
state.down=false;tick();state.down=true;tick();assert(state.drops==1)
state.pc.props.Pawn=nil;state.down=false;tick();assert(state.key.props.gamepadKeys==nil)
state.pc.props.Pawn=state.pawn;tick();state.down=true;tick();healthy();assert(state.drops==2)
''')
run('native hint rebuild and unrelated override retain their ownership', '''
tick();state.image.props.Visibility=1;state.text.props.Visibility=3;tick();healthy()
assert(state.image.props.Visibility==3 and state.text.props.Visibility==1)
state.key.props.gamepadKeys=state.drop;feature.reset();assert(state.key.props.gamepadKeys==state.drop)
''')
run('unknown event layout stops before hint mutation or input dispatch', '''
state.bad_event=true;tick();assert(state.drops==0 and state.key.props.gamepadKeys==nil)
state.bad_event=false;state.down=true;tick();assert(state.drops==0)
''')
run('destroyed hint receives no restore writes', '''
tick();state.objects[state.key.index]=nil;state.key.dead=true;feature.reset();healthy()
''')
run('alternate possession layout is skipped and normal pickaxe Drop recovers without a script restart', '''
state.item.name='BP_Item_Pickaxe_C'
tick();assert(state.key.props.gamepadKeys==state.interact)
state.alternate_layout=true;state.down=true;tick();tick();healthy()
assert(state.drops==0 and state.key.props.gamepadKeys==nil)
state.alternate_layout=false;tick();assert(state.drops==0)
state.down=false;tick();state.down=true;tick();healthy()
assert(state.drops==1 and state.key.props.gamepadKeys==state.interact)
local skipped=0
for _,s in ipairs(state.logs) do if s:find('Skipping unsupported pawn',1,true) then skipped=skipped+1 end end
assert(skipped==1)
''')
