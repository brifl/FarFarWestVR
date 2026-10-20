# Far Far West VR controls and backlog

Updated October 19, 2026. Changes stay in this profile repository; the isolated
UEVR backend uses the guarded source build installed by
`tools/deploy_native_backend.py`. Earlier binary patch tools apply only to the
previous backend; restore that backend before using them.

## Working baseline

- World scale default is 0.010000, matching the user's saved minimum-slider value.
  Native VR.hpp confirms the supported slider range is 0.01 through 10.0. The user
  reports the minimum removed ghosting and sharpened the image. Other runtime
  graphics settings differ from the repo and are preserved; do not infer a
  controlled comparison of world scale alone from that report.
- Stereo views align with symmetrical horizontal projection.
- Menus accepted after `9e94640`: readable, stationary, working cursor/control,
  and B pause/resume. The user reports "Much better" and is ready to move on.
  Screen textures survive resets; immersive play clears the cached menu layer.
- Quest X now activates F/X interaction prompts (confirmed in the saloon).
- Left stick movement, grips/spells, Y/weapon switching, and triggers/aim-fire
  were reported working. The user now confirms that gun aim follows the right
  controller. The user also confirms that shot grouping stays fixed when turning
  the head with the controller held still. The projected reticle is confirmed
  working at different ranges and with spells after `8a8e8b2`.
- The repeating upward-moving distortion is absent on the repeat test with
  `r.PostProcessing.DisableMaterials=1`. The October 17 01:17 startup log confirms
  the engine applied it; the same run reached the saloon with aiming and menu
  transitions working. Keep this workaround while checking gameplay effects.

## Continuation checkpoint

- NEW PLAYTEST REQUESTS (October 19): record only; no runtime settings changed.
  Tentative easiest-first order: expose third spell C through intentional D-pad
  shifting, resize the train mission preview, investigate reticle stepping,
  replace relevant input hints with VR labels/icons, investigate central vertical
  stretching, then correct train cinematic viewpoints. Inspect dependencies
  before implementation; preview size may depend on the cinematic camera.
  Backend VR.hpp confirms thumbrest + joystick shifting modes; repository default
  VR_DPadShifting=false. User has tested enabling it. Left Thumbrest + Right Joystick is a candidate, not an
  applied setting. Suppress our Lua snap-turn and native look/movement input on
  the shifted stick, and reconcile JoyToKey's existing D-pad G/middle-click
  bindings without duplicating native game actions. User reports existing D-pad
  actions when enabled: Left enters screenshot/photo mode (low priority), Up uses
  Utility (purpose unknown), Right opens the map (preserve), Down has no observed
  effect. Preserve these existing actions; Down is the candidate for third spell
  C after checking for a context-dependent native action. Do not treat all four
  directions as unused or guess what Utility does.
  Preserve grips/spells, interaction, pause/resume and controller menu pointing.
- OBJECT/LOCATION TAGS USER-CONFIRMED: "Tags stay anchored and follow the chickens."
  UI_ObjectPing_C is shared by BP_ObjectPing_Default_C and
  BP_ObjectPing_Animal_Chicken_C; match the BP_ObjectPing actor family rather than
  individual targets. Guarded fields: Image_Logo=824, Location=864; actor Widget=688,
  Scene=696. Widget attaches to Scene, then the actor root. Preserve the native
  relative offset (chickens use Z=64), icon, distance and target data. Each update
  transforms that saved local offset through the untouched parent's current
  transform, then uses the shared inverse-projection correction on the visual
  child only. This follows moving objects and preserves rotation/scale without
  feedback from the warped widget or delayed distance data. Parent/root/component
  identities are checked before writes; menus/reset restore the original offset.
  K2_GetComponentToWorld=96 and KismetMathLibrary.TransformLocation=144 were
  verified read-only in-game, including native/calculated positions agreeing.
  All 24 marker checks pass, including moving targets, rotated/scaled offsets,
  changed attachments and wrong component bindings. Live logs confirm two object
  tags use headset projection. tools/probe_reticle.ps1 -Pings is bounded/read-only;
  snapshots are on robot1-x at C:/src/uevr_far_west_build/ffw-tests/player-ping.json
  and player-ping-current.json. The ordered work queue below includes new requests.
