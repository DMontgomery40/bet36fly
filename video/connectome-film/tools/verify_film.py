"""Verify the factory export, approved narration, reused images and delivery media."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

from production_contract import validate_plan

ROOT = Path(__file__).resolve().parents[1]


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-show_format', '-show_chapters',
        '-of', 'json', str(path),
    ]))


def main():
    plan = json.loads((ROOT / 'plan.json').read_text())
    approval = json.loads((ROOT / 'qa/claude-v4/approval.json').read_text())
    accepted = json.loads((ROOT / 'sources/accepted-image-hashes.json').read_text())
    validate_plan(plan, approval, ROOT, accepted)
    timeline = json.loads((ROOT / 'timeline.json').read_text())
    movie = ROOT / 'bet36fly-connectomes.mp4'
    media = probe(movie)
    video = next(s for s in media['streams'] if s['codec_type'] == 'video')
    audio = next(s for s in media['streams'] if s['codec_type'] == 'audio')
    assert (video['width'], video['height'], video['r_frame_rate']) == (1920, 1080, '24/1')
    assert audio['sample_rate'] == '48000' and audio['channels'] == 2
    assert any(s['codec_name'] == 'mov_text' for s in media['streams'])
    assert len(media['chapters']) == len(plan['scenes']) == len(timeline['scenes'])
    duration = float(media['format']['duration'])
    assert 480 <= duration <= 720
    assert abs(duration - timeline['duration']) < .15
    assert plan['meta']['image_model'] == 'gpt-image-2.5-sunburst'
    assert plan['meta']['factory_export_sha256'] == hashlib.sha256(
        (ROOT / plan['meta']['video_path']).read_bytes()).hexdigest()
    total_words, previous_end = 0, 0
    for scene, cut in zip(plan['scenes'], timeline['scenes']):
        assert scene['id'] == cut['id']
        assert abs(cut['start'] - previous_end) < 1e-6
        previous_end = cut['start'] + cut['duration']
        alignment = json.loads((ROOT / f'qa/alignments/{scene["id"]:02}.json').read_text())
        assert alignment['fingerprint'] == hashlib.sha256(
            (ROOT / scene['audio_path']).read_bytes() + scene['narration'].encode()).hexdigest()
        assert ''.join(c['text'] for c in alignment['characters']) == scene['narration']
        words = [w for w in alignment['words'] if w['text'].strip()]
        assert words[0]['start'] >= 0 and words[-1]['end'] <= scene['duration_seconds'] + .05
        assert all(a['end'] <= b['start'] + .001 for a, b in zip(words, words[1:]))
        total_words += len(words)
    captions = (ROOT / 'captions.srt').read_text()
    mentions = sum(s['narration'].count('bet three sixty fly') for s in plan['scenes'])
    assert captions.count('bet36fly') == mentions >= 1
    assert not re.search(r'BET36FLY|Bet36fly', captions)
    subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(movie),
                    '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-'], check=True)
    report = {
        'passed': True, 'duration_seconds': duration, 'width': 1920, 'height': 1080, 'fps': 24,
        'video_codec': video['codec_name'], 'audio_codec': audio['codec_name'],
        'sample_rate': 48000, 'chapters': len(plan['scenes']), 'aligned_words': total_words,
        'caption_cues': timeline['caption_cues'], 'reused_still_scenes': len(plan['scenes']),
        'new_images_generated': 0, 'bespoke_animation_scenes': 0,
        'reviewer': approval['reviewer'], 'approved_narration_sha256': approval['narration_sha256'],
        'voice': 'River', 'accent': 'american', 'pronunciation_mentions': mentions,
        'factory': 'md-video-maker/mdvm.py render', 'full_decode': 'passed',
        'bytes': movie.stat().st_size, 'sha256': hashlib.sha256(movie.read_bytes()).hexdigest(),
    }
    (ROOT / 'qa/media-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
