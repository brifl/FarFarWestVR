# Gameplay UI capture

This optional read-only capture catalogs UI across normal play so we can address
widget families together. It changes no UI, controls, camera settings, or game
state. It requires the profile's `ffw-ue58-sdk-v1` backend.

The current capture is intended to identify missing edge HUD (health, shields,
ammo, cooldowns), additional world-marker families, and interaction hints that
switch back to keyboard presentation.

## Multiple play sessions

The installed [tuning.ini](../data/tuning.ini) enables `audit.auto_start = 1`.
Each game launch or **Reset scripts** starts a separate capture, limited to one
hour or 16 MiB. Earlier captures are preserved. The helper stays idle after that
limit or a manual Stop until the next launch/reset. Set `auto_start = 0` to prevent
automatic capture on future launches; Stop ends the current capture immediately.

The game automatically appends start/checkpoint/end counts to
`data/ui_audit_sessions.md` in the installed profile. An unfinished entry may mean
the game exited without a final script callback; its JSONL checkpoints survive.

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
python3 tools/ui_audit.py status
python3 tools/ui_audit.py stop
python3 tools/ui_audit.py fetch
```

Start also works during play. Fetch downloads only the most recent capture to
`diagnostics/ui-audit/`, including `summary.txt`, `widgets.csv`, `edge-hud.csv`,
`marker-candidates.csv`, `interaction-hints.csv`, and `capture.jsonl`. Fetch and
Collect work while recording or afterward. To summarize an individual archived file:

```bash
python3 tools/ui_audit.py report path/to/capture.jsonl
```

If SSH is unavailable, write `start 3600` or `stop` to
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
The capture stops after 3,600 seconds of engine time or at 16 MiB, with caps of
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
