"""Bypass incompatible rendering hooks in the isolated Far Far West UEVR build."""

import argparse
import hashlib
import os
from pathlib import Path
import struct
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
# OpenVR::copy_left and copy_left_to_right, RVAs 0x104eb7 / 0x104f7b.
# Extreme Compatibility Mode uses full-width eye textures. Remove the two
# SHR EAX,1 instructions that otherwise limit copies to the left half.
COPY_WIDTH_OFFSETS = (0x1042B7, 0x10437B)
COPY_WIDTH_GUARD = bytes.fromhex('8b82300f0000d1e88944243c')
PROFILE_CONFIG = Path('/mnt/c/Users/brian/AppData/Roaming/UnrealVRMod/FarFarWest-Win64-Shipping/config.txt')
# PDB-verified camera entry, existing pose-update call, and unused bytes inside
# the disabled Slate installer. VR.m_runtime = 0x80; VRRuntime's render counter
# is at 0x28c. g_frame_count (uint32) lives at RVA 0xa9f438.
CAMERA_RVA, CAMERA_OFFSET = 0x14DF30, 0x14D330
CAMERA_ENTRY = bytes.fromhex('488bc448895818')
POSE_CALL_OFFSET = 0x14D6F8
POSE_CALL = bytes.fromhex('e83349f7ff')
STUB_RVA, STUB_OFFSET = 0x14ADC0, 0x14A1C0
STUB_CAPACITY = 128
# D3D12Component::on_frame's draw_2d_view lambda, RVA 0x10354f.
# In Extreme Compatibility Mode the backbuffer contains one full-width view.
# Keep its width instead of multiplying it by 0.5 for a double-wide texture.
SCREEN_WIDTH_OFFSET = 0x10294F
SCREEN_WIDTH_GUARD = bytes.fromhex('f30f5905cd257100')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def patched(original, view_offset_fallback=False, full_width_openvr=False):
    if digest(original) != ORIGINAL_SHA256:
        raise SystemExit('Backend version does not match this patch; nothing changed.')
    if original[OFFSET:OFFSET + len(PROLOGUE)] != PROLOGUE:
        raise SystemExit('Hook function prologue does not match; nothing changed.')
    candidate = original[:OFFSET] + b'\xc3' + original[OFFSET + 1:]
    if view_offset_fallback:
        if original[VIEW_OFFSET:VIEW_OFFSET + len(VIEW_PROLOGUE)] != VIEW_PROLOGUE:
            raise SystemExit('View-extension function prologue does not match; nothing changed.')
        candidate = candidate[:VIEW_OFFSET] + b'\x31\xc0\xc3' + candidate[VIEW_OFFSET + 3:]
    if full_width_openvr:
        for offset in COPY_WIDTH_OFFSETS:
            if original[offset - 6:offset + 6] != COPY_WIDTH_GUARD:
                raise SystemExit('OpenVR width-copy instructions do not match; nothing changed.')
            candidate = candidate[:offset] + b'\x90\x90' + candidate[offset + 2:]
    return candidate


