# Far Far West VR backlog

Updated October 23, 2026. Completed features and current controls are summarized
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
| Validate first | Fear Fear West 0.3.0.0 compatibility | Guarded backend and updated key/slot/grading layouts are deployed. Startup confirms SDK access, reticle/marker projection, and grading; controller menu pointing is confirmed. The native cursor copy is visible and its centered hotspot aligns. Recheck remaining visuals and hints through normal play. |
| Validate next relaunch | Map control | The game lists View/Back (overlapping squares) for Map. Route shifted Right to that native button and remove the old middle-mouse binding. The earlier black-screen capture contained HUD/chat, with no active map widget. Confirm the map opens with its contents visible, closes normally, and does not focus chat. |
| Validate next boss | Boss-bar size and position | The previous shared proportions/edge changes passed validation, with this exception. Scale the boss overlay about top center to eliminate the full-screen center-pivot displacement; add independent `[hud] boss_health_scale_multiplier = 0.85`. Existing boss offset remains 0.15 and edge margins do not participate. Confirm size and height in combat after a normal relaunch. |
| Validate next | Shared health-bar and dropped-card markers | Implemented for captured enemy, Cryptic Train, barrel, boss-spawn, and dropped Joker families. Confirm native values/content, moving attachment offsets, visibility, and target anchoring in combat. Socket/absolute attachments remain native. |
| Validate next | Shared interaction hints | Implemented for action-bound IA_Interact keys, including targeting, dialogue, and dropped-item contexts. Confirm X stays stable and hold progress works. Literal embedded FText remains a separate discovery case. |
| Deferred until recurrence | Elongated gameplay cursor | The user cannot currently reproduce it; no further investigation for now. Menu defaults are restored to scale 1 / aspect correction 0. If it returns, identify the actual gameplay widget/presentation path; existing suppression covers only known native cursor classes. |
| Ongoing | Additional marker/HUD/hint families | Use stable IDs and native relationships from monitoring. Teammate nameplates are corrected and user-confirmed stable; watch for distinct revive/downed or other unhandled families. Reuse shared projection/placement logic while preserving native content and edge behavior. |
| Validate next long session | Late multiplayer capture coverage | Reserved ID capacity worked in capture 16, but its broad all-widget query stopped after 421.8 seconds at the native query budget. Query viewport roots and explicitly seed discovered component widgets instead. Keep record/byte/query budgets and persist errors/status per session. Most of that night's mission discoveries are missing; collect again after a new normal launch. |
| Ongoing | Combat validation | Confirm boss-bar height and remaining combat HUD after shared placement; keep heights adjustable in tuning.ini. |

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
