"""Enable the isolated backend's UE5 camera/aim-pose bridge without a build."""

import argparse
from pathlib import Path

from disable_slate_hook import BACKUP, TARGET, digest, persistent_menu_screen, replace


PROFILE = Path('/mnt/c/Users/brian/AppData/Roaming/UnrealVRMod/FarFarWest-Win64-Shipping')
MARKER = PROFILE / 'data/controller_aim_backend.txt'
MARKER_TEXT = 'ue5-camera-aim-pose-v1\n'
AIM_BACKUP = TARGET.with_name('UEVRBackend.dll.before-controller-aim.bak')
# PDB: lua::utility::is_ue5, RVA 0x5e3b30. Its UObject-based size lookup
# returns false when GUObjectArray discovery fails, casting UE5 doubles as floats.
PRECISION_OFFSET = 0x5E2F30
PRECISION_GUARD = bytes.fromhex('4883ec288b0d06ab4d0065488b042558000000baac0d0000488b04c88b040239')
# PDB: uevr::vr::get_pose, RVA 0x580ee. The compiler shares a get_transform
# call for position and rotation. R9B=0 selects the runtime's aim pose instead
# of grip. HMD poses are identical in either mode. No game SDK objects are used.
POSE_OFFSET = 0x574EE
POSE_GUARD = bytes.fromhex('41b101488d55e7448bc3488b08e830ef0500')


def patched(original):
    candidate = bytearray(persistent_menu_screen(original))
    for offset, guard in ((PRECISION_OFFSET, PRECISION_GUARD), (POSE_OFFSET, POSE_GUARD)):
        if original[offset:offset + len(guard)] != guard:
            raise SystemExit('Controller-aim instructions do not match; nothing changed.')
    candidate[PRECISION_OFFSET:PRECISION_OFFSET + 3] = b'\xb0\x01\xc3'  # bool true
    candidate[POSE_OFFSET + 2] = 0  # get_transform(index, grip=false)
    return bytes(candidate)


def apply(restore=False):
    original = BACKUP.read_bytes()
    baseline = persistent_menu_screen(original)
    candidate = patched(original)
    current = TARGET.read_bytes()
    if current not in (baseline, candidate):
        raise SystemExit('Backend differs from the validated menu baseline; nothing changed.')
    if AIM_BACKUP.exists() and AIM_BACKUP.read_bytes() != baseline:
        raise SystemExit('Controller-aim backup differs from the baseline; nothing changed.')
    if MARKER.exists() and MARKER.read_text() != MARKER_TEXT:
        raise SystemExit('Controller-aim marker is already in use; nothing changed.')
    if restore:
        if current != baseline:
            replace(baseline)
        MARKER.unlink(missing_ok=True)
        print('Controller bridge disabled; validated menu backend restored.')
    else:
        if not AIM_BACKUP.exists():
            AIM_BACKUP.write_bytes(baseline)
        if current != candidate:
            replace(candidate)
        assert TARGET.read_bytes() == candidate
        MARKER.parent.mkdir(exist_ok=True)
        MARKER.write_text(MARKER_TEXT)
        print('UE5 double camera values and controller aim poses enabled for Lua.')
    print('Backend SHA256:', digest(TARGET.read_bytes()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('apply', 'restore'))
    args = parser.parse_args()
    apply(restore=args.mode == 'restore')
