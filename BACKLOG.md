# Far Far West VR controls and backlog

Updated October 17, 2026. Changes stay in this profile repository; the isolated
UEVR backend is patched with `tools/disable_slate_hook.py`.

## Working baseline

- Stereo views align with symmetrical horizontal projection.
- Menus accepted after `9e94640`: readable, stationary, working cursor/control,
  and B pause/resume. The user reports "Much better" and is ready to move on.
  Screen textures survive resets; immersive play clears the cached menu layer.
- Quest X now activates F/X interaction prompts (confirmed in the saloon).
- Left stick movement, grips/spells, Y/weapon switching, and triggers/aim-fire
  were reported working. The user now confirms that gun aim follows the right
  controller. The user also confirms that shot grouping stays fixed when turning
  the head with the controller held still. Reticle alignment remains unfinished.

## Continuation checkpoint

- Current task: isolate a repeating upward-scrolling, transparent amoeba-like
  distortion pattern (not random circles). User offered a live debug session.
  The 01:06 run's Lua setter stopped with 'caught (...) exception' before any
  readback. Thus neither distortion test established r.DisableDistortion=1.
  The failed Lua helper is now inactive in experiments/distortion_test.lua.
  Next one-category test: r.PostProcessing.DisableMaterials=1 through Engine.ini,
  using `python3 tools/prepare_menu_helper.py --material-test` before launch.
  Its material-probe preset includes existing menu logging and LogConfig=Verbose
  so startup application can be checked without the failing native console API.
  Both CVar names are present in the installed game executable. Have the user
  leave the game open at the visible pattern; inspect LogConfig and any warnings
  for this exact setting before interpreting the visual result. This test also
  removes other custom post-process materials and is not yet a permanent fix.
