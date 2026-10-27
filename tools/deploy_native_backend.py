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
MENU_POINTER_BUILD_SHA = '6aa7868a2dd745f5d6a8a34865d3866d5d95ffac924bed09e75d6eb3486f3691'
MENU_POINTER_PDB_SHA = 'efa1bad0f7d0a3c494c7abed53e712b7615b5c6e94858bc5cbac16a72e4006fd'
THEMED_CURSOR_BUILD_SHA = '98cb830717c2b0e942b456271dfee30987b25e90ad75164c5cd4119879804249'
THEMED_CURSOR_PDB_SHA = '18d13de0b607d46f6c5a9cc5fcab44de24cd23b11a6a93bd680c67b2e9fb05cb'
FIRST_UPDATE_BUILD_SHA = '0a60a4fc4c7781794207f61a253e4a313f34f885ffb98004cf81a50724a1ab5e'
FIRST_UPDATE_PDB_SHA = '75c7b1d88362cdd514fd6b3db89ea4e432c53cc029bbeeb1fbc52066611dfd81'
PRE_HOTFIX_BUILD_SHA = 'db624486a6f2baf528c41acab28f8d03d1e9b9f4d0e57cc0cde5ff370cc0b9ef'
PRE_HOTFIX_PDB_SHA = 'e1dfb86b5147eb29b6c6e174c9e532c34d6e8c9a1c44406fa6d55da2dfb28877'
PRE_DIAGNOSTICS_BUILD_SHA = 'a419a24829a0291fde5cb6e13c4e93a76a04bee243a0888a16f425f90727c82d'
PRE_DIAGNOSTICS_PDB_SHA = 'ff46aa1f0ee162cf3dfdab2dae2a51ec1d49624ac501d40883864dc776aa4d79'
BUILD_SHA = '67308d7e1d341f86cd55a7333d5f9c5e31dd5f323eafa8414801549581cffc55'
PDB_SHA = '920fd2f232b2c69cb9f49e660d13ddce5f15b37605ff1277f19a18ba75eb0045'
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
    pointer_dll = runtime/'UEVRBackend.dll.before-themed-cursor.bak'
    pointer_pdb = runtime/'UEVRBackend.pdb.before-themed-cursor.bak'
    themed_dll = runtime/'UEVRBackend.dll.before-fear-fear-west.bak'
    themed_pdb = runtime/'UEVRBackend.pdb.before-fear-fear-west.bak'
    update_dll = runtime/'UEVRBackend.dll.before-native-game-cursor.bak'
    update_pdb = runtime/'UEVRBackend.pdb.before-native-game-cursor.bak'
    hotfix_dll = runtime/'UEVRBackend.dll.before-0307-hotfix.bak'
    hotfix_pdb = runtime/'UEVRBackend.pdb.before-0307-hotfix.bak'
    diagnostics_dll = runtime/'UEVRBackend.dll.before-diagnostics.bak'
    diagnostics_pdb = runtime/'UEVRBackend.pdb.before-diagnostics.bak'
    current = digest(dll)
    if current not in (BASELINE_SHA, PREVIOUS_BUILD_SHA, MENU_POINTER_BUILD_SHA, THEMED_CURSOR_BUILD_SHA, FIRST_UPDATE_BUILD_SHA, PRE_HOTFIX_BUILD_SHA, PRE_DIAGNOSTICS_BUILD_SHA, BUILD_SHA):
        raise SystemExit('Runtime differs from the verified baseline/build; nothing changed.')
    if old_dll.exists() and digest(old_dll) != BASELINE_SHA:
        raise SystemExit('Native backend backup differs from the baseline; nothing changed.')
    if restore:
        if not old_dll.is_file() or not old_pdb.is_file():
            raise SystemExit('Native backend backups are missing; nothing changed.')
        if digest(pdb) not in (digest(old_pdb), PREVIOUS_PDB_SHA, MENU_POINTER_PDB_SHA, THEMED_CURSOR_PDB_SHA, FIRST_UPDATE_PDB_SHA, PRE_HOTFIX_PDB_SHA, PRE_DIAGNOSTICS_PDB_SHA, PDB_SHA):
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
    expected_symbols = {PREVIOUS_BUILD_SHA: PREVIOUS_PDB_SHA,
                        MENU_POINTER_BUILD_SHA: MENU_POINTER_PDB_SHA,
                        THEMED_CURSOR_BUILD_SHA: THEMED_CURSOR_PDB_SHA,
                        FIRST_UPDATE_BUILD_SHA: FIRST_UPDATE_PDB_SHA,
                        PRE_HOTFIX_BUILD_SHA: PRE_HOTFIX_PDB_SHA,
                        PRE_DIAGNOSTICS_BUILD_SHA: PRE_DIAGNOSTICS_PDB_SHA, BUILD_SHA: PDB_SHA}
    if current in expected_symbols and digest(pdb) != expected_symbols[current]:
        raise SystemExit('Runtime symbols do not match the installed build; nothing changed.')
    if old_pdb.exists() and digest(pdb) not in (digest(old_pdb), PREVIOUS_PDB_SHA, MENU_POINTER_PDB_SHA, THEMED_CURSOR_PDB_SHA, FIRST_UPDATE_PDB_SHA, PRE_HOTFIX_PDB_SHA, PRE_DIAGNOSTICS_PDB_SHA, PDB_SHA):
        raise SystemExit('Runtime symbols differ from the baseline/build; nothing changed.')
    if previous_dll.exists() and digest(previous_dll) != PREVIOUS_BUILD_SHA:
        raise SystemExit('Previous source-build backup changed; nothing changed.')
    if previous_pdb.exists() and digest(previous_pdb) != PREVIOUS_PDB_SHA:
        raise SystemExit('Previous source-build symbols changed; nothing changed.')
    if pointer_dll.exists() and digest(pointer_dll) != MENU_POINTER_BUILD_SHA:
        raise SystemExit('Controller-pointer backend backup changed; nothing changed.')
    if pointer_pdb.exists() and digest(pointer_pdb) != MENU_POINTER_PDB_SHA:
        raise SystemExit('Controller-pointer symbols backup changed; nothing changed.')
    if themed_dll.exists() and digest(themed_dll) != THEMED_CURSOR_BUILD_SHA:
        raise SystemExit('Pre-update themed-cursor backup changed; nothing changed.')
    if themed_pdb.exists() and digest(themed_pdb) != THEMED_CURSOR_PDB_SHA:
        raise SystemExit('Pre-update themed-cursor symbols backup changed; nothing changed.')
    if update_dll.exists() and digest(update_dll) != FIRST_UPDATE_BUILD_SHA:
        raise SystemExit('First 0.3.0.0 backend backup changed; nothing changed.')
    if update_pdb.exists() and digest(update_pdb) != FIRST_UPDATE_PDB_SHA:
        raise SystemExit('First 0.3.0.0 symbols backup changed; nothing changed.')
    if hotfix_dll.exists() and digest(hotfix_dll) != PRE_HOTFIX_BUILD_SHA:
        raise SystemExit('Pre-hotfix backend backup changed; nothing changed.')
    if hotfix_pdb.exists() and digest(hotfix_pdb) != PRE_HOTFIX_PDB_SHA:
        raise SystemExit('Pre-hotfix symbols backup changed; nothing changed.')
    if diagnostics_dll.exists() and digest(diagnostics_dll) != PRE_DIAGNOSTICS_BUILD_SHA:
        raise SystemExit('Pre-diagnostics backend backup changed; nothing changed.')
    if diagnostics_pdb.exists() and digest(diagnostics_pdb) != PRE_DIAGNOSTICS_PDB_SHA:
        raise SystemExit('Pre-diagnostics symbols backup changed; nothing changed.')
    if not old_dll.exists():
        shutil.copyfile(dll, old_dll)
    if not old_pdb.exists():
        shutil.copyfile(pdb, old_pdb)
    if current == PREVIOUS_BUILD_SHA:
        if not previous_dll.exists():
            shutil.copyfile(dll, previous_dll)
        if not previous_pdb.exists():
            shutil.copyfile(pdb, previous_pdb)
    if current == MENU_POINTER_BUILD_SHA:
        if not pointer_dll.exists():
            shutil.copyfile(dll, pointer_dll)
        if not pointer_pdb.exists():
            shutil.copyfile(pdb, pointer_pdb)
    if current == THEMED_CURSOR_BUILD_SHA:
        if not themed_dll.exists():
            shutil.copyfile(dll, themed_dll)
        if not themed_pdb.exists():
            shutil.copyfile(pdb, themed_pdb)
    if current == FIRST_UPDATE_BUILD_SHA:
        if not update_dll.exists():
            shutil.copyfile(dll, update_dll)
        if not update_pdb.exists():
            shutil.copyfile(pdb, update_pdb)
    if current == PRE_HOTFIX_BUILD_SHA:
        if not hotfix_dll.exists():
            shutil.copyfile(dll, hotfix_dll)
        if not hotfix_pdb.exists():
            shutil.copyfile(pdb, hotfix_pdb)
    if current == PRE_DIAGNOSTICS_BUILD_SHA:
        if not diagnostics_dll.exists(): shutil.copyfile(dll, diagnostics_dll)
        if not diagnostics_pdb.exists(): shutil.copyfile(pdb, diagnostics_pdb)
    rollback_pdb = (diagnostics_pdb if current == PRE_DIAGNOSTICS_BUILD_SHA else
                    hotfix_pdb if current == PRE_HOTFIX_BUILD_SHA else
                    update_pdb if current == FIRST_UPDATE_BUILD_SHA else
                    themed_pdb if current == THEMED_CURSOR_BUILD_SHA else
                    pointer_pdb if current == MENU_POINTER_BUILD_SHA else
                    previous_pdb if current == PREVIOUS_BUILD_SHA else old_pdb)
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
    print('UE5.8 SDK backend deployed with report haptic priority and read-only performance support; compatibility ports retained.')
    print('Backend SHA256:', BUILD_SHA)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('apply', 'restore'))
    args = parser.parse_args()
    deploy(restore=args.mode == 'restore')
