The files in this enlistment can be zipped into FarFarWest-Win64-Shipping.zip and imported into UEVR.

See [BACKLOG.md](BACKLOG.md) for the intended controls, working baseline, and next changes.

Quest B sends Escape. The menu helper now follows the game's logged input-mode
changes, including clicking Resume, instead of toggling presentation on B presses.
Logged level/loading state keeps the title screen in menu mode even when UEVR
saved immersive mode and verbose input-mode events are unavailable.
It restores the readable menu distance and disables the cached menu overlay
when returning to immersive play.
The menu behavior is confirmed. Install its logging and the distortion workaround
in WSL on robot1-x:
`python3 tools/prepare_menu_helper.py --material-test`.
The tool links the game log into the profile's Lua data directory and enables
focused menu logging and the tested distortion workaround. Settings now go in
the game's `FarFarWest/Config/UserEngine.ini`; the generated Saved/Config copy
was repeatedly deleted. Persistence through this source layer awaits a relaunch
test. Reapply preparation after changing the repository's settings preset.
F8 remains a manual presentation fallback.

Controller aiming is being tested with
[scripts/controller_aim.lua](scripts/controller_aim.lua). Right-controller
orientation drives the game's look input while head direction remains independent.
Horizontal right-stick deflection requests one 45-degree snap turn, rearmed at
center. The existing menu controls are preserved. Gun position/hand attachment
and reticle alignment are still queued.
Aiming and snap turns require a loaded gameplay level; menus cannot activate them.

The isolated backend needs the guarded compatibility patch:
`python3 tools/enable_controller_aim.py apply` (WSL on robot1-x).
It enables correct UE5 camera vectors and controller aim poses for Lua.

The repeating upward-moving distortion is absent on the repeat test with the
startup override `r.PostProcessing.DisableMaterials=1`, confirmed in the live
game log. This suppresses all custom post-process materials; the exact offending
material remains unidentified. Check damage/status effects during further play.
The prepared FXAA experiment is retained outside the autorun scripts in
[experiments/temporal_aa_test.lua](experiments/temporal_aa_test.lua).