- WATCH ONLY: October 19 user completed another mission/extraction with no issues
  and will report recurrence. The first successful extraction left the user looking at the island/train
  station after boarding and departure, with the same view on the desktop. No
  fatal error or new map/loading transition was logged. October 18 ~21:13:24
  PlayerArray index warnings also occurred at mission start, so they are not
  sufficient evidence of the cause. Read-only live state: controller StateName
  Inactive, Pawn/AcknowledgedPawn null; GameState hasFinishedMainObjective=true,
  amountPlayersSaved=1, hasFinishedMission=false. departCinematic points to
  LS_Tain_MissionExtract's AnimationPlayer, Status=0, OnFinished unbound.
  Those states may be normal while awaiting results; do not force mission flags,
  sequence events, rewards or travel. UEVR remained in immersive mode. User's F8
  test showed only a black screen with Version 0.2.0.20, not a summary; toggling
  produced no new errors. The clean repeat succeeded; no extraction fix is proven.
  Reticle exception logs now identify the
  operation that failed; no behavior changes. Bounded read-only snapshots are under
  C:/src/uevr_far_west_build/ffw-tests/extraction-state-2.json and
  extraction-departure.json. Reticle helper stopped safely at 21:13:31 with a
  caught native exception after pawn removal; inspect its cached pawn lifetime
  if this recurs, and reset scripts/relaunch before another gameplay test.
- IN PROGRESS (loaded and live-verified): user requests editable saturation/contrast
  multipliers, lower boss-health/mission-info HUD panels, and faster stabilization
  after loading. data/tuning.ini + libs/tuning.lua + scripts/tuning.lua provide
  bounded numeric INI reloads every second. Starting values: saturation=.95,
  contrast=1.10, fog-density=0; HUD fractions dialogue=-.10, boss=.08, mission=.10,
  compass=.10 (increased from .08 after the user requested a little lower)
  (positive down). Malformed/unknown/out-of-range values retain previous settings.
  Mission info also increased from .08 to .10 at the user's request; its control
  is independent of compass and boss health.
  Grading now supports saturation with neutral effective RGB when enabling an
  inactive native override, restores original flags/vectors, avoids compounding,
  and preserves different game-controlled grades. Fog scaling uses its captured
  native density, not its own previous result. New libs/hud_layout.lua reuses the
  screen-widget pixel basis for viewport-height offsets; dialogue_layout.lua is
  a compatibility alias. Confirmed loaded class metadata binds UI_Lifebar_Boss_C
  (ProgressBar_Boss=840), UI_Counter_C (Text_Title=816), UI_Timer_C
  (TextBlock_Seconds=816). User accepted compass and objective-info placement at
  .10: "It looks good now." Boss-bar visual acceptance remains pending. The compass
  uses UI_Player_C.Image_Compass=1008 plus Overlay_Pings=944; both share
  MovingCanvas, which also contains other HUD, so only these two children move.
  tools/probe_reticle.ps1 now has a bounded read-only -Hud mode for those widgets
  and UI_Player_C references, plus metadata for loaded but inactive HUD classes.
  Live weather ColorSaturation=(1.15,1.15,1.15,1), override=true; native contrast
  RGB=1.2/master=1 with the old accepted helper currently setting W=1.10. LumenPP
  has higher priority but overrides neither saturation nor contrast. New modules require
  a normal relaunch/Reset scripts to enter UEVR's module cache; do not double-run
  old/new grading factories live and compound the accepted contrast baseline.
  Marker discovery now uses an initial/new-object scan burst capped at 2 ms
  (8192 slots maximum), retains supported component candidates until their widget
  appears, binds hidden widgets early, and prioritizes newly appended object slots.
  All 19 marker checks and 7 tuning/graphics/HUD checks pass with lupa at
  PYTHONPATH=/tmp/ffw-lua-test. Lua syntax passes. No native build needed.
  Native ScriptState.cpp opens the os library and leaves os.clock available, so
  the time budget is supported. README documents the editable values and installed
  path. Commit 3d797a7 is pushed and pulled to robot1-x; existing runtime changes
  to config.txt/imgui.ini were preserved. The temporary read-only
  data/world_markers_dev.lua probe was removed. October 18 20:44 runtime logs
  confirm saturation master 1 -> .95 and contrast master 1 -> 1.10, with no
  compounding. Both compass children applied .08 and dialogue applied -.10;
  the user requests the compass a little lower, so its setting is now .10.
  Mission-info .08 was logged live at 20:54; its later .10 setting reloaded and
  was user-confirmed. Probe JSON persists at
  C:/src/uevr_far_west_build/ffw-tests/hud-probe.json and hud-names.json. The
  boss bar still needs later visual acceptance.
