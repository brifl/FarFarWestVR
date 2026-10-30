// Read-only process probe using exactly the backend's startup checks.
#include "FFWCompatibility.hpp"
#include <TlHelp32.h>
#include <cstdlib>
#include <iostream>

int main(int argc,char** argv) {
    if (argc!=2) return 2;
    const auto pid=static_cast<DWORD>(std::strtoul(argv[1],nullptr,10));
    auto snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPMODULE,pid);
    if (snapshot==INVALID_HANDLE_VALUE) return 3;
    MODULEENTRY32W module{};module.dwSize=sizeof(module);
    const bool found=Module32FirstW(snapshot,&module)!=0;CloseHandle(snapshot);
    if (!found || _wcsicmp(module.szModule,L"FarFarWest-Win64-Shipping.exe")!=0) return 4;
    auto process=OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION,FALSE,pid);
    if (!process) return 5;
    const auto began=std::chrono::steady_clock::now();
    const auto base=reinterpret_cast<uint64_t>(module.modBaseAddr);
    const auto result=ffw::compat::discover(process,base);CloseHandle(process);
    const auto ms=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now()-began).count();
    std::cout<<"{\"ok\":"<<(result?"true":"false")<<",\"reason\":\""<<result.reason
        <<"\",\"timestamp\":"<<result.timestamp<<",\"image_size\":"<<result.image_size
        <<",\"array_rva\":"<<(result?result.array-base:0)<<",\"pool_rva\":"<<(result?result.pool-base:0)
        <<",\"objects\":"<<result.count<<",\"milliseconds\":"<<ms<<"}\n";
    return result?0:1;
}
