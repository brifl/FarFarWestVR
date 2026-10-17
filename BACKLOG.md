# Far Far West VR controls and backlog

Updated October 16, 2026. Changes stay in this profile repository; the isolated
UEVR backend is patched with `tools/disable_slate_hook.py`.

## Working baseline

- Stereo views align with symmetrical horizontal projection.
- Screen mode provides a readable, stationary menu with working cursor/control.
  The Escape menu looks correct and B opens it. The latest log has no missing
  screen-texture errors after the reset-allocation patch.
- Quest X now activates F/X interaction prompts (confirmed in the saloon).
- Left stick movement, grips/spells, Y/weapon switching, and triggers/aim-fire
  were reported working. Controller-directed weapon aiming is still missing.

## Current pass — awaiting headset validation

- Continuation checkpoint: the launch popup came from `os.getenv`, which UEVR
  explicitly removes. Absolute `io.open` paths are also rejected. The corrected
  helper reads the relative `FarFarWest.log` name in profile/data; a native
  Windows file link connects it to the game log. Run
  `python3 tools/prepare_menu_helper.py` on robot1-x before the next launch.
  The failed-script run nevertheless confirmed the game's capture-mode logs
  change between `CaptureDuringMouseDown` (menu) and `CapturePermanently` (play).
  Restricted Lua 5.4 checks pass with `os.getenv=nil` and relative-only file
  access; Windows can read the installed native log link. The old test harness
  incorrectly supplied unrestricted APIs and missed the launch failure.
  Next headset check is B -> click Resume without F8. Custom UEVR build remains
  a last resort; no build is needed for this Lua correction.
- Remove A's synthetic Enter binding, which can open chat. Keep its native action.
- Keep the confirmed Quest X -> F/interact binding, including its grip-held mapping.
- Preserve Quest B -> Escape, including while the left grip is held.
- Replace the independent B/presentation toggle: clicking Resume previously left
  UEVR in screen mode, showing a black world with a visible HUD. B then toggled
  the game and presentation into the opposite mismatch.
- Follow `LogViewport` mouse-capture transitions instead, with cursor visibility
  as a fallback until capture mode is known. Menu input selects screen mode;
  gameplay input restores immersive view, including after clicking Resume.
  Confirm this game emits those transitions with the focused `menu-logging`
  Engine.ini preset. No unsafe world/player lookup is used.
- Prevent held Quest B from also reaching the game as native X after JoyToKey
  has already sent Escape. Keep the synthetic Escape binding in both grip modes.
- Allocate screen textures even when a renderer reset occurs in immersive mode;
  the log showed null screen-texture copies after such a reset.
- Center the startup/menu screen in front of the headset. Preserve and restore
  the prior immersive orientation across menu transitions.
- Test a non-temporal rendering baseline through the game's Engine.ini:
  DLSS and frame generation off, FXAA, motion blur off. The game log confirmed
  DLSS Performance (1280x720 -> 2560x1440) and anti-aliasing method 4. These are
  suspects in the severe ghosting/wavy image; the fallback's eye timing is also
  unresolved. The latest log still shows active DLSS and method 4; Engine.ini
  was absent after that run. Do not assume the rendering overrides are active.
- Disable UEVR's thumbrest D-pad shifting to avoid unintended alternate controls.

## Work queue

| Priority | Change | Acceptance condition / constraint |
| --- | --- | --- |
| 0 | Eliminate ghosting and wavy, unstable imagery | Comfort blocks further gameplay testing. Current test removes temporal upscaling/AA and blur; if instability persists, examine fallback eye/pose timing and reprojection next. |
| 0 | Reliable pause/resume without another device | Validate input-mode detection with B to open, click Resume to close, and B to open/close again. Submenus must stay readable. No required keyboard step. |
| 1 | Restore safe world/player discovery for the updated engine | Address the earlier `UEngine::get_world` crash before enabling dependent features. |
| 2 | Right-stick horizontal snap turn | Start with the existing 45-degree preference; one turn per deflection, rearm at center. Dead Island's Lua uses this latch and changes pawn/controller yaw. Reuse the approach after safe pawn/controller access is restored; stock snap remains disabled. |
| 2 | Separate menu cursor movement from gameplay look input | Keep the working menu controls; stop JoyToKey mouse movement and vertical camera/HUD movement during immersive gameplay. Right-stick up/down should initially do nothing in gameplay. |
| 2 | Right-controller gun aiming and accurate reticle | Gun/barrel direction, shot direction, and reticle must agree. Remove the current dependence on joystick mouse aim; restore engine-dependent aiming only after its crash is fixed. |
| 3 | Reticle and HUD presentation | Reduce the oversized reticle and keep HUD placement stable when looking around. |
| 3 | Simplify the input layers | Audit JoyToKey plus RemapControls, their overlapping native gamepad inputs, grip-shift behavior, and RemapControls' repeated invalid-shift warning. Preserve working actions. |
| 4 | Choose stick-click actions | Left click currently produces a forward leap/dash; right click produces a multiplayer ping. Decide desired assignments before changing them. |
| 4 | Raise dialogue subtitles/text | Character dialogue is low in the field of view and hard to read; user reports this as nonblocking. |

## Dead Island reference inspected

Local reference: `/mnt/c/Users/brian/Downloads/DeadIsland-Win64-Shipping/`.
`scripts/libs/input.lua` implements `updateDecoupledYaw` with `snapAngle`,
`snapTurnDeadZone`, and a center-to-rearm latch; pawn/controller rotation applies
the accumulated yaw. `scripts/libs/uevr_utils.lua` detects pause through
`Statics:IsGamePaused(world)`. Both depend on game-object access that currently
fails in Far Far West. The supplied saved `useSnapTurn` preference is false,
although the Lua snap-turn implementation is present. The reference was read
only; its libraries and DLL were not copied into this profile.

## Intended controls

UEVR uses Xbox-style internal names. Quest X is internal **B**; Quest B is
internal **X**. This distinction matters when editing `plugins/joytokey.txt`.

| Quest control | Intended behavior | Status |
| --- | --- | --- |
| Left stick | Move and strafe | Preserve working behavior |
| Right stick left/right | Snap turn | Queued |
| Right stick up/down | No gameplay action initially | Queued; menu cursor must keep working |
| A | Native primary action, without opening chat | Enter override removed; test native action |
| B | Pause and resume with readable menu | Game input-mode helper awaiting test; Resume click must work too |
| X | Interact with F/X prompts | Confirmed working |
| Y | Switch weapons | Preserve working behavior |
| Left/right grip | Spells | Preserve working behavior |
| Left trigger | Aim | Preserve action; sight/reticle alignment queued |
| Right trigger | Fire; click in menus | Preserve working behavior |
| Left/right stick click | To be decided | Dash/ping observed; unchanged |