- The initial distortion text entry was a no-op: the installed
  CVarManager loads only its predefined variables, and r.DisableDistortion is
  absent from both lists in CVarManager.hpp. The ignored entry was removed;
  the replacement IConsoleManager setter also failed. Diagnose its exact failing
  call separately before reusing it (the saved script's pcall caught the error).
  Controller aiming and menu behavior remain at their accepted baseline.
- Deferred correction requested: remove mouse/aim pitch from location-marker
  projection; looking up must move a fixed-world marker down the screen (and
  vice versa), preserving its world elevation. Keep controller firing and the
  accepted menu placement. Reproject using the actual game camera's inverse
  projection, camera-to-world rotation, then the inverse headset-view rotation
  and headset projection; do not invert global headset tracking or gun input.
- Read-only live probe found a concrete SDK mismatch. See
  `tools/ue58_object_layout.json`: compact chunked-array header at game RVA
  0xad3d980 has Objects/Num/Max/NumChunks/MaxChunks at 0/8/12/16/20; item stride
  remains 24 but its UObject pointer is at +8. Four consecutive item pointers
  lead to UObjects with indices 0/1/2/3 and vtables in the game image. This
  verifies the measured layout mismatch with the old SDK, whose object pointer
  is expected at +0, and explains its rejection of these entries. The chunked
  array is not necessarily the FUObjectArray base.
  `tools/probe_object_array.ps1` reproduces this read-only check, restricted to
  aligned candidates from UEVR's own log in writable game sections, capped at
  512 headers. Full bounded probe result: /tmp/ffw-object-array-probe.json.
- Source access restored October 17: the user repaired Epic/GitHub access, and
  SSH `git ls-remote` now succeeds for both EpicGames/UnrealEngine and
  praydog/UESDK from this workspace. The SDK source prerequisite is cleared.
  Keep the installed heat-distortion test active pending the user's result;
  source access restoration alone does not deploy a native/marker patch. Pinned SDK
  revision: 14478dfae61e8385e0e62116718925c4099b1d18. No native or gameplay patch
  has been applied during this probe; the isolated backend remains SHA256
  3d2c8647dc10409a8d3d014c248f69f10f60895aede9c2d1fbee442d557c7527.
  Local analysis copy: /tmp/ffw-controller-backend.dll. PDB symbols:
  /tmp/ffw-pdb-object-array-symbols.txt; FUObjectArray::get RVA 0x636ca0,
  get_object RVA 0x9aee0. Do not simply shift item pointers: native flag reads
  would then read unrelated item fields. Repair the layout coherently first.
- User accepts pause/Resume after `0e18e34`. Menu spawn height nevertheless
  follows controller pitch: OverlayComponent applies pre-flattened game camera
  pitch while VR_DecoupledPitchUIAdjust is enabled. The menu helper now disables
  that adjustment in screen mode and restores it in immersive gameplay. Menu
  recentering remains based on the HMD. The user confirms the menu works great
  after `07b58d9`; location markers remain unchanged, as this affects overlays.
- Add right-controller ray pointing/clicking for game menus, replacing stick
  cursor movement. Keep the screen placement independent of the pointing ray.
  The UEVR framework panel already has controller pointing; the game menu does not.
- Quest/location markers shift vertically opposite controller aim. These are
  baked into the game image and need head/view-relative projection, separately
  from the gun's firing direction and the menu overlay pitch adjustment.
  The 00:18 run still reports Failed to find GUObjectArray and Failed to find
  UGameViewportClient::Draw (CanvasObject has no string references). Existing
  Lua object access and viewport callbacks cannot safely reach this path yet.
  Target world-to-screen projection (ULocalPlayer/GetProjectionData or the HUD's
  projection helper) with the HMD view while preserving the controller-driven
  firing camera. Do not toggle unrelated overlay/aim settings as a marker test.
- The 00:10 run contains working pause input-mode logs, but Engine.ini is still
  absent after exit despite the section-save opt-in. Logging persistence is not
  yet confirmed; prepare the logging preset again before the next test.
- Pause-menu regression in the 23:51 run: UI distance/size remained 3m/1.8m,
  but Engine.ini was absent and no LogViewport transitions were recorded. The
  level fallback restored the title/lobby correctly but cannot detect pause.
  The menu-logging preset now opts Core.Log and SectionsToSave into UE's section
  persistence rules. Reapply before the next launch and verify B pause/Resume,
  then persistence across a relaunch; this is the likely reason logging kept
  disappearing, pending that test. No aiming or menu-size settings changed.
- Controller aiming confirmed after `dbf1633`. The original reticle remains
  head-locked. The visible mouse pointer follows gun aim but does not coincide
  with shot impacts; it must not be used as the accuracy reference. The user
  confirmed head rotation does not change shot grouping. Next reposition the
  original crosshair or replace it with a stereo reticle
  based on the actual firing ray/hit point, hiding only the old crosshair and
  preserving the rest of the HUD and working menu pointer.
- Heat-distortion test requested by the user: `r.DisableDistortion=1` has not
  been verified active; text and native Lua setter routes both failed. The user
  found other reports of excessive heat
  distortion, especially on large screens, and a now-withdrawn removal mod.
  Treat heat distortion as the first isolation target before the FXAA experiment.
- Main-menu regression after `313a7eb`: the 23:26 run loaded only credits/title,
  had no LogViewport transitions, and retained saved immersive mode. The aim
  bridge therefore activated on the title screen. The menu helper now also
  follows LogLoad/loading-screen messages, forces startup levels into screen
  mode, and publishes an explicit gameplay gate for aiming and snap turns.
  Restricted Lua checks cover saved immersive mode on the title, lobby entry
  without verbose capture logs, pause/Resume, and the existing aim/snap math.
  Menu access and controller aiming subsequently confirmed. Snap
  turning was observed by the user, but only from the title screen so far.
- Controller-directed aiming is working; HUD/marker projection work is deferred
  pending source access. The shimmer is visible in the desktop image too. The FXAA experiment
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
| 0 | Eliminate remaining ghosting and wavy, unstable imagery | Test r.PostProcessing.DisableMaterials=1 via startup INI against repeating upward-scrolling patterns. Check config logs before interpreting. Native Lua console API failed; FXAA experiment remains inactive. |
| 1 | Restore safe world/player discovery for the updated engine | Source access verified October 17; deferred while the current heat-distortion test is evaluated. Address the earlier `UEngine::get_world` crash before enabling dependent features. |
| 2 | Right-stick horizontal snap turn | Orientation bridge implements a 45-degree world-anchor latch; awaiting test. Stock snap remains disabled because it calls the unsafe world lookup. |
| 2 | Separate menu cursor movement from gameplay look input | Keep the working menu controls; stop JoyToKey mouse movement and vertical camera/HUD movement during immersive gameplay. Right-stick up/down should initially do nothing in gameplay. |
| 2 | Right-controller gun aiming and accurate reticle | Controller-driven gun aim and head-independent shot grouping confirmed. Align or replace the head-locked crosshair using the firing ray/hit point. Preserve HUD/menu controls. Full object-dependent aiming still needs safe discovery. |
| 2 | Controller pointer in game menus | Right-controller ray moves the menu pointer and trigger clicks. Replace stick-driven cursor movement; keep menu placement independent of hand direction. |
| 2 | Head-relative quest/location markers | Deferred with the SDK correction. Project markers using the headset view so aiming up/down does not move them inversely. Keep shot direction controller-driven. |
| 3 | Reticle and HUD presentation | Reduce the oversized reticle and keep HUD placement stable when looking around. Menu height decoupling confirmed after 07b58d9; marker projection remains separate. |
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