- Quest objective correction is USER-CONFIRMED: "Anchored; title and distance
  correct." The bounded read-only scan found UI_PingObjective_C on nine
  BP_ObjectivePing-derived actors, including main/TNT, arrival, extraction, NPC,
  lighthouse, boss and side objectives. Guarded fields: OwningActor=912,
  Location=872; sampled AttachComponent fields were null. Preserve these live
  widgets and target fields. Reuse the accepted Start Mission component path:
  project the widget's live Location through the eye, then inverse-project that
  pixel through the game camera to move only the visual child. Actor/root, live
  title/distance and target Location stay intact. This also works when the aiming
  camera points away from the marker. Mission UI_Guide_C on BP_TextGuide-derived
  actors uses that same path, with actor position as its true target. Resolve
  actor class rather than generated ChildActor instance names. Binding errors are
  contained to the affected component, restoring any partial changes.
  All 15 marker/interaction checks pass, including backward aim, updated objective
  targets, preserved title/distance, mismatched-actor rejection and generated guide
  names. Live logs confirm nine objective bindings, a mission guide, and successful
  projection without helper errors. Commit 2023004 is synced to robot1-x and the
  temporary data/world_markers_dev.lua was removed; the accepted correction stays
  active in memory and future launches load the committed implementation.
  Probe JSON persists on robot1-x at C:/src/uevr_far_west_build/ffw-tests/quest-probe.json.
- NPC interaction prompt correction is USER-CONFIRMED: "It worked." The user
  then entered a mission. The live read-only probe identified UI_Interact_C on the local
  pawn's unattached screen-space WidgetInteract component (Space=1). UI_Key is at
  816; text/description/progress are live children and must not be cloned. Native
  ProjectWorldLocationToScreen parameters=48 verified. world_marker_impl now
  tracks this family and applies only root render translation, retaining the
  game's world location, label, key icon, progress and visibility. The new shared
  libs/screen_widget_projection.lua converts the difference between native and
  final-eye projection through the widget's inherited pixel basis. Its position
  comes from fresh native projection, preventing feedback from stale/previously
  corrected cached geometry. Original translation/opacity restore on reset/menu;
  failed prompt writes restore locally without disabling vendor/mission fixes.
  All 11 marker/interaction checks pass, including both axes, changing world
  targets, 120 repeated updates with stale geometry, aim independence, visibility,
  failed native projection and partial-write cleanup. No native rebuild needed.
  The initial game shut down before the live correction loaded; the subsequent
  launch loaded the committed modules and the user confirmed success.
  A newly added Lua module is absent from the running loader's initial module
  cache; a live override would need to seed package.loaded or scripts reset.
  The read-only probe is retained on robot1-x at /tmp/ffw-interact-probe.json.
  User reports player pings have the same problem; that adapter is next after
  confirming NPC prompts. Reuse the shared correction, identify only its actual
  widget/world target when a ping is visible, and preserve accepted marker families.
- The themed menu cursor appearance is USER-ACCEPTED: "It looks so good." User's
  128-pixel PNG is retained unchanged as assets/menu_cursor.png; the duplicate
  256/512 sizes were removed with permission. Display height is viewport-scaled
  (48 pixels at 1440p, bounded 32-64); click hotspot is the top-left tip. The native
  Framework patch uses the existing RGBA font atlas, with a transparent gutter,
  and replaces only the game-menu cursor. Controller ray/click input, gameplay
  hiding and the UEVR panel cursor retain their working behavior. Missing image
  falls back to the standard cursor. Native build and PNG/alpha/color/atlas
  rebuild/hotspot/fallback smoke checks passed. Installer migration, repeat/restore,
  hash guards and failed-copy recovery passed. Public patch and smoke source are
  in native_patches; deployment hashes are in tools/deploy_native_backend.py.
