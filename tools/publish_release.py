#!/usr/bin/env python3
"""Publish the tested profile/installer assets, using the GitHub Actions token or GITHUB_TOKEN."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def validate(directory, tag):
    release = json.loads((ROOT/'release.json').read_text())
    if tag != 'v' + release['version'] or release.get('runtime_included') is not False:
        raise ValueError('Tag/version mismatch, or an unsupported runtime redistribution request')
    expected = {f"FarFarWestVR-{release['version']}-{kind}.zip" for kind in ('Profile', 'Setup')}
    found = set()
    for line in (directory/'SHA256SUMS.txt').read_text().splitlines():
        m = re.fullmatch(r'([0-9a-f]{64})  ([A-Za-z0-9.-]+\.zip)', line)
        if not m or m[2] not in expected or m[2] in found:
            raise ValueError('Unexpected or duplicate release checksum entry')
        if hashlib.sha256((directory/m[2]).read_bytes()).hexdigest() != m[1]:
            raise ValueError(f'Checksum mismatch: {m[2]}')
        found.add(m[2])
    if found != expected:
        raise ValueError('Missing release assets')
    notes = ROOT/'docs'/'releases'/(tag + '.md')
    return release, notes.read_text(), [directory/p for p in sorted(expected)] + [directory/'SHA256SUMS.txt']


def publish(directory, tag, check=False):
    release, notes, assets = validate(directory, tag)
    if check:
        print(f'{tag}: release assets/checksums/notes validated; no network writes.')
        return
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if not token:
        raise SystemExit('Set GITHUB_TOKEN with repository contents:write permission, or push the version tag to run the release workflow.')
    repo = os.environ.get('GITHUB_REPOSITORY', 'brifl/FarFarWestVR')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
        raise ValueError('Invalid repository')
    base = 'https://api.github.com/repos/' + repo

    def request(method, url, body=None, binary=False):
        headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                   'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'FarFarWestVR-release',
                   'Content-Type': 'application/octet-stream' if binary else 'application/json'}
        data = body if binary else json.dumps(body).encode() if body is not None else None
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers, method=method), timeout=120) as response:
            content = response.read()
            return json.loads(content) if content else None

    try:
        draft = request('GET', base + '/releases/tags/' + tag)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        draft = request('POST', base + '/releases', {
            'tag_name': tag, 'name': f"Far Far West VR {release['version']} - First public beta",
            'body': notes, 'draft': True, 'prerelease': True,
        })
    if not draft['draft']:
        raise SystemExit('This release is already public; create a new version instead of replacing published assets.')
    endpoint = base + '/releases/' + str(draft['id'])
    for asset in assets:
        for old in draft.get('assets', []):
            if old['name'] == asset.name:
                request('DELETE', base + '/releases/assets/' + str(old['id']))
        upload = draft['upload_url'].split('{')[0] + '?name=' + urllib.parse.quote(asset.name)
        request('POST', upload, asset.read_bytes(), binary=True)
    uploaded = request('GET', endpoint)
    sizes = {a['name']: a['size'] for a in uploaded['assets']}
    if any(sizes.get(a.name) != a.stat().st_size for a in assets):
        raise RuntimeError('Uploaded asset verification failed; the release remains a draft')
    result = request('PATCH', endpoint, {'draft': False, 'prerelease': True, 'body': notes})
    print('Published:', result['html_url'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT/'dist')
    parser.add_argument('--tag', required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    publish(args.directory, args.tag, args.check)
