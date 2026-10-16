"""Skip Slate hook installation in the isolated Far Far West UEVR build."""

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


def digest(data):
    return hashlib.sha256(data).hexdigest()


def patched(original):
    if digest(original) != ORIGINAL_SHA256:
        raise SystemExit('Backend version does not match this patch; nothing changed.')
    if original[OFFSET:OFFSET + len(PROLOGUE)] != PROLOGUE:
        raise SystemExit('Hook function prologue does not match; nothing changed.')
    return original[:OFFSET] + b'\xc3' + original[OFFSET + 1:]


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
    mode = parser.parse_args().mode
    current = TARGET.read_bytes()
    if mode == 'apply':
        if BACKUP.exists():
            original = BACKUP.read_bytes()
            candidate = patched(original)
            if current == candidate:
                print('Slate hook installation is already disabled.')
                return
            if current != original:
                raise SystemExit('Backend differs from the original and patched versions; nothing changed.')
        else:
            original = current
            candidate = patched(original)
            with BACKUP.open('xb') as stream:
                stream.write(original)
                stream.flush()
                os.fsync(stream.fileno())
        replace(candidate)
        assert TARGET.read_bytes() == candidate
        assert BACKUP.read_bytes() == original
        print('Disabled Slate hook installation in the isolated UEVR backend (one byte).')
        print('Backend SHA256:', digest(candidate))
    else:
        original = BACKUP.read_bytes()
        candidate = patched(original)
        if current not in (original, candidate):
            raise SystemExit('Backend has other changes; nothing changed.')
        if current != original:
            replace(original)
        assert digest(TARGET.read_bytes()) == ORIGINAL_SHA256
        print('Restored the original isolated UEVR backend; backup retained.')


if __name__ == '__main__':
    main()
