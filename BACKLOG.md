# Far Far West VR backlog

Updated October 25, 2026. Completed features and current controls are summarized
in the [README](README.md). Technical constraints and deployment details live in
[DEVELOPMENT.md](docs/DEVELOPMENT.md); earlier troubleshooting remains in Git history.

## Ongoing monitoring and small fixes

Continue collecting across play sessions and addressing newly discovered cases
in small batches. This remains ongoing until representative missions, menus,
interactions, and item types stop revealing new unresolved families. A clean
session alone does not close it; repeated IDs do not count as new discoveries.

At check-ins, run `python3 tools/ui_audit.py collect` and review the cumulative
[UI findings](docs/UI-FINDINGS.md). Prefer shared widget/action/owner-family fixes
over separate per-instance patches, with one focused behavior change per test.
Keep historical observations distinct from active problems and verified fixes.

| Priority | Open work | Acceptance condition |
| --- | --- | --- |
| Validate next boss | Boss-bar size and position | The previous shared proportions/edge changes passed validation, with this exception. Scale the boss overlay about top center to eliminate the full-screen center-pivot displacement; add independent `[hud] boss_health_scale_multiplier = 0.85`. Existing boss offset remains 0.15 and edge margins do not participate. Confirm size and height in combat after a normal relaunch. |
| Validate next play | Captured world-marker families | Captures 26–30 recorded correction coverage for health bars and floating damage, in addition to existing objective/object/teammate markers. NPC names had no visible samples; dropped-Joker validation remains pending. Two health bars were rejected while their parent chain did not reach their owner root. Incomplete attachments now retry without moving an unverified component; rejected bindings follow component/widget identities, and expired candidates release discovery capacity. Confirm anchoring, proportions, native values/text, and visibility after relaunch; socket/absolute attachments remain native. |
| Watch future play | Shared interaction hints and Drop discovery | The bounded viewport/world-widget traversal completed the 2½-hour October 25 capture without the old retained-key query failure. Recorded IA_Interact hints used gamepad presentation, with no keyboard mode observed. Continue checking menus, carrying, and possession changes; literal embedded FText remains a separate discovery case. |
| Validate next play | Additional standalone HUD proportions | Captures identified short messages, disturbance notifications, teammate-death notices, and the Cryptic Snake status meter outside the existing shape adapters. Their shared content groups now receive one aspect correction without scaling their fullscreen roots or moving their native anchors. Verify readability, animations, and proportions after relaunch; existing `hud.aspect_correction` controls them. |
| Needs a visible example | Directional locator projection | `UI_Locator_C` (`w-a7611ac3e29f`) has Location@832, AttachedComponent@912, and an animated/rotated Border. It is separate from the corrected WidgetComponent marker families. Identify what it indicates and inspect its live transforms before changing tracking or size; a symptom and approximate encounter time would help. |
| Deferred until recurrence | Elongated gameplay cursor | The user cannot currently reproduce it; no further investigation for now. Menu defaults are restored to scale 1 / aspect correction 0. If it returns, identify the actual gameplay widget/presentation path; existing suppression covers only known native cursor classes. |
| Validate next relaunch | Low Ammo warning proportions and size | `UI_LowAmmo_C` (`w-afa1c0cbd4b9`) now uses shared eye-aspect correction and `[hud] scale_multiplier` (profile 0.85). Confirm the warning is smaller and no longer elongated when ammo runs low. |
| Ongoing | Additional marker/HUD/hint families | Use stable IDs and native relationships from monitoring. Teammate nameplates are corrected and user-confirmed stable; watch for distinct revive/downed or other unhandled families. Reuse shared projection/placement logic while preserving native content and edge behavior. |
| Optional offline-prepared test | Suppress Niagara activation | The `niagara-suppression` preset sets `fx.SuppressNiagaraSystems=1` in persistent UserEngine.ini while preserving the existing baseline. Not enabled by default or applied to robot1-x. On a later launch, verify the setting loads, check missing combat/interaction effects, and compare component growth. Suppressing activation does not guarantee allocation stops. Application/restore tests pass. |
| Validate next long session | Helpers stopped above 250,000 UObject slots | At 02:57 on October 23, grading, fog, HUD, cursor, hints, reticle and markers hit the same old probe limit. A shared native-count validator now accepts positive int32 slot counts; existing per-frame scan/time/query caps remain. Live counts exceeded 286,000. Confirm helpers remain active across the former limit after a normal relaunch. A census found about 190,000 Niagara components; overlay instances were few. Keep the effects-growth question separate and attribute it before changing effects. |
| Ongoing | Combat validation | Confirm boss-bar height and remaining combat HUD after shared placement; keep heights adjustable in tuning.ini. |

