"""Replace the retained backend's exact-build gate with read-only ABI discovery.

Does not reset the SDK or publish private sources. All insertions are guarded.
"""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
START = '        // Only validated Far Far West executable builds may use this compact layout.'
END = '        s_is_chunked = true;'
INSERT = '''        // FFW bounded compatibility discovery: validate tables and core ABI once.
        const auto compatibility = ffw::compat::discover_current();
        if (!compatibility) {
            SPDLOG_ERROR("[FFW compatibility] SDK access disabled: {} (timestamp={}, image={})",
                compatibility.reason, compatibility.timestamp, compatibility.image_size);
            return nullptr;
        }
        const auto address = compatibility.array;
        const auto count = compatibility.count;
        SPDLOG_INFO("[FFW compatibility] Validated object/name tables and core reflection ABI (timestamp={}, image={}, array=0x{:x}, pool=0x{:x}, objects={})",
            compatibility.timestamp, compatibility.image_size,
            address - (uintptr_t)GetModuleHandleW(nullptr),
            compatibility.pool - (uintptr_t)GetModuleHandleW(nullptr), count);
'''


def prepare(root):
    path = root/'dependencies/submodules/UESDK/src/sdk/UObjectArray.cpp'
    text = path.read_text()
    include = '#include "FFWCompatibility.hpp"'
    if INSERT not in text:
        if text.count(START) != 1 or text.count(END) != 1:
            raise ValueError('SDK source differs from the verified compact-array port; nothing changed.')
        start, end = text.index(START), text.index(END)
        if end <= start or '715567327' not in text[start:end] or 'IsBadReadPtr' not in text[start:end]:
            raise ValueError('Expected previous allowlist/validation is absent; nothing changed.')
        text = text[:start]+INSERT+text[end:]
    if include not in text:
        anchor = '#include "UObjectArray.hpp"'
        if text.count(anchor) != 1:
            raise ValueError('Expected SDK include is absent; nothing changed.')
        text = text.replace(anchor, anchor+'\n'+include, 1)
    target = path.parent/'FFWCompatibility.hpp'
    backup = root/'ffw-tests/compatibility-20261030/source-before'
    backup.mkdir(parents=True, exist_ok=True)
    saved = backup/path.name
    if not saved.exists():
        shutil.copyfile(path, saved)
    shutil.copyfile(ROOT/'native/FFWCompatibility.hpp', target)
    path.write_text(text)
    print('Prepared bounded object/name discovery with core ABI checks; other SDK ports preserved.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('/mnt/c/src/uevr_far_west_build'))
    prepare(parser.parse_args().source)
