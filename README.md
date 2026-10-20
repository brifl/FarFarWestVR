# Far Far West VR

A UEVR profile and custom backend for playing **Far Far West** in VR, with
controller aiming, readable menus, and world markers that stay where they belong.

- **Right-controller aiming:** aim with your controller while looking around
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
- **Corrected interaction prompts:** NPC prompts follow the aiming target while
  preserving the game's interaction text and hold-progress display.
- **Adjustable HUD placement:** raised dialogue text and separate height controls
  for the compass, mission counters/timers, and boss health bar.
- **Graphics tuned for VR:** reduced distance haze, a heat-distortion workaround,
  and editable contrast and saturation multipliers.
- **Live tuning:** adjust graphics multipliers and HUD heights during play.
- **Earlier marker initialization:** prepare markers as a level loads to reduce
  the delay before stabilization.

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
| X | Interact |
| Y | Switch weapons |
| B | Pause/resume |

Directional actions require UEVR's **D-pad Shifting** to be enabled. The tested
activation method is **Gesture (Head) + Left Joystick**.

## Personal tuning

Edit [data/tuning.ini](data/tuning.ini) in the installed profile. Numeric changes
reload during play, about once a second.

| Setting | Default | Effect |
| --- | --- | --- |
| `saturation_multiplier` | `0.95` | Slightly lower saturation |
| `contrast_multiplier` | `1.10` | Ten percent more contrast |
| `fog_density_multiplier` | `0.00` | Remove primary distance haze |
| `dialogue_offset_y` | `-0.10` | Raise conversation text |
| `boss_health_offset_y` | `0.08` | Lower boss health |
| `mission_info_offset_y` | `0.10` | Lower mission counters and timers |
| `compass_offset_y` | `0.10` | Lower the compass and its markers together |

A graphics multiplier of `1.0` uses the game's original amount. HUD offsets are
fractions of viewport height: positive moves down, negative moves up, and `0`
restores the original position. For example, `0.10` moves a panel down by ten
percent. Invalid edits retain the previous settings.

## Development status

This mod is still in development. Controller aiming currently controls weapon
orientation; full weapon/hand attachment is planned. Reticle stepping and broader
multiplayer-marker coverage remain on the backlog. Boss-bar height needs further
combat verification.

The reticle now follows possession changes when mounting and dismounting; a full
mission completed without issues after this correction.

The heat-distortion workaround disables all custom post-process materials;
some damage or status effects may also be affected. One post-extraction stall
was observed; a repeat mission completed normally, and recurrence is being watched.

See [the backlog](BACKLOG.md) for progress and planned improvements, or
[development notes](docs/DEVELOPMENT.md) for backend deployment, diagnostics, and
implementation details.
