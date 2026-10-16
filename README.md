The files in this enlistment can be zipped into FarFarWest-Win64-Shipping.zip and imported into UEVR.

See [BACKLOG.md](BACKLOG.md) for the intended controls, working baseline, and next changes.

F8 switches between immersive VR and the readable menu screen. Quest B sends
Escape and switches between the pause screen and immersive view in both
directions. F8 remains an optional fallback; B does not require a keyboard to resume.

The current rendering test is defined in
[game_settings/temporal_baseline.ini](game_settings/temporal_baseline.ini) and
applied to the game's Engine.ini by `tools/apply_render_baseline.py`.
