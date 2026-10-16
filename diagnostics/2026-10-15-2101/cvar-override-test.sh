#!/usr/bin/env bash
# Prepared only. Changes the installed profile only when run with "apply".
set -euo pipefail
mode="${1:-}"
case "$mode" in
  apply|rollback) ;;
  *) printf 'Usage: bash %s apply|rollback\n' "$0" >&2; exit 2 ;;
esac

# robot1-x's SSH shell accepts WSL commands through stdin.
{
  printf 'mode=%s\n' "$mode"
  cat <<'REMOTE'
set -euo pipefail
python3 - "$mode" <<'PY'
import hashlib
import os
from pathlib import Path
import sys
import tempfile

profile = Path('/mnt/c/Users/brian/AppData/Roaming/UnrealVRMod/FarFarWest-Win64-Shipping')
target = profile / 'cvars_standard.txt'
backup = profile / 'cvars_standard.txt.pre-shadow-freeze-test-20261015-2101.bak'
expected = '1f7211d737209924829d24a68c7e08fce6f686d629c24396c8a0dd10136aa1c3'
entry = b'Renderer_r.Shadow.Virtual.Enable=1'
digest = lambda data: hashlib.sha256(data).hexdigest()

def patched(data):
    lines = data.splitlines(keepends=True)
    if sum(line.rstrip(b'\r\n') == entry for line in lines) != 1:
        raise SystemExit('Expected exactly one shadow override; no change made.')
    return b''.join(line for line in lines if line.rstrip(b'\r\n') != entry)

def replace(data):
    fd, name = tempfile.mkstemp(prefix='.cvar-shadow-test-', dir=profile)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, target)
    finally:
        if os.path.exists(name):
            os.unlink(name)

current = target.read_bytes()
if sys.argv[1] == 'apply':
    if digest(current) != expected:
        raise SystemExit('Profile differs from the diagnosed version; no change made.')
    candidate = patched(current)
    if backup.exists():
        if backup.read_bytes() != current:
            raise SystemExit('Backup differs from the original; no change made.')
    else:
        with backup.open('xb') as stream:
            stream.write(current)
            stream.flush()
            os.fsync(stream.fileno())
    replace(candidate)
    print('Removed only Renderer_r.Shadow.Virtual.Enable=1.')
    print('Backup:', backup)
else:
    original = backup.read_bytes()
    if digest(original) != expected:
        raise SystemExit('Backup hash mismatch; no change made.')
    if current == original:
        print('Original already restored.')
    elif current == patched(original):
        replace(original)
        print('Original cvars_standard.txt restored; backup retained.')
    else:
        raise SystemExit('Profile changed since the test; refusing to overwrite it.')
PY
REMOTE
} | ssh -T -o BatchMode=yes -o ConnectTimeout=10 robot1-x
