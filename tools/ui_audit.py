#!/usr/bin/env python3
"""Arm/fetch a bounded UI census on robot1-x, or summarize an existing JSONL."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import re
import zipfile

PROFILE = '/mnt/c/Users/brian/AppData/Roaming/UnrealVRMod/FarFarWest-Win64-Shipping/data'


def remote(host, body, binary=False):
    script = "set -euo pipefail\npython3 - <<'FFW_AUDIT_PY'\n" + body + '\nFFW_AUDIT_PY\n'
    return subprocess.run(['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', host],
                          input=script.encode() if binary else script, text=not binary,
                          check=True, capture_output=True).stdout


def load_capture(source):
    records, meta, errors = {}, {}, []
    lines = source.splitlines()
    for number, line in enumerate(lines, 1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            # A running game/crash may leave only the final line incomplete.
            if number == len(lines):
                errors.append('Ignored incomplete final line')
                continue
            raise ValueError(f'Invalid JSON on line {number}') from None
        if record.get('type') == 'widget':
            key = record['id']
            if record.get('revision', 0) >= records.get(key, {}).get('revision', -1):
                records[key] = record
        elif record.get('type') == 'error':
            errors.append(record.get('message', 'Unknown capture error'))
        else:
            meta[record.get('type', 'unknown')] = record
    return records, meta, errors


def summarize(source, directory):
    return write_reports(*load_capture(source), directory)


def write_reports(records, meta, errors, directory):
    directory.mkdir(parents=True, exist_ok=True)
    rows = list(records.values())
    columns = ['audit_id', 'id', 'kind', 'class', 'root_class', 'path', 'parent', 'visible', 'seen',
               'edge_samples', 'x0', 'y0', 'x1', 'y1', 'x0_min', 'y0_min', 'x1_max', 'y1_max',
               'action', 'modes', 'flags', 'coverage', 'owners', 'component', 'space', 'contexts', 'fields',
               'owner_fields', 'attachment', 'relative_x', 'relative_y', 'relative_z', 'component_is_actor_root',
               'sessions', 'first_session', 'last_session', 'latest_coverage']

    def write_csv(name, selected):
        with (directory / name).open('w', newline='', encoding='utf-8') as out:
            writer = csv.DictWriter(out, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            for row in sorted(selected, key=lambda r: r['id']):
                row = dict(row, audit_id=widget_id(row['id']))
                writer.writerow({k: ';'.join(sorted(v)) if isinstance(v, dict) else v
                                 for k, v in row.items()})

    edges = [r for r in rows if 'edge_hud_candidate' in r.get('flags', {})]
    markers = [r for r in rows if 'unhandled_screen_marker_candidate' in r.get('flags', {}) and not r.get('coverage')]
    hints = [r for r in rows if r.get('action') == 'IA_Interact']
    write_csv('widgets.csv', rows)
    write_csv('edge-hud.csv', edges)
    write_csv('marker-candidates.csv', markers)
    write_csv('interaction-hints.csv', hints)
    families = sorted({(r.get('root_class') or r['class'], owner) for r in markers for owner in r.get('owners', {})})
    lines = [f'Catalog: {len(rows)} stable widget IDs.',
             f'Edge HUD candidates: {len(edges)}. Unhandled screen-marker families: {len(families)}.',
             f'IA_Interact hint contexts: {len(hints)}; keyboard presentation observed in '
             f'{sum("interact_keyboard_hint" in r.get("flags", {}) for r in hints)}.',
             f'Capture status: {meta.get("end", {}).get("reason", "active or interrupted; last checkpoint used")}.',
             'Candidates require review: bounds alone cannot prove headset clipping or tracking errors.',
             'Action-bound F hints are captured; arbitrary literal FText strings are unavailable.']
    if errors:
        lines.append(f'Capture/parse errors: {len(errors)}. See capture-errors.txt.')
        (directory / 'capture-errors.txt').write_text('\n'.join(errors) + '\n')
    if families:
        lines.extend(['', 'Unhandled marker widget / owner families:'] +
                     [f'- {widget} / {owner}' for widget, owner in families])
    text = '\n'.join(lines) + '\n'
    (directory / 'summary.txt').write_text(text)
    return text


def merge_captures(paths, archive):
    """Rebuild from each session's latest revisions; repeated collection is idempotent."""
    merged, sessions = {}, []
    for path in sorted(paths):
        rows, meta, errors = load_capture(path.read_text(encoding='utf-8'))
        session = path.relative_to(archive).with_suffix('').as_posix()
        end = meta.get('end', {})
        sessions.append({'id': session, 'widgets': len(rows),
                         'reason': end.get('reason', 'unfinished; last checkpoint'),
                         'elapsed': end.get('elapsed', max((r.get('last', 0) for r in rows.values()), default=0)),
                         'ended': bool(end), 'errors': max(end.get('errors', 0), len(errors)),
                         'dropped': end.get('dropped'), 'notes': errors})
        for key, row in rows.items():
            target = merged.setdefault(key, {'id': key, 'sessions': {}, 'first_session': session,
                                             'seen': 0, 'visible': 0, 'edge_samples': 0})
            target['audit_id'] = widget_id(key)
            target['sessions'][session] = True
            target['last_session'] = session
            target['latest_coverage'] = row.get('coverage', {})
            for name, value in row.items():
                if name in ('seen', 'visible', 'edge_samples'):
                    target[name] += value
                elif name in ('contexts', 'modes', 'owners', 'coverage', 'flags'):
                    target.setdefault(name, {}).update(value)
                elif name.endswith('_min'):
                    target[name] = min(target.get(name, value), value)
                elif name.endswith('_max'):
                    target[name] = max(target.get(name, value), value)
                elif name not in ('revision', 'first', 'last', 'dirty'):
                    target[name] = value
    return merged, sessions


