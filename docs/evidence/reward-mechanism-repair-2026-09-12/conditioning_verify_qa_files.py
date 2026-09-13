"""Record/check protected file bytes around browser QA without opening databases."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCOPES = ('data', 'bet36fly', 'scripts', 'web/dist',
          'output/runs', 'output/experiments', 'output/native', 'output/diagnostics',
          'wiki/imports/microduck-2026-09-12')


def snapshot():
    paths = set()
    inventory = []
    for name in SCOPES:
        directory = ROOT / name
        if directory.exists():
            inventory.append(name + '/')
            for path in directory.rglob('*'):
                inventory.append(str(path.relative_to(ROOT)) + ('/' if path.is_dir() else ''))
                if path.is_file():
                    paths.add(path)
    paths.update(path for path in (ROOT / 'output').iterdir() if path.is_file())
    files = {}
    for path in sorted(paths):
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        files[str(path.relative_to(ROOT))] = {'sha256': digest, 'bytes': path.stat().st_size}
    return {'root': str(ROOT), 'scopes': list(SCOPES),
            'inventory': sorted(inventory), 'files': files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--result', type=Path)
    args = parser.parse_args()
    current = snapshot()
    now = datetime.now(timezone.utc).isoformat()
    if args.result is None:
        with args.baseline.open('x') as stream:
            json.dump({'checked_at': now, **current}, stream, indent=2)
            stream.write('\n')
        print(json.dumps({'baseline': str(args.baseline), 'files': len(current['files']),
                          'bytes': sum(item['bytes'] for item in current['files'].values())}))
        return
    baseline = json.loads(args.baseline.read_text())
    old, new = baseline['files'], current['files']
    changes = {name: {'before': old.get(name), 'after': new.get(name)}
               for name in sorted(old.keys() | new.keys()) if old.get(name) != new.get(name)}
    inventory_changed = baseline['inventory'] != current['inventory']
    result = {'checked_at': now, 'baseline': str(args.baseline), 'files_checked': len(new),
              'file_changes': changes, 'inventory_changed': inventory_changed,
              'added_entries': sorted(set(current['inventory']) - set(baseline['inventory'])),
              'removed_entries': sorted(set(baseline['inventory']) - set(current['inventory'])),
              'passed': not changes and not inventory_changed}
    with args.result.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result))
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