## Quest controller hint icons

**Planned; normal priority after validating the current marker/hint fixes.**
**Assets ready:** the 16 individual [PNGs](assets/controls_png/) are 128×128 with
verified transparency and antialiased edges. [SVG sources](assets/controls_svg/)
and a [sprite sheet](assets/quest3_controls_sprite_sheet.png) are included.
Use these for consistent Quest button, trigger, grip, stick, and gesture hints.
Runtime cost should be small: reuse the spell-vendor texture cache and existing
hint Image widgets.

- Use the individual PNGs directly; cropping and background removal are no longer
  needed. Preserve their proportions and allow wider sizing for head-gesture
  hints so they remain readable at headset hint sizes.
- Share one action/context-to-icon map across interaction, dialogue, carried-item,
  spell-vendor, and gameplay hints. Start with X, B, triggers, and grips; combine
  both grips for spell three. Add gesture combinations after the basic set works.
- Preserve native action bindings, hold-progress displays, widget sizing/aspect
  corrections, and unknown-action fallback. Do not label unimplemented controls
  as available or replace literal keyboard text without knowing its action.
- Cache imported textures and update brushes only when needed. Reapply after
  native input-mode changes or widget rebuilds; make the visual override reversible.

Acceptance: readable, correctly mapped Quest icons remain stable across input
modes, menus, carrying, and scene transitions without repeated texture creation.

## Additional gesture controls

**Design/backlog only.** The newly visible right-side hint panel lists
**Emote, Battlecry, Melee, and Challenges**. The user reports these actions are
not reachable with the current VR controls. Add access to all four and update
their hints to match the eventual VR bindings.

Proposed activation: bring the **right controller near the head**, then use the
**right thumbstick's four directions** as an additional directional layer,
similar to the existing left-controller head gesture. Direction assignments are
still undecided; identify each native action/binding before choosing mappings.

- Check whether UEVR supports an independent right-hand layer alongside the
  existing left-hand gesture; use a shared Lua input router if necessary.
- Preserve right-stick snap turning and tagging outside the gesture. While the
  gesture is active, consume its directions and gate the Lua snap-turn path so
  selecting an action cannot also turn the view.
- Trigger once per deliberate deflection; require neutral before rearming, use
  separate enter/exit thresholds, and cancel on menus or tracking loss.
- Keep the left-hand shifted D-pad, horse/map/utility/photo actions, aiming,
  spells, and menu pointing usable. Verify native press/hold/release behavior
  for each new action and avoid duplicate synthetic/native input.
- Make the experimental layer switchable while testing. It can be implemented
  independently of loose hands; later physical emote/melee gestures remain
  separate work.

Acceptance: all four actions are reachable with stable matching hints, no
accidental snap turns or repeated actions, and normal controls return cleanly
when the controller leaves the head area or the layer is disabled.

## Weapon-specific pointer angle tuning

**Planned; configuration and design only for now.** Add per-weapon pitch/yaw
offsets in degrees to `data/tuning.ini` so the aiming pointer better matches the
way each equipped gun is held. This can be implemented independently of loose hands.