def md(value):
    return str(value).replace('\\', '\\\\').replace('|', '\\|').replace('`', "'").replace('\n', ' ')


def widget_id(value):
    return 'w-' + hashlib.sha256(value.encode()).hexdigest()[:12]


def history_document(records, sessions):
    rows = list(records.values())
    candidates = [r for r in rows if r.get('flags')]
    edge = [r for r in rows if 'edge_hud_candidate' in r.get('flags', {})]
    markers = [r for r in rows if 'unhandled_screen_marker_candidate' in r.get('flags', {})]
    hints = [r for r in rows if 'interact_keyboard_hint' in r.get('flags', {})]
    families = sorted({(r.get('root_class') or r['class'], owner)
                       for r in markers for owner in r.get('owners', {})})
    covered_families = {(r.get('root_class') or r['class'], owner)
                        for r in markers if r.get('latest_coverage') for owner in r.get('owners', {})}
    uncovered = len(set(families)-covered_families)
    lines = ['# Gameplay UI findings', '',
             'Cumulative record of captured play sessions. Updated by '
             '`python3 tools/ui_audit.py collect`; previous sessions remain in the archive.', '',
             f'Updated {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}. '
             f'**{len(sessions)} {"session" if len(sessions)==1 else "sessions"}, '
             f'{len(rows):,} distinct {"widget ID" if len(rows)==1 else "widget IDs"}.**', '',
             f'{len(edge)} edge-HUD candidates, {uncovered} marker widget/owner families without '
             f'latest recorded coverage ({len(families)} historical), and {len(hints)} '
             f'interaction-hint {"context" if len(hints)==1 else "contexts"} with visible keyboard presentation.', '',
             'These are observations for review. Edge bounds do not prove headset clipping; '
             'screen components do not prove faulty tracking. Missing from a later session '
             'does not mean fixed. Arbitrary literal FText strings are not inspected.', '',
             '## Sessions', '', '| Session | Engine seconds | IDs | Skipped observations | Errors/parse notes | End |',
             '| --- | ---: | ---: | ---: | ---: | --- |']
    for s in sessions:
        duration = f"{s['elapsed']:.1f}" if s['ended'] else f"at least {s['elapsed']:.1f}"
        skipped=s.get('dropped')
        lines.append(f"| {md(s['id'])} | {duration} | {s['widgets']} | {skipped if skipped is not None else 'not recorded'} | {s['errors']} | {md(s['reason'])} |")
    lines += ['', 'A capture at its record or byte limit can omit late widget families. '
              'Skipped observations count attempts, not distinct IDs; older captures did not record that count.']
    lines += ['', '## HUD near the edges', '',
              'Bounds and widget paths are in the dictionary below. Diagnostic margins are '
              'configurable in `data/tuning.ini`; capture does not reposition HUD.', '',
              '| HUD root | Candidate IDs |', '| --- | ---: |']
    roots = {}
    for r in edge:
        root = r.get('root_class') or r['class']
        roots[root] = roots.get(root, 0) + 1
    for root, count in sorted(roots.items()):
        lines.append(f'| {md(root)} | {count} |')
    lines += ['', '## World-marker families', '',
              'Historical unhandled observations are retained even if coverage is observed later.', '',
              '| Widget class | World owner class | Latest coverage |', '| --- | --- | --- |']
    for widget, owner in families:
        state='correction observed' if (widget,owner) in covered_families else 'none recorded'
        lines.append(f'| {md(widget)} | {md(owner)} | {state} |')
    if not families:
        lines += ['| No unhandled visible screen components recorded | | |']
    lines += ['', '## Interaction hints that displayed keyboard input', '',
              '| ID | Widget path | Modes observed | Sessions |', '| --- | --- | --- | --- |']
    for r in sorted(hints, key=lambda r: r['id']):
        lines.append(f"| {widget_id(r['id'])} | `{md(r.get('path', ''))}` | "
                     f"{md(', '.join(sorted(r.get('modes', {}))))} | {len(r['sessions'])} |")
    if not hints:
        lines += ['| None recorded | | | |']
    lines += ['', '## Candidate dictionary', '',
              'IDs are stable SHA-256 abbreviations of the full class/path ID stored in '
              '`catalog.json` and the CSV reports. Coordinates are fractions of viewport '
              'width/height from the latest visible observation. Counts deduplicate session '
              'checkpoints. Each raw session keeps its original measurements.', '',
              '<details>', f'<summary>{len(candidates)} candidate widget IDs</summary>', '',
              '| ID | Type | Widget path | Bounds (left, top → right, bottom) | Sessions | Latest coverage |',
              '| --- | --- | --- | --- | ---: | --- |']
    for r in sorted(candidates, key=lambda r: r['id']):
        bounds = (f"{r['x0']:.3f}, {r['y0']:.3f} → {r['x1']:.3f}, {r['y1']:.3f}"
                  if 'x0' in r else 'not measured')
        category = ', '.join(sorted(r.get('flags', {}))).replace('_candidate', '')
        coverage = ', '.join(sorted(r.get('latest_coverage', {}))) or 'none recorded'
        lines.append(f"| {widget_id(r['id'])} | {md(category)} | `{md(r.get('path', ''))}` | "
                     f"{bounds} | {len(r['sessions'])} | {md(coverage)} |")
    lines += ['', '</details>', '']
    return '\n'.join(lines)