- Contrast is USER-ACCEPTED at ten percent above the original (master W=1.10).
  User requested an increase from the initial five-percent test, then confirmed
  the more cartoon-like look and clearer detail. Native readbacks verified both
  1.05 and 1.10. scripts/contrast.lua + libs/contrast.lua preserve the accepted
  multiplier on active unbound BP_BlendableAtmosphere weather grading components.
  The sampled `postprocess` component had ColorContrast=(1.2,1.2,1.2,1), override
  enabled and blend weight=1; only W changes. RGB, saturation and flags stay native.
  The helper caches the original W to prevent compounding across frames, leaves
  different game-controlled W values alone, and restores its own value on reset.
  Existing higher-priority LumenPP does not override contrast; do not change it.
  The native IConsoleVariable path remains unusable; reflection works.
- The accepted helpers are committed as standalone autorun scripts. The game was
  closed after the contrast test and data/world_markers_dev.lua was removed;
  the old live payloads described below are historical, not active overrides.
  The next launch uses the committed dialogue/fog/contrast helpers normally.
- Distance haze is USER-CONFIRMED "looks good now" with primary ambient fog
  density zero. A 25-percent reduction (0.02 -> 0.015) had no visible effect;
  the controlled zero-density comparison identified the desired clear-distance
  appearance. scripts/fog.lua + libs/fog_density.lua preserve this tested setting
  on ambient BP_BlendableAtmosphere actors as levels/weather components load.
  They use reflected SetFogDensity, retain native values for script-reset cleanup,
  and leave secondary fog, lighting, color/contrast and other effects unchanged.
  Current temporary development override carries this factory through the stable
  marker callbacks for live verification. Remove it before pulling the standalone
  fog autorun, as with the dialogue helper; the in-memory instance stays active
  until the next reset/launch. Local payload /tmp/ffw-fog-live.lua.
  Live verification of the persistent factory logged ambient density 0.02 -> 0.
  User skipped saturation/vibrance because clearing the haze already helped.
  The accepted contrast increase is recorded above.
- Live view has one visible ExponentialHeightFog component on
  BP_BlendableAtmosphere_Afternoon_Heat_C: FogDensity=0.02 (offset 592), secondary
  density=0, volumetric enabled, extinction scale=1. SetFogDensity parameters=4
  verified. Native readback confirmed both 0.015 and the accepted 0.0 test.
  Do not use the IConsoleVariable interface:
  get_float returned a bogus denormal for r.Fog and r.VolumetricFog, while the
  engine log confirms the latter is 1. It also did not find r.FogDensity. This
  path remains incompatible; reflected properties/UFunctions work correctly.
- Conversation height is USER-CONFIRMED "perfect." UI_NpcTalk_C is the live
  dialogue panel; scripts/dialogue.lua + libs/dialogue_layout.lua raise its root
  render translation by one tenth of its cached local height, preserving the live
  text, name, choices and controls. This run measured 108 local units, equivalent
  to 144 pixels at the observed 1.333 DPI scale. Original translation is restored
  on script reset/headset deactivation/error; stale objects are not written.
  Native widget fields/geometry and SetRenderTranslation=16 parameters were read
  live before applying the change. Lua syntax and headset acceptance passed.
  During this session the stable marker loader carries both factories in memory
  through a temporary override; remove that file before pulling the new standalone
  dialogue autorun script to avoid duplicate helpers after a future script reset.
  Deleting the override keeps the accepted in-memory helper alive until reset.
  The accepted distance-fog change is recorded above.
- October 18: vendor markers AND Start Mission are USER-CONFIRMED anchored
  correctly on both axes, independent of aim, with the correct mission label.
  Do not clone UI_Guide_C: its actual TextBlock is updated separately from the
  InteractText field, and cloning showed the default "Interact" label. The helper
  now preserves the live widget, projects its actor's real location through the
  headset, and uses the engine's inverse screen projection to reposition only
  the visual child component. The Billboard root and mission actor stay fixed.
  The verified child offset is zero; guarded native parameter sizes are
  DeprojectScreenPositionToWorld=64, K2_SetWorldLocation/RelativeLocation=296.
  Pause/reset/error restores the original attachment offset and opacity.
  Native read-only projection round trip recovered exactly (1280,720).
  The current development override is the corrected full helper; remove it after
  pulling the committed implementation so future launches use the repo version.
