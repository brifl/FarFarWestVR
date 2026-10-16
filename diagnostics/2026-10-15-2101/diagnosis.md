# Far Far West UEVR crash — October 15, 2026, 9:01 PM CDT

Most likely trigger: the imported profile's frozen `r.Shadow.Virtual.Enable=1`
override invokes an incompatible console-variable interface in the installed
UEVR/game combination. The trigger is well supported; the exact interface
incompatibility is an inference, and the proposed change has not been run.

Evidence from robot1-x, read over SSH into WSL:

- `C:\Users\brian\AppData\Roaming\UnrealVRMod\FarFarWest-Win64-Shipping\log.txt`
  records the exception at `2026-10-15 21:01:39.531`.
- Immediately preceding it: `Found r.Shadow.Virtual.Enable ... (via console manager)`,
  `(Standard) First time freezing "r.Shadow.Virtual.Enable"...`, then an attempted
  null dereference and `Exception occurred: c0000005`.
- The matching 746,929-byte `crash.dmp` has timestamp `2026-10-16 02:01:39 UTC`
  and confirms an invalid read at `0xffffffffffffffff` in
  `FarFarWest-Win64-Shipping.exe+0x12fa70f`.
- Unwinding the exception thread using the installed executables' x64 unwind
  metadata gives these frames, from the fault outward. UEVR function names were
  resolved against its installed PDB:

  ```text
  FarFarWest-Win64-Shipping.exe+0x12fa70f
  UEVRBackend.dll+0xf4af3  CVarManager::CVarStandard::freeze+0x293
  UEVRBackend.dll+0xf5a12  CVarManager::on_pre_engine_tick+0x32
  UEVRBackend.dll+0xbf476  VR::on_pre_engine_tick+0x36
  UEVRBackend.dll+0x154102
  FarFarWest-Win64-Shipping.exe+0x48d57d1
  ```

- `cvars_standard.txt` contains `Renderer_r.Shadow.Virtual.Enable=1`.
- Game `FarFarWest.log` identifies engine `5.8.1-915+++depot+CanyonEngine_Dev`
  and build `0.2.0.20`. Its log timestamps use UTC, five hours ahead of CDT.
- Installed UEVR identifies revision `4ee5c6b6162dee2291fc75f9dfc57667f6d45a2d`,
  built August 30, 2026. Its startup also reports missing viewport discovery and
  unimplemented XR vtables for the detected engine version. These strengthen
  the compatibility inference but do not establish the exact root cause.
- The profile's Lua scripts directory is empty. `user_script.txt` contains
  console commands. Disabling Lua would not target this crash path.
- `Saved\Config\CrashReportClient\UECC-Windows-ED9368994E861B59970926BE2609F378`
  contains only `CrashReportClient.ini`; no game crash report was present under
  `Saved\Crashes`. The UEVR log and dump provide the exception evidence.

One controlled next action: with the game and injector closed, remove only the
frozen shadow override, then repeat the same launch/injection once. The script
below is prepared but unapplied. It checks the original SHA256, backs up the
installed file before changing it, preserves all other bytes, and refuses to
overwrite subsequent edits during rollback.

```bash
bash diagnostics/2026-10-15-2101/cvar-override-test.sh apply
```

Rollback, with the game and injector closed:

```bash
bash diagnostics/2026-10-15-2101/cvar-override-test.sh rollback
```

Backup on robot1-x:
`C:\Users\brian\AppData\Roaming\UnrealVRMod\FarFarWest-Win64-Shipping\cvars_standard.txt.pre-shadow-freeze-test-20261015-2101.bak`.
The backup is created when `apply` runs. A local copy of the diagnosed original
is included as `cvars_standard.txt.before`.

No installed settings, plugins, runtime selection, or binaries were changed.
No software was installed, cloned, or built. Preparation was checked with Bash
syntax validation and a local sandbox exercise of apply and rollback; no game
reproduction was run.
