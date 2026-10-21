# Far Far West VR

A UEVR profile and custom backend for playing **Far Far West** in VR, with
controller aiming, readable menus, and world markers that stay where they belong.

- **Aligned stereo rendering:** the custom backend provides matching eye views
  and full-width menu presentation.
- **Right-controller aiming:** aim smoothly with your controller while looking around
  independently. The reticle follows the firing target, including at different
  ranges and when casting spells.
- **Controller-operated menus:** point with the right controller and click with
  the trigger. Menus stay readable and stationary, with B handling pause/resume.
- **Themed menu cursor:** a custom arrow with a precise tip hotspot.
- **Movement and snap turning:** left-stick movement and 45-degree turns on the
  right stick.
- **Stable world markers:** vendor icons, Start Mission, quest objectives, and
  mission guides follow their world locations independently of controller aim.
- **Object and location tags:** tag a spot or object with the right-stick click.
  Tags follow moving targets, including chickens, and retain their icons,
  distances, and height offsets.
- **Corrected UI proportions:** reticles and world markers compensate for the
  eye projection's aspect ratio, keeping dots round and attachment points fixed.
- **Corrected interaction prompts:** NPC prompts follow the aiming target while
  preserving the game's interaction text and hold-progress display. Dialogue's
  Next prompt keeps the X icon when the game switches to keyboard input hints.
- **VR spell-selection hints:** the joker card vendor shows LG, RG, and LG+RG
  for left grip, right grip, and both grips. Labels stay stable across input modes.
- **Readable train mission previews:** the title/objective card uses the readable
  menu presentation, with faster detection during loading transitions.
- **Native spell controls:** left grip, right grip, and both grips cast the three
  spells while preserving the native shifted D-pad actions.
- **Possession-aware reticle:** aiming traces follow the current player after
  mounting and dismounting, avoiding the earlier stale-pawn freeze.
- **Adjustable HUD placement:** raised dialogue text and separate height controls
  for the compass, mission counters/timers, and boss health bar.
- **Graphics tuned for VR:** reduced distance haze, a heat-distortion workaround,
  and editable contrast and saturation multipliers.
- **Live tuning:** adjust graphics multipliers and HUD heights during play.
- **Earlier marker initialization:** prepare markers as a level loads to reduce
  the delay before stabilization.
- **UI monitoring across play sessions:** optional automatic capture preserves
  widget IDs, positions, marker coverage, and input-hint observations in a
  cumulative findings document.

## Requirements and setup

The current setup is tested with **Far Far West 0.2.0.20**, **Meta Quest 3**,
**Virtual Desktop**, and **SteamVR**. It requires the custom UEVR backend developed
for this profile; importing the profile alone does not install that backend.
See [development and deployment](docs/DEVELOPMENT.md) for the existing installation
workflow and compatibility details.

Package the profile files as `FarFarWest-Win64-Shipping.zip` and import them into
UEVR, or update an existing profile checkout with `git pull`. After updating Lua
helpers, use **UEVR → Main → Reset scripts** or restart the game. Keep the game
window focused for menu input.

## Controls

These are the tested Quest button labels.

| Control | Action |
| --- | --- |
| Left stick | Move forward/back and strafe |
| Right stick left/right | 45-degree snap turn |
| Right-stick click | Tag an object or location |
| Right trigger | Fire; click in menus |
| Left trigger | Native aim action |
| Left/right grip | Spells |
| Both grips together | Third spell |
| Shifted D-pad Left | Native photo mode |
| Shifted D-pad Down | Summon horse (native action) |
| Shifted D-pad Up | Native Utility action |
| Shifted D-pad Right | Map |
| X | Interact; advance dialogue |
| Y | Switch weapons |
| B | Pause/resume |

Directional actions require UEVR's **D-pad Shifting** to be enabled. The tested
activation method is **Gesture (Head) + Left Joystick**.

## Personal tuning

Edit [data/tuning.ini](data/tuning.ini) in the installed profile. Numeric changes
reload during play, about once a second.

| Setting | Profile value | Effect |
| --- | --- | --- |
| `saturation_multiplier` | `0.95` | Slightly lower saturation |
| `contrast_multiplier` | `1.10` | Ten percent more contrast |
| `fog_density_multiplier` | `0.20` | Reduce primary distance haze to twenty percent |
| `dialogue_offset_y` | `-0.10` | Raise conversation text |
| `boss_health_offset_y` | `0.10` | Lower boss health |
| `mission_info_offset_y` | `0.15` | Lower mission counters and timers |
| `compass_offset_y` | `0.15` | Lower the compass and its markers together |

A graphics multiplier of `1.0` uses the game's original amount. HUD offsets are
fractions of viewport height: positive moves down, negative moves up, and `0`
restores the original position. For example, `0.10` moves a panel down by ten
percent. Invalid edits retain the previous settings. The saved world scale is
`0.010000`, matching the tested setup; preserve personal runtime adjustments.

## Development status

Controller aiming currently follows the right controller’s orientation. Full
position and wrist-roll tracking for hands/weapons is a
[planned design project](docs/LOOSE-HANDS.md); implementation has not started.

[Ongoing UI monitoring](docs/UI-FINDINGS.md) is identifying additional edge HUD,
health-bar markers, and control hints to improve. Those remaining cases are
tracked in the [backlog](BACKLOG.md). Boss-bar height still needs combat validation.

The heat-distortion workaround disables all custom post-process materials;
some damage or status effects may also be affected. One post-extraction stall
was observed; a repeat mission completed normally, and recurrence is being watched.

See [the backlog](BACKLOG.md) for progress and planned improvements, or
[development notes](docs/DEVELOPMENT.md) for backend deployment, diagnostics, and
implementation details.

## UI diagnostics

A [gameplay capture](docs/UI-AUDIT.md) catalogs edge HUD, marker families, and
action-bound interaction hints across play sessions. Capture starts on each launch
when `[audit] auto_start = 1`. The [cumulative findings](docs/UI-FINDINGS.md) retain
widget IDs, positions, and session history; refresh them with
`python3 tools/ui_audit.py collect`. Capture does not change gameplay.
