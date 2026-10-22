# Development and deployment

Commands below run from the repository root. The documented deployment paths
refer to the existing WSL installation on robot1-x.

See the [README](../README.md) for completed features and controls,
[BACKLOG.md](../BACKLOG.md) for open work, and the
[loose-hands design](LOOSE-HANDS.md) for the planned experiment.

## Working environment

- Profile on robot1-x: `/mnt/c/Users/brian/AppData/Roaming/UnrealVRMod/FarFarWest-Win64-Shipping`.
- Isolated UEVR runtime: `/mnt/c/Manual Installs/uevr_far_west/`.
- Retained source/build checkout: `/mnt/c/src/uevr_far_west_build`.
  Build artifacts are in `build/bin/uevr`; focused probes are in `ffw-tests/`.
- Last recorded source bases: UEVR `4ee5c6b`, private UESDK `14478df`.
  The retained checkout contains local compatibility fixes. Preserve those edits;
  verify the current tree before building, and do not reset it or rerun the older
  source-preparation script over it. Private source/patch cache is recorded at
  `/home/brifl/.cache/ffw-native/`; keep private engine material outside this repo.

robot1-x's SSH workflow executes scripts sent on stdin; command arguments are
not reliable. For example:

```bash
ssh -T -o BatchMode=yes -o ConnectTimeout=10 robot1-x <<'REMOTE'
set -euo pipefail
cd /mnt/c/Users/brian/AppData/Roaming/UnrealVRMod/FarFarWest-Win64-Shipping
git -c core.autocrlf=true pull --ff-only
REMOTE
```

Use `git -c core.autocrlf=true` for this checkout. Give Windows executables
`< /dev/null` inside SSH scripts so they cannot consume the remaining script.
Preserve user/runtime changes to `config.txt`, `imgui.ini`, and personal tuning.

## Native access constraints

The backend tag is `ffw-ue58-sdk-v1`; observed games 0.2.0.20 and 0.3.0.0 use
UE5.8.1 CanyonEngine. Guard reflected layouts and function parameter metadata
before native calls. Old binary-patch tools target the previous backend, not
this source build.

The Fear Fear West release on October 22 initially disabled all SDK-dependent
helpers because the backend deliberately rejected an unvalidated executable.
The retained SDK source now selects an explicit compact-array address per build;
unknown executables still fail closed. Read-only process inspection verified
object identities, names, chunk-boundary indices, UI_Player.MovingCanvas at 960,
and CanvasPanelSlot.LayoutData at 56 in 0.3.0.0. First-backend startup confirmed
object access, reticle tracing, marker aspect correction, and fixed HUD placement
running in 0.3.0.0. Controller menu pointing and visible health/cooldown groups
are confirmed; remaining visual regressions still need validation. Compatibility
fixes also cover the shifted UI_Key/UI_Spell_CardSlot layouts, the renamed
F_RefreshKey.bIsGamepad parameter, and lowercase PostProcessComponent.settings.
Do not loosen Lua layout assertions to bypass this gate.

| Game | PE timestamp | Image size | Object-array RVA | Name-pool RVA |
| --- | --- | --- | --- | --- |
| 0.2.0.20 | 907750432 | 203960320 | 0xad3d980 | 0xac9b900 |
| 0.3.0.0 | 1404130593 | 207814656 | 0xb08f680 | 0xafed600 |

`tools/probe_game_layout.ps1` finds these tables read-only within the executable's
bounded .data section, checking unique candidates and UObject/name identities.
`tools/probe_reticle.ps1` supports both verified builds. Native source and private
SDK patches remain in the retained build checkout; the profile repository contains
deployment tooling and artifact hashes, not those private sources.

- Use the engine supplied to an engine-tick callback and its native GameViewport
  as world context. Verified viewport offset is 3448; native GameplayStatics
  GetPlayerController is the accepted route to the current player controller.
  SDK `UEngine::get_world`, SDK player-controller/local-pawn helpers, and
  discovery calls that activate UObjectHook remain unsuitable here.