def aligned_eyes(original):
    candidate = bytearray(patched(original, True, True))
    if original[CAMERA_OFFSET:CAMERA_OFFSET + len(CAMERA_ENTRY)] != CAMERA_ENTRY:
        raise SystemExit('Camera entry does not match; nothing changed.')
    if original[POSE_CALL_OFFSET:POSE_CALL_OFFSET + len(POSE_CALL)] != POSE_CALL:
        raise SystemExit('Existing pose-update call does not match; nothing changed.')

    def branch(opcode, source, target):
        return bytes([opcode]) + struct.pack('<i', target - source - 5)

    # Source-equivalent fallback: select the pending compositor frame's eye,
    # then refresh/enqueue poses on BOTH alternating eye frames. The old
    # fallback ran only for the left eye and never advanced g_frame_count.
    stub = bytearray.fromhex('85d27800')  # Ignore negative (non-stereo) view indices.
    stub += bytes.fromhex('4883ec68')  # Align RSP; reserve call shadow space.
    stub += bytes.fromhex('48894c242048895424284c89442430f30f7f5c2440')
    stub += branch(0xe8, STUB_RVA + len(stub), 0xB64C0)  # VR::get()
    stub += bytes.fromhex('488b08488b81800000008b808c020000')
    stub += b'\x89\x05' + struct.pack('<i', 0xA9F438 - (STUB_RVA + len(stub) + 6))
    stub += bytes.fromhex('31d24531c0')  # update_hmd_state(false, 0)
    stub += branch(0xe8, STUB_RVA + len(stub), 0xC2C30)
    stub += bytes.fromhex('f30f6f5c24404c8b442430488b542428488b4c24204883c468')
    replay_offset = len(stub)
    stub[3] = replay_offset - 4
    stub += CAMERA_ENTRY
    stub += branch(0xe9, STUB_RVA + len(stub), CAMERA_RVA + len(CAMERA_ENTRY))
    if len(stub) > STUB_CAPACITY or replay_offset - 4 > 127:
        raise SystemExit('Camera trampoline exceeds its reserved space; nothing changed.')
    candidate[STUB_OFFSET:STUB_OFFSET + len(stub)] = stub
    candidate[CAMERA_OFFSET:CAMERA_OFFSET + len(CAMERA_ENTRY)] = (
        branch(0xe9, CAMERA_RVA, STUB_RVA) + b'\x90\x90')
    # The entry trampoline handles pose updates; remove the old left-only call.
    candidate[POSE_CALL_OFFSET:POSE_CALL_OFFSET + len(POSE_CALL)] = b'\x90' * len(POSE_CALL)
    return bytes(candidate)


def menu_screen(original):
    candidate = bytearray(aligned_eyes(original))
    if original[SCREEN_WIDTH_OFFSET:SCREEN_WIDTH_OFFSET + 8] != SCREEN_WIDTH_GUARD:
        raise SystemExit('Screen-mode width instruction does not match; nothing changed.')
    candidate[SCREEN_WIDTH_OFFSET:SCREEN_WIDTH_OFFSET + 8] = b'\x90' * 8
    return bytes(candidate)


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
    parser.add_argument('--full-width-openvr', action='store_true',
                        help='Also copy full eye images; requires Extreme Compatibility Mode.')
    parser.add_argument('--align-fallback-eyes', action='store_true',
                        help='Also synchronize fallback eye selection with compositor frame counts.')
    parser.add_argument('--full-width-menu-screen', action='store_true',
                        help='Also copy the complete compatibility-mode view into the 2D screen.')
    args = parser.parse_args()
    mode = args.mode
    current = TARGET.read_bytes()
    original = BACKUP.read_bytes() if BACKUP.exists() else current
    slate_only = patched(original)
    fallback = patched(original, True)
    full_width = patched(original, True, True)
    aligned = aligned_eyes(original)
    screen = menu_screen(original)
    if current not in (original, slate_only, fallback, full_width, aligned, screen):
        raise SystemExit('Backend differs from the known original and patched versions; nothing changed.')
    if mode == 'apply':
        if (args.full_width_openvr or args.align_fallback_eyes or args.full_width_menu_screen
                or current in (full_width, aligned, screen)):
            flags = dict(line.split(b'=', 1) for line in PROFILE_CONFIG.read_bytes().splitlines() if b'=' in line)
            if flags.get(b'VR_ExtremeCompatibilityMode') != b'true':
                raise SystemExit('Full-width copies require Extreme Compatibility Mode; nothing changed.')
            if flags.get(b'Frontend_RequestedRuntime') != b'openvr_api.dll':
                raise SystemExit('Full-width patch is for the OpenVR profile; nothing changed.')
            if args.full_width_menu_screen or current == screen:
                candidate = screen
            else:
                candidate = aligned if args.align_fallback_eyes or current == aligned else full_width
        else:
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
        if candidate in (fallback, full_width, aligned, screen):
            print('View extensions bypassed; view-offset pose-update fallback enabled.')
        if candidate in (full_width, aligned, screen):
            print('OpenVR copies full-width images into both full-width eye textures.')
        if candidate in (aligned, screen):
            print('Camera eye selection follows compositor frames; poses update for both eyes.')
        if candidate == screen:
            print('2D screen mode copies the complete compatibility-mode view.')
        print('Backend SHA256:', digest(candidate))
    else:
        if current != original:
            replace(original)
        assert digest(TARGET.read_bytes()) == ORIGINAL_SHA256
        print('Restored the original isolated UEVR backend; backup retained.')


if __name__ == '__main__':
    main()
