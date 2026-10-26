#!/usr/bin/env python3
"""Build scrubbed, reproducible profile and Windows installer ZIPs from a Git commit."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOP_LEVEL = {
    'config.txt', 'cameras.txt', 'cvars_data.txt', 'cvars_standard.txt',
    'actions.json', 'binding_rift.json', 'binding_vive.json',
    'bindings_knuckles.json', 'bindings_oculus_touch.json', 'bindings_vive_controller.json',
}
PLUGINS = {'joytokey.dll', 'joytokey.txt', 'remapcontrols.dll', 'remapcontrols.txt'}
ASSETS = {'assets/menu_cursor.png', 'assets/control_hints/left_grip.png',
          'assets/control_hints/right_grip.png', 'assets/control_hints/both_grips.png'}


def selected(path):
    p = PurePosixPath(path)
    return (path in TOP_LEVEL or path in ASSETS
            or (len(p.parts) >= 2 and p.parts[0] == 'scripts' and p.suffix == '.lua')
            or (len(p.parts) == 2 and p.parts[0] == 'plugins' and p.name in PLUGINS)
            or (len(p.parts) == 2 and p.parts[0] == 'uobjecthook' and p.suffix == '.json')
            or path == 'data/tuning.ini')


def archive(files):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, content in sorted(files.items()):
            p = PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or '\\' in name:
                raise ValueError(f'Unsafe archive path: {name}')
            entry = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            z.writestr(entry, content, compresslevel=9)
    return out.getvalue()


def sha(content):
    return hashlib.sha256(content).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def build(root, output, revision='HEAD'):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args])
    commit = git('rev-parse', '--verify', revision + '^{commit}').decode().strip()
    paths = git('ls-tree', '-r', '--name-only', '-z', commit).decode().strip('\0').split('\0')
    def read(path):
        return git('show', commit + ':' + path)
    release = json.loads(read('release.json'))
    version = release['version']
    if not re.fullmatch(r'\d+\.\d+\.\d+-beta\.\d+', version):
        raise ValueError('Expected a beta version such as 0.1.0-beta.1')
    if release.get('runtime_included') is not False:
        raise ValueError('This packager publishes profile/installer only; no UEVR runtime redistribution.')
    files = {p: read(p) for p in paths if selected(p)}
    for path,content in files.items():
        if not path.endswith('.lua'): continue
        for dependency in re.findall(rb'\brequire\s*(?:\(\s*|,\s*)?[\'"](libs/[^\'"]+)[\'"]',content):
            expected='scripts/'+dependency.decode()+'.lua'
            if expected not in files: raise ValueError(f'{path} requires missing packaged module {expected}')
    missing = TOP_LEVEL - files.keys()
    if missing or 'data/tuning.ini' not in files or 'scripts/controller_aim.lua' not in files:
        raise ValueError(f'Incomplete profile: {sorted(missing)}')
    tuning = files['data/tuning.ini'].decode('utf-8-sig').replace('\r\n', '\n')
    tuning = tuning.replace('; Edit this file in the installed profile on robot1-x, or edit here and deploy.',
                            '; Edit this file in your installed profile; save numeric changes to apply them.')
    tuning, count = re.subn(r'(?m)^auto_start[ \t]*=[ \t]*[01][ \t]*$', 'auto_start = 0', tuning)
    if count != 1:
        raise ValueError('Expected exactly one development audit auto_start default')
    files['data/tuning.ini'] = tuning.encode()
    files['data/controller_aim_backend.txt'] = b'ue5-camera-aim-pose-v1\n'
    files['data/release.json'] = json_bytes(dict(release, source_commit=commit))
    files['PROFILE-INFO.txt'] = (
        f"Far Far West VR {version} (beta)\n"
        "Requires the matching custom UEVR runtime, which is not included.\n"
        "Installation and help: https://github.com/brifl/FarFarWestVR\n"
        "Issues: https://github.com/brifl/FarFarWestVR/issues/new/choose\n"
        "Built on praydog's UEVR: https://github.com/praydog/UEVR\n"
        "Original profile by HeadsetVR:\n"
        "https://www.patreon.com/HeadsetVR/posts/is-far-far-west-163314637\n"
    ).encode()
    profile = archive(files)
    manifest = dict(release, source_commit=commit, profile_sha256=sha(profile),
                    files={p: sha(b) for p, b in sorted(files.items())})
    setup = archive({
        'Install-FarFarWestVR.cmd': read('installer/Install-FarFarWestVR.cmd').replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'),
        'Install-FarFarWestVR.ps1': read('installer/Install-FarFarWestVR.ps1'),
        'START-HERE.md': read('docs/SETUP.md'),
        'manifest.json': json_bytes(manifest),
        'payload/profile.zip': profile,
    })
    output.mkdir(parents=True, exist_ok=True)
    prefix = f'FarFarWestVR-{version}'
    assets = {f'{prefix}-Profile.zip': profile, f'{prefix}-Setup.zip': setup}
    for name, content in assets.items():
        (output/name).write_bytes(content)
    (output/'SHA256SUMS.txt').write_text(''.join(f'{sha(b)}  {p}\n' for p, b in sorted(assets.items())), encoding='utf-8', newline='\n')
    print(f'{version}: {len(files)} profile files; source {commit[:12]}; runtime NOT included.')
    for name, content in assets.items():
        print(f'{name}: {len(content):,} bytes; SHA256 {sha(content)}')
    return assets, manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'dist')
    parser.add_argument('--revision', default='HEAD', help='Committed Git revision, never loose local files')
    args = parser.parse_args()
    build(ROOT, args.output, args.revision)