- Avoid `get_objects_matching`, `get_first_object_matching`, and `api:to_uobject`
  until their hook path is validated. Use bounded direct compact-array discovery
  or the already-verified native widget query for appropriate UI classes.
  UObject array offset 0, item stride 24, and object index at offset 12 are the
  verified compact layout. Validate index/address/name before reusing a reference.
- Re-read the current pawn/equipped item through possession changes. A cached
  pawn in a trace caused the earlier dismount freeze; the reticle now resolves
  its current owning pawn on each update and handles no-pawn gaps.
- Native setters may require typed values from their matching getters. A named
  Lua table did not round-trip SetControlRotation; the typed GetControlRotation
  result does. Likewise obtain typed FVector2D temporaries for widget setters.
  Generic reflected boolean reads work where typed get_bool_property threw.
  The custom controller pose bridge was prepared for aiming; verify grip/aim
  pose meaning before using it to attach a hand or weapon.
- Lua file access is confined to profile/data and `os.getenv` is unavailable.
  New modules require normal script loading/reset; require paths in callbacks
  do not necessarily match their paths during initial load.
- Restore only owned changes on valid objects, respecting subsequent native
  updates. Keep marker actor targets/root transforms separate from corrected
  visual children and avoid per-eye gameplay mutations.

## Tuning and accepted behavior

Personal tuning is in [data/tuning.ini](../data/tuning.ini). On robot1-x, edit
`C:\Users\brian\AppData\Roaming\UnrealVRMod\FarFarWest-Win64-Shipping\data\tuning.ini`.
Numeric edits reload while playing, about once a second. After installing new
helper code, use a normal game relaunch. The user reports that **Reset scripts**
commonly breaks the current session; do not use it as the routine update workflow.
Keep script-reset recovery as an open issue rather than requiring repeated resets.

| Section | Setting | Profile value | Meaning |
| --- | --- | --- | --- |
| graphics | saturation_multiplier | 0.95 | Five percent less saturation; 1.0 uses the native amount. |
| graphics | contrast_multiplier | 1.15 | Preserved installed preference; 1.0 uses the native amount. |
| graphics | fog_density_multiplier | 0.20 | Current reduced-haze setting; 1.0 uses native density. |
| hud | dialogue_offset_y | -0.10 | Raise conversation text by ten percent of viewport height. |
| hud | boss_health_offset_y | 0.15 | Preserved installed boss-bar offset. |
| hud | mission_info_offset_y | 0.15 | Lower mission counters and timers by fifteen percent. |
| hud | compass_offset_y | 0.15 | Lower the compass background and marker overlay together by fifteen percent. |
| hud | scale_multiplier | 0.85 | Fixed HUD size, separate from projection-aspect correction. |
| hud | aspect_correction | 1 | Correct fixed HUD vertical stretch using the active eye projection. |
| hud | left_margin / right_margin | 0.20 / 0.20 | Independent horizontal edge insets for selected fixed HUD groups. |
| hud | top_margin / bottom_margin | 0.15 / 0.30 | Independent vertical edge insets. |

HUD offsets use the full viewport height: positive moves down, negative moves up,
and zero restores the original position. Saturation accepts 0–2, contrast 0.5–2,
fog 0–1 and HUD offsets -0.5–0.5. Invalid edits retain the previous values.
The boss-bar and mission-counter controls apply as those widgets appear; their
height can be tuned during later fights/objectives without restarting scripts.

