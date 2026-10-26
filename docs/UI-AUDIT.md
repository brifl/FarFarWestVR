# Gameplay UI capture

This optional read-only capture catalogs UI across normal play so we can address
widget families together. It changes no UI, controls, camera settings, or game
state. It requires the profile's `ffw-ue58-sdk-v1` backend.

The current capture is intended to identify missing edge HUD (health, shields,
ammo, cooldowns), additional world-marker families, and interaction hints that
switch back to keyboard presentation.

## Multiple play sessions

The development [tuning.ini](../data/tuning.ini) enables `audit.auto_start = 1`.
Public release ZIPs default to `0`; set it to `1` to opt in for troubleshooting.
Each game launch starts a one-hour monitoring window by default. Recording rotates
into a fresh capture every 30 minutes, or sooner if a file reaches 16 MiB, so late
missions get fresh ID capacity. Earlier captures and their final status are preserved.
A window is limited to 12 files (192 MiB of capture data). The helper stays idle after the
window, segment limit, or a manual Stop until the next launch or Start command.
Set `auto_start = 0` to prevent
automatic capture on future launches; Stop ends the current capture immediately.

The game automatically appends start/checkpoint/end counts to
`data/ui_audit_sessions.md` in the installed profile. An unfinished entry may mean
the game exited without a final script callback; its JSONL checkpoints survive.
Five-minute JSONL checkpoints also record current and peak UObject slot counts
for diagnosing growth over long sessions. This adds no object census or gameplay
writes. Status includes the remaining monitoring time. One gameplay session may
produce several capture files; each appears separately in the cumulative report.

The repository's cumulative findings document is
[UI-FINDINGS.md](UI-FINDINGS.md). Refresh it at check-ins from the development
machine using the existing SSH-to-WSL workflow on **robot1-x**:

```bash
python3 tools/ui_audit.py collect
```

Collect copies only changed captures, keeps a local archive of all sessions under
`diagnostics/ui-audit/sessions/`, and rebuilds the document and combined reports.
The document is tracked in Git; raw captures and generated CSV/JSON reports are
ignored. They also remain in the installed profile. Collecting again replaces the
same session's checkpoint instead of double-counting its observations. Interrupted
sessions and historical problems remain visible even when coverage is recorded
later. Files already archived locally remain in history if removed from the
installed profile.

The combined CSV reports and full stable-ID catalog are in
`diagnostics/ui-audit/history/`. The Markdown dictionary contains flagged candidates
with stable abbreviated IDs, widget paths, coordinates, and session counts. The
CSV and JSON include both abbreviated IDs and the full class/path IDs.

The cumulative repository document refreshes when Collect runs; no background SSH
service is required. The game's session ledger updates automatically while playing.

## Manual capture controls

```bash
python3 tools/ui_audit.py start
python3 tools/ui_audit.py start --seconds 9000
python3 tools/ui_audit.py status
python3 tools/ui_audit.py stop
python3 tools/ui_audit.py fetch
```

The second Start example arms 2½ hours, including a buffer around a two-hour play
session. Start accepts 10–10,800 engine seconds and also works during play or can
be armed before launch. Its command is consumed when the scripts load.
Fetch downloads only the most recent capture to
`diagnostics/ui-audit/`, including `summary.txt`, `widgets.csv`, `edge-hud.csv`,
`marker-candidates.csv`, `interaction-hints.csv`, and `capture.jsonl`. Fetch and
Collect work while recording or afterward. To summarize an individual archived file:

```bash
python3 tools/ui_audit.py report path/to/capture.jsonl
```

If SSH is unavailable, write `start 3600`, `start 9000`, or `stop` to
`data/ui_audit_command.txt` in the installed profile. After deploying new Lua
helpers, relaunch the game normally; script reset is unreliable in this profile. Play normally;
there is no need to hold a particular screen open or reproduce each case separately.

## HUD margins and capture thresholds

In [data/tuning.ini](../data/tuning.ini):

```ini
[hud]
left_margin = 0.20
right_margin = 0.20
top_margin = 0.15
bottom_margin = 0.30
scale_multiplier = 0.85
aspect_correction = 1

[audit]
auto_start = 1
```

Each edge reserves its own fraction of viewport width/height. Numeric changes
reload during play. The HUD placement helper moves selected fixed groups
(health/shield, weapons/ammo, spells/cooldowns, party health, currency/level,
control hints and tweak indicators) inside that rectangle during gameplay.
Size and aspect correction preserve each group's internal layout; oversized
groups are centered. Setting both margins on an axis to zero restores native placement there.
World markers, reticles, full-screen effects, and separately height-controlled
panels are excluded. Menus/reset restore the helper's owned translations.

