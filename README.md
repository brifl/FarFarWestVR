# Far Far West VR — Beta 0.1.0-beta.1

Play the Windows PC game **Far Far West** in VR, with controller aiming,
readable menus, and a HUD adapted for the headset.

[**Download the beta**](https://github.com/brifl/FarFarWestVR/releases/tag/v0.1.0-beta.1) ·
[Installation help](docs/SETUP.md) ·
[Report a problem](https://github.com/brifl/FarFarWestVR/issues/new/choose)

**UEVR** is praydog’s tool for adding VR to Unreal Engine games. This project is
a game-specific **profile**: settings, scripts, and controller mappings that run
inside UEVR. It requires a VR-capable Windows PC and your own copy of the game;
it is not a standalone Quest app.

**Runtime availability:** this release contains the profile and Windows installer.
The matching **custom UEVR runtime is not publicly downloadable yet**, pending
redistribution permission. The installer currently serves users who already have
that runtime. First-time users need to wait for its availability;
[ask about installation or runtime availability](https://github.com/brifl/FarFarWestVR/issues/new?template=installation.yml)
if unsure. Stock UEVR does not provide the required backend.

**This is a beta build.** It is playable and under active development as we refine
controls, expand UI coverage, and work through the [backlog](BACKLOG.md). Expect
some rough edges, especially after game updates.

## Features

- **Stereo VR and controller aiming:** aim with the right controller while looking around
  independently. The reticle follows the firing target. Adjustable stabilization
  reduces small hand movements. Development builds include an optional black-halo
  dot reticle for visibility against bright backgrounds, enabled by default.
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

**In development:** the newer backend detects and validates the game's object
tables at startup, so minor patches can work without adding each executable to
a version list. Updates that change engine or UI layouts can still need fixes.
This improvement is newer than the published beta.1 downloads.

## Installation

You need the game installed through Steam, a working PC VR connection, SteamVR,
and the matching custom UEVR folder. The tested setup uses Quest 3 with Virtual
Desktop connected to the PC; the headset must be able to run PC VR games first.

1. **Start Far Far West once normally, then close it.** This creates its game log.
2. From the [beta release page](https://github.com/brifl/FarFarWestVR/releases/tag/v0.1.0-beta.1),
   download **`FarFarWestVR-0.1.0-beta.1-Setup.zip`**. Use this asset, rather than
   GitHub’s automatically generated “Source code” ZIP.
3. Right-click the downloaded ZIP → **Properties → Unblock → Apply**, if Unblock
   is shown. Then right-click → **Extract All**. See
   [download warnings](docs/SETUP.md#download-and-windows-warnings) if the browser blocks it.
4. Open the extracted folder and double-click **`Install-FarFarWestVR.cmd`**.
   Select your matching custom UEVR folder. The installer finds the Steam game or
   asks you to select it, checks the backend, and requests Windows administrator
   approval for the game-log link and configuration.

The installer places the profile in the correct AppData folder, enables the menu
helper and controller aiming, and applies the heat-distortion workaround. It
backs up an existing profile and game configuration, preserves `data/tuning.ini`,
and creates a desktop shortcut to the selected UEVR injector. Other UEVR profile
settings use this beta’s defaults. It does not download or replace UEVR.

## Launching in VR

1. Connect your headset to PC VR and start **SteamVR**.
2. Start **Far Far West** through Steam.
3. Open the **Far Far West VR** desktop shortcut, or `UEVRInjector.exe` in your
   matching custom runtime folder.
4. In UEVR, select **`FarFarWest-Win64-Shipping`**, choose **OpenVR**, and click
   **Inject**. Injection loads the VR mod into the running game.
5. Put on the headset. Press **Insert** on the keyboard to close the UEVR settings
   panel if it covers the game. Point with the right controller and click with
   its trigger. Keep the game window focused on the desktop so controls reach it.

For map and horse shortcuts, open UEVR with **Insert**, enable **D-pad Shifting**,
and select **Gesture (Head) + Left Joystick**. Close the panel again. These
shortcuts activate when you bring the left controller near your head and move
its stick; normal left-stick movement continues outside the gesture.

For updates, close the game and run the newer Setup package. Use a normal relaunch
instead of **Reset scripts**, which can disrupt the running game. Development Git
checkouts continue to use `git pull`; the installer protects them from replacement.

[Detailed setup, manual profile installation, and troubleshooting](docs/SETUP.md)

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
| `[aim]` | `halo_reticle` | `1` in development builds | `1` uses the black-halo aim graphic; `0` restores the game's graphic. Reloads while playing. |
| `[aim]` | `halo_reticle_scale` | `0.25` | Halo width/height multiplier; smaller values shrink it. Applies only to the halo graphic. Reloads while playing. |
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
| `[audit]` | `auto_start` | `0` in release ZIPs | Set to `1` to collect UI diagnostics locally on future launches when requested for troubleshooting. |

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

For download/installation trouble or fixable gameplay issues,
[open an issue](https://github.com/brifl/FarFarWestVR/issues/new/choose). Include
the game version, beta/profile version, headset/runtime, what happened,
and steps to reproduce it. A screenshot or short video helps with UI issues.

Optional UI capture saves observations locally under the profile’s `data` folder;
it uploads nothing automatically. It is off in release packages and on in our
development checkout. See [UI diagnostics](docs/UI-AUDIT.md) for
collection instructions and the [cumulative findings](docs/UI-FINDINGS.md) for
current coverage. Progress and planned improvements are in the [backlog](BACKLOG.md).

For building, backend deployment, and troubleshooting internals, see
[development notes](docs/DEVELOPMENT.md).

**Current Git builds, after the published beta:** a deliberate issue-marker
gesture saves recent diagnostic context for later investigation. Bring both
controllers to your ears and hold both triggers for about 0.6 seconds; two short
vibrations confirm it. Take screenshots yourself with Virtual Desktop or SteamVR
and use the [offline issue-capture workflow](docs/ISSUE-CAPTURE.md) to match them
by time. This feature is not in the 0.1.0-beta.1 release ZIPs yet.
Current development builds also add matching right-ear proximity feedback,
distinct report confirmation, and performance history for investigating long-session
slowdowns. See the same workflow for a capture-only isolation switch.

## Credits

Built on [praydog's UEVR](https://github.com/praydog/UEVR) and the starting
Far Far West profile shared by [HeadsetVR](https://www.patreon.com/HeadsetVR/posts/is-far-far-west-163314637).
This project builds on that work with additional aiming, UI, controls, and
compatibility fixes.
