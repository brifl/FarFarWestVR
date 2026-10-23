"""Native slot-count validation, independent of discovery work budgets (lupa)."""
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
lua = LuaRuntime(unpack_returned_tuples=True)
lua.globals().script_path = str(ROOT / 'scripts/?.lua')
lua.execute("package.path=script_path..';'..package.path")
lua.execute('''
local count=require('libs/object_count')
local reads=0
local array={get_object_count=function() return 286344 end,
 get_object=function() error('Validating a count must not scan the object array') end}
assert(count(array)==286344)
for _,n in ipairs({1,249999,250000,250001,1000000,0x7fffffff}) do
 array.get_object_count=function() reads=reads+1;return n end
 assert(count(array)==n)
end
assert(reads==6)
for _,n in ipairs({0,-1,.5,0x80000000,math.huge,-math.huge,0/0,'286344',false}) do
 array.get_object_count=function() return n end
 local ok,err=pcall(count,array)
 assert(not ok and tostring(err):find('Invalid native UObject array count',1,true))
end
array.get_object_count=function() return nil end
assert(not pcall(count,array))
''')
print('PASS valid native counts above the old 250,000-slot limit remain usable')
print('PASS count validation never scans objects and reads the native count once')
print('PASS invalid, nonintegral and out-of-int32 counts are rejected')
