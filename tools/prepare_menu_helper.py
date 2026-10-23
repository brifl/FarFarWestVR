"""Prepare the game log for UEVR's restricted Lua filesystem before launch."""

import argparse
import os
from pathlib import Path, PureWindowsPath
import subprocess

from apply_render_baseline import PRESETS, apply


PROFILE = Path('/mnt/c/Users/brian/AppData/Roaming/UnrealVRMod/FarFarWest-Win64-Shipping')
GAME_LOG = Path('/mnt/c/Users/brian/AppData/Local/FarFarWest/Saved/Logs/FarFarWest.log')
LINK = PROFILE / 'data/FarFarWest.log'
# This is a source layer in the game's config hierarchy. Saved/Config/Windows/
# Engine.ini is generated output and this game deletes our additions to it.
USER_CONFIG = Path('/mnt/c/Program Files (x86)/Steam/steamapps/common/FarFarWest/FarFarWest/Config/UserEngine.ini')


def windows_path(path):
    if path.parts[:3] != ('/', 'mnt', 'c'):
        raise ValueError('Expected a path on the Windows C drive')
    return str(PureWindowsPath('C:/', *path.parts[3:]))


def prepare(preset='menu-logging', restore=False):
    if not GAME_LOG.is_file():
        raise SystemExit('The known Far Far West log is missing; nothing changed.')
    if os.path.lexists(LINK):
        if not LINK.is_symlink() or LINK.resolve() != GAME_LOG.resolve():
            raise SystemExit('The profile log path is already in use; nothing changed.')
    else:
        LINK.parent.mkdir(exist_ok=True)
        # A WSL-created symlink cannot be read reliably by Windows Lua. Create
        # a Windows file link so the current log remains reachable after rotation.
        subprocess.run(
            ['/mnt/c/Windows/System32/cmd.exe', '/d', '/c', 'mklink',
             windows_path(LINK), windows_path(GAME_LOG)],
            stdin=subprocess.DEVNULL, check=True,
        )
    with LINK.open('rb') as stream:
        stream.read(1)
    USER_CONFIG.parent.mkdir(exist_ok=True)
    apply(target=USER_CONFIG, preset=preset, restore=restore)
    print('Game configuration installed:', USER_CONFIG)
    print('Menu helper ready: profile/data/FarFarWest.log links to the game log.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--material-test', action='store_true',
                        help='Disable custom post-process materials and log INI CVar application.')
    selection.add_argument('--preset', choices=tuple(PRESETS), default='menu-logging',
                           help='Apply a preset to the persistent UserEngine.ini layer.')
    parser.add_argument('--restore', action='store_true',
                        help='Restore the selected preset backup, preserving the prior baseline.')
    args = parser.parse_args()
    prepare(preset='material-probe' if args.material_test else args.preset, restore=args.restore)
