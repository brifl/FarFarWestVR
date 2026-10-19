The files in this enlistment can be zipped into FarFarWest-Win64-Shipping.zip and imported into UEVR.

See [BACKLOG.md](BACKLOG.md) for the intended controls, working baseline, and next changes.

Personal tuning is in [data/tuning.ini](data/tuning.ini). On robot1-x, edit
`C:\Users\brian\AppData\Roaming\UnrealVRMod\FarFarWest-Win64-Shipping\data\tuning.ini`.
Numeric edits reload while playing, about once a second. Installing new helper
code still requires UEVR's **Reset scripts** or a normal game relaunch.

| Section | Setting | Starting value | Meaning |
| --- | --- | --- | --- |
| graphics | saturation_multiplier | 0.95 | Five percent less saturation; 1.0 uses the native amount. |
| graphics | contrast_multiplier | 1.10 | The accepted ten-percent increase; 1.0 uses the native amount. |
| graphics | fog_density_multiplier | 0.00 | The accepted clear-distance setting; 1.0 uses native density. |
| hud | dialogue_offset_y | -0.10 | Raise conversation text by ten percent of viewport height. |
| hud | boss_health_offset_y | 0.08 | Lower boss health by eight percent. |
| hud | mission_info_offset_y | 0.08 | Lower mission counters and timers by eight percent. |
| hud | compass_offset_y | 0.08 | Lower the compass background and marker overlay together by eight percent. |

HUD offsets use the full viewport height: positive moves down, negative moves up,
and zero restores the original position. Saturation accepts 0–2, contrast 0.5–2,
fog 0–1 and HUD offsets -0.5–0.5. Invalid edits retain the previous values.
The boss-bar and mission-counter controls apply as those widgets appear; their
height can be tuned during later fights/objectives without restarting scripts.

Marker discovery front-loads the initial and newly allocated objects within a
two-millisecond scan budget. Known components are retained while their widgets
load, and hidden markers are prepared before they become visible. This reduces
the former multi-second scan delay without a blocking full-array sweep.

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

Menu pointing now uses the right controller's ray intersection with the existing
screen. Move/rotate the controller to move the pointer and use the right trigger
to click. JoyToKey's stick-to-mouse movement is disabled in both grip modes;
gameplay snap turns keep their native stick input. This requires the latest
isolated backend below and is confirmed working. The game window must have
focus. Menu placement, B pause/resume and gameplay aiming are preserved.

Game menus use the supplied themed arrow in [assets/menu_cursor.png](assets/menu_cursor.png).
Its top-left tip is the click hotspot; it displays at 48 pixels high in a 1440p
view and scales with the viewport. The UEVR panel retains its standard cursor,
and immersive gameplay keeps the menu cursor hidden. The isolated backend loads
the PNG into its existing font texture; a missing image falls back to the standard
cursor. Changes to the image load on the next game launch.

The isolated backend now uses a source build with the modern UE5.8 object
layout and the accepted rendering/aim compatibility fixes. After pulling this
profile on robot1-x, deploy its verified DLL/PDB while the game is closed:
`python3 tools/deploy_native_backend.py apply`.
The build artifacts live in `C:/src/uevr_far_west_build/build/bin/uevr`.
The installer preserves the prior pair; `restore` reinstates it. Older binary
patch tools require that prior backend and cannot patch the source build.
The cursor source change is in [native_patches/menu_cursor.patch](native_patches/menu_cursor.patch);
[its native smoke test](native_patches/tests/menu_cursor.cpp) checks PNG decoding,
atlas rebuilds, alpha/color preservation, the hotspot and missing-image fallback.

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

The accepted clear-distance setting is applied by [scripts/fog.lua](scripts/fog.lua).
It sets primary fog density to zero on the game's ambient weather components as
they load, using the guarded UE5.8 backend. This matches the tested haze removal;
a 25-percent reduction was imperceptible. Script reset restores captured native
density values before the helper reloads. Other atmosphere layers keep their settings.

[scripts/contrast.lua](scripts/contrast.lua) applies configurable contrast and
saturation multipliers to weather grading. The accepted contrast increase remains
the default. Native RGB balance is preserved; a previously inactive saturation
override starts from neutral RGB. Its original vector/override flags restore on
script reset, and repeated updates do not compound the multipliers.

Location markers are being tested with
[scripts/world_markers.lua](scripts/world_markers.lua). It displays copies of the
saloon's `UI_WorldIcon` markers at their world positions projected through the
headset camera. Looking up/right moves a fixed-world marker down/left; controller
aiming cannot change its position. The originals are hidden only during immersive
play and restored for menus or script reset. Other marker families are separate.

NPC interaction prompts use the same headset projection while keeping the
game's live text, key icon and hold-progress display. Only the prompt's visual
translation changes; its world target and X interaction remain native. The
shared screen-widget correction also supports further marker adapters, with
player pings queued next. NPC placement is confirmed working.

Mission objective markers and text guides retain their live title/distance widgets
and use the same visual-child correction as Start Mission. Objective target data
and actor roots remain in place; controller aiming cannot move their headset
projection. The user confirms quest markers stay anchored with correct title and distance.
