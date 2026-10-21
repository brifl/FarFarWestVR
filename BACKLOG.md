# Far Far West VR backlog

Updated October 21, 2026. Completed features and current controls are summarized
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
| Next | Shared safe placement for fixed HUD | Configurable minimum horizontal/vertical margins bring health, ammo, weapons, and cooldown groups into view. Preserve group layout; exclude world markers, reticles, and full-screen effects. Current capture margins only identify candidates. |
| Next | Extend marker stabilization to health bars | One adapter covers UI_Lifebar_C on the observed enemy, radioactive barrel, and boss-spawn object. Preserve native bar values, visibility, attachment offsets, moving targets, and collision roots. |
| Next | Stabilize remaining interaction hints | Address the captured UI_Interact_C/IA_Interact F/X flip and related action-key contexts. Keep Quest X stable without changing bindings or hold progress; inspect literal embedded FText separately if reported. |
| Ongoing | Additional marker/HUD/hint families | Use stable IDs and native relationships from monitoring; include other-player markers when encountered. Reuse shared projection/placement logic while preserving native content and edge behavior. |
| Ongoing | Combat validation | Confirm boss-bar height and remaining combat HUD after shared placement; keep heights adjustable in tuning.ini. |

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
| Polish | Remaining initialization delay | Distinguish widget creation from discovery latency; use targeted native queries or bounded preparation where supported. Mission-card detection and earlier marker initialization are already improved. |
| Low | Narrow heat-distortion workaround | Identify the offending material if worthwhile and check damage/status effects. Current workaround disables all custom post-process materials; the temporal-AA experiment remains inactive. |
| Low; coordinate with hands design | Simplify input layers | Investigate RemapControls' repeated shift warning and overlapping synthetic/native input. Confirm any still-unclear A, Utility, and left-stick-click semantics before rebinding. Preserve working spells, pause, movement, snap turns, menus, and shifted D-pad actions. |

## Working rules

- Preserve personal runtime/tuning preferences and the accepted stereo/menu baseline.
- Validate current object identities and possession before native access. The
  earlier horse-dismount stale-pawn issue is fixed; keep its lifetime discipline.
- Native SDK world lookup and implicit UObjectHook discovery are not prerequisites
  to enable casually. Follow the guarded access paths in development notes.
- Keep monitoring improvements independent of the loose-hands experiment so a
  hands toggle does not disable unrelated HUD, menu, or marker corrections.
