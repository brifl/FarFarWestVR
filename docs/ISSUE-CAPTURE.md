# Marking a VR issue for later investigation

**Development feature after 0.1.0-beta.1.** This is in the current Git profile;
it is not in the already published 0.1.0-beta.1 ZIPs. Relaunch the game normally
after pulling the update. Do not use Reset scripts.

## While playing

1. When you notice something wrong, bring **both controllers to your ears**, one
   on each side of the headset, and pull **both triggers** for about **0.6 seconds**.
2. **Two short vibrations** confirm that a marker/report was started. Release
   both triggers before marking another issue; there is an eight-second cooldown.
3. Take a screenshot with your existing **Virtual Desktop or SteamVR** controls
   immediately before or after the marker. Aim for within ten seconds so the
   screenshot overlaps the recorded context.

The extension does **not** take screenshots, call screenshot APIs, record video,
or upload files. This gesture observes the existing triggers: their normal game
actions can still occur while they are held. It works in gameplay and game menus
with the UEVR panel closed. Keep the game running for several seconds afterward
so the short follow-up can finish; the pre-marker context starts flushing immediately.

You do not need to remember the exact time. Reports contain UTC, local time, a
Unix timestamp, and the active numeric tuning values. The recorder retains about
ten seconds of sampled context before the marker and five seconds afterward.
It keeps working after the ordinary UI-catalog recording window has finished.

## Where to put your screenshots

Copy the original images into this folder on robot1-x:

```text
%APPDATA%\UnrealVRMod\FarFarWest-Win64-Shipping\data\issue_screenshots\
```

Alternatively, drop them into this ignored folder in the development checkout:

```text
diagnostics/issues/robot1-x/screenshots/
```

Preserve the original file modification times when copying. The collector suggests
the nearest marker within **30 seconds**. If an image was edited or its timestamp
changed, prefix its name with the issue ID (for example,
`issue-20261026T220000Z-0001-pipes.png`) to associate it explicitly.
Unmatched images remain listed for manual review.

## Collect and review later

From the development repository, using the existing SSH/WSL connection:

```bash
python3 tools/issue_report.py collect
```

Open `diagnostics/issues/robot1-x/REPORT.md`. It links the individual reports and
screenshots, lists marker owner/attachment families and relevant widget IDs, and
summarizes repeated messages as dictionary entries with counts. Personal notes
can go in a file with the same issue ID followed by `.notes.md`; collecting again preserves them.

To rebuild the local index after adding images or notes:

```bash
python3 tools/issue_report.py report --output diagnostics/issues/robot1-x
```

`collect --screenshots /some/remote/folder` can read another screenshot folder on
robot1-x. `--tolerance 60` widens matching when necessary. For a deliberate desktop
marker without the gesture, `python3 tools/issue_report.py mark` writes a one-shot
request consumed by the running scripts.

The ordinary cumulative catalog remains available through:

```bash
python3 tools/ui_audit.py collect
```

## Tuning and limits

In the installed `data/tuning.ini`:

```ini
[diagnostics]
gesture_enabled = 1
head_radius_m = 0.40
hold_seconds = 0.60
cooldown_seconds = 8

[audit]
auto_start = 1
auto_seconds = 9000
```

`gesture_enabled = 0` disables the rolling recorder/gesture. The radius controls
how close the controllers must be; they must also be on opposite sides, rather
than held together in front of your face. The ordinary catalog rotates every
30 minutes; its window is now adjustable, with 2½ hours in development defaults.

The recorder uses a bounded in-memory ring and caps each report at 2 MiB. Writes
are spread over frames. It records sampled widget geometry/transforms, reflected
class/field metadata, marker targets/projection state, and relevant warning/error
counts. It does not read arbitrary UI text or chat, and creates no game actors.
Limits and interrupted captures are identified instead of presented as complete.

`data/UEVR.log` links to the profile’s `log.txt`, alongside the existing game-log
link. The installer prepares both links for future packages; the development
profile is prepared separately. If the UEVR link is absent, UI/gesture capture
still works, but UEVR message counters will be unavailable.

Log digests keep one normalized entry per message, its first/last observation,
and a counter. Known messages such as `invalid shift 0` are labelled documented;
unknown errors remain visible. Only bounded portions of appended logs are read,
and skipped bytes are reported. This reduces diagnostic/report volume; it does
not change the upstream plugin’s raw log output. Raw log suppression remains
separate work so control behavior is preserved.

Generated reports, digests, and screenshots stay local and are excluded from Git
and release ZIPs. Review engine warning text and screenshots before posting them
to a public issue. This workflow is intended to make live debugging a fallback.