- Marker checks now persist in tools/test_world_markers.py so credit interruptions
  do not lose them. Seven cases cover vendor projection, live text preservation,
  both head axes/aim independence, no accumulated warp, pause/reset, partial-move
  error cleanup, root-component rejection, visibility/stale camera/deprojection
  failure, and stale-object handling. Run with Python + lupa; this session used
  PYTHONPATH=/tmp/ffw-lua-test (lupa 2.8). Headset acceptance also passed.
- 19:15 live probe isolates the failure: get_bool_property throws for bVisible
  and bHidden, while get_property returns the correct booleans. All other marker
  reads, including owner/location/size/opacity/pivot, succeed. The helper now uses
  generic reads for those bitfields; the mock forbids the typed bool getter and
  all 12 checks pass. Corrected implementation is live in the development override.
  A temporary diagnostic logged runtime=false and hmd=false at 19:16; returning
  to the headset made both true and activated projection. Keep generic bitfield
  reads; no native rebuild is required for this failure.
- 19:05 retry also stopped before icon replacement, now during component
  inspection. The marker implementation is split into a factory module and a
  stable callback loader, so further reads/fixes can be tested without repeated
  launches. Optional profile/data/world_markers_dev.lua overrides the factory;
  it is ignored by Git and polled at 0.5s. Reload validates callbacks, restores
  the previous icons, then swaps handlers without registering more callbacks.
  Invalid overrides leave the current helper intact. Remove the development
  file after successful inspection; the next restart uses the committed module.
  A temporary read-only factory at /tmp/ffw-marker-read-probe.lua checks each
  relevant getter separately. It ran after the user's script reset.
  Canonical discovery now filters BP_WorldIcon actor owners before inspecting
  widget fields and uses the established generic getter / direct short name.
  Live-reload lifecycle/error checks pass alongside the marker fixture tests.
- The d778bc1 marker test retained old behavior because the helper stopped at
  discovery before tracking/hiding any icon (18:58 log: API verified, then
  `caught (...) exception`). API.hpp reveals get_objects_matching implicitly
  activates UObjectHook; that native path is still unsupported. Replace it with
  the reticle's proven direct array scan, bounded to 512 slots/tick, filtering
  the observed Widget components. Do not use get_objects_matching or
  get_first_object_matching in this profile until that activation path is fixed.
  The fixture now makes get_objects_matching throw and verifies chunked
  discovery succeeds without calling it. Failure logs now include the operation.
  The subsequent reflected-bool fix reaches icon tracking (see above).
- Active task: decouple location markers from controller aiming on BOTH axes.
  Live saloon probe identifies four UI_WorldIcon_C instances owned by screen-space
  WidgetComponents on BP_WorldIcon actors. Their world position comes from the
  component, not the empty UI_PlayerLobby ping collection. The normal world-widget
  screen layer uses LocalPlayer projection data, explaining camera/aim coupling.
  New `scripts/world_markers.lua` creates matching viewport widgets and positions
  them using the existing tested final-eye projection math. It copies brush/color,
  size, pivot and layer order, hides only original widget opacity, and restores it
  on menus/reset/error. Vendor components/actors are unchanged. The mission guide
  instead preserves its live widget and adjusts its visual child as described above.
  Actor/component visibility still gates the copies. Other marker families remain
  separate; vendors are confirmed and the lobby-guide addition is next.
- Marker helper mock checks pass backend/layout guards, head pitch AND yaw inverse
  projection, independence from gun direction, behind/offscreen/stale-camera hiding,
  original style, game visibility, pause/reset/error restoration, stale-object
  avoidance and sizing icons outside the gun camera. Harness:
  `/tmp/ffw-test-world-markers.py`, with Lupa at `/tmp/ffw-lua-test`.
  Live native function signatures were checked read-only before deployment;
  e.g. Create=32, SetPositionInViewport=24, SetBrush=176, component location=24.
  Headset validation is next; no additional native rebuild is needed.
- `tools/probe_reticle.ps1 -Markers` now performs the narrowly targeted read-only
  world-icon/component lookup, including reflected properties/function sizes.
  Last result `/tmp/ffw-worldicon-probe.json`: about 10 MB / 0.54 seconds. Instance
  addresses are per-process. Relevant fields: WidgetComponent Space=1512,
  WidgetClass=1520, Pivot=1568, Widget=1800; UI_WorldIcon.Image_Icon=808.
