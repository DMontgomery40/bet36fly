"""Assemble pre-rendered scenes following md-video-maker's mixed-scene convention.

All video already shares one 1080p24 profile, so preserve it with stream copy.
Use frame-exact scene offsets for captions and chapters; pad audio to each cut.
"""
from pathlib import Path
import json
import math
import subprocess
import re

ROOT = Path(__file__).resolve().parents[1]


def run(args):
    subprocess.run(args, check=True)


def stamp(seconds, separator=','):
    value = round(seconds * 1000)
    hours, value = divmod(value, 3600000)
    minutes, value = divmod(value, 60000)
    seconds, millis = divmod(value, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02}{separator}{millis:03}'


def caption_words(alignment):
    words = [dict(w) for w in alignment['words'] if w['text'].strip()]
    result = []
    i = 0
    while i < len(words):
        phrase = ' '.join(w['text'] for w in words[i:i+4])
        if re.fullmatch(r'bet three sixty fly[.,]?', phrase, re.I):
            end = words[i+3]
            result.append({'text': 'bet36fly' + (end['text'][-1] if end['text'][-1] in '.,' else ''), 'start': words[i]['start'], 'end': end['end']})
            i += 4
        else:
            result.append(words[i])
            i += 1
    return result


def main():
    plan = json.loads((ROOT / 'plan.json').read_text())
    mux = ROOT / 'clips/mux'
    mux.mkdir(exist_ok=True)
    timeline, cues, concat = [], [], []
    offset = 0.0
    for scene in plan['scenes']:
        index = scene['id']
        duration = math.ceil(scene['duration_seconds'] * 24) / 24
        segment = mux / f'{index:02}.mp4'
        run(['ffmpeg', '-v', 'error', '-y', '-i', str(ROOT / scene['video_source_path']),
             '-i', str(ROOT / scene['audio_path']), '-map', '0:v:0', '-map', '1:a:0',
             '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
             '-af', 'apad', '-t', f'{duration:.9f}', str(segment)])
        concat += [f"file '{segment.as_posix()}'", f'duration {duration:.9f}']
        alignment = json.loads((ROOT / f'qa/alignments/{index:02}.json').read_text())
        group = []
        for word in caption_words(alignment):
            if group and (len(' '.join(w['text'] for w in group + [word])) > 74 or word['end'] - group[0]['start'] > 4.7):
                cues.append((offset + group[0]['start'], offset + group[-1]['end'], ' '.join(w['text'] for w in group)))
                group = []
            group.append(word)
            if len(group) >= 5 and word['text'].endswith(('.', '?', '!')):
                cues.append((offset + group[0]['start'], offset + group[-1]['end'], ' '.join(w['text'] for w in group)))
                group = []
        if group:
            cues.append((offset + group[0]['start'], offset + group[-1]['end'], ' '.join(w['text'] for w in group)))
        timeline.append({'id': index, 'title': scene['title'], 'start': offset, 'duration': duration})
        offset += duration
        print(f'assembled scene {index:02}', flush=True)
    (mux / 'concat.txt').write_text('\n'.join(concat) + '\n')
    (ROOT / 'captions.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(a)} --> {stamp(b)}\n{text}' for i, (a, b, text) in enumerate(cues)) + '\n')
    (ROOT / 'captions.vtt').write_text('WEBVTT\n\n' + '\n\n'.join(f'{stamp(a, ".")} --> {stamp(b, ".")}\n{text}' for a, b, text in cues) + '\n')
    metadata = [';FFMETADATA1', 'title=An unlikely colleague: building with a fly connectome', 'artist=bet36fly', 'comment=Technical introduction for bet365. Source notes accompany the film.']
    for item in timeline:
        metadata += ['[CHAPTER]', 'TIMEBASE=1/1000', f'START={round(item["start"]*1000)}', f'END={round((item["start"]+item["duration"])*1000)}', f'title={item["title"]}']
    (mux / 'chapters.txt').write_text('\n'.join(metadata) + '\n')
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(mux / 'concat.txt'),
         '-i', str(ROOT / 'captions.srt'), '-f', 'ffmetadata', '-i', str(mux / 'chapters.txt'),
         '-map', '0:v:0', '-map', '0:a:0', '-map', '1:0', '-map_metadata', '2', '-map_chapters', '2',
         '-c:v', 'copy', '-c:a', 'copy', '-c:s', 'mov_text', '-metadata:s:s:0', 'language=eng',
         '-t', f'{offset:.9f}', '-movflags', '+faststart', str(ROOT / 'bet36fly-connectomes.mp4')])
    (ROOT / 'timeline.json').write_text(json.dumps({'duration': offset, 'scenes': timeline, 'caption_cues': len(cues)}, indent=2) + '\n')
    print(f'Final duration: {offset:.3f} seconds; {len(cues)} caption cues', flush=True)


if __name__ == '__main__':
    main()
