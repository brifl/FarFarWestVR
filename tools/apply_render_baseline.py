"""Apply or restore the non-temporal rendering test through the game's Engine.ini."""

import argparse
import os
from pathlib import Path
import tempfile


TARGET = Path('/mnt/c/Users/brian/AppData/Local/FarFarWest/Saved/Config/Windows/Engine.ini')
FRAGMENT = Path(__file__).resolve().parents[1] / 'game_settings/temporal_baseline.ini'


def apply(target=TARGET, restore=False):
    backup = target.with_name(target.name + '.before-ffw-temporal.bak')
    current = target.read_bytes() if target.exists() else b''
    if restore and not backup.exists():
        raise SystemExit('No rendering-test backup exists; nothing changed.')
    original = backup.read_bytes() if backup.exists() else current
    if original.startswith((b'\xff\xfe', b'\xfe\xff')):
        raise SystemExit('Engine.ini uses UTF-16; nothing changed.')
    fragment = FRAGMENT.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    candidate = original + (b'\r\n' if original else b'') + fragment
    if current not in (original, candidate):
        raise SystemExit('Engine.ini changed since the backup; nothing changed.')
    desired = original if restore else candidate
    if current != desired:
        if not backup.exists():
            with backup.open('xb') as stream:
                stream.write(original)
        fd, name = tempfile.mkstemp(prefix='.ffw-render-', dir=target.parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(desired)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, target)
        finally:
            if os.path.exists(name):
                os.unlink(name)
    assert target.read_bytes() == desired
    print('Rendering test restored.' if restore else 'Non-temporal rendering test applied for the next launch.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('apply', 'restore'))
    args = parser.parse_args()
    apply(restore=args.mode == 'restore')
