"""Projection aspect, attachment invariance and transform ownership (lupa)."""
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
MOCK = r'''
shape=require('libs/ui_shape')
function near(a,b) assert(math.abs(a-b)<1e-5,tostring(a)..' differs from '..tostring(b)) end
function widget(sx,sy)
    local o={scale={X=sx or 1,Y=sy or 1},pivot={X=.5,Y=.5},writes=0}
    function o:get_property(name)
        if name=='RenderTransform' then return {Scale=self.scale} end
        assert(name=='RenderTransformPivot');return self.pivot
    end
    function o:GetDesiredSize() return {X=64,Y=32,typed=true} end
    function o:SetRenderScale(v)
        assert(v.typed);self.scale={X=v.X,Y=v.Y};self.writes=self.writes+1
        if self.fail then error('partial setter failure') end
    end
    function o:SetRenderTransformPivot(v)
        assert(v.typed);self.pivot={X=v.X,Y=v.Y};self.writes=self.writes+1
    end
    return o
end
function point(o,x,y)
    return {X=(x-o.pivot.X*64)*o.scale.X+o.pivot.X*64,
        Y=(y-o.pivot.Y*32)*o.scale.Y+o.pivot.Y*32}
end
'''


def run(name, test):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().script_path = str(ROOT / 'scripts/?.lua')
    lua.execute("package.path=script_path..';'..package.path")
    lua.execute(MOCK)
    lua.execute(test)
    print('PASS', name)


run('live eye projection normalizes angular extents independently of resolution', '''
local projection={[0]={[0]=.72654},[1]={[1]=.83548},[2]={[0]=0,[1]=.19319}}
local k=shape.height_factor(projection,2560,1440)
near(k,.64685)
near(1/(2560*.72654),k/(1440*.83548))
near(shape.height_factor(projection,1280,720),k)
near(shape.height_factor({[0]={[0]=1},[1]={[1]=1}},1000,1000),1)
assert(shape.height_factor(projection,0,1440)==nil)
assert(shape.height_factor({[0]={[0]=0},[1]={[1]=1}},1000,500)==nil)
''')
run('bottom attachment stays fixed and original transform is restored', '''
local o=widget();local before=point(o,32,32)
local binding=shape.bind(o,{X=.5,Y=1});assert(shape.apply(binding,.647))
local after=point(o,32,32);near(before.X,after.X);near(before.Y,after.Y)
near(o.scale.Y,.647);near(o.pivot.Y,1)
local writes=o.writes;for i=1,120 do assert(shape.apply(binding,.647)) end
assert(o.writes==writes)
shape.restore(binding);near(o.scale.Y,1);near(o.pivot.Y,.5)
''')
run('centered reticle keeps center and responds without compounded scaling', '''
local o=widget();local binding=shape.bind(o,{X=.5,Y=.5})
shape.apply(binding,.647);local center=point(o,32,16);near(center.X,32);near(center.Y,16)
shape.apply(binding,.8);near(o.scale.Y,.8)
shape.apply(binding,nil);near(o.scale.Y,1)
''')
run('native scale animation is respected when the pivot already matches', '''
local o=widget(1.5,.5);local binding=shape.bind(o)
shape.apply(binding,.6);near(o.scale.Y,.3)
o.scale={X=2,Y=.8};shape.apply(binding,.6);near(o.scale.Y,.48)
shape.restore(binding);near(o.scale.X,2);near(o.scale.Y,.8)
''')
run('unsafe pivot changes are skipped without moving a pre-scaled widget', '''
local o=widget(1.5,.5);local binding=shape.bind(o,{X=.5,Y=1})
assert(not shape.apply(binding,.6) and o.writes==0)
near(o.scale.Y,.5);near(o.pivot.Y,.5)
''')
run('external game transforms survive cleanup', '''
local o=widget();local binding=shape.bind(o,{X=.5,Y=1});shape.apply(binding,.6)
o.scale={X=1,Y=.8};assert(not shape.apply(binding,.6))
near(o.scale.Y,.8);near(o.pivot.Y,.5)
local p=widget();local b=shape.bind(p);shape.apply(b,.6)
p.pivot={X=.2,Y=.3};assert(not shape.apply(b,.6))
near(p.scale.Y,1);near(p.pivot.X,.2);near(p.pivot.Y,.3)
''')
run('partial native setter writes can be restored', '''
local o=widget();local binding=shape.bind(o,{X=.5,Y=1});o.fail=true
assert(not pcall(shape.apply,binding,.6));o.fail=false
shape.restore(binding);near(o.scale.Y,1);near(o.pivot.Y,.5)
''')