The capture uses the same values to flag candidates. Earlier versions used
`[audit]` margins only for capture classification; those keys remain aliases, but
explicit `[hud]` values win. The read-only capture itself still changes no UI.

## What gets recorded

- Stable IDs made from class asset paths and widget hierarchy names. Generated
  instance-number suffixes are removed; designer names such as `Text_Key_1` stay
  distinct. Repeated instances aggregate under their widget type/hierarchy.
- Visible bounds normalized to viewport width/height, extrema over time, edge
  samples, parent paths, and map/gameplay/menu context. Hidden ancestors and
  detached widgets do not count as visible edge HUD.
- Screen/world widget components, owner classes, attachment names, relative
  offsets, and reflected widget/owner property names and offsets. Existing marker
  helpers publish metadata so corrected sources/proxies are distinguished from
  unhandled candidates. Tracking faults are candidates for review, not diagnoses
  made from position alone.
- `UI_Key_C` action bindings and keyboard/gamepad presentation modes. An
  `IA_Interact` keyboard presentation identifies the game's normal F-hint path.
  Lua cannot read arbitrary FText strings in this backend, so literal `[F]` text
  embedded outside action-key widgets is **not** recognized automatically. Those
  widgets still appear in the general hierarchy catalog.

No player names, dialogue/chat strings, save files, or raw game memory are dumped.
The widget asset paths and map names are diagnostic metadata.

Discovery is incremental (up to 16 widgets and 256 UObject entries per engine
tick, with a soft 0.75 ms Lua work budget). Native calls and checkpoint writes may
exceed that soft budget; the status file reports the largest observed active tick.
Viewport roots seed nested widget traversal, and discovered WidgetComponents
explicitly seed their screen/world widgets. The native query no longer includes
every retained UserWidget: that broad query stopped capture 16 after seven minutes
when it exceeded 1,024 results. The query budget stays unchanged. Collect retains
per-session status files so a known failed capture stays identified in history;
new failures also write explicit error/end records when the output remains writable.
The native object-array count is validated as a positive int32 separately from
per-frame work limits; the old 250,000-slot probe guard stopped capture 17 and
other helpers during a long session. Native slot counts are not live-widget counts.
Each capture segment rotates after 1,800 seconds of engine time or at 16 MiB, with caps of
4,096 catalog IDs, 8,192 queued widgets, 2,048 component associations, and 512 class
schemas. Capture 15 reached the ID limit before every late multiplayer family
could be recorded. New captures reserve 1,024 slots for screen-marker roots,
visible action hints, and visible gameplay edge candidates, so retained menu
trees cannot consume the entire catalog first. End records include skipped
observation counts; these count attempts, not distinct missing IDs. Older captures
do not have those end counts. Reaching a limit still makes a capture incomplete.
New IDs, new contexts/modes/flags, and bounds-extrema changes of at least two
percentage points checkpoint about every 30 seconds in small batches. Repeated
static samples update in-memory totals without filling the file; stopping writes
final totals for every ID. The status includes errors and dropped samples so an incomplete sweep is visible.

## October 25 multiplayer review

Captures 26–30 completed the full 9,000-engine-second monitoring window with no
capture errors or helper shutdowns in the matching UEVR log. Segment 29 skipped
295 ordinary observation attempts at its ID reservation; the other four skipped
none. These counts do not identify distinct omitted widgets. Object-array slots
rose from 97,165 to 181,830 and then stayed at that high-water count through the
remaining checkpoints. Slot counts alone cannot establish live-object growth.

Coverage was recorded for objective markers, tagged objects, teammates, health
bars, and damage numbers. This confirms the adapters ran, not visual correctness
of every instance. All recorded interaction-key modes were gamepad presentation.
NPC labels had no visible samples in this window.

The review added shared content-group proportion corrections for short messages,
disturbance notices, teammate-death notices, and the Cryptic Snake status meter.
Two health-bar attachment rejections also exposed a retry/lifetime problem:
incomplete chains now wait, and replaced/reused widget identities can bind again.
Future rejection/deferred-attachment logs include widget/owner class and component
name for correlation without capturing player names or dialogue.

The separate `UI_Locator_C` directional overlay still needs a visible example.
It has a world location and attachment reference, but no WidgetComponent, and
its Border is rotated/animated. Its geometry alone does not establish the correct
tracking behavior. A brief symptom and approximate time are useful for this and
literal text hints; the captured class dictionary supplies the corresponding IDs.
