The files in this enlistment can be zipped into FarFarWest-Win64-Shipping.zip and imported into UEVR.

See [BACKLOG.md](BACKLOG.md) for the intended controls, working baseline, and next changes.

Quest B sends Escape. The menu helper now follows the game's logged input-mode
changes, including clicking Resume, instead of toggling presentation on B presses.
This needs headset validation with the focused menu logging enabled:
`python3 tools/apply_render_baseline.py apply --preset menu-logging`.
F8 remains a manual presentation fallback.

The current rendering test is defined in
[game_settings/temporal_baseline.ini](game_settings/temporal_baseline.ini) and
applied to the game's Engine.ini by `tools/apply_render_baseline.py`.