`libs/hud_margins.lua` uses a guarded native query for UI_Player_C (including its
lobby subclass), then selects disjoint direct children of MovingCanvas:
HB_Spells, HB_JokerCooldown, HB_Moneys, VerticalBox_PlayerHealths,
HorizontalBox_1 (health/shield), and VerticalBox_0 (weapons/ammo). It also selects
UI_Equipment_PlayerStats (level/currency) and VB_Lobby (corner hints) under the
verified NamedSlot_216/CanvasPanel_86 chain. It never shifts MovingCanvas or
individual inventory children. `libs/hud_safe_area.lua` clamps full
group bounds using CanvasPanelSlot.LayoutData at 56 and the parent geometry's
pixel basis. It does not feed corrected child positions back into placement.
The stereo callback caches only eye projection values; the engine tick uses
`ui_shape.height_factor` for aspect correction. Each group's native scale is
multiplied by scale_multiplier on X and scale_multiplier * height_factor on Y,
with its existing pivot preserved. Bounds and packing use these planned scales
before native writes. This fixes the newly visible fixed HUD's stretch without
scaling reticles, markers, or full-screen effects a second time.
Only fixed anchors without rotation/shear are supported; other layouts stay
native. Groups sharing a HUD root are then packed without overlap where space
permits, prioritizing health, spells, cooldowns, and ammo before other panels.
The measured seven-group layout fits inside 20% horizontal/30% vertical margins.
Owned scale and translation restore independently on menus/reset; native animation
changes become the new baseline. Size accepts 0.25–1.50, aspect correction is 0/1,
and margins accept 0–0.4. Both edges at zero restore native placement on that axis;
size/aspect remain independent. Explicit HUD edges override legacy HUD axis pairs,
which override legacy audit axis pairs, regardless of INI ordering. Monitoring
records and flags the same four edge margins. Numeric edits reload live.

The user confirmed improved fixed-HUD proportions and separated cooldowns, but
the corner control hints still rendered doubled. A read-only scan found one hint
panel with separated rows. Bypassing UI_Player's RetainerBox_0 live eliminated
the duplication. `libs/hud_retainer.lua` applies that bypass only in gameplay,
using the existing widgets and preserving the normal renderer for menus. It
requires the DPIScalerBox_2 parent chain, bRetainRender at 400, EffectMaterial at
416 with the exact MI_CurvedUI asset, and SetRetainRendering's one-byte parameter
bInRetainRendering at zero. Ownership and compact-array identity checks restore
only a valid retainer's owned flag; unrelated materials/retainers stay native.
The test identifies the retained/curved rendering stage, not the material alone.

Marker discovery front-loads the initial and newly allocated objects within a
two-millisecond scan budget. Known components are retained while their widgets
load, and hidden markers are prepared before they become visible. This reduces
the former multi-second scan delay without a blocking full-array sweep.
`libs/marker_discovery.lua` also queries the verified ObjectPing, WorldIcon,
TextGuide, and Player actor families every 50 ms, then gets their native widget
components. This catches tags allocated into reused UObject slots without waiting
for array-count growth or a background pass. Native metadata was measured:
GetAllActorsOfClass is 32 bytes (world 0, class 8, output 16), and
K2_GetComponentsByClass is 24 bytes (class 0, return 8). Queries are bounded to
128 actors per family and 16 widget components per actor; a failed fast path
leaves the existing array discovery active. Widget construction time remains
outside the helper's control.

Reticle and marker shapes use `libs/ui_shape.lua` to compensate for unequal
horizontal/vertical pixel-to-eye scaling. The height factor is
`abs(projection[1][1]) * viewport_height / (abs(projection[0][0]) * viewport_width)`;
it follows the active eye projection and resolution instead of a fixed preset.
The measured 2560x1440 setup needs about 0.64684. The user confirmed a round,
aligned reticle and improved marker appearance. Existing world-to-screen centers
are unchanged. Marker visuals scale around their component attachment pivot;
reticles retain their center pivot. Non-unit original scales that make a pivot
change unsafe are skipped. Original transforms are restored for menus/reset,
with external game changes preserved. World rendering and menu sizing are unchanged.

