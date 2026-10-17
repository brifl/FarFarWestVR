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

The current rendering test is defined in
[game_settings/temporal_baseline.ini](game_settings/temporal_baseline.ini) and
applied to the game's Engine.ini by `tools/apply_render_baseline.py`.
