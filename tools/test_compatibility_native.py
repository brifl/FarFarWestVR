"""Exercise discovery against moved tables and incompatible/ambiguous fake memory."""
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from prepare_compatibility_backend import prepare, INSERT

ROOT = Path(__file__).resolve().parents[1]
with TemporaryDirectory() as temp:
    root = Path(temp)
    source = root/'test.cpp'
    source.write_text(r'''
#include "FFWCompatibility.hpp"
#include <cassert>
#include <iostream>
using namespace ffw::compat;
struct Memory {
 static constexpr uint64_t base=0x10000000;
 std::vector<uint8_t> data=std::vector<uint8_t>(0x800000);
 unsigned calls=0;bool denied=false;
 bool read(uint64_t p,void* out,size_t n) {
  ++calls;if(denied || p<base || p-base>data.size() || n>data.size()-(p-base))return false;
  memcpy(out,data.data()+p-base,n);return true;
 }
 template<class T> void put(uint64_t offset,T v) {memcpy(data.data()+offset,&v,sizeof(v));}
 uint32_t cursor=0;
 uint32_t name(const std::string& n) {
  if(cursor&1)++cursor;
  auto id=cursor/2;
  put<uint16_t>(0x600000+cursor,static_cast<uint16_t>(n.size()<<6));
  memcpy(data.data()+0x600002+cursor,n.data(),n.size());cursor+=2+n.size();return id;
 }
 uint64_t obj(unsigned i) {return base+0x400000+i*128;}
 void object(unsigned i,const std::string& n,unsigned klass=2,unsigned outer=0) {
  auto o=obj(i)-base;put<uint64_t>(o,base+0x500);put<uint32_t>(o+12,i);
  put<uint64_t>(o+16,obj(klass));put<uint32_t>(o+24,name(n));put<uint64_t>(o+32,i?obj(outer):0);
  put<uint64_t>((i<65536?0x20000:0x1a0000)+(i%65536)*24+8,obj(i));
 }
 uint64_t next=0x500000;
 void property(unsigned klass,const char* n,uint32_t offset) {
  auto p=next;next+=128;put<uint64_t>(p,base+0x500);
  auto owner=obj(klass)-base;auto previous=value<uint64_t>(data.data()+owner,80);
  put<uint64_t>(p+24,previous);put<uint32_t>(p+32,name(n));put<uint32_t>(p+68,offset);
  put<uint64_t>(owner+80,base+p);
 }
 void function(unsigned klass,const char* n,uint32_t size) {
  auto p=next;next+=128;put<uint64_t>(p,base+0x500);
  auto owner=obj(klass)-base;auto previous=value<uint64_t>(data.data()+owner,72);
  put<uint64_t>(p+40,previous);put<uint32_t>(p+24,name(n));put<uint32_t>(p+88,size);
  put<uint64_t>(owner+72,base+p);
 }
 void setup(unsigned shift=0) {
  auto a=0x1000+shift,p=0x1100+shift;
  put<uint64_t>(a,base+0x10000);put<int32_t>(a+8,65537);put<int32_t>(a+12,4*65536);
  put<int32_t>(a+16,2);put<int32_t>(a+20,4);
  put<uint64_t>(0x10000,base+0x20000);put<uint64_t>(0x10008,base+0x1a0000);
  put<uint64_t>(p+16,base+0x600000);name("None");
  object(0,"/Script/CoreUObject",3);object(1,"Object");object(2,"Class");object(3,"Package");
  object(4,"/Script/Engine",3);object(5,"/Script/UMG",3);
  object(6,"Engine",2,4);object(7,"Widget",2,5);object(8,"CanvasPanelSlot",2,5);
  object(9,"WidgetLayoutLibrary",2,5);object(10,"GameplayStatics",2,4);
  for(unsigned i=11;i<1024;++i)object(i,"Item");
  // Last object lives in a separate chunk, without allocating a giant object buffer.
  put<uint64_t>(0x1a0008,obj(11));put<uint32_t>(obj(11)-base+12,65536);
  put<uint64_t>(0x20000+11*24+8,0);
  property(6,"GameViewport",3448);property(7,"RenderTransform",144);property(7,"RenderTransformPivot",200);
  property(8,"LayoutData",56);function(7,"SetRenderScale",16);function(7,"GetDesiredSize",16);
  function(9,"GetViewportSize",24);function(10,"GetPlayerController",24);
  put<uint32_t>(p+12,cursor);
 }
 Result scan() {return Discovery<Memory>(*this,base,0x4000).scan(0x1000,0x2000);}
};
int main() {
 {Memory m;m.setup();auto r=m.scan();assert(r && r.array==m.base+0x1000 && r.pool==m.base+0x1100 && r.count==65537);}
 {Memory m;m.setup(0x500);auto r=m.scan();assert(r && r.array==m.base+0x1500);}
 std::cout<<"PASS relocated tables and compact chunk boundaries\n";
 {Memory m;m.setup();memcpy(m.data.data()+0x1800,m.data.data()+0x1000,24);assert(!m.scan());}
 {Memory m;m.setup();memcpy(m.data.data()+0x1800,m.data.data()+0x1100,24);assert(!m.scan());}
 std::cout<<"PASS duplicate object/name candidates fail closed\n";
 {Memory m;m.setup();m.put<uint32_t>(m.obj(1)-m.base+12,4);assert(!m.scan());}
 {Memory m;m.setup();m.put<uint32_t>(m.obj(1)-m.base+24,0);assert(!m.scan());}
 {Memory m;m.setup();m.put<uint32_t>(m.obj(11)-m.base+12,11);assert(!m.scan());}
 {Memory m;m.setup();m.put<uint64_t>(0x1000,m.base+0xf00000);assert(!m.scan());}
 std::cout<<"PASS wrong identities, chunk stride/index and unreadable pointers rejected\n";
 {Memory m;m.setup();m.property(6,"GameViewport",3456);auto r=m.scan();assert(!r && std::string(r.reason)=="core reflection layout changed");}
 {Memory m;m.setup();m.function(9,"GetViewportSize",32);assert(!m.scan());}
 {Memory m;m.setup();m.denied=true;assert(!m.scan());}
 {Memory m;m.setup();assert(!Discovery<Memory>(m,m.base,0x4000).scan(0x1000,32*1024*1024));}
 std::cout<<"PASS changed field/function ABI, unreadable memory and scan extent rejected\n";
}
''')
    binary = root/'test'
    subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-I', str(ROOT/'native'), str(source), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
    path = root/'dependencies/submodules/UESDK/src/sdk/UObjectArray.cpp'
    path.parent.mkdir(parents=True)
    original = '#include "UObjectArray.hpp"\nvoid untouched() {}\n'+'''        // Only validated Far Far West executable builds may use this compact layout.
        // 715567327 IsBadReadPtr
        s_is_chunked = true;
        // Preserve every other SDK port.
'''
    path.write_text(original)
    prepare(root);first=path.read_bytes();prepare(root)
    assert path.read_bytes()==first and INSERT in path.read_text()
    assert 'Preserve every other SDK port.' in path.read_text()
    assert (root/'ffw-tests/compatibility-20261030/source-before/UObjectArray.cpp').read_text()==original
    path.write_text('unexpected source')
    try:
        prepare(root)
    except ValueError:
        pass
    else:
        raise AssertionError('unguarded source mutation')
    assert path.read_text()=='unexpected source'
    print('PASS guarded preparation preserves ports/originals, is repeatable and rejects mismatches')