The HUD helper also keeps the dialogue's Next hint on Quest X. JoyToKey sends F
for X, which can make the game select keyboard presentation during a conversation.
`libs/dialogue_hint.lua` uses the existing tracked `UI_NpcTalk_C`, finds its
`UI_Key_C` child in `HorizontalBox_NextKey`, and calls the native
`F_RefreshKey(true)` only when its interaction hint switches away from
the gamepad icon. Shared `libs/interaction_key.lua` preserves Text_Hold visibility
and validates either verified isGamepad/bIsGamepad parameter name at offset zero,
and leaves unrelated or explicitly overridden actions alone. The separate
`interaction_hints.lua` helper uses the same correction across native UI_Key_C
widgets, including targeting and dropped-item contexts. `libs/live_widgets.lua`
centralizes guarded native queries and compact-array lifetime checks for this
helper and HUD margins. No UObjectHook discovery, FText bridge, binding changes,
or backend rebuild is required.
The read-only UI audit uses the same hint-layout guard; its former hardcoded
0.2 offsets caused captures in 0.3.0.0 to stop at the 64-error budget.

`scripts/spell_hints.lua` handles the joker vendor's three spell-slot rows. A
guarded native query finds only `UI_Spell_CardSlot_C` widgets; their ID and
`actionKey` must agree before applying a label. The existing key image displays
`assets/control_hints/{left_grip,right_grip,both_grips}.png` at the native hint
height. Q/SpellA is LG, E/SpellB is RG, and C/SpellC is LG+RG. The asset directory
is resolved beside the loaded profile scripts, so it follows profile installation.
Unreal imports the textures through its own `ImportFileAsTexture2D` function.
Native input-mode changes can rebuild the key row, so the helper reads its current
children instead of retaining old key widgets. It preserves selection bindings
and leaves the separate gameplay cooldown hints unchanged.

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

Accepted controller aiming is implemented in
[scripts/controller_aim.lua](../scripts/controller_aim.lua). Right-controller
orientation drives typed native control rotation while head direction remains independent;
older backends retain analog fallback.
Horizontal right-stick deflection requests one 45-degree snap turn, rearmed at
center. The existing menu controls are preserved. Gun position/hand attachment
is still queued. The projected crosshair is confirmed aligned at different
ranges and with spells. The menu helper hides UEVR's extra mouse cursor in
immersive gameplay and restores it for menus.
Aiming and snap turns require a loaded gameplay level; menus cannot activate them.
`libs/aim_stabilization.lua` filters controller yaw/pitch with a time-based
exponential response, shortening its time constant as angular speed increases.
`[aim] stabilization` accepts 0–1, starts at 0.35, and reloads live. Zero bypasses
the filter. Filtering occurs before adding the world/snap anchor, with shortest
yaw-wrap interpolation, one sample per engine tick, and resets across menus,
tracking/controller changes, and long frame gaps. It does not change shot traces
separately from aim, or smooth headset movement/menu input.

The new carried pig advertises IA_Drop, bound separately from IA_Interact.
`libs/carry_drop.lua` resolves the current pawn/items/equipped object on each tick,
checks BP_Player.AC_PlayerItems at 1768, equipedItem at 208, UI_ItemContext at
1120 and item.OwningPlayer at 736. Only a visible UI_DropItem_C context with a
descendant IA_Drop key enables X. The native 0.3 event
InpActEvt_IA_Drop_K2Node_EnhancedInputActionEvent_14 is 48 bytes (ActionValue 0,
ElapsedTime 32, TriggeredTime 36, SourceAction 40). A fresh Quest AButtonLeft/X
press calls that entry with a typed Boolean value from the native
MakeInputActionValueOfType, preserving the game's permission/replication path.
Only the hint's gamepadKeys presentation is temporarily set to IA_Interact for
its X icon; its action and normal keyboard/X-to-Interact mapping stay intact.
Hold presentation is preserved. Guns, menus, missing prompts, and held buttons
across transitions do not invoke Drop. Unknown layouts stop this helper alone.
The user confirmed the live pig test drops correctly and displays X; the permanent
helper loads on a normal relaunch.

Menu pointing now uses the right controller's ray intersection with the existing
screen. Move/rotate the controller to move the pointer and use the right trigger
to click. JoyToKey's stick-to-mouse movement is disabled in both grip modes;
gameplay snap turns keep their native stick input. This requires the latest
isolated backend below and is confirmed working. The game window must have
focus. Menu placement, B pause/resume and gameplay aiming are preserved.

