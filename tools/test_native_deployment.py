"""Verify backend/symbol pairing when upgrading the pre-update runtime."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import deploy_native_backend as deployment


class NativeDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.runtime, self.build = root/'runtime', root/'build'
        self.runtime.mkdir()
        self.build.mkdir()
        self.old_dll, self.old_pdb = b'previous-themed-backend', b'previous-themed-symbols'
        self.new_dll, self.new_pdb = b'new-ffw-ue58-sdk-v1-backend', b'new-symbols'
        self.update_dll, self.update_pdb = b'first-update-backend', b'first-update-symbols'
        self.pre_hotfix_dll, self.pre_hotfix_pdb = b'pre-hotfix-backend', b'pre-hotfix-symbols'
        sha = lambda data: hashlib.sha256(data).hexdigest()
        patched = patch.multiple(deployment, require_closed=lambda: None,
                                 BASELINE_SHA=sha(b'baseline'),
                                 THEMED_CURSOR_BUILD_SHA=sha(self.old_dll),
                                 THEMED_CURSOR_PDB_SHA=sha(self.old_pdb),
                                 FIRST_UPDATE_BUILD_SHA=sha(self.update_dll),
                                 FIRST_UPDATE_PDB_SHA=sha(self.update_pdb),
                                 PRE_HOTFIX_BUILD_SHA=sha(self.pre_hotfix_dll),
                                 PRE_HOTFIX_PDB_SHA=sha(self.pre_hotfix_pdb),
                                 BUILD_SHA=sha(self.new_dll), PDB_SHA=sha(self.new_pdb))
        patched.start()
        self.addCleanup(patched.stop)
        for name, data in (('UEVRBackend.dll', self.old_dll), ('UEVRBackend.pdb', self.old_pdb),
                           ('UEVRBackend.dll.before-ue58-sdk.bak', b'baseline'),
                           ('UEVRBackend.pdb.before-ue58-sdk.bak', b'baseline-symbols')):
            (self.runtime/name).write_bytes(data)
        (self.build/'UEVRBackend.dll').write_bytes(self.new_dll)
        (self.build/'UEVRBackend.pdb').write_bytes(self.new_pdb)

    def deploy(self):
        deployment.deploy(runtime=self.runtime, build=self.build)

    def test_upgrade_preserves_themed_pair_and_repeated_deployment(self):
        self.deploy()
        self.deploy()
        self.assertEqual((self.runtime/'UEVRBackend.dll').read_bytes(), self.new_dll)
        self.assertEqual((self.runtime/'UEVRBackend.pdb').read_bytes(), self.new_pdb)
        self.assertEqual((self.runtime/'UEVRBackend.dll.before-fear-fear-west.bak').read_bytes(), self.old_dll)
        self.assertEqual((self.runtime/'UEVRBackend.pdb.before-fear-fear-west.bak').read_bytes(), self.old_pdb)

    def test_failed_dll_replacement_restores_matching_previous_symbols(self):
        copy = deployment.atomic_copy

        def fail_dll(source, target):
            if target.name == 'UEVRBackend.dll':
                raise OSError('simulated locked DLL')
            copy(source, target)

        with patch.object(deployment, 'atomic_copy', fail_dll), self.assertRaises(OSError):
            self.deploy()
        self.assertEqual((self.runtime/'UEVRBackend.dll').read_bytes(), self.old_dll)
        self.assertEqual((self.runtime/'UEVRBackend.pdb').read_bytes(), self.old_pdb)

    def test_first_update_build_upgrades_with_its_own_paired_backup(self):
        (self.runtime/'UEVRBackend.dll').write_bytes(self.update_dll)
        (self.runtime/'UEVRBackend.pdb').write_bytes(self.update_pdb)
        self.deploy()
        self.assertEqual((self.runtime/'UEVRBackend.dll').read_bytes(), self.new_dll)
        self.assertEqual((self.runtime/'UEVRBackend.dll.before-native-game-cursor.bak').read_bytes(), self.update_dll)
        self.assertEqual((self.runtime/'UEVRBackend.pdb.before-native-game-cursor.bak').read_bytes(), self.update_pdb)

    def test_mismatched_build_symbols_are_rejected_before_runtime_writes(self):
        (self.build/'UEVRBackend.pdb').write_bytes(b'unrelated symbols')
        with self.assertRaises(SystemExit):
            self.deploy()
        self.assertEqual((self.runtime/'UEVRBackend.dll').read_bytes(), self.old_dll)
        self.assertEqual((self.runtime/'UEVRBackend.pdb').read_bytes(), self.old_pdb)
        self.assertFalse((self.runtime/'UEVRBackend.dll.before-fear-fear-west.bak').exists())

    def test_pre_hotfix_upgrade_preserves_pair_and_is_repeatable(self):
        (self.runtime/'UEVRBackend.dll').write_bytes(self.pre_hotfix_dll)
        (self.runtime/'UEVRBackend.pdb').write_bytes(self.pre_hotfix_pdb)
        self.deploy()
        self.deploy()
        self.assertEqual((self.runtime/'UEVRBackend.dll').read_bytes(), self.new_dll)
        self.assertEqual((self.runtime/'UEVRBackend.dll.before-0307-hotfix.bak').read_bytes(), self.pre_hotfix_dll)
        self.assertEqual((self.runtime/'UEVRBackend.pdb.before-0307-hotfix.bak').read_bytes(), self.pre_hotfix_pdb)

    def test_pre_hotfix_failed_dll_copy_restores_its_matching_symbols(self):
        (self.runtime/'UEVRBackend.dll').write_bytes(self.pre_hotfix_dll)
        (self.runtime/'UEVRBackend.pdb').write_bytes(self.pre_hotfix_pdb)
        copy = deployment.atomic_copy

        def fail_dll(source, target):
            if target.name == 'UEVRBackend.dll':
                raise OSError('simulated locked DLL')
            copy(source, target)

        with patch.object(deployment, 'atomic_copy', fail_dll), self.assertRaises(OSError):
            self.deploy()
        self.assertEqual((self.runtime/'UEVRBackend.dll').read_bytes(), self.pre_hotfix_dll)
        self.assertEqual((self.runtime/'UEVRBackend.pdb').read_bytes(), self.pre_hotfix_pdb)


if __name__ == '__main__':
    unittest.main()
