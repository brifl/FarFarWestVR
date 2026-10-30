// Original read-only compatibility checks for the Far Far West extension.
// No engine headers, engine calls, hooks, or writes to game memory.
#pragma once
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>

namespace ffw::compat {
struct Result {
    uint64_t array=0, pool=0;
    uint32_t count=0, timestamp=0, image_size=0;
    const char* reason="not checked";
    explicit operator bool() const { return array && pool; }
};
template<class T> T value(const void* p,size_t offset=0) {
    T result{};std::memcpy(&result,static_cast<const uint8_t*>(p)+offset,sizeof(T));return result;
}
inline bool pointer(uint64_t p) {return p>=65536 && p<0x0000800000000000ULL && !(p&7);}

// Reader.read must copy safely and enforce an overall read/time budget.
template<class Reader> class Discovery {
    Reader& reader;
    uint64_t base,end;
    bool inside(uint64_t p,size_t size) const {return p>=base && p<end && size<=end-p;}
    template<size_t N> bool read(uint64_t p,std::array<uint8_t,N>& out) {
        return p>=65536 && p<0x0000800000000000ULL-N && reader.read(p,out.data(),N);
    }
    std::string name(uint64_t pool,uint32_t id) {
        const auto block=id>>16;
        if (block>=8192) return {};
        std::array<uint8_t,8> ptr{};
        if (!read(pool+16+block*8ULL,ptr)) return {};
        const auto page=value<uint64_t>(ptr.data());if (!pointer(page)) return {};
        const auto entry=page+(id&65535)*2ULL;
        std::array<uint8_t,2> header{};if (!read(entry,header)) return {};
        const auto bits=value<uint16_t>(header.data());const auto length=bits>>6;
        // Canaries are ASCII. Reject wide/oversize names without calling engine code.
        if ((bits&1) || length<1 || length>1023) return {};
        std::string text(length,'\0');
        return reader.read(entry+2,text.data(),text.size())?text:std::string{};
    }
    bool object(uint64_t array,uint32_t index,std::array<uint8_t,40>& out,uint64_t* address=nullptr) {
        std::array<uint8_t,8> ptr{};
        if (!read(array,ptr)) return false;
        const auto chunks=value<uint64_t>(ptr.data());if (!pointer(chunks)) return false;
        if (!read(chunks+(index/65536)*8ULL,ptr)) return false;
        const auto chunk=value<uint64_t>(ptr.data());if (!pointer(chunk)) return false;
        if (!read(chunk+(index%65536)*24ULL+8,ptr)) return false;
        const auto obj=value<uint64_t>(ptr.data());if (!pointer(obj) || !read(obj,out)) return false;
        if (address) *address=obj;
        return value<uint32_t>(out.data(),12)==index && inside(value<uint64_t>(out.data()),8);
    }
    bool array_candidate(const uint8_t* h,uint64_t address) {
        const auto count=value<int32_t>(h,8),capacity=value<int32_t>(h,12);
        const auto chunks=value<int32_t>(h,16),max=value<int32_t>(h,20);
        if (!pointer(value<uint64_t>(h)) || count<1024 || count>1000000 || chunks<1 || chunks>16
            || max<chunks || max>4096 || capacity!=max*65536 || count>chunks*65536) return false;
        std::array<uint8_t,40> obj{};
        for (uint32_t i=0;i<4;++i) if (!object(address,i,obj)) return false;
        return true;
    }
    bool pool_candidate(const uint8_t* h,uint64_t address) {
        const auto block=value<uint32_t>(h,8),cursor=value<uint32_t>(h,12);
        return block<8192 && cursor>0 && cursor<=131072 && pointer(value<uint64_t>(h,16))
            && name(address,0)=="None";
    }
    bool identities(uint64_t array,uint64_t pool,uint32_t count) {
        std::array<uint8_t,40> obj{},klass{};uint64_t first=0;
        if (!object(array,0,obj,&first) || name(pool,value<uint32_t>(obj.data(),24))!="/Script/CoreUObject") return false;
        if (!object(array,1,obj) || name(pool,value<uint32_t>(obj.data(),24))!="Object"
            || value<uint64_t>(obj.data(),32)!=first) return false;
        if (!read(value<uint64_t>(obj.data(),16),klass) || name(pool,value<uint32_t>(klass.data(),24))!="Class") return false;
        // Include every live chunk boundary, rather than assuming the old chunk count.
        std::vector<uint32_t> samples;
        for (uint32_t i=0;i<1024;++i) samples.push_back(i);
        for (uint32_t i=65536;i<count;i+=65536) {samples.push_back(i-1);samples.push_back(i);}
        for (auto index:samples) {
            std::array<uint8_t,8> ptr{};
            if (!read(array,ptr)) return false;
            const auto chunks=value<uint64_t>(ptr.data());
            if (!read(chunks+(index/65536)*8ULL,ptr)) return false;
            const auto chunk=value<uint64_t>(ptr.data());
            if (!pointer(chunk) || !read(chunk+(index%65536)*24ULL+8,ptr)) return false;
            if (!value<uint64_t>(ptr.data())) continue; // Legitimately vacant slot.
            if (!object(array,index,obj) || name(pool,value<uint32_t>(obj.data(),24)).empty()) return false;
        }
        return true;
    }
    bool property(uint64_t klass,uint64_t pool,const char* wanted,uint32_t offset) {
        std::array<uint8_t,96> prefix{};if (!read(klass,prefix)) return false;
        auto p=value<uint64_t>(prefix.data(),80);
        for (unsigned i=0;p && i<2048;++i) {
            std::array<uint8_t,72> f{};if (!pointer(p) || !read(p,f) || !inside(value<uint64_t>(f.data()),8)) return false;
            if (name(pool,value<uint32_t>(f.data(),32))==wanted) return value<uint32_t>(f.data(),68)==offset;
            auto next=value<uint64_t>(f.data(),24);if (next==p) return false;p=next;
        }
        return false;
    }
    bool function(uint64_t klass,uint64_t pool,const char* wanted,uint32_t size) {
        std::array<uint8_t,96> prefix{};if (!read(klass,prefix)) return false;
        auto p=value<uint64_t>(prefix.data(),72);
        for (unsigned i=0;p && i<2048;++i) {
            std::array<uint8_t,96> f{};if (!pointer(p) || !read(p,f) || !inside(value<uint64_t>(f.data()),8)) return false;
            if (name(pool,value<uint32_t>(f.data(),24))==wanted) return value<uint32_t>(f.data(),88)==size;
            auto next=value<uint64_t>(f.data(),40);if (next==p) return false;p=next;
        }
        return false;
    }
    bool core_layout(uint64_t array,uint64_t pool,uint32_t count) {
        std::array<uint8_t,40> obj{};if (!object(array,1,obj)) return false;
        const auto class_type=value<uint64_t>(obj.data(),16);
        // Read chunks in batches; inspect only native UClass objects for these canaries.
        std::array<uint64_t,16> chunks{};
        std::array<uint8_t,8> ptr{};if (!read(array,ptr)) return false;
        if (!reader.read(value<uint64_t>(ptr.data()),chunks.data(),((count+65535)/65536)*8)) return false;
        unsigned found=0;
        for (uint32_t first=0;first<count;first+=256) {
            std::array<uint8_t,256*24> items{};auto n=std::min<uint32_t>(256,count-first);
            if (!reader.read(chunks[first/65536]+(first%65536)*24ULL,items.data(),n*24)) return false;
            for (uint32_t j=0;j<n;++j) {
                const auto address=value<uint64_t>(items.data(),j*24+8);
                if (!address) continue;
                if (!pointer(address) || !read(address,obj) || value<uint32_t>(obj.data(),12)!=first+j) return false;
                if (value<uint64_t>(obj.data(),16)!=class_type) continue;
                const auto label=name(pool,value<uint32_t>(obj.data(),24));
                unsigned bit=label=="Engine"?1:label=="Widget"?2:label=="CanvasPanelSlot"?4:
                    label=="WidgetLayoutLibrary"?8:label=="GameplayStatics"?16:0;
                if (!bit || (found&bit)) continue;
                std::array<uint8_t,40> outer{};
                if (!read(value<uint64_t>(obj.data(),32),outer)) return false;
                const auto package=name(pool,value<uint32_t>(outer.data(),24));
                if (package!=((bit==1 || bit==16)?"/Script/Engine":"/Script/UMG")) continue;
                bool valid=false;
                if (bit==1) valid=property(address,pool,"GameViewport",3448);
                if (bit==2) valid=property(address,pool,"RenderTransform",144) && property(address,pool,"RenderTransformPivot",200)
                    && function(address,pool,"SetRenderScale",16) && function(address,pool,"GetDesiredSize",16);
                if (bit==4) valid=property(address,pool,"LayoutData",56);
                if (bit==8) valid=function(address,pool,"GetViewportSize",24);
                if (bit==16) valid=function(address,pool,"GetPlayerController",24);
                if (!valid) return false;
                found|=bit;if (found==31) return true;
            }
        }
        return false;
    }
public:
    Discovery(Reader& r,uint64_t module,uint32_t size):reader(r),base(module),end(module+size) {}
    Result scan(uint32_t data_rva,uint32_t data_size) {
        Result out;out.image_size=static_cast<uint32_t>(end-base);
        if (data_size<24 || data_size>16*1024*1024 || !inside(base+data_rva,data_size)) {
            out.reason="invalid .data extent";return out;
        }
        std::vector<uint8_t> data(data_size);
        if (!reader.read(base+data_rva,data.data(),data.size())) {out.reason="unreadable .data";return out;}
        std::vector<uint64_t> arrays,pools;
        for (size_t i=0;i+24<=data.size();i+=8) {
            const auto address=base+data_rva+i;
            if (array_candidate(data.data()+i,address)) arrays.push_back(address);
            if (pool_candidate(data.data()+i,address)) pools.push_back(address);
            if (arrays.size()>8 || pools.size()>8) {out.reason="ambiguous candidate budget";return out;}
        }
        if (arrays.size()!=1 || pools.size()!=1) {out.reason="object/name tables not unique";return out;}
        std::array<uint8_t,24> header{};
        if (!read(arrays[0],header)) {out.reason="object table unreadable";return out;}
        const auto count=value<uint32_t>(header.data(),8);
        if (!identities(arrays[0],pools[0],count)) {out.reason="object/name identities changed";return out;}
        if (!core_layout(arrays[0],pools[0],count)) {out.reason="core reflection layout changed";return out;}
        out.array=arrays[0];out.pool=pools[0];out.count=count;out.reason="validated";return out;
    }
};
} // namespace ffw::compat

