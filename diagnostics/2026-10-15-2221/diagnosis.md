# Far Far West UEVR crash — October 15, 2026, 10:21 PM CDT

The shadow-only change did not resolve the crash. The next exception occurred
while freezing another standard CVar, `r.LightCulling.Quality`. This strengthens
the inference that standard CVar writes are incompatible with this game/build,
rather than the failure being specific to virtual shadows.

Evidence read from robot1-x:

- UEVR log: `2026-10-15 22:21:17.872`, `(Standard) First time freezing
  "r.LightCulling.Quality"...`, followed immediately by the failed null-pointer
  recovery and `Exception occurred: c0000005`.
- The new 742,522-byte dump records an invalid read at `0xffffffffffffffff`,
  with RIP at `FarFarWest-Win64-Shipping.exe+0x12fa8bf`. The first caller at
  `RSP+0x28` is `UEVRBackend.dll+0xf4a61`, consistent with the previously
  identified standard-CVar freeze path.
- The dump confirms the loaded backend is
  `C:\Manual Installs\uevr_far_west\UEVRBackend.dll`. This isolated folder
  still reports revision `4ee5c6b6162dee2291fc75f9dfc57667f6d45a2d`.
- The shadow override was absent in the tested installed profile. Data-CVar
  processing progressed through several entries before the standard-CVar crash.
- The new CrashReportClient folder again contains only an INI. The game log
  ends during normal title-screen activity without a separate fatal report.

One controlled next test: empty `cvars_standard.txt` to disable all four remaining
standard overrides together. Keep `cvars_data.txt`, scripts, plugins, aiming,
runtime selection, and UEVR binaries unchanged. This tests the implicated write
path without repeatedly removing one crashing CVar per launch. The exact
underlying interface incompatibility remains unproven.

The four removed overrides are screen percentage, light-culling quality,
temporal upsampling, and upscale quality. Their game defaults may affect image
quality or performance during this test. The empty file is intentional.

Deploy the repository commit with `git pull`, then repeat the same
launch/injection once. No UEVR binary modification is needed for this test.
Runtime validation is pending the user's reproduction.

The pre-test installed file was backed up on robot1-x as
`cvars_standard.txt.pre-disable-standard-20261015-2221.bak`. Its SHA256 is
`8dd1aba7282abff936a50f736b00f80b14f98372e247cb0c8cf07f00bc45841d`.
It is also available in commit `fe7a920`.

To undo this test before making further edits, close the game and injector and
run this from the installed profile directory on robot1-x:

```bash
cp -- cvars_standard.txt.pre-disable-standard-20261015-2221.bak cvars_standard.txt
```

This rollback returns to the shadow-only version, which is already known to
crash. The older single-entry rollback script refuses to overwrite this new
empty-file state.
