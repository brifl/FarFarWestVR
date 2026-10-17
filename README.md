The files in this enlistment can be zipped into FarFarWest-Win64-Shipping.zip and imported into UEVR.

See [BACKLOG.md](BACKLOG.md) for the intended controls, working baseline, and next changes.

Quest B sends Escape. The menu helper now follows the game's logged input-mode
changes, including clicking Resume, instead of toggling presentation on B presses.
It restores the readable menu distance and disables the cached menu overlay
when returning to immersive play.
This needs headset validation. Prepare it in WSL on robot1-x before launch:
`python3 tools/prepare_menu_helper.py`.
The tool links the game log into the profile's Lua data directory and enables
focused menu logging. Engine.ini was absent after the last run; prepare again
before another launch if it is absent.
F8 remains a manual presentation fallback.

Controller aiming is being tested with
[scripts/controller_aim.lua](scripts/controller_aim.lua). Right-controller
orientation drives the game's look input while head direction remains independent.
Horizontal right-stick deflection requests one 45-degree snap turn, rearmed at
center. The existing menu controls are preserved. Gun position/hand attachment
and reticle alignment are still queued.

The isolated backend needs the guarded compatibility patch:
`python3 tools/enable_controller_aim.py apply` (WSL on robot1-x).
It enables correct UE5 camera vectors and controller aim poses for Lua.

The shimmer is also visible on desktop and is deferred while aiming is addressed.
The prepared FXAA experiment is retained outside the autorun scripts in
[experiments/temporal_aa_test.lua](experiments/temporal_aa_test.lua).
