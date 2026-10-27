"""Compile the original haptic/measurement core and check guarded source preparation."""
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from prepare_diagnostics_backend import prepare

ROOT=Path(__file__).resolve().parents[1]
with TemporaryDirectory() as temp:
    root=Path(temp)
    source=root/'test.cpp'
    source.write_text(r'''
#include "FFWDiagnostics.hpp"
#include <cassert>
int main() {
 ffw::ReportHaptics cue;auto start=ffw::Clock::time_point{};
 auto at=[&](int ms){return start+std::chrono::milliseconds(ms);};
 float delay=0,duration=.1f,frequency=1,amplitude=5;
 assert(cue.route(0,delay,duration,frequency,amplitude,at(0)));
 cue.start(start);assert(cue.active(at(0)));
 for(int hand=0;hand<2;++hand) {
  assert(cue.route(hand,delay,duration,frequency,amplitude,at(0)) && amplitude==0);
  assert(!cue.route(hand,delay,duration,frequency,amplitude,at(50)));
  assert(cue.route(hand,delay,duration,frequency,amplitude,at(120)) && amplitude==5 && duration==.1f && frequency==1);
  assert(!cue.route(hand,delay,duration,frequency,amplitude,at(130)));
  assert(cue.route(hand,delay,duration,frequency,amplitude,at(220)) && amplitude==0);
  assert(cue.route(hand,delay,duration,frequency,amplitude,at(400)) && amplitude==5);
  assert(cue.route(hand,delay,duration,frequency,amplitude,at(500)) && amplitude==0);
 }
 assert(!cue.active(at(650)));
 amplitude=3;assert(cue.route(0,delay,duration,frequency,amplitude,at(650)) && amplitude==3);
 cue.start(at(1000));assert(cue.active(at(1001)));
 assert(cue.route(1,delay,duration,frequency,amplitude,at(1001)) && amplitude==0);
 {ffw::ScopedCost scope(ffw::pre);}
 assert(ffw::costs().group[ffw::pre].peak==0);
 ffw::costs().enabled=true;
 {ffw::ScopedCost scope(ffw::pre);for(volatile int i=0;i<1000;++i){}}
 assert(ffw::costs().group[ffw::pre].peak>0);
}
''')
    binary=root/'test'
    subprocess.run(['g++','-std=c++17','-pthread','-I',str(ROOT/'native'),str(source),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
    print('PASS native cue interrupts both hands, sends two pulses, blocks conflicting buzz and expires')
    print('PASS native callback timing stays dormant until requested')
    files={
        'src/mods/VR.cpp':'#include "VR.hpp"\nvoid input() {\n    update_dpad_gestures();\n}\nvoid haptic() {\n    if (get_runtime()->is_openvr()) {\n        vr::VRInput()->TriggerHapticVibrationAction();\n    }\n}\n',
        'src/mods/PluginLoader.cpp':'#include "VR.hpp"\n// Existing SDK ports must survive\n// TODO: Optimize this with a map\nvoid set_mod_value() {\n    auto& mods = g_framework->get_mods()->get_mods();\n}\nvoid get_mod_value() {\n    auto& mods = g_framework->get_mods()->get_mods();\n}\nvoid save_config() {}\n',
        'lua-api/lib/src/ScriptContext.cpp':'#include "ScriptContext.hpp"\n'+''.join('void ScriptContext::'+name+'() {}\n' for name in ['on_pre_engine_tick','on_post_engine_tick','on_xinput_get_state','on_xinput_set_state','on_early_calculate_stereo_view_offset','on_pre_calculate_stereo_view_offset','on_post_calculate_stereo_view_offset']),
    }
    for name,text in files.items():
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    (root/'include/uevr').mkdir(parents=True)
    prepare(root);first={name:(root/name).read_bytes() for name in files}
    prepare(root);assert all((root/name).read_bytes()==data for name,data in first.items())
    assert 'Existing SDK ports must survive' in (root/'src/mods/PluginLoader.cpp').read_text()
    assert (root/'ffw-tests/diagnostics-20261026/source-before/src/mods/PluginLoader.cpp').read_text()==files['src/mods/PluginLoader.cpp']
    print('PASS source preparation is idempotent and preserves existing ports and originals')
    p=root/'src/mods/VR.cpp';p.write_text('unsupported source');before=p.read_bytes()
    try:prepare(root)
    except ValueError:pass
    else:raise AssertionError('unverified source changed')
    assert p.read_bytes()==before
    print('PASS source mismatch fails before mutations')