- Controller pointing in title/pause menus is confirmed after `001206f`. The backend now feeds
  the existing OpenVR menu-quad ray hit into absolute Windows mouse movement,
  only in 2D screen mode, with controllers active and the game window focused.
  Existing JoyToKey trigger clicks remain. Normal/shifted right-stick mouse
  bindings are disabled (0xFF); native stick/snap input remains. Native patch:
  `native_patches/menu_pointer.patch`, applied to the retained source checkout.
  The incremental Windows build passed; installer migration/restore/failure
  checks passed. The user confirms menu targeting/clicks and return to gameplay.
  The live log also confirms the native menu-pointer path is active.
  No menu-plane placement or reticle code changed.
- The user confirms the `9115d41` cursor fix works: no extra gameplay mouse
  pointer, and the cursor returns for menus.
- Reticle alignment is confirmed by the user at different ranges and for
  spells. The live 18:20 October 17 log verifies compact-array discovery,
  widget/function metadata, 2560x1440 viewport calibration and active projection.
  No reticle helper exception was logged. The existing RemapControls shift
  warning and old UObjectHook JSON errors remain separate backlog items.
  The menu helper now toggles FrameworkConfig_AlwaysShowCursor with its
  presentation state to remove the redundant gameplay pointer while preserving
  menu pointing. Transition/reset fixture checks and headset confirmation passed.
- The existing Crosshair_Top image now follows controller-driven
  shots. `scripts/reticle.lua` traces the pre-stereo firing camera on the game
  thread and projects the target through the final eye camera. It calibrates
  the image's actual viewport geometry, preserves its material/spread, and
  restores translation/opacity in menus or on reset. Menu/input behavior and
  quest markers are separate. Range/spell testing passed.
- Native backend `ffw-ue58-sdk-v1` builds successfully with the installed Visual
  Studio 2026 tools on robot1-x. Persistent source/build checkout:
  `/mnt/c/src/uevr_far_west_build`, pinned UEVR 4ee5c6b and private UESDK
  14478df. Do not reset it: source corrections are uncommitted there. Private
  source/patch cache: `/home/brifl/.cache/ffw-native/`. Keep it out of this repo.
  `prepare_sources.py` predates the final Lua projection/API wrapper changes;
  use the retained checkout and final patches instead of rerunning it blindly.
- Modern object layout is repaired coherently: FUObjectArray starts with its
  compact chunked array; 24-byte FUObjectItems contain refcount/flags/object/
  serial/cluster at 0/4/8/16/20, with unreachable/garbage bits 28/21. Discovery
  checks the exact game timestamp/image size, known RVA, bounds and four object
  indices before allowing SDK access. Native Windows and Linux layout fixtures
  passed count/index/chunk-boundary/metadata tests.
- The source build retains the accepted Slate/view-extension bypass, both-eye
  fallback pose refresh, full-width screen copies/textures, aim-pose access
  and UE5 double camera ABI. It adds active-eye projection selection (-1) and
  a bounds-checked Lua matrix getter. Hash-guarded deployment preserves the
  previous DLL/PDB in `.before-ue58-sdk.bak` files. Never apply old binary
  patch offsets to this source build.
- Reticle math tests passed head pitch/yaw, eye parallax, offscreen/behind
  targets and scaled/rotated parent geometry. Lua mock checks passed old-backend
  gating, probe mode, projection, menu/reset restoration, stale camera hiding,
  recycled-object avoidance and contained metadata/callback errors. These
  supplement the successful live SDK discovery and wall-shot test. Test harness:
  `/tmp/ffw-test-reticle-helper.py` (Lupa at `/tmp/ffw-lua-test`). Installer
  fixtures also passed apply/restore/idempotence and failure/unknown-file guards.
- Read-only live probe identifies UI_Player_C.Crosshair_Top at 0x480; Image/
  Widget Slot 0x30, RenderTransform 0x90, Pivot 0xc8, Visibility 0xdd and
  RenderOpacity 0xe0. FField Next/Name are 0x18/0x20; property offset/element
  size are 0x44/0x34. Results: `/tmp/ffw-reticle-properties.json` and
  `/tmp/ffw-reticle-probe.json`; addresses are per-process, never reuse them.