#ifdef _WIN32
#include <Windows.h>
namespace ffw::compat {
struct WindowsReader {
    HANDLE process;
    size_t calls=0,bytes=0;
    bool exhausted=false;
    std::chrono::steady_clock::time_point began=std::chrono::steady_clock::now();
    bool read(uint64_t p,void* out,size_t size) {
        if (exhausted) return false;
        if (++calls>250000 || size>64*1024*1024-bytes ||
            (calls%256==1 && std::chrono::steady_clock::now()-began>std::chrono::seconds(2))) {
            exhausted=true;return false;
        }
        bytes+=size;SIZE_T got=0;
        return p>=65536 && p<0x0000800000000000ULL-size &&
            ReadProcessMemory(process,reinterpret_cast<const void*>(p),out,size,&got) && got==size;
    }
};
inline Result discover(HANDLE process,uint64_t base) {
    WindowsReader reader{process};Result out;
    std::array<uint8_t,4096> headers{};
    if (!reader.read(base,headers.data(),headers.size()) || value<uint16_t>(headers.data())!=0x5a4d) {
        out.reason="invalid DOS header";return out;
    }
    const auto pe=value<uint32_t>(headers.data(),60);
    if (pe>3000 || value<uint32_t>(headers.data(),pe)!=0x4550 ||
        value<uint16_t>(headers.data(),pe+4)!=0x8664 || value<uint16_t>(headers.data(),pe+24)!=0x20b) {
        out.reason="invalid x64 PE header";return out;
    }
    out.timestamp=value<uint32_t>(headers.data(),pe+8);out.image_size=value<uint32_t>(headers.data(),pe+80);
    const auto sections=value<uint16_t>(headers.data(),pe+6),optional=value<uint16_t>(headers.data(),pe+20);
    const auto table=pe+24+optional;
    if (!sections || sections>32 || table+sections*40>headers.size() || out.image_size<4096 || out.image_size>1024*1024*1024) {
        out.reason="invalid PE sections";return out;
    }
    unsigned found=0;uint32_t rva=0,size=0;
    for (unsigned i=0;i<sections;++i) {
        const auto h=headers.data()+table+i*40;
        if (std::memcmp(h,".data\0\0\0",8)!=0) continue;
        if ((value<uint32_t>(h,36)&0xc0000000)!=0xc0000000) continue;
        ++found;size=value<uint32_t>(h,8);rva=value<uint32_t>(h,12);
    }
    if (found!=1) {out.reason="missing unique writable .data";return out;}
    auto result=Discovery<WindowsReader>(reader,base,out.image_size).scan(rva,size);
    result.timestamp=out.timestamp;
    if (reader.exhausted) {result.array=0;result.pool=0;result.reason="startup read budget exceeded";}
    return result;
}
inline Result discover_current() {
    wchar_t filename[1024]{};
    if (!GetModuleFileNameW(nullptr,filename,1024)) return {};
    const auto slash=wcsrchr(filename,L'\\');const auto name=slash?slash+1:filename;
    if (_wcsicmp(name,L"FarFarWest-Win64-Shipping.exe")!=0) {
        Result out;out.reason="unexpected executable";return out;
    }
    return discover(GetCurrentProcess(),reinterpret_cast<uint64_t>(GetModuleHandleW(nullptr)));
}
}
#endif
