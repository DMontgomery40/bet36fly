"""Compose every approved generated still into a gently moving full-HD shot."""
from pathlib import Path
import concurrent.futures
import hashlib
import json
import math
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'gpt-image-2.5-sunburst'


def render(scene):
    source = ROOT / scene['image_source_path']
    if not source.is_file():
        raise FileNotFoundError(source)
    frames = math.ceil(scene['duration_seconds'] * 24)
    dest = ROOT / scene['video_source_path']
    dest.parent.mkdir(parents=True, exist_ok=True)
    fingerprint = hashlib.sha256(source.read_bytes() + Path(__file__).read_bytes() + str(frames).encode()).hexdigest()
    stamp = dest.with_suffix('.json')
    if dest.exists() and stamp.exists() and json.loads(stamp.read_text())['fingerprint'] == fingerprint:
        return scene['id']
    # Full composition stays within the generated artwork's safe margins.
    z = f'1.006+0.018*on/{frames}' if scene['id'] % 2 == 0 else f'1.024-0.018*on/{frames}'
    vf = (f'scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,'
          f"zoompan=z='{z}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1920x1080:fps=24,"
          f'fade=t=in:st=0:d=0.18,fade=t=out:st={frames/24-.18}:d=0.18,format=yuv420p')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', '24', '-i', str(source),
                    '-vf', vf, '-frames:v', str(frames), '-an', '-c:v', 'libx264', '-crf', '19',
                    '-preset', 'veryfast', '-threads', '2', '-movflags', '+faststart', str(dest)], check=True)
    stamp.write_text(json.dumps({'fingerprint': fingerprint, 'model': MODEL,
                                 'source': str(source.relative_to(ROOT)), 'frames': frames}, indent=2) + '\n')
    print(f'rendered still {scene["id"]:02}', flush=True)
    return scene['id']


def main():
    plan = json.loads((ROOT / 'plan.json').read_text())
    assert all(s.get('image_source_path') for s in plan['scenes'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(render, plan['scenes']))


if __name__ == '__main__':
    main()
