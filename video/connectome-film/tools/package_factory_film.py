"""Add aligned captions and chapters to the actual md-video-maker export."""
from pathlib import Path
import hashlib
import json
import subprocess

from moviepy import AudioFileClip

from assemble import caption_words, stamp

ROOT = Path(__file__).resolve().parents[1]


def probe_duration(path):
    return float(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', str(path),
    ]))


def main():
    plan = json.loads((ROOT / 'plan.json').read_text())
    source = ROOT / plan['meta']['video_path']
    assert source.name == f'{ROOT.name}.mp4', 'Expected actual factory output'
    timeline, cues = [], []
    offset = 0.0
    for scene in plan['scenes']:
        # Use the same duration parser as the factory's MoviePy still assembler.
        with AudioFileClip(str(ROOT / scene['audio_path'])) as audio_clip:
            duration = audio_clip.duration
        alignment = json.loads((ROOT / f'qa/alignments/{scene["id"]:02}.json').read_text())
        group = []
        for word in caption_words(alignment):
            if group and (len(' '.join(w['text'] for w in group + [word])) > 74
                          or word['end'] - group[0]['start'] > 4.7):
                cues.append((offset + group[0]['start'], offset + group[-1]['end'],
                             ' '.join(w['text'] for w in group)))
                group = []
            group.append(word)
            if len(group) >= 5 and word['text'].endswith(('.', '?', '!')):
                cues.append((offset + group[0]['start'], offset + group[-1]['end'],
                             ' '.join(w['text'] for w in group)))
                group = []
        if group:
            cues.append((offset + group[0]['start'], offset + group[-1]['end'],
                         ' '.join(w['text'] for w in group)))
        timeline.append({'id': scene['id'], 'title': scene['title'],
                         'start': offset, 'duration': duration})
        scene['duration_seconds'] = duration
        scene['start_seconds'] = offset
        offset += duration
    assert abs(probe_duration(source) - offset) < .15
    (ROOT / 'captions.srt').write_text('\n\n'.join(
        f'{i+1}\n{stamp(a)} --> {stamp(b)}\n{text}'
        for i, (a, b, text) in enumerate(cues)) + '\n')
    (ROOT / 'captions.vtt').write_text('WEBVTT\n\n' + '\n\n'.join(
        f'{stamp(a, ".")} --> {stamp(b, ".")}\n{text}' for a, b, text in cues) + '\n')
    metadata = [';FFMETADATA1', f'title={plan["meta"]["title"]}', 'artist=bet36fly']
    for cut in timeline:
        title = cut['title'].replace('=', '\\=').replace(';', '\\;').replace('#', '\\#')
        metadata += ['[CHAPTER]', 'TIMEBASE=1/1000', f'START={round(cut["start"]*1000)}',
                     f'END={round((cut["start"]+cut["duration"])*1000)}', f'title={title}']
    metadata_path = ROOT / 'qa/factory-chapters.txt'
    metadata_path.write_text('\n'.join(metadata) + '\n')
    subprocess.run([
        'ffmpeg', '-v', 'error', '-y', '-i', str(source), '-i', str(ROOT / 'captions.srt'),
        '-f', 'ffmetadata', '-i', str(metadata_path), '-map', '0:v:0', '-map', '0:a:0',
        '-map', '1:0', '-map_metadata', '2', '-map_chapters', '2', '-c:v', 'copy',
        '-af', 'loudnorm=I=-18:TP=-1.5:LRA=11', '-c:a', 'aac', '-b:a', '192k',
        '-ar', '48000', '-ac', '2', '-c:s', 'mov_text', '-metadata:s:s:0', 'language=eng',
        '-movflags', '+faststart', str(ROOT / 'bet36fly-connectomes.pending.mp4'),
    ], check=True)
    (ROOT / 'bet36fly-connectomes.pending.mp4').replace(ROOT / 'bet36fly-connectomes.mp4')
    (ROOT / 'timeline.json').write_text(json.dumps(
        {'duration': offset, 'scenes': timeline, 'caption_cues': len(cues)}, indent=2) + '\n')
    plan['meta']['factory_export_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    (ROOT / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    print(f'Packaged actual factory export: {offset:.2f} seconds, {len(cues)} captions')


if __name__ == '__main__':
    main()
