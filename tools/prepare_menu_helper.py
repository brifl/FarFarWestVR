"""Prepare the game log for UEVR's restricted Lua filesystem before launch."""

import os
from pathlib import Path, PureWindowsPath
import subprocess

from apply_render_baseline import apply


PROFILE = Path('/mnt/c/Users/brian/AppData/Roaming/UnrealVRMod/FarFarWest-Win64-Shipping')
GAME_LOG = Path('/mnt/c/Users/brian/AppData/Local/FarFarWest/Saved/Logs/FarFarWest.log')
LINK = PROFILE / 'data/FarFarWest.log'


def windows_path(path):
    if path.parts[:3] != ('/', 'mnt', 'c'):
        raise ValueError('Expected a path on the Windows C drive')
    return str(PureWindowsPath('C:/', *path.parts[3:]))


def prepare():
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
    apply(preset='menu-logging')
    print('Menu helper ready: profile/data/FarFarWest.log links to the game log.')


if __name__ == '__main__':
    prepare()