- Identify the currently equipped weapon by stable item/class ID and select its
  offsets automatically on equip, weapon switch, or possession change.
- Apply offsets in controller-local orientation, with a shared default and
  per-weapon overrides. Zero offsets preserve the current aiming behavior.
- Reload numeric tuning during play for calibration. Preserve stabilization,
  head-look independence, snap turning, and the separate menu pointer behavior.
- Keep the firing direction, reticle, and actual hit location consistent; avoid
  correcting only the visible pointer while leaving shots elsewhere.

Acceptance: switching weapons selects the corresponding tuning, unknown weapons
use the shared default, and aiming remains aligned with the held gun and impacts.
Document the configuration keys and angle directions when implemented.

## Loose hands and tracked weapons

**Design stage; implementation has not started.** See
[LOOSE-HANDS.md](docs/LOOSE-HANDS.md) for the proposed architecture, milestones,
reference research, open decisions, and acceptance gates.

Goal: controller position and full orientation drive both hands and held weapons,
including forward/back movement and wrist roll. The experiment must toggle on/off
during play and restore the current accepted aiming and controls when disabled.

| Stage | Planned work |
| --- | --- |
| LH-0 | Inspect the hand/weapon rig, native firing path, animation ownership, and item-action families; settle the access/pose model. |
| LH-1 | Live toggle, ownership/restoration, calibration, and pose preview. |
| LH-2 | First playable slice: both hands and one one-handed gun, with muzzle, impacts, and reticle agreeing. |
| LH-3 | Item profiles and reversible input routing; decide grip/spell mappings before remapping anything. |
| LH-4 | Pickaxe/mining: native button behavior first, then optional physical swings. |
| LH-5 | Throwing: one native item end to end, then other families. |
| LH-6 | Melee adapters: preserve attack/charge/alt behavior, then optional physical swings. |
| Later | Two-hand support, handedness, special item interactions, and gestures for emotes/spells. |

Current grips cast spells, including both grips for spell three; they are not
unassigned grab buttons. Keep them through initial pose work. Moving a visible
mesh alone is not a completed aiming solution. Resolve translated shot origin,
reticle agreement, native action semantics, and the live-toggle restoration path.
Use the retained isolated backend only if inspection proves a native change necessary.

## Other open work

| Priority | Item | Next step / constraint |
| --- | --- | --- |
| Watch for recurrence | Extraction station/island stall | A later full mission/extraction succeeded. If repeated, capture current game/sequence/pawn state before restarting; no extraction-specific fix is proven. See development notes for saved observations. |
| Low | Train cinematic viewpoint below the train | Compare with normal 2D behavior before changing camera offsets; preserve headset look. The readable mission preview is already complete. |
| Low; use relaunches meanwhile | Script-reset recovery | The user reports Reset scripts commonly breaks the running session. Diagnose separately; use normal relaunches for helper-code updates. Numeric tuning still reloads live. |
| Low | Narrow heat-distortion workaround | Identify the offending material if worthwhile and check damage/status effects. Current workaround disables all custom post-process materials; the temporal-AA experiment remains inactive. |
| Low; coordinate with hands design | Simplify input layers | Investigate RemapControls' repeated shift warning and overlapping synthetic/native input. Confirm any still-unclear A, Utility, and left-stick-click semantics before rebinding. Preserve working spells, pause, movement, snap turns, menus, and shifted D-pad actions. |

## Working rules

- Preserve personal runtime/tuning preferences and the accepted stereo/menu baseline.
- Use normal game relaunches for helper-code updates; script reset is unreliable.
- Validate current object identities and possession before native access. The
  earlier horse-dismount stale-pawn issue is fixed; keep its lifetime discipline.
- Native SDK world lookup and implicit UObjectHook discovery are not prerequisites
  to enable casually. Follow the guarded access paths in development notes.
- Keep monitoring improvements independent of the loose-hands experiment so a
  hands toggle does not disable unrelated HUD, menu, or marker corrections.
