"""Add the extension's optional haptic/performance bridge to the retained UEVR build.

Does not clone, reset, build, or touch the engine SDK. Originals stay private.
"""
import argparse
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]


def replace_once(text,old,new):
    if new in text:return text
    if text.count(old)!=1:raise ValueError('Native source does not match the expected insertion: '+old[:100])
    return text.replace(old,new,1)


def prepare(root):
    edits={}
    path=root/'src/mods/VR.cpp';s=path.read_text()
    s=replace_once(s,'#include "VR.hpp"','#include "VR.hpp"\n#include "uevr/FFWDiagnostics.hpp"')
    s=replace_once(s,'    update_dpad_gestures();','''    // Report confirmation owns haptics briefly, without changing D-pad input.
    if (ffw::report_haptics().active()) {
        trigger_haptic_vibration(0,.02f,1,0,get_left_joystick());
        trigger_haptic_vibration(0,.02f,1,0,get_right_joystick());
    }
    update_dpad_gestures();''')
    s=replace_once(s,'    if (get_runtime()->is_openvr()) {\n        vr::VRInput()->TriggerHapticVibrationAction',
        '''    const int hand=source==get_left_joystick()?0:source==get_right_joystick()?1:-1;
    if (!ffw::report_haptics().route(hand,seconds_from_now,duration,frequency,amplitude)) return;
    if (get_runtime()->is_openvr()) {
        vr::VRInput()->TriggerHapticVibrationAction''')
    edits[path]=s
    path=root/'src/mods/PluginLoader.cpp';s=path.read_text()
    s=replace_once(s,'#include "VR.hpp"','#include "VR.hpp"\n#include "uevr/FFWDiagnostics.hpp"\n#include <psapi.h>')
    marker='// Read-only, bounded diagnostics for the profile.'
    if marker in s:
        start=s.index(marker);end=s.index('// TODO: Optimize this with a map',start)
        s=s[:start]+s[end:]
    s=replace_once(s,'// TODO: Optimize this with a map\nvoid set_mod_value',r'''// Read-only, bounded diagnostics for the profile. No process or GPU settings change.
std::string ffw_diagnostic_stats() {
    ffw::costs().enabled.store(true,std::memory_order_relaxed);
    PROCESS_MEMORY_COUNTERS_EX process{};process.cb=sizeof(process);
    MEMORYSTATUSEX memory{};memory.dwLength=sizeof(memory);
    const bool process_ok=GetProcessMemoryInfo(GetCurrentProcess(),reinterpret_cast<PROCESS_MEMORY_COUNTERS*>(&process),sizeof(process))!=0;
    const bool memory_ok=GlobalMemoryStatusEx(&memory)!=0;
    std::array<double,ffw::cost_groups> peak{};
    for (size_t i=0;i<peak.size();++i) {
        peak[i]=ffw::costs().group[i].peak.exchange(0,std::memory_order_relaxed)/1e6;
    }
    ::vr::Compositor_FrameTiming timing{};timing.m_nSize=sizeof(timing);
    ::vr::Compositor_CumulativeStats stats{};bool timing_ok=false;
    auto runtime=VR::get()->get_runtime();
    if (runtime && runtime->loaded && runtime->is_openvr()) {
        if (auto compositor=::vr::VRCompositor()) {
            timing_ok=compositor->GetFrameTiming(&timing);
            compositor->GetCumulativeStats(&stats,sizeof(stats));
        }
    }
    return fmt::format("v=1;ws={};commit={};free={};gpu={:.2f};interval={:.2f};present={};drop={};reproj={};lp={:.2f};lq={:.2f};ls={:.2f};li={:.2f}",
        process_ok?static_cast<int64_t>(process.WorkingSetSize/1048576):-1,
        process_ok?static_cast<int64_t>(process.PrivateUsage/1048576):-1,
        memory_ok?static_cast<int64_t>(memory.ullAvailPhys/1048576):-1,
        timing_ok?timing.m_flTotalRenderGpuMs:-1.0f,timing_ok?timing.m_flClientFrameIntervalMs:-1.0f,
        stats.m_nNumFramePresents,stats.m_nNumDroppedFrames,stats.m_nNumReprojectedFrames,
        peak[0],peak[1],peak[2],peak[3]);
}

// TODO: Optimize this with a map
void set_mod_value''')
    old='''    auto& mods = g_framework->get_mods()->get_mods();'''
    # Scope each insertion to its existing API function, leaving unrelated methods alone.
    start=s.index('void set_mod_value(');end=s.index('void get_mod_value(',start)
    part=s[start:end]
    part=replace_once(part,old,'''    if (std::string_view{key}=="FFW_ReportHaptics") {
        if (std::string_view{value}=="1") {
            ffw::report_haptics().start();
            VR::get()->trigger_haptic_vibration(0,.02f,1,0,VR::get()->get_left_joystick());
            VR::get()->trigger_haptic_vibration(0,.02f,1,0,VR::get()->get_right_joystick());
        }
        return;
    }
''' + old)
    s=s[:start]+part+s[end:]
    start=s.index('void get_mod_value(');end=s.index('void save_config(',start);part=s[start:end]
    part=replace_once(part,old,'''    if (std::string_view{key}=="FFW_ReportHaptics" || std::string_view{key}=="FFW_DiagnosticStats") {
        const auto result=std::string_view{key}=="FFW_ReportHaptics"?std::string{"1"}:ffw_diagnostic_stats();
        const auto length=std::min<size_t>(result.size(),max_size-1);
        memcpy(out_value,result.data(),length);out_value[length]='\\0';return;
    }
''' + old)
    s=s[:start]+part+s[end:];edits[path]=s
    path=root/'lua-api/lib/src/ScriptContext.cpp';s=path.read_text()
    s=replace_once(s,'#include "ScriptContext.hpp"','#include "ScriptContext.hpp"\n#include "uevr/FFWDiagnostics.hpp"')
    names={'on_pre_engine_tick':'pre','on_post_engine_tick':'post','on_xinput_get_state':'input',
        'on_xinput_set_state':'input','on_early_calculate_stereo_view_offset':'stereo',
        'on_pre_calculate_stereo_view_offset':'stereo','on_post_calculate_stereo_view_offset':'stereo'}
    for name,group in names.items():
        start=s.index('void ScriptContext::'+name+'(');end=s.index('{',start)+1
        insert='\n    ffw::ScopedCost ffw_cost{ffw::'+group+'};'
        if not s[end:].startswith(insert):s=s[:end]+insert+s[end:]
    edits[path]=s
    backup=root/'ffw-tests/diagnostics-20261026/source-before';backup.mkdir(parents=True,exist_ok=True)
    for path,text in edits.items():
        saved=backup/path.relative_to(root);saved.parent.mkdir(parents=True,exist_ok=True)
        if not saved.exists():shutil.copyfile(path,saved)
        path.write_text(text)
    target=root/'include/uevr/FFWDiagnostics.hpp'
    shutil.copyfile(ROOT/'native/FFWDiagnostics.hpp',target)
    print('Prepared optional haptic arbitration and read-only diagnostics; existing SDK ports retained.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path('/mnt/c/src/uevr_far_west_build'))
    prepare(parser.parse_args().source)
