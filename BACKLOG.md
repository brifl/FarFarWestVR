# Far Far West VR controls and backlog

Updated October 16, 2026. Changes stay in this profile repository; the isolated
UEVR backend is patched with `tools/disable_slate_hook.py`.

## Working baseline

- Stereo views align with symmetrical horizontal projection.
- F8 switches between immersive VR and a readable, stationary screen.
- Menu cursor/control works in screen mode.
- Left stick movement, grips/spells, Y/weapon switching, and triggers/aim-fire
  were reported working. Controller-directed weapon aiming is still missing.

## Current pass — awaiting headset validation

- Remove A's synthetic Enter binding, which can open chat. Keep its native action.
- Bind Quest X to F/interact, including while the left grip is held.
- Preserve Quest B -> Escape, including while the left grip is held.
- On B, switch to the readable screen for the pause menu. After resuming, use F8
  to return to immersive VR. The helper does not detect actual game menu state.
- Disable UEVR's thumbrest D-pad shifting to avoid unintended alternate controls.

## Work queue

| Priority | Change | Acceptance condition / constraint |
| --- | --- | --- |
| 1 | Restore safe world/player discovery for the updated engine | Address the earlier `UEngine::get_world` crash before enabling dependent features. |
| 2 | Right-stick horizontal snap turn | Start with the existing 45-degree preference; one turn per deflection, rearm at center. Stock UEVR snap turn calls the incompatible world lookup, so it remains disabled. |
| 2 | Separate menu cursor movement from gameplay look input | Keep the working menu controls; stop JoyToKey mouse movement and vertical camera/HUD movement during immersive gameplay. Right-stick up/down should initially do nothing in gameplay. |
| 2 | Right-controller gun aiming and accurate reticle | Gun/barrel direction, shot direction, and reticle must agree. Remove the current dependence on joystick mouse aim; restore engine-dependent aiming only after its crash is fixed. |
| 3 | Reticle and HUD presentation | Reduce the oversized reticle and keep HUD placement stable when looking around. |
| 3 | Pause/menu transitions | Eventually detect real menu state and return to immersive VR automatically on resume; B/F8 is the interim workflow. |
| 3 | Simplify the input layers | Audit JoyToKey plus RemapControls, their overlapping native gamepad inputs, grip-shift behavior, and RemapControls' repeated invalid-shift warning. Preserve working actions. |
| 4 | Choose stick-click actions | Left click currently produces a forward leap/dash; right click produces a multiplayer ping. Decide desired assignments before changing them. |

## Intended controls

UEVR uses Xbox-style internal names. Quest X is internal **B**; Quest B is
internal **X**. This distinction matters when editing `plugins/joytokey.txt`.

| Quest control | Intended behavior | Status |
| --- | --- | --- |
| Left stick | Move and strafe | Preserve working behavior |
| Right stick left/right | Snap turn | Queued |
| Right stick up/down | No gameplay action initially | Queued; menu cursor must keep working |
| A | Native primary action, without opening chat | Enter override removed; test native action |
| B | Pause/back with readable menu | Escape retained; screen helper awaiting test |
| X | Interact with F/X prompts | F binding awaiting test |
| Y | Switch weapons | Preserve working behavior |
| Left/right grip | Spells | Preserve working behavior |
| Left trigger | Aim | Preserve action; sight/reticle alignment queued |
| Right trigger | Fire; click in menus | Preserve working behavior |
| Left/right stick click | To be decided | Dash/ping observed; unchanged |
