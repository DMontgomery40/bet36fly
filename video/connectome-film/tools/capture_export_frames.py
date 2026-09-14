"""Extract early/middle/late samples from each actual delivered scene."""
from pathlib import Path
import concurrent.futures
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def capture(task):
    scene, label, proportion = task
    target = ROOT / f'qa/frames/{scene["id"]:02}-{label}.jpg'
    seconds = scene['start'] + scene['duration'] * proportion
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(seconds),
                    '-i', str(ROOT / 'bet36fly-connectomes.mp4'), '-frames:v', '1',
                    '-q:v', '2', str(target)], check=True)


if __name__ == '__main__':
    timeline = json.loads((ROOT / 'timeline.json').read_text())
    tasks = [(scene, label, proportion) for scene in timeline['scenes']
             for label, proportion in [('early', .18), ('mid', .53), ('late', .85)]]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(capture, tasks))
    subprocess.run(['python3', str(ROOT / 'tools/contact_sheets.py')], check=True)
    print(f'Extracted {len(tasks)} samples from the exported MP4.')
