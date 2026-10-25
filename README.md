# Far Far West VR — Beta

A VR extension for **Far Far West**, built on UEVR, with controller aiming,
readable menus, and a HUD adapted for the headset.

**This is a beta build.** It is playable and under active development as we refine
controls, expand UI coverage, and work through the [backlog](BACKLOG.md). Expect
some rough edges, especially after game updates.

## Features

- **Stereo VR and controller aiming:** aim with the right controller while looking around
  independently. The reticle follows the firing target. Adjustable stabilization
  reduces small hand movements.
- **Point-and-click menus:** use the right controller and trigger, with readable
  menus, a visible cursor, and B to pause or resume. Train mission previews have
  a readable presentation too.
- **Movement and riding:** left-stick movement, 45-degree snap turning, gesture
  access to the map, and adjustable horse steering.
- **VR spell controls:** left grip, right grip, and both grips cast the three spells.
  The spell vendor uses matching grip labels.
- **World markers:** corrections for vendor icons, mission objectives, teammates,
  tagged locations and objects, and interaction prompts. Coverage is expanding to
  health bars, NPC names, floating damage numbers, and dropped cards.
- **Readable HUD:** corrected proportions, adjustable size, four edge margins,
  and separate height controls for dialogue, the compass, objectives, and boss health.
- **Item interaction:** X interacts, advances dialogue, and drops carried items
  when their Drop prompt is active.
- **Tunable visuals:** reduced haze, a heat-distortion workaround, and editable
  contrast and saturation.

## Compatibility

The current beta is tested with **Far Far West 0.3.0.7**, **Windows**, **Meta Quest 3**,
**Virtual Desktop**, and **SteamVR using OpenVR**. Other headsets and runtimes have
not been verified. Game updates may require a matching backend update.

**A matching custom UEVR runtime is required.** The profile alone cannot provide
all these features. This repository contains the profile and scripts; backend
binaries are not included, and a packaged runtime has not yet been published on
this project's [Releases page](https://github.com/brifl/FarFarWestVR/releases).
Obtain the matching beta runtime from the maintainer before installing.

## Installation

1. **Extract the matching beta UEVR runtime** into its own folder. Keep its files
   together, including `UEVRInjector.exe` and the supplied `UEVRBackend.dll`.
2. **Launch Far Far West normally once, then close it.** This creates the game log
   used by the menu helper.
3. **Install the profile.** Download this repository with **Code → Download ZIP**,
   extract it, and copy the contents of `FarFarWestVR-main` into:

   ```text
   %APPDATA%\UnrealVRMod\FarFarWest-Win64-Shipping\
   ```

   Create that folder if needed. `config.txt` must be directly inside it, alongside
   `scripts`, `plugins`, `assets`, and `data`. Copy the contents, not the outer
   `FarFarWestVR-main` folder. The repository ZIP is not a ready-made UEVR profile
   import archive.
4. **Complete the [required one-time Windows setup](docs/SETUP.md).** It connects
   the menu helper to the game log, enables controller aiming, and applies the
   game configuration. This step is required on each new installation.
5. **Play.** Connect through Virtual Desktop, start SteamVR and Far Far West, then
   open the supplied `UEVRInjector.exe`. Select `FarFarWest-Win64-Shipping`, choose
   **OpenVR**, and click **Inject**. Keep the game window focused for input. Press **Insert** to open or close the
   UEVR settings panel.

To enable the directional shortcuts below, turn on UEVR's **D-pad Shifting** and
select **Gesture (Head) + Left Joystick**. It is off in the checked-in profile.

For updates, close the game first and keep a copy of your personal
`data/tuning.ini` and UEVR settings. Replace the profile files, restore your tuning,
then relaunch normally. Update the custom runtime too when a beta requires it.
Existing Git checkouts can use `git pull`. Use a normal relaunch instead of
**Reset scripts**, which can disrupt the current session.

## Quest controls

| Control | Action |
| --- | --- |
| Left stick | Move forward/back and strafe |
| Right stick left/right | 45-degree snap turn |
| Right-stick click | Tag a location or object |
| Right trigger | Fire; click in menus |
| Left trigger | Aim |
| Left grip / right grip | First / second spell |
| Both grips together | Third spell |
| X | Interact; advance dialogue; drop when a Drop prompt is active |
| Y | Switch weapons |
| B | Pause/resume |
| Left controller near head + left stick Right | Map |
| Left controller near head + left stick Down | Summon horse / dismount |
| Left controller near head + left stick Up | Utility |
| Left controller near head + left stick Left | Photo mode |

