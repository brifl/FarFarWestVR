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
was repeatedly deleted. The startup log confirms this source layer loads; check persistence on
further launches. Reapply preparation after changing the repository's settings preset.
F8 remains a manual presentation fallback.

Controller aiming is being tested with
[scripts/controller_aim.lua](scripts/controller_aim.lua). Right-controller
orientation drives the game's look input while head direction remains independent.
Horizontal right-stick deflection requests one 45-degree snap turn, rearmed at
center. The existing menu controls are preserved. Gun position/hand attachment
is still queued. The projected crosshair is confirmed aligned at different
ranges and with spells. The menu helper hides UEVR's extra mouse cursor in
immersive gameplay and restores it for menus.
Aiming and snap turns require a loaded gameplay level; menus cannot activate them.

The isolated backend now uses a source build with the modern UE5.8 object
layout and the accepted rendering/aim compatibility fixes. After pulling this
profile on robot1-x, deploy its verified DLL/PDB while the game is closed:
`python3 tools/deploy_native_backend.py apply`.
The build artifacts live in `C:/src/uevr_far_west_build/build/bin/uevr`.
The installer preserves the prior pair; `restore` reinstates it. Older binary
patch tools require that prior backend and cannot patch the source build.

[scripts/reticle.lua](scripts/reticle.lua) validates the backend identity,
widget layout and function metadata before moving the original crosshair to
the firing-camera trace target. It restores the crosshair in menus and leaves
quest markers alone. For a read-only geometry probe, put `probe` in the
profile's `data/reticle_mode.txt`; remove the file to enable movement again.

The repeating upward-moving distortion is absent on the repeat test with the
startup override `r.PostProcessing.DisableMaterials=1`, confirmed in the live
game log. This suppresses all custom post-process materials; the exact offending
material remains unidentified. Check damage/status effects during further play.
The prepared FXAA experiment is retained outside the autorun scripts in
[experiments/temporal_aa_test.lua](experiments/temporal_aa_test.lua).
