"""Deploy the verified UE5.8 build to the isolated Far Far West runtime."""

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


RUNTIME = Path('/mnt/c/Manual Installs/uevr_far_west')
BUILD = Path('/mnt/c/src/uevr_far_west_build/build/bin/uevr')
BASELINE_SHA = '3d2c8647dc10409a8d3d014c248f69f10f60895aede9c2d1fbee442d557c7527'
PREVIOUS_BUILD_SHA = '91a287bc456dd84c6f497030b65bb83af6977efc4f1ed8249b1d09c9905795d8'
PREVIOUS_PDB_SHA = 'f5a06b25d9613843449bddf14846b9f8474040eee48ea6b9614e1050219c5b2b'
BUILD_SHA = '6aa7868a2dd745f5d6a8a34865d3866d5d95ffac924bed09e75d6eb3486f3691'
PDB_SHA = 'efa1bad0f7d0a3c494c7abed53e712b7615b5c6e94858bc5cbac16a72e4006fd'
POWERSHELL = '/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'


def digest(path):
    with path.open('rb') as stream:
        h = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
        return h.hexdigest()


def atomic_copy(source, target):
    fd, name = tempfile.mkstemp(prefix='.ffw-native-', dir=target.parent)
    os.close(fd)
    try:
        shutil.copyfile(source, name)
        os.replace(name, target)
    finally:
        Path(name).unlink(missing_ok=True)


def require_closed():
    result = subprocess.run(
        [POWERSHELL, '-NoProfile', '-NonInteractive', '-Command',
         'if (Get-Process -Name FarFarWest-Win64-Shipping -ErrorAction SilentlyContinue) { exit 7 }; exit 0'],
        stdin=subprocess.DEVNULL, check=False,
    )
    if result.returncode:
        raise SystemExit('Game is running or the process check failed; nothing changed.')


def deploy(restore=False, runtime=RUNTIME, build=BUILD):
    require_closed()
    dll, pdb = runtime/'UEVRBackend.dll', runtime/'UEVRBackend.pdb'
    old_dll = runtime/'UEVRBackend.dll.before-ue58-sdk.bak'
    old_pdb = runtime/'UEVRBackend.pdb.before-ue58-sdk.bak'
    previous_dll = runtime/'UEVRBackend.dll.before-menu-pointer.bak'
    previous_pdb = runtime/'UEVRBackend.pdb.before-menu-pointer.bak'
    current = digest(dll)
    if current not in (BASELINE_SHA, PREVIOUS_BUILD_SHA, BUILD_SHA):
        raise SystemExit('Runtime differs from the verified baseline/build; nothing changed.')
    if old_dll.exists() and digest(old_dll) != BASELINE_SHA:
        raise SystemExit('Native backend backup differs from the baseline; nothing changed.')
    if restore:
        if not old_dll.is_file() or not old_pdb.is_file():
            raise SystemExit('Native backend backups are missing; nothing changed.')
        if digest(pdb) not in (digest(old_pdb), PREVIOUS_PDB_SHA, PDB_SHA):
            raise SystemExit('Runtime symbols changed; nothing changed.')
        if current != BASELINE_SHA:
            atomic_copy(old_dll, dll)
        if digest(pdb) != digest(old_pdb):
            atomic_copy(old_pdb, pdb)
        print('Previous controller-aim backend and symbols restored.')
        return

    source_dll, source_pdb = build/dll.name, build/pdb.name
    if digest(source_dll) != BUILD_SHA or digest(source_pdb) != PDB_SHA:
        raise SystemExit('Build artifacts differ from the verified build; nothing changed.')
    if b'ffw-ue58-sdk-v1' not in source_dll.read_bytes():
        raise SystemExit('Custom build identity is absent; nothing changed.')
    if current != BASELINE_SHA and (not old_dll.exists() or not old_pdb.exists()):
        raise SystemExit('The installed build has no complete baseline backup; nothing changed.')
    expected_symbols = {PREVIOUS_BUILD_SHA: PREVIOUS_PDB_SHA, BUILD_SHA: PDB_SHA}
    if current in expected_symbols and digest(pdb) != expected_symbols[current]:
        raise SystemExit('Runtime symbols do not match the installed build; nothing changed.')
    if old_pdb.exists() and digest(pdb) not in (digest(old_pdb), PREVIOUS_PDB_SHA, PDB_SHA):
        raise SystemExit('Runtime symbols differ from the baseline/build; nothing changed.')
    if previous_dll.exists() and digest(previous_dll) != PREVIOUS_BUILD_SHA:
        raise SystemExit('Previous source-build backup changed; nothing changed.')
    if previous_pdb.exists() and digest(previous_pdb) != PREVIOUS_PDB_SHA:
        raise SystemExit('Previous source-build symbols changed; nothing changed.')
    if not old_dll.exists():
        shutil.copyfile(dll, old_dll)
    if not old_pdb.exists():
        shutil.copyfile(pdb, old_pdb)
    if current == PREVIOUS_BUILD_SHA:
        if not previous_dll.exists():
            shutil.copyfile(dll, previous_dll)
        if not previous_pdb.exists():
            shutil.copyfile(pdb, previous_pdb)
    rollback_pdb = previous_pdb if current == PREVIOUS_BUILD_SHA else old_pdb
    try:
        if digest(pdb) != PDB_SHA:
            atomic_copy(source_pdb, pdb)
        if current != BUILD_SHA:
            atomic_copy(source_dll, dll)
    except OSError:
        if current != BUILD_SHA and digest(dll) == current:
            atomic_copy(rollback_pdb, pdb)
        raise
    assert digest(dll) == BUILD_SHA and digest(pdb) == PDB_SHA
    print('UE5.8 SDK backend deployed with controller menu pointing; compatibility ports retained.')
    print('Backend SHA256:', BUILD_SHA)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('apply', 'restore'))
    args = parser.parse_args()
    deploy(restore=args.mode == 'restore')