- Repeat restart (18:19 October 17) confirms
  `LogConfig: Set CVar [[r.PostProcessing.DisableMaterials:1]]` from per-game
  `FarFarWest/Config/UserEngine.ini`; that file survives into the saloon.
  The override persisted without preparation. Generated Saved/Config Engine.ini
  was repeatedly deleted and is no longer used. The workaround removes all
  custom post-process materials; damage/status effects still need assessment.
  Reapply `python3 tools/prepare_menu_helper.py --material-test` only when the
  preset changes. The failed native console-setter experiment remains inactive.
- Head-relative markers need both horizontal and vertical correction. Validate
  the UI_WorldIcon helper first; other quest/ping families may need their own
  world-target adapters. Preserve controller firing and accepted menu placement.
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
  The subsequent startup custom-material override reduced or removed the pattern;
  do not activate the FXAA experiment on top of this result.
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
  while easier fixes are addressed; source access is now restored. The shimmer
  was visible in the desktop image too. The FXAA experiment
  was never deployed and is retained in `experiments/temporal_aa_test.lua`, outside
  autorun scripts. Only the custom post-process material startup override is active.
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
  `python3 tools/prepare_menu_helper.py --material-test` on robot1-x before the next launch.
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
  This remains the current default; an intentional four-direction action layer
  is now queued below with explicit input-conflict handling.

## Work queue

Start Mission is confirmed fixed. Take the new requests in the following initial
order, based on expected effort; adjust when inspection reveals a dependency.
Use one focused visual change/test at a time and preserve working controls.

| Order | Improvement | Acceptance condition / constraint |
| --- | --- | --- |
| Done | Anchor Start Mission | User confirms correct label and anchoring on both axes. Live UI_Guide_C is preserved; only its visual child is reprojected, with actor/root unchanged. |
| Done | Make the tested minimum world scale the default | Repo VR_WorldScale=0.010000 matches the saved working profile. Native slider minimum verified as 0.01. User reports ghosting gone and sharper imagery; preserve other runtime adjustments. |
| Done | Raise conversation text | User confirms "perfect." Live UI_NpcTalk_C panel is raised by one tenth of its local viewport height; text/name/choices/input and headset coupling are preserved. |
| Done | Reduce distance fog/dust | User accepted zero primary ambient fog density after 25-percent reduction was imperceptible. Apply the tested setting to BP_BlendableAtmosphere fog components; preserve secondary fog, other rendering settings and the heat-distortion workaround. |
| Skipped | Increase color saturation/vibrance slightly | User chose to skip this after the accepted haze change improved the image. |
| Done | Increase contrast slightly | User accepted ten percent above original after comparing five percent. Preserve native RGB/color balance and saturation; user reports the desired cartoon look and clearer detail. |
| Done | Use the themed menu cursor | User accepted its headset appearance: "It looks so good." assets/menu_cursor.png is the unchanged user-authored 128-pixel arrow; unused duplicate scales removed with permission. Native overlay displays it at 48 pixels high at 1440p with a top-left hotspot. Native checks passed; controller pointing/click logic and gameplay cursor policy are unchanged. |
| Done | Correct the NPC “Press X” prompt | User confirmed "It worked" and proceeded into a mission. Shared screen-widget translation preserves live text/key/progress and native world location/X behavior. |
| Done | Anchor quest objective markers | User confirmed anchoring with title and distance correct. UI_PingObjective_C and mission UI_Guide_C reuse the live-label component correction, preserving target data and actor roots. Fifteen checks pass. |
| Done | Stabilize object/location tags (right-stick ping) | User confirms tags stay anchored and follow moving chickens. UI_ObjectPing_C on the BP_ObjectPing actor family preserves native icon/distance and attachment offsets using the shared visual-child correction. |
| Next | Third spell through shifted D-pad Down; preserve existing actions | Third spell is currently C. When shifting is enabled, user reports Left = photo mode, Up = Utility (purpose unknown), Right = map, Down = no observed action. Preserve existing actions and verify Down is free in relevant contexts before assigning C. Reconcile JoyToKey G/middle-click mappings with native inputs to avoid duplicate actions. Suppress normal movement/look/snap turns on the shifted stick; preserve grips/spells and menus. |
| 2 | Resize the train mission-preview screen | User cannot read the oversized preview. Identify its widget or in-world screen during the ride, then adjust only its scale/placement. Keep main/pause menus unchanged; if the apparent size comes from the cinematic camera, address that dependency first. |
| 3 | Investigate reticle stepping | Reticle appears to snap to a grid and makes aiming look like low FPS. Identify whether input sampling, projection timing, pixel rounding, or UI placement quantizes it; preserve the confirmed shot alignment at different ranges and with spells. |
| 4 | Show VR controls in action hints | Replace relevant keyboard/gamepad hint text or glyphs with the actual Quest controls, including interact, spells and shifted actions. Preserve context, live labels and hold-progress behavior. Inspect the hint binding first; Lua FText access is limited, so a narrow native text/glyph bridge may be needed. Avoid global string replacements. |
| 5 | Investigate central vertical stretching | User reports a fisheye-like effect: the center is stretched vertically more than the top/bottom. Compare a fixed scene/grid in headset and desktop, and distinguish world rendering from curved menu presentation. Check projection/aspect/copy geometry before changing settings; preserve accepted eye alignment, full-width rendering and reticle/marker projection. |
| 6 | Correct train cinematic viewpoints | Ride viewpoint seems displaced relative to 2D. Inspect the game's active cinematic camera and our camera/aim offsets during the sequence. Match the intended camera position while preserving headset look and restore normal aiming afterward. Keep this separate from the extraction stall, which did not recur. |
| Later | Other-player and remaining marker families | Reuse shared projection where applicable; inspect only their widget/world-target binding when visible. Preserve visibility, labels, distance indicators and any edge clamping. No separate full debugging effort for every individual marker. |