The Fear Fear West release supplies a native menu cursor. Preserve the menu
helper's FrameworkConfig_AlwaysShowCursor policy: it also controls overlay
intersection/input and SetCursorPos handling. Turning it off broke menu pointing.
The backend now sets ImGui MouseDrawCursor only for UEVR's own panel and omits
the themed arrow draw call, suppressing graphics independently of input policy.
The previous asset remains available. The new DLL requires a game restart.

In 0.3.0.0 the game's software cursor was invisible in both desktop and VR,
despite bShowMouseCursor=true; clicking briefly exposed it. CommonUI cursor cvars
were already enabled. `libs/native_cursor.lua` draws a viewport copy of the native
UI_Cursor_C asset during menus, leaving input policy and ray movement alone. Its
internal canvas translates the image by 32 pixels, so centered viewport alignment
is required; the user confirmed the cursor tip aligns with highlighted buttons.
Viewport-local mouse coordinates must not have DPI scaling removed a second time.
Only the owned copy is removed for gameplay, UEVR's panel, inactive headset,
viewport changes, errors, and script reset. Native metadata and object identities
are guarded; the older game with no cursor asset simply skips this helper.
Bounded native widget queries also hide the original UI_Cursor/UI_Cursor_Hand
copies with owned opacity changes, restoring them when the helper is inactive.
This targets gameplay flashes without changing input flags; the remaining
elongated gameplay cursor needs a live reproduction to identify its actual path.
The menu copy uses live `[cursor] scale_multiplier` (1.0) and
`aspect_correction` (0). The user confirmed its menu proportions were already
correct; applying the immersive eye-projection correction squashed it in screen
mode. Keep that correction off by default and inspect the gameplay variant
separately. Scale changes preserve the centered hotspot.

The isolated backend now uses a source build with the modern UE5.8 object
layout and the accepted rendering/aim compatibility fixes. After pulling this
profile on robot1-x, deploy its verified DLL/PDB while the game is closed:
`python3 tools/deploy_native_backend.py apply`.
The build artifacts live in `C:/src/uevr_far_west_build/build/bin/uevr`.
The installer preserves the prior pair; `restore` reinstates it. Older binary
patch tools require that prior backend and cannot patch the source build.
The cursor source change is in [native_patches/menu_cursor.patch](../native_patches/menu_cursor.patch);
[its native smoke test](../native_patches/tests/menu_cursor.cpp) checks PNG decoding,
atlas rebuilds, alpha/color preservation, the hotspot and missing-image fallback.

[scripts/reticle.lua](../scripts/reticle.lua) validates the backend identity,
widget layout and function metadata before moving the original crosshair to
the firing-camera trace target. It restores the crosshair in menus and leaves
quest markers alone. For a read-only geometry probe, put `probe` in the
profile's `data/reticle_mode.txt`; remove the file to enable movement again.

The repeating upward-moving distortion is absent on the repeat test with the
startup override `r.PostProcessing.DisableMaterials=1`, confirmed in the live
game log. This suppresses all custom post-process materials; the exact offending
material remains unidentified. Check damage/status effects during further play.
The prepared FXAA experiment is retained outside the autorun scripts in
[experiments/temporal_aa_test.lua](../experiments/temporal_aa_test.lua).

The configurable haze reduction is applied by [scripts/fog.lua](../scripts/fog.lua).
It scales captured native primary density on the game's ambient weather components
as they load. A value of zero was accepted during testing; the current profile
uses 0.20 after personal tuning. A 25-percent reduction was imperceptible. Script reset restores captured native
density values before the helper reloads. Other atmosphere layers keep their settings.

[scripts/contrast.lua](../scripts/contrast.lua) applies configurable contrast and
saturation multipliers to weather grading. The accepted contrast increase remains
the default. Native RGB balance is preserved; a previously inactive saturation
override starts from neutral RGB. Its original vector/override flags restore on
script reset, and repeated updates do not compound the multipliers.

