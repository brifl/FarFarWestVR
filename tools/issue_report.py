#!/usr/bin/env python3
"""Collect gesture reports and correlate manually supplied screenshots by timestamp."""
import argparse
from collections import Counter
import io
import json
from pathlib import Path
import re
import zipfile

from ui_audit import PROFILE, remote, widget_id

ISSUE = r'issue-\d{8}T\d{6}Z-\d+\.jsonl'
DIGEST = r'log-digest-\d{8}T\d{6}Z(?:-\d+)?\.json'


def read_issue(path):
    result = {'file': path.name, 'definitions': {}, 'samples': [], 'logs': Counter(), 'notes': []}
    lines = path.read_text(encoding='utf-8').splitlines()
    for i, line in enumerate(lines):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            if i == len(lines)-1:
                result['notes'].append('Incomplete final line'); break
            raise
        kind = row.get('type')
        if kind == 'issue': result.update(row)
        elif kind == 'definition': result['definitions'][row['key']] = row
        elif kind == 'sample': result['samples'].append(row)
        elif kind == 'log_count': result['logs'][row['key']] += row['count']
        elif kind == 'end': result['end'] = row
    if 'end' not in result: result['notes'].append('Report still writing or interrupted')
    elif result['end'].get('truncated'): result['notes'].append('File-size limit reached; report is incomplete')
    if result.get('end',{}).get('skipped_samples',0):
        result['notes'].append(f"Recorder budget skipped {result['end']['skipped_samples']} observations since script load")
    return result


def match_screenshots(issues, images, tolerance=30):
    matches, unmatched = {x['file']: [] for x in issues}, []
    for name, info in sorted(images.items()):
        explicit = next((x for x in issues if Path(name).stem.startswith(Path(x['file']).stem)), None)
        choices = [x for x in issues if isinstance(x.get('unix_time'), (int, float))]
        nearest = explicit or (min(choices, key=lambda x: abs(info['mtime']-x['unix_time'])) if choices else None)
        delta = info['mtime']-nearest['unix_time'] if nearest and isinstance(nearest.get('unix_time'),(int,float)) else None
        if explicit or (nearest and abs(delta) <= tolerance):
            matches[nearest['file']].append((name, delta, bool(explicit)))
        else: unmatched.append(name)
    return matches, unmatched


def markdown(value):
    return str(value).replace('|', '\\|').replace('`', "'").replace('\n', ' ')


