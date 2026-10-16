"""Bypass incompatible rendering hooks in the isolated Far Far West UEVR build."""

import argparse
import hashlib
import os
from pathlib import Path
import tempfile


TARGET = Path('/mnt/c/Manual Installs/uevr_far_west/UEVRBackend.dll')
BACKUP = TARGET.with_name('UEVRBackend.dll.before-slate-hook-disable.bak')
ORIGINAL_SHA256 = '1a34cf65e4c12002ec967ed167ddda4e1cc7ae1da82157d0e279597beddeed75'
# Installed PDB: FFakeStereoRenderingHook::attempt_hook_slate_thread,
# RVA 0x14ad80. Return before its prologue; leave the native Slate renderer alone.
OFFSET = 0x14A180
PROLOGUE = bytes.fromhex('48895c24105556574154415541564157488dac2430ffffff')
# FFakeStereoRenderingHook::setup_view_extensions, RVA 0x161240.
# Returning false leaves m_has_view_extension_hook unset, enabling the
# update_hmd_state fallback in calculate_stereo_view_offset.
VIEW_OFFSET = 0x160640
VIEW_PROLOGUE = bytes.fromhex('4053565741544155415641574881ec000e00004c8bf1e895')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def patched(original, view_offset_fallback=False):
    if digest(original) != ORIGINAL_SHA256:
        raise SystemExit('Backend version does not match this patch; nothing changed.')
    if original[OFFSET:OFFSET + len(PROLOGUE)] != PROLOGUE:
        raise SystemExit('Hook function prologue does not match; nothing changed.')
    candidate = original[:OFFSET] + b'\xc3' + original[OFFSET + 1:]
    if view_offset_fallback:
        if original[VIEW_OFFSET:VIEW_OFFSET + len(VIEW_PROLOGUE)] != VIEW_PROLOGUE:
            raise SystemExit('View-extension function prologue does not match; nothing changed.')
        candidate = candidate[:VIEW_OFFSET] + b'\x31\xc0\xc3' + candidate[VIEW_OFFSET + 3:]
    return candidate


def replace(data):
    fd, name = tempfile.mkstemp(prefix='.uevr-slate-', suffix='.tmp', dir=TARGET.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, TARGET)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('apply', 'restore'))
    parser.add_argument('--view-offset-fallback', action='store_true',
                        help='Also skip view extensions to use view-offset pose updates.')
    args = parser.parse_args()
    mode = args.mode
    current = TARGET.read_bytes()
    original = BACKUP.read_bytes() if BACKUP.exists() else current
    slate_only = patched(original)
    fallback = patched(original, True)
    if current not in (original, slate_only, fallback):
        raise SystemExit('Backend differs from the known original and patched versions; nothing changed.')
    if mode == 'apply':
        candidate = fallback if args.view_offset_fallback or current == fallback else slate_only
        if current == candidate:
            print('Requested rendering-hook bypass is already applied.')
            return
        if not BACKUP.exists():
            with BACKUP.open('xb') as stream:
                stream.write(original)
                stream.flush()
                os.fsync(stream.fileno())
        replace(candidate)
        assert TARGET.read_bytes() == candidate
        assert BACKUP.read_bytes() == original
        print('Slate hook installation disabled in the isolated UEVR backend.')
        if candidate == fallback:
            print('View extensions bypassed; view-offset pose-update fallback enabled.')
        print('Backend SHA256:', digest(candidate))
    else:
        if current != original:
            replace(original)
        assert digest(TARGET.read_bytes()) == ORIGINAL_SHA256
        print('Restored the original isolated UEVR backend; backup retained.')


if __name__ == '__main__':
    main()