def write_history(archive, document):
    paths = list(archive.glob('*/ui-audit-*.jsonl'))
    records, sessions = merge_captures(paths, archive)
    document.parent.mkdir(parents=True, exist_ok=True)
    document.write_text(history_document(records, sessions), encoding='utf-8')
    reports = archive.parent / 'history'
    errors = [note for s in sessions for note in s['notes']]
    write_reports(records, {'end': {'reason': 'cumulative history'}}, errors, reports)
    (reports / 'catalog.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
    return f'{len(sessions)} {"session" if len(sessions)==1 else "sessions"}; {len(records):,} distinct IDs. Updated {document}'


def collect(host, archive, document):
    """Copy changed captures; rebuild from every locally archived session."""
    host_key = re.sub(r'[^a-zA-Z0-9_.-]', '_', host)
    if host_key in ('.', '..', ''):
        raise ValueError('Invalid archive host')
    dest = archive / host_key
    dest.mkdir(parents=True, exist_ok=True)
    manifest_path = dest / 'manifest.json'
    known = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    known = {name: stamp for name, stamp in known.items() if (dest / name).exists()}
    body = ('from pathlib import Path\nimport io, json, re, sys, zipfile\np=Path(' + repr(PROFILE) + ')\n'
            'known=' + repr(known) + '\n' + r'''
manifest={}
output=io.BytesIO()
with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for pth in sorted(p.glob('ui-audit-*.jsonl')):
  if not re.fullmatch(r'ui-audit-[0-9]+\.jsonl',pth.name): continue
  st=pth.stat();stamp=[st.st_size,st.st_mtime_ns]
  manifest[pth.name]=stamp
  if known.get(pth.name)!=stamp: z.write(pth,pth.name)
 for name in ['ui_audit_sessions.md','ui_audit_status.json']:
  pth=p/name
  if pth.exists(): z.write(pth,name)
 z.writestr('manifest.json',json.dumps(manifest))
sys.stdout.buffer.write(output.getvalue())
''')
    payload = remote(host, body, binary=True)
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        for info in z.infolist():
            name = info.filename
            if not (re.fullmatch(r'ui-audit-[0-9]+\.jsonl', name) or
                    name in ('manifest.json', 'ui_audit_sessions.md', 'ui_audit_status.json')):
                raise ValueError('Unexpected archive entry: ' + name)
            if info.file_size > 20 * 1024 * 1024:
                raise ValueError('Oversized capture: ' + name)
            tmp = (dest / name).with_suffix('.tmp')
            tmp.write_bytes(z.read(info));tmp.replace(dest / name)
    return write_history(archive, document)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('start', 'stop', 'status', 'fetch', 'collect'):
        p = sub.add_parser(name)
        p.add_argument('--host', default='robot1-x')
        if name == 'start':
            p.add_argument('--seconds', type=int, default=3600, choices=range(10, 3601), metavar='10..3600')
        if name == 'fetch':
            p.add_argument('--output', type=Path, default=Path('diagnostics/ui-audit'))
        if name == 'collect':
            p.add_argument('--archive', type=Path, default=Path('diagnostics/ui-audit/sessions'))
            p.add_argument('--document', type=Path, default=Path('docs/UI-FINDINGS.md'))
    p = sub.add_parser('report')
    p.add_argument('source', type=Path)
    p.add_argument('--output', type=Path, default=Path('diagnostics/ui-audit'))
    args = parser.parse_args()
    if args.command == 'collect':
        print(collect(args.host, args.archive, args.document))
        return
    if args.command == 'report':
        print(summarize(args.source.read_text(), args.output), end='')
        return
    prefix = 'from pathlib import Path\nimport json, re\np = Path(' + repr(PROFILE) + ')\n'
    if args.command in ('start', 'stop'):
        value = f'start {args.seconds}' if args.command == 'start' else 'stop'
        body = prefix + f"(p/'ui_audit_command.txt').write_text({value!r}+'\\n')\nprint({value!r})"
        print(remote(args.host, body).strip())
    elif args.command == 'status':
        print(remote(args.host, prefix + "f=p/'ui_audit_status.json'\nprint(f.read_text() if f.exists() else 'No capture status yet')").strip())
    else:
        body = prefix + "s=json.loads((p/'ui_audit_status.json').read_text())\nf=s['file']\nassert re.fullmatch(r'ui-audit-[0-9]+\\.jsonl',f)\nprint((p/f).read_text(),end='')"
        source = remote(args.host, body)
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / 'capture.jsonl').write_text(source)
        print(summarize(source, args.output), end='')


if __name__ == '__main__':
    main()
