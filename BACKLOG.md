# Far Far West VR controls and backlog

Updated October 16, 2026. Changes stay in this profile repository; the isolated
UEVR backend is patched with `tools/disable_slate_hook.py`.

## Working baseline

- Stereo views align with symmetrical horizontal projection.
- Menus accepted after `9e94640`: readable, stationary, working cursor/control,
  and B pause/resume. The user reports "Much better" and is ready to move on.
  Screen textures survive resets; immersive play clears the cached menu layer.
- Quest X now activates F/X interaction prompts (confirmed in the saloon).
- Left stick movement, grips/spells, Y/weapon switching, and triggers/aim-fire
  were reported working. Controller-directed weapon aiming is still missing.

## Continuation checkpoint

- Active task: controller-directed aiming, now prioritized by the user over
  graphics. The shimmer is visible in the desktop image too. The FXAA experiment
  was never deployed and is retained in `experiments/temporal_aa_test.lua`, outside
  autorun scripts. Rendering settings remain at the accepted menu baseline.
- `scripts/controller_aim.lua` is a first-pass orientation bridge: read the
  right-controller aim quaternion and raw game camera yaw/pitch, then feed a
  closed-loop right-stick look signal after JoyToKey. Compensate actual camera
  yaw through UEVR's rotation offset so the aiming wrist does not turn the head
  view. A raw-stick latch changes that world anchor by 45 degrees for snap turns.
  Menus keep their existing input path. Native gun/hand position attachment and
  reticle alignment remain unfinished; first validate that shot direction follows
  the right wrist with the stick centered.
- The native log reports IXRTrackingSystemVT/IXRCameraVT unimplemented for engine
  5.8. Native manual control rotation still requires unsafe world/player lookup.
  The bridge keeps those native options disabled. Its early camera callback also
  needs a narrow Lua ABI fix: `lua::utility::is_ue5` otherwise returns false when
  object discovery fails and interprets camera doubles as floats.
- Backend preparation: `python3 tools/enable_controller_aim.py apply` on robot1-x.
  It derives from the verified persistent-menu backend and changes four bytes:
  raw `0x5e2f30..32` return true for UE5 Lua camera dispatch; raw `0x574f0` selects
  the runtime aim pose in the plugin API's get_pose wrapper. No game objects are
  accessed. A marker in profile/data gates callback registration. Expected hash
  `3d2c8647dc10409a8d3d014c248f69f10f60895aede9c2d1fbee442d557c7527`.
  The tool's restore mode returns the prior menu baseline and removes the marker;
  restore this stage before using the older disable_slate_hook.py tool.
  Lua math/input checks and temporary-file patch apply/restore guards pass;
  native gamepad response, aim direction/sign and gun/reticle presentation need
  headset validation. Look for `[FarFarWest aim]` in the profile log.
- Continuation checkpoint: the Lua startup failure is fixed. The October 16
  21:40 run confirms successful load and matching game/menu transitions. Lua
  uses the relative `FarFarWest.log` link in profile/data because UEVR removes
  `os.getenv` and rejects absolute file paths. Run
  `python3 tools/prepare_menu_helper.py` on robot1-x before the next launch.
- The installed `UI_Distance` was 9.169m while the repo baseline is 3m, making
  all menus tiny. The helper now restores distance 3m and size 1.8m on entering
  screen mode.
- The game reported loading hidden and input returned to gameplay, but UEVR
  kept showing Loading/menu imagery. In OpenVR, without a captured Slate UI
  target, the overlay texture retains its last screen frame. The helper now
  sets `VR_EnableGUI=false` in immersive mode, which calls ClearOverlayTexture,
  and re-enables it for menus. The baked-in game HUD is unaffected. The user
  accepted this menu baseline; avoid reopening menu troubleshooting without
  a new regression.
- Custom UEVR build remains a last resort; the compatibility bridge uses guarded
  edits to the existing isolated backend.
- Remove A's synthetic Enter binding, which can open chat. Keep its native action.
- Keep the confirmed Quest X -> F/interact binding, including its grip-held mapping.
- Preserve Quest B -> Escape, including while the left grip is held.
- Replace the independent B/presentation toggle: clicking Resume previously left
  UEVR in screen mode, showing a black world with a visible HUD. B then toggled
  the game and presentation into the opposite mismatch.
- Follow `LogViewport` mouse-capture transitions instead, with cursor visibility
  as a fallback until capture mode is known. Menu input selects screen mode;
  gameplay input restores immersive view, including after clicking Resume.
  The focused `menu-logging` preset and latest run confirm those transitions.
  No unsafe world/player lookup is used.
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
  The latest October 16 test still reports anti-aliasing method 4 and motion
  blur quality 0. Before changing rendering, confirm whether the reported
  ghosting/waviness remains after removing the stale overlay. If it is stable,
  proceed to safe player discovery and right-stick controls instead.
- Disable UEVR's thumbrest D-pad shifting to avoid unintended alternate controls.

## Work queue

| Priority | Change | Acceptance condition / constraint |
| --- | --- | --- |
| 0 | Eliminate remaining ghosting and wavy, unstable imagery | Visible in desktop and headset; deferred by user until controller aiming works. FXAA experiment remains inactive. |
| 1 | Restore safe world/player discovery for the updated engine | Address the earlier `UEngine::get_world` crash before enabling dependent features. |
| 2 | Right-stick horizontal snap turn | Orientation bridge implements a 45-degree world-anchor latch; awaiting test. Stock snap remains disabled because it calls the unsafe world lookup. |
| 2 | Separate menu cursor movement from gameplay look input | Keep the working menu controls; stop JoyToKey mouse movement and vertical camera/HUD movement during immersive gameplay. Right-stick up/down should initially do nothing in gameplay. |
| 2 | Right-controller gun aiming and accurate reticle | First validate orientation bridge with stick centered. Then align gun/barrel, shots and reticle, and remove remaining gameplay mouse emulation. Full object-dependent aiming still needs safe discovery. |
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
| Right stick left/right | Snap turn | 45-degree bridge latch awaiting test |
| Right stick up/down | No gameplay action initially | Queued; menu cursor must keep working |
| A | Native primary action, without opening chat | Enter override removed; test native action |
| B | Pause and resume with readable menu | Accepted baseline after cached-overlay fix |
| X | Interact with F/X prompts | Confirmed working |
| Y | Switch weapons | Preserve working behavior |
| Left/right grip | Spells | Preserve working behavior |
| Left trigger | Aim | Preserve action; sight/reticle alignment queued |
| Right trigger | Fire; click in menus | Preserve working behavior |
| Left/right stick click | To be decided | Dash/ping observed; unchanged |
