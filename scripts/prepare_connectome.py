"""Download hash-pinned official data and prepare the complete neuronal graph."""
from pathlib import Path
import json
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bet36fly.connectome import ROOT, digest, prepare


def main():
    lock = json.loads((ROOT / 'docs/connectome-source-lock.json').read_text())
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    for name, source in lock.items():
        destination = raw / name
        if destination.exists() and digest(destination) == source['sha256']:
            print(f'Verified {name}', flush=True)
            continue
        partial = destination.with_suffix('.partial')
        print(f'Downloading official data: {name} ({source["bytes"]:,} bytes)', flush=True)
        with urllib.request.urlopen(source['url'], timeout=120) as response, partial.open('wb') as target:
            while chunk := response.read(8 * 1024 * 1024):
                target.write(chunk)
        if digest(partial) != source['sha256']:
            raise ValueError(f'Hash mismatch for {name}; downloaded data was not installed.')
        partial.replace(destination)
    print(json.dumps(prepare(), indent=2))


if __name__ == '__main__':
    main()
