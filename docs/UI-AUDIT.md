# Gameplay UI capture

This optional read-only capture catalogs UI across normal play so we can address
widget families together. It changes no UI, controls, camera settings, or game
state. It requires the profile's `ffw-ue58-sdk-v1` backend.

The current capture is intended to identify missing edge HUD (health, shields,
ammo, cooldowns), additional world-marker families, and interaction hints that
switch back to keyboard presentation.

## Capture a session

Run these commands from this repository on the development machine. The tool
uses the existing SSH-to-WSL workflow on **robot1-x**.

```bash
python3 tools/ui_audit.py start
python3 tools/ui_audit.py status
```

After deploying new scripts, restart the game or use **UEVR → Main → Reset
scripts**. Start arms the next loaded helper; it also works during play once the
helper is loaded. Play normally for up to one hour, including menus, conversations,
missions, and any uncommon marker/hint cases. There is no need to reproduce each
case separately or keep a particular screen open.

```bash
python3 tools/ui_audit.py stop
python3 tools/ui_audit.py fetch
```

Fetching works while the capture is active or afterward. Results go to
`diagnostics/ui-audit/`: `summary.txt`, `widgets.csv`, `edge-hud.csv`,
`marker-candidates.csv`, `interaction-hints.csv`, and the original `capture.jsonl`.
The CSV files are suitable for sorting/filtering. To summarize an archived file:

```bash
python3 tools/ui_audit.py report path/to/capture.jsonl
```

If SSH is unavailable, write `start 3600` or `stop` to
`data/ui_audit_command.txt` in the installed profile. Raw captures and status live
in that same directory and are ignored by Git. Each capture gets a new filename;
starting another capture preserves earlier ones. Resetting scripts or restarting
the game ends the current capture; issue Start again for another session. A crash
retains the last flushed checkpoint. The helper is otherwise idle.

## Safe-area thresholds

In [data/tuning.ini](../data/tuning.ini):

```ini
[audit]
horizontal_margin = 0.10
vertical_margin = 0.15
```

These mean ten percent of viewport width at **each** horizontal edge and fifteen
percent of height at **each** vertical edge. Numeric changes reload during play.
They classify candidates in the capture; **they do not move widgets**. This first
pass avoids shifting full-screen effects, reticles, world markers, and fixed HUD
indiscriminately. The resulting parent paths and native field names let us choose
appropriate HUD groups for a later shared positioning rule.

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
The capture stops after 3,600 seconds of engine time or at 16 MiB, with caps of
4,096 catalog IDs, 8,192 queued widgets, 2,048 component associations, and 512 class
schemas. New IDs, new contexts/modes/flags, and bounds-extrema changes of at least two
percentage points checkpoint about every 30 seconds in small batches. Repeated
static samples update in-memory totals without filling the file; stopping writes
final totals for every ID. The
status includes errors and dropped samples so an incomplete sweep is visible.
