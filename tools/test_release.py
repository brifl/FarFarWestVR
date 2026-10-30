"""Packaging checks against committed fixtures; no dependencies or runtime binaries needed."""
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import zipfile

from package_release import ROOT, build
import publish_release


class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)/'source'
        cls.root.mkdir()
        tracked = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z']).decode().strip('\0').split('\0')
        extra = ['release.json', 'installer/Install-FarFarWestVR.ps1', 'installer/Install-FarFarWestVR.cmd', 'docs/SETUP.md']
        for name in sorted(set(tracked + extra)):
            p = ROOT/name
            if p.is_file():
                target = cls.root/name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, target)
        for name in ['log.txt', 'crash.dmp', 'data/world_markers_dev.lua', 'data/ui-audit-999999.jsonl',
                     'data/ui_audit_command.txt', 'UEVRBackend.dll', 'secret.bak']:
            p = cls.root/name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b'MUST NOT SHIP')
        subprocess.run(['git', 'init', '-q', str(cls.root)], check=True)
        subprocess.run(['git', '-C', str(cls.root), 'add', '-f', '.'], check=True, capture_output=True)
        subprocess.run(['git', '-C', str(cls.root), '-c', 'user.name=Release Test', '-c', 'user.email=test@example.invalid',
                        'commit', '-qm', 'fixture'], check=True)
        (cls.root/'scripts/untracked-debug.lua').write_text('MUST NOT SHIP')
        cls.out = Path(cls.temp.name)/'output'
        with redirect_stdout(io.StringIO()):
            cls.assets, cls.manifest = build(cls.root, cls.out)
        cls.profile = zipfile.ZipFile(io.BytesIO(next(b for n, b in cls.assets.items() if n.endswith('-Profile.zip'))))
        cls.setup = zipfile.ZipFile(io.BytesIO(next(b for n, b in cls.assets.items() if n.endswith('-Setup.zip'))))

    @classmethod
    def tearDownClass(cls):
        cls.profile.close(); cls.setup.close(); cls.temp.cleanup()

    def test_profile_is_importable_with_no_outer_directory(self):
        names = set(self.profile.namelist())
        self.assertIn('config.txt', names)
        self.assertIn('scripts/controller_aim.lua', names)
        self.assertIn('plugins/joytokey.dll', names)
        self.assertIn('uobjecthook/1402486413757807057_mc_state.json', names)
        self.assertIn('scripts/libs/reticle_style.lua', names)
        self.assertEqual(self.profile.read('assets/aiming_reticle.png'), (self.root/'assets/aiming_reticle.png').read_bytes())

    def test_allowlist_scrubs_tracked_and_untracked_development_files(self):
        names = self.profile.namelist()
        forbidden = ['log.txt', 'crash.dmp', 'cache/', 'diagnostics/', 'experiments/', 'tools/', 'docs/',
                     'imgui.ini', 'UEVRBackend.dll', 'scripts/untracked-debug.lua', 'data/world_markers_dev.lua']
        for name in names:
            self.assertFalse(any(name == p or name.startswith(p) for p in forbidden), name)
            self.assertFalse(name.endswith(('.bak', '.pdb', '.jsonl')), name)
        self.assertNotIn('assets/quest3_controls_sprite_sheet.png', names)
        self.assertFalse(any(p.startswith('assets/controls_') for p in names))

    def test_public_capture_default_and_exact_aim_marker(self):
        tuning = self.profile.read('data/tuning.ini').decode()
        self.assertIn('auto_start = 0', tuning)
        self.assertIn('halo_reticle = 1', tuning)
        self.assertNotIn('robot1-x', tuning)
        self.assertIn('auto_start = 1', (self.root/'data/tuning.ini').read_text())
        self.assertEqual(self.profile.read('data/controller_aim_backend.txt'), b'ue5-camera-aim-pose-v1\n')

    def test_every_profile_file_has_a_verified_manifest_hash(self):
        manifest = json.loads(self.setup.read('manifest.json'))
        self.assertEqual(set(manifest['files']), set(self.profile.namelist()))
        for name, expected in manifest['files'].items():
            self.assertEqual(hashlib.sha256(self.profile.read(name)).hexdigest(), expected)
        self.assertEqual(manifest['profile_sha256'], hashlib.sha256(self.setup.read('payload/profile.zip')).hexdigest())
        self.assertFalse(manifest['runtime_included'])

    def test_setup_contains_offline_profile_installer_and_help(self):
        self.assertEqual(set(self.setup.namelist()), {'Install-FarFarWestVR.cmd', 'Install-FarFarWestVR.ps1',
                         'START-HERE.md', 'manifest.json', 'payload/profile.zip'})
        cmd = self.setup.read('Install-FarFarWestVR.cmd')
        self.assertIn(b'-ExecutionPolicy Bypass', cmd)
        self.assertNotIn(b'\n', cmd.replace(b'\r\n', b''))

    def test_reproducible_and_ignores_loose_runtime_configuration(self):
        self.assertTrue(all(e.create_system == 3 for e in self.profile.infolist()))
        original = (self.root/'config.txt').read_bytes()
        try:
            (self.root/'config.txt').write_bytes(b'PRIVATE LOCAL SETTINGS')
            with redirect_stdout(io.StringIO()):
                second, manifest = build(self.root, Path(self.temp.name)/'second')
            self.assertEqual(self.assets, second)
            self.assertEqual(self.manifest, manifest)
        finally:
            (self.root/'config.txt').write_bytes(original)

    def test_release_checksums_match_both_downloads(self):
        for line in (self.out/'SHA256SUMS.txt').read_text().splitlines():
            digest, name = line.split('  ')
            self.assertEqual(digest, hashlib.sha256((self.out/name).read_bytes()).hexdigest())

    def test_missing_committed_lua_dependency_stops_packaging(self):
        original=self.manifest['source_commit']
        try:
            subprocess.run(['git','-C',str(self.root),'rm','--cached','-q','scripts/libs/reticle_projection.lua'],check=True)
            subprocess.run(['git','-C',str(self.root),'-c','user.name=Release Test','-c','user.email=test@example.invalid',
                            'commit','-qm','missing runtime dependency'],check=True)
            with self.assertRaisesRegex(ValueError,'missing packaged module'):
                build(self.root,Path(self.temp.name)/'broken')
        finally:
            subprocess.run(['git','-C',str(self.root),'reset','--mixed','--quiet',original],check=True)

    def test_missing_halo_asset_stops_packaging(self):
        original=self.manifest['source_commit']
        try:
            subprocess.run(['git','-C',str(self.root),'rm','--cached','-q','assets/aiming_reticle.png'],check=True)
            subprocess.run(['git','-C',str(self.root),'-c','user.name=Release Test','-c','user.email=test@example.invalid',
                            'commit','-qm','missing halo asset'],check=True)
            with self.assertRaisesRegex(ValueError,'Halo reticle asset is missing'):
                build(self.root,Path(self.temp.name)/'broken-halo')
        finally:
            subprocess.run(['git','-C',str(self.root),'reset','--mixed','--quiet',original],check=True)

    def test_publisher_validates_before_requesting_credentials(self):
        with patch.dict('os.environ', {}, clear=True), patch('urllib.request.urlopen') as request:
            with self.assertRaises(SystemExit):
                publish_release.publish(self.out, 'v' + self.manifest['version'])
            request.assert_not_called()
        with self.assertRaises(ValueError):
            publish_release.validate(self.out, 'v99.99.99-beta.1')

    def test_publisher_rejects_corrupted_downloads_before_network_writes(self):
        bad = Path(self.temp.name)/'bad'
        shutil.copytree(self.out, bad)
        name = next(iter(self.assets))
        (bad/name).write_bytes(b'CORRUPT')
        with patch('urllib.request.urlopen') as request:
            with self.assertRaises(ValueError):
                publish_release.publish(bad, 'v' + self.manifest['version'])
            request.assert_not_called()

    def publisher_run(self, wrong_size=False):
        calls, uploaded = [], []
        def response(request, **kwargs):
            method, url = request.get_method(), request.full_url
            calls.append((method, url, request.data))
            if '/releases/tags/' in url:
                raise urllib.error.HTTPError(url, 404, 'missing', {}, None)
            if method == 'POST' and url.endswith('/releases'):
                value = {'id': 7, 'draft': True, 'assets': [],
                         'upload_url': 'https://uploads.github.com/repos/brifl/FarFarWestVR/releases/7/assets{?name,label}'}
            elif method == 'POST' and 'uploads.github.com' in url:
                from urllib.parse import parse_qs, urlparse
                name = parse_qs(urlparse(url).query)['name'][0]
                value = {'name': name, 'size': len(request.data)}
                uploaded.append(value)
            elif method == 'GET':
                if wrong_size:
                    uploaded[0]['size'] -= 1
                value = {'assets': uploaded}
            else:
                self.assertEqual(method, 'PATCH')
                self.assertEqual(len(uploaded), 3)
                value = {'html_url': 'https://github.com/brifl/FarFarWestVR/releases/tag/test'}
            return io.BytesIO(json.dumps(value).encode())
        with patch.dict('os.environ', {'GITHUB_TOKEN': 'test-only', 'GITHUB_REPOSITORY': 'brifl/FarFarWestVR'}), \
             patch('urllib.request.urlopen', side_effect=response), redirect_stdout(io.StringIO()):
            if wrong_size:
                with self.assertRaises(RuntimeError):
                    publish_release.publish(self.out, 'v' + self.manifest['version'])
            else:
                publish_release.publish(self.out, 'v' + self.manifest['version'])
        return calls

    def test_publisher_uploads_all_assets_before_making_the_draft_public(self):
        calls = self.publisher_run()
        self.assertEqual(calls[-1][0], 'PATCH')
        self.assertFalse(json.loads(calls[-1][2])['draft'])
        self.assertTrue(json.loads(calls[-1][2])['prerelease'])

    def test_failed_upload_verification_leaves_release_a_draft(self):
        self.assertFalse(any(method == 'PATCH' for method, _, _ in self.publisher_run(wrong_size=True)))


if __name__ == '__main__':
    unittest.main(verbosity=2)
