"""Exercise the optional preset against temporary persistent game configuration."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import prepare_menu_helper as helper


class NiagaraPresetTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(redirect_stdout(StringIO()))
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        profile = root / 'profile'
        (profile / 'data').mkdir(parents=True)
        log = root / 'FarFarWest.log'
        log.write_text('existing log\n')
        link = profile / 'data/FarFarWest.log'
        link.symlink_to(log)
        self.config = root / 'game/Config/UserEngine.ini'
        self.config.parent.mkdir(parents=True)
        self.baseline = b'[Core.Log]\r\nLogViewport=VeryVerbose\r\n[SystemSettings]\r\nr.PostProcessing.DisableMaterials=1\r\n'
        self.config.write_bytes(self.baseline)
        self.enterContext(patch.multiple(helper, PROFILE=profile, GAME_LOG=log,
                                        LINK=link, USER_CONFIG=self.config))

    def apply(self, restore=False):
        helper.prepare(preset='niagara-suppression', restore=restore)

    def test_persistent_layer_preserves_baseline_and_round_trips(self):
        self.apply()
        data = self.config.read_bytes()
        self.assertTrue(data.startswith(self.baseline))
        self.assertIn(b'fx.SuppressNiagaraSystems=1', data)
        self.assertEqual(self.config.with_name('UserEngine.ini.before-ffw-niagara-suppression.bak').read_bytes(), self.baseline)
        self.assertFalse((self.config.parent / 'Engine.ini').exists())
        self.apply(restore=True)
        self.assertEqual(self.config.read_bytes(), self.baseline)

    def test_reapplying_does_not_duplicate_the_override(self):
        self.apply()
        data = self.config.read_bytes()
        self.apply()
        self.assertEqual(self.config.read_bytes(), data)
        self.assertEqual(data.count(b'fx.SuppressNiagaraSystems=1'), 1)

    def test_restore_refuses_to_overwrite_later_user_edits(self):
        self.apply()
        changed = self.config.read_bytes() + b'UserSetting=preserve\r\n'
        self.config.write_bytes(changed)
        with self.assertRaisesRegex(SystemExit, 'changed since the backup'):
            self.apply(restore=True)
        self.assertEqual(self.config.read_bytes(), changed)

    def test_missing_backup_does_not_change_configuration(self):
        with self.assertRaisesRegex(SystemExit, 'No preset backup'):
            self.apply(restore=True)
        self.assertEqual(self.config.read_bytes(), self.baseline)


if __name__ == '__main__':
    unittest.main()