Accepted location-marker correction is implemented in
[scripts/world_markers.lua](../scripts/world_markers.lua). It displays copies of the
saloon's `UI_WorldIcon` markers at their world positions projected through the
headset camera. Looking up/right moves a fixed-world marker down/left; controller
aiming cannot change its position. The originals are hidden only during immersive
play and restored for menus or script reset. Other marker families are separate.

NPC interaction prompts use the same headset projection while keeping the
game's live text, key icon and hold-progress display. Only the prompt's visual
translation changes; its world target and X interaction remain native. The
shared screen-widget correction also supports further marker adapters.
NPC placement is confirmed working.

Mission objective markers and text guides retain their live title/distance widgets
and use the same visual-child correction as Start Mission. Objective target data
and actor roots remain in place; controller aiming cannot move their headset
projection. The user confirms quest markers stay anchored with correct title and distance.

Object/location tags (`UI_ObjectPing_C`) reuse that correction across the
`BP_ObjectPing` actor family. The tag's original local offset is transformed
through its unchanged parent each frame, preserving height, rotation and scale
while following moving targets. Native icons, distances and target data remain
intact. The user confirms tags stay anchored and follow tagged chickens.

## Monitoring and retained diagnostics

UI monitoring is ongoing. [UI-AUDIT.md](UI-AUDIT.md) documents per-launch capture,
the automatic session ledger, and incremental collection across sessions;
[UI-FINDINGS.md](UI-FINDINGS.md) contains the cumulative candidate dictionary.
Use `python3 tools/ui_audit.py collect` at check-ins. Keep historical candidates
separate from current coverage; absence in a later capture does not prove a fix.

The October 22 collection contains four sessions, 6,227 distinct IDs, 509 edge
candidates, seven uncovered marker families, and two visible IA_Interact keyboard
contexts (targeting and dropped items). Historical observations remain in the
generated report. Raw capture/status from the first completed mission are also
archived on robot1-x in `ffw-tests/ui-census-20261021/` under the retained build
checkout. Later interrupted sessions retain their last complete checkpoints.

Shared marker adapters now cover UI_Lifebar_C (ProgressBar_Boss at 808) on the
observed enemy, Cryptic Train, radioactive-barrel, and boss-spawn families, plus
UI_JokerCard_InGame_C (Overlay_Transform at 840) on BP_Pickable_Joker_C. They track
the native component's parent chain and transform its saved local offset through
the current untouched parent, preserving live content and collision roots. Socket
or absolute-location attachments are skipped. New attached entries are capped
at 32 to reserve room for established markers, and hidden components release slots.
These changes and the shared HUD/hint helpers have regression coverage; native
geometry, combat behavior, and visual validation remain pending. Do not treat
historical capture flags as a current failure or a verified fix.

The earlier extraction stall remains unproven: train departure finished, but the
view stayed at the station/island. Desktop showed the same scene; F8 showed a black
screen with the version text. Controller StateName was Inactive with null pawn,
mission-completion flags were incomplete, and LS_Tain_MissionExtract was present.
These may be transition states. A full repeat mission/extraction succeeded. If it
recurs, inspect the existing bounded snapshots `ffw-tests/extraction-state-2.json`
and `extraction-departure.json` and capture the current state before restarting.
No extraction-specific repair is established; do not force mission/reward/travel
flags based on those observations. The separate stale-pawn dismount fix is accepted.

Optional live marker override `data/world_markers_dev.lua` is polled by the stable
loader; normal play needs no override. New factories must clean up the old one and
avoid adding duplicate callbacks. Remove temporary overrides after validation and
relaunch the game to verify the normal committed path. Profile `log.txt`
can be noisy; read bounded recent slices or start from a recorded byte offset.

Earlier troubleshooting chronology and completed work remain in Git history.
This document retains the current technical constraints rather than old patch steps.