def write_report(directory, tolerance=30):
    issues = [read_issue(p) for p in sorted(directory.glob('issue-*.jsonl'))]
    index_path = directory/'source-files.json'
    index = json.loads(index_path.read_text()) if index_path.exists() else {}
    images = {k: v for k, v in index.items() if k.startswith('screenshots/') and (directory/k).exists()}
    local_images=directory/'screenshots'
    if local_images.exists():
        for path in local_images.iterdir():
            if path.is_file() and path.suffix.lower() in ('.png','.jpg','.jpeg'):
                images.setdefault('screenshots/'+path.name,{'mtime':path.stat().st_mtime})
    matches, unmatched = match_screenshots(issues, images, tolerance)
    lines = ['# Marked VR issues', '',
             'Local diagnostic files only. Screenshots are supplied manually through Virtual Desktop/SteamVR.',
             'The marker records the preceding ten seconds and up to five seconds afterward; it does not record video.',
             f'Screenshot matches use preserved file modification times within ±{tolerance}s. They are suggestions, not proof.', '',
             '| Marker | Local time / UTC | Samples | Screenshots |', '| --- | --- | ---: | --- |']
    for issue in issues:
        links = ', '.join(f'[{markdown(Path(n).name)}](<{n}>) '+(f'({d:+.0f}s)' if d is not None else '(explicit)') for n, d, _ in matches[issue['file']]) or 'none matched'
        lines.append(f"| [{markdown(issue['file'])}]({issue['file']}) | {markdown(issue.get('local_time','?'))} / {markdown(issue.get('utc','?'))} | {len(issue['samples'])} | {links} |")
    for issue in issues:
        lines += ['', '## ' + issue['file'], '',
                  f"Reason: {markdown(issue.get('reason','?'))}. " + '; '.join(issue['notes']), '']
        owners = sorted({d['metadata'].get('owner_class', '') for d in issue['definitions'].values()} - {''})
        if owners:
            lines += ['Marker owner families:', ''] + ['- `' + markdown(x) + '`' for x in owners[:40]] + ['']
        targets=set()
        for sample in issue['samples']:
            for group in sample.get('references',{}).values():
                for ref in group.values():
                    targets.update(x for x in (ref.get('class'),ref.get('outer_class')) if x)
        if targets:
            lines += ['Referenced target/attachment families:', ''] + ['- `'+markdown(x)+'`' for x in sorted(targets)[:40]] + ['']
        candidates = {}
        for sample in issue['samples']:
            d = issue['definitions'].get(sample['definition'])
            if d and (sample.get('flag') or d['metadata'].get('fields') or d['metadata'].get('kind') in ('marker_tracking','shape_adapter')):
                candidates[d['id']] = d
        lines += ['Relevant widget/tracking IDs:', '', '| ID | Class/path |', '| --- | --- |']
        for key, d in sorted(candidates.items())[:80]:
            lines.append(f"| {widget_id(key)} | `{markdown(d['metadata'].get('class',''))}` / `{markdown(d['metadata'].get('path',''))}` |")
        if issue['logs']:
            lines += ['', 'Messages in the captured window:', '', '| Message key | Count |', '| --- | ---: |']
            lines += [f'| `{markdown(key)}` | {count} |' for key, count in issue['logs'].most_common(30)]
        note = directory/(Path(issue['file']).stem + '.notes.md')
        if note.exists(): lines += ['', f'[Your notes]({note.name})']
    totals = Counter(); messages = {}; gesture_sessions=[]; performance_sessions=[]; overflow=0
    for path in sorted(directory.glob('log-digest-*.json')):
        digest = json.loads(path.read_text())
        overflow+=digest.get('overflow',0)
        if digest.get('gesture'): gesture_sessions.append((path.name,digest['gesture']))
        if digest.get('performance'): performance_sessions.append((path.name,digest['performance']))
        for key, value in digest.get('messages', {}).items():
            # Older captures included Unreal's changing frame prefix in the key.
            # Merge those existing counters without altering the archived evidence.
            value=dict(value,message=value['message'].strip())
            if value.get('source')=='game':
                value['message']=re.sub(r'^\[\s*[0-9]+\]\s*','',value['message'])
                key='game:'+value['message']
            totals[key] += value['count']; messages[key] = value
    if gesture_sessions:
        lines += ['', '## Gesture recognition', '',
                  'Trigger counts are sampled frames, not separate presses. Failed chords retain their geometry and detector state in the session digest.', '',
                  '| Session | Ready frames | Left / right trigger frames | Both-trigger attempts | Marked | Last result / closest result |',
                  '| --- | ---: | ---: | ---: | ---: | --- |']
        for name,g in gesture_sessions:
            last=g.get('last_attempt',{}).get('reason',g.get('state','?'))
            closest=g.get('closest_attempt',{}).get('attempt',{}).get('reason','none recorded')
            lines.append(f"| [{name}]({name}) | {g.get('ready_frames',0)} / {g.get('frames',0)} | "
                         f"{g.get('left_trigger_frames',0)} / {g.get('right_trigger_frames',0)} | "
                         f"{g.get('attempts',0)} | {g.get('marked',0)} | {markdown(last)} / {markdown(closest)} |")
    if performance_sessions:
        performance_notes=[]
        lines += ['', '## Performance history', '',
                  'Engine delta and Lua callback wall times are separate from headset delivery. Native samples are read every five seconds; GPU timing is an instantaneous OpenVR sample. Cumulative dropped/reprojected counts and bounded 30-second history remain in each digest.', '',
                  '| Session | Worst engine delta ms | Worst Lua callback ms | Latest working set / private MiB | OpenVR dropped / reprojected |',
                  '| --- | ---: | ---: | ---: | ---: |']
        for name,p in performance_sessions:
            peak=p.get('peak',{});latest=p.get('latest',{})
            lines.append(f"| [{name}]({name}) | {peak.get('engine_delta_ms','?')} | {peak.get('lua_callback_ms','?')} | "
                         f"{latest.get('ws','?')} / {latest.get('commit','?')} | {latest.get('drop','?')} / {latest.get('reproj','?')} |")
            if p.get('discarded_history',0): performance_notes.append(f"{name}: {p['discarded_history']} oldest history records expired at the bounded retention limit.")
        for note in performance_notes: lines += ['',note]
    lines += ['', '## Repeated messages across collected sessions', '',
              'One dictionary entry and counter per message. Counts cover the tailed intervals; raw UEVR/plugin logs are unchanged.', '',
              '| Message | Count | Documented |', '| --- | ---: | --- |']
    ordered=sorted(totals,key=lambda key:(messages[key].get('documented',False),messages[key].get('severity')!='error',-totals[key],key))
    for key in ordered[:50]:
        count=totals[key]
        value = messages[key]
        lines.append(f"| `{markdown(value['message'])}` | {count} | {'yes' if value.get('documented') else 'no'} |")
    if overflow:
        lines += ['',f'Dictionary capacity omitted {overflow} message observations across these sessions. Counts are incomplete; the raw logs retain those messages.']
    if unmatched: lines += ['', '## Unmatched screenshots', ''] + [f'- [{markdown(n)}](<{n}>)' for n in unmatched]
    lines += ['', 'Rename an image with an issue filename prefix to associate it explicitly. '
              'Keep personal notes in a same-named `.notes.md` file; regenerating this report preserves them.', '']
    (directory/'REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    return len(issues), sum(len(v) for v in matches.values()), len(unmatched)


def collect(host, output, screenshots=None):
    host_key = re.sub(r'[^A-Za-z0-9_.-]', '_', host)
    if host_key in ('', '.', '..'): raise ValueError('Invalid host')
    dest = output/host_key;dest.mkdir(parents=True, exist_ok=True)
    index_path = dest/'source-files.json'
    known = json.loads(index_path.read_text()) if index_path.exists() else {}
    known = {k:v for k,v in known.items() if (dest/k).exists()}
    body = ('from pathlib import Path\nimport io,json,re,sys,zipfile\np=Path(' + repr(PROFILE) + ')\n'
            + 'images=Path(' + repr(screenshots or PROFILE + '/issue_screenshots') + ')\nknown=' + repr(known) + '\n' + r'''
files=[(f.name,f) for pattern in ['issue-*.jsonl','log-digest-*.json'] for f in p.glob(pattern)]
files += [('screenshots/'+f.name,f) for f in images.iterdir() if f.is_file() and f.suffix.lower() in ('.png','.jpg','.jpeg')] if images.exists() else []
index={};size=0;output=io.BytesIO()
with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,strict_timestamps=False) as z:
 for name,f in sorted(files):
  if not (re.fullmatch(r'issue-[0-9]{8}T[0-9]{6}Z-[0-9]+[.]jsonl',name) or re.fullmatch(r'log-digest-[0-9]{8}T[0-9]{6}Z(?:-[0-9]+)?[.]json',name) or name.startswith('screenshots/')): continue
  st=f.stat();info={'size':st.st_size,'mtime':st.st_mtime,'mtime_ns':st.st_mtime_ns};index[name]=info
  if known.get(name)==info: continue
  if st.st_size>20*1024*1024: raise ValueError('File exceeds 20 MiB: '+name)
  size+=st.st_size
  if size>128*1024*1024: raise ValueError('Changed files exceed 128 MiB; collect a smaller screenshot folder')
  z.write(f,name)
 z.writestr('source-files.json',json.dumps(index))
sys.stdout.buffer.write(output.getvalue())
''')
    payload = remote(host, body, binary=True)
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        for info in z.infolist():
            name = info.filename
            safe_image = bool(re.fullmatch(r'screenshots/[^/\\:]+\.(?i:png|jpg|jpeg)', name)) and '..' not in Path(name).parts
            if not (re.fullmatch(ISSUE, name) or re.fullmatch(DIGEST, name) or name == 'source-files.json' or safe_image):
                raise ValueError('Unexpected entry: ' + name)
            if info.file_size > 20*1024*1024: raise ValueError('Oversized entry')
            if name=='source-files.json':
                incoming=json.loads(z.read(info));continue
            target = dest/name;target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(info))
    known.update(incoming)
    index_path.write_text(json.dumps(known,indent=2)+'\n',encoding='utf-8')
    return dest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('collect','report','mark'))
    parser.add_argument('--host', default='robot1-x')
    parser.add_argument('--output', type=Path, default=Path('diagnostics/issues'))
    parser.add_argument('--screenshots', help='Remote screenshot folder; default: profile/data/issue_screenshots')
    parser.add_argument('--tolerance', type=int, default=30)
    args = parser.parse_args()
    if args.command == 'mark':
        payload='mark\n'
        body="from pathlib import Path\n(Path(" + repr(PROFILE) + ")/'issue_capture_command.txt').write_text("+repr(payload)+")\nprint('Marker requested')"
        print(remote(args.host,body).strip())
        return
    directory = collect(args.host,args.output,args.screenshots) if args.command == 'collect' else args.output
    issues, matched, unmatched = write_report(directory,args.tolerance)
    print(f'{issues} issue reports; {matched} matched / {unmatched} unmatched screenshots. {directory}/REPORT.md')


if __name__ == '__main__': main()