The last four shortcuts require D-pad Shifting. `LG` and `RG` in spell hints mean
**left grip** and **right grip**. Some other in-game prompts still show keyboard
or gamepad labels; Quest-specific icons are planned.

## Configuration

Open this file in a text editor:

```text
%APPDATA%\UnrealVRMod\FarFarWest-Win64-Shipping\data\tuning.ini
```

Save numeric changes to apply them while playing, usually within a second.
Keep each setting in its existing section. Invalid edits leave the previous
settings active.

| Section | Setting | Included value | Adjustment |
| --- | --- | --- | --- |
| `[aim]` | `stabilization` | `0.35` | `0` disables smoothing; `1` is strongest. More smoothing can add aim lag. |
| `[horse]` | `steering_exponent` | `2.0` | `1` is the original response; higher values soften small left-stick turns. Full steering is preserved. |
| `[hud]` | `scale_multiplier` | `0.85` | Overall fixed-HUD size; smaller values shrink it. |
| `[hud]` | `left_margin`, `right_margin` | `0.20` each | Minimum left/right inset as a fraction of screen width. |
| `[hud]` | `top_margin`, `bottom_margin` | `0.15`, `0.30` | Minimum top/bottom inset as a fraction of screen height. |
| `[hud]` | `dialogue_offset_y` | `-0.10` | Conversation text height. |
| `[hud]` | `compass_offset_y` | `0.15` | Compass height. |
| `[hud]` | `mission_info_offset_y` | `0.15` | Mission counter/timer height. |
| `[hud]` | `boss_health_offset_y` | `0.15` | Boss-bar height. |
| `[hud]` | `boss_health_scale_multiplier` | `0.85` | Boss-bar size, independently of the fixed HUD. |
| `[graphics]` | `saturation_multiplier` | `0.95` | Color saturation; `1.0` uses the original amount. |
| `[graphics]` | `contrast_multiplier` | `1.15` | Contrast; `1.0` uses the original amount. |
| `[graphics]` | `fog_density_multiplier` | `0.20` | Primary weather haze; `1.0` is the original density. |
| `[cursor]` | `scale_multiplier` | `1.0` | Menu cursor size. |
| `[audit]` | `auto_start` | `1` | Set to `0` to disable automatic UI capture on future launches. |

For height offsets, **positive moves down**, **negative moves up**, and `0` uses
the original position. For example, `-0.10` raises a panel by 10% of screen height.
Margins accept `0`–`0.40`; `0.20` means 20%. They apply to supported fixed-HUD
groups, while the height settings control their separate panels. Keep the included
aspect-correction settings unless you are troubleshooting proportions.

## Beta limitations and feedback

- Aiming follows controller **orientation**. Full hand/weapon position tracking,
  wrist roll, and physical melee/throwing are [planned](docs/LOOSE-HANDS.md).
- Some UI elements still need placement or tracking fixes. The newest NPC-label,
  damage-number, and health-bar corrections need more gameplay validation.
- Emote, Battlecry, Melee, and Challenges do not yet have dedicated VR mappings.
- The heat workaround disables custom post-process materials, which may also
  change some damage/status effects. The train camera and some scene transitions
  still have rough edges.

Report problems through [GitHub Issues](https://github.com/brifl/FarFarWestVR/issues),
including the game version, beta/profile version, headset/runtime, what happened,
and steps to reproduce it. A screenshot or short video helps with UI issues.

UI capture is enabled by default for beta testing and saves observations locally
under the profile's `data` folder. See [UI diagnostics](docs/UI-AUDIT.md) for
collection instructions and the [cumulative findings](docs/UI-FINDINGS.md) for
current coverage. Progress and planned improvements are in the [backlog](BACKLOG.md).

For building, backend deployment, and troubleshooting internals, see
[development notes](docs/DEVELOPMENT.md).

## Credits

Built on [praydog's UEVR](https://github.com/praydog/UEVR) and the starting
Far Far West profile shared by [HeadsetVR](https://www.patreon.com/HeadsetVR/posts/is-far-far-west-163314637).
This project builds on that work with additional aiming, UI, controls, and
compatibility fixes.