Earlier items remain below; the new ordered queue takes precedence after the
current mission-marker fix.

| Priority | Change | Acceptance condition / constraint |
| --- | --- | --- |
| 0 | Retain the distortion workaround and assess remaining artifacts | Startup r.PostProcessing.DisableMaterials=1 verified; user confirms no distortion on the repeat launch. Check gameplay effects before narrowing to the offending material. Other ghosting is not separately assessed; FXAA remains inactive. |
| 1 | Restore safe world/player discovery for the updated engine | Source access verified October 17; deferred while easier fixes are addressed. Address the earlier `UEngine::get_world` crash before enabling dependent features. |
| 2 | Right-stick horizontal snap turn | Orientation bridge implements a 45-degree world-anchor latch; awaiting test. Stock snap remains disabled because it calls the unsafe world lookup. |
| 2 | Separate menu cursor movement from gameplay look input | Keep the working menu controls; stop JoyToKey mouse movement and vertical camera/HUD movement during immersive gameplay. Right-stick up/down should initially do nothing in gameplay. |
| Done | Right-controller gun aiming and accurate reticle | Controller aim, head-independent shot grouping and projected crosshair confirmed, including different ranges and spells. |
| Done | Controller pointer in game menus | Controller targeting/clicks and return to gameplay confirmed after 001206f. |
| Done | Saloon location markers | Vendors and Start Mission confirmed anchored correctly with the original mission label. Quest/player marker families remain queued. |
| 3 | Reticle and HUD presentation | Reduce the oversized reticle and keep HUD placement stable when looking around. Menu height decoupling confirmed after 07b58d9; marker projection remains separate. |
| 3 | Simplify the input layers | Audit JoyToKey plus RemapControls, their overlapping native gamepad inputs, grip-shift behavior, and RemapControls' repeated invalid-shift warning. Preserve working actions. |
| 4 | Choose stick-click actions | Left click currently produces a forward leap/dash; right click produces a multiplayer ping. Decide desired assignments before changing them. |
| 4 | Raise dialogue subtitles/text | Promoted to the ordered queue above. |

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
| Shift modifier + stick direction | Preserve photo mode (Left), Utility (Up), map (Right); third spell C proposed on Down | Existing actions reported when enabled; Down is only apparently free. Confirm modifier and prevent duplicate actions/movement/look/snap conflicts |
| Left trigger | Aim | Preserve action; sight/reticle alignment queued |
| Right trigger | Fire; click in menus | Preserve working behavior |
| Left/right stick click | To be decided | Dash/ping observed; unchanged |
