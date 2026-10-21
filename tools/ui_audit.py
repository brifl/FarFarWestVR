#!/usr/bin/env python3
"""Arm/fetch a bounded UI census on robot1-x, or summarize an existing JSONL."""
import argparse
import csv
import json
from pathlib import Path
import subprocess

PROFILE = '/mnt/c/Users/brian/AppData/Roaming/UnrealVRMod/FarFarWest-Win64-Shipping/data'


def remote(host, body):
    script = "set -euo pipefail\npython3 - <<'FFW_AUDIT_PY'\n" + body + '\nFFW_AUDIT_PY\n'
    return subprocess.run(['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', host],
                          input=script, text=True, check=True, capture_output=True).stdout


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
    records, meta, errors = load_capture(source)
    directory.mkdir(parents=True, exist_ok=True)
    rows = list(records.values())
    columns = ['id', 'kind', 'class', 'root_class', 'path', 'parent', 'visible', 'seen',
               'edge_samples', 'x0', 'y0', 'x1', 'y1', 'x0_min', 'y0_min', 'x1_max', 'y1_max',
               'action', 'modes', 'flags', 'coverage', 'owners', 'component', 'space', 'contexts', 'fields',
               'owner_fields', 'attachment', 'relative_x', 'relative_y', 'relative_z', 'component_is_actor_root']

    def write_csv(name, selected):
        with (directory / name).open('w', newline='', encoding='utf-8') as out:
            writer = csv.DictWriter(out, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            for row in sorted(selected, key=lambda r: r['id']):
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('start', 'stop', 'status', 'fetch'):
        p = sub.add_parser(name)
        p.add_argument('--host', default='robot1-x')
        if name == 'start':
            p.add_argument('--seconds', type=int, default=3600, choices=range(10, 3601), metavar='10..3600')
        if name == 'fetch':
            p.add_argument('--output', type=Path, default=Path('diagnostics/ui-audit'))
    p = sub.add_parser('report')
    p.add_argument('source', type=Path)
    p.add_argument('--output', type=Path, default=Path('diagnostics/ui-audit'))
    args = parser.parse_args()
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
