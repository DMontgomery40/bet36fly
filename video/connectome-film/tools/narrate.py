"""Generate narration with the framework helper and cache every voice control."""
from pathlib import Path
import hashlib
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def speech_settings(scene, meta):
    return {'narration': scene['narration'], 'voice': meta['voice_id'],
            'speed': meta['audio_speed'], 'model': meta['elevenlabs_model_id'],
            **meta['voice_settings']}


def settings_digest(settings):
    return hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()


def main():
    from dotenv import load_dotenv
    load_dotenv('/Users/davidmontgomery/local-explainer-video/.env', override=False)
    sys.path.insert(0, '/Users/davidmontgomery/local-explainer-video')
    from core.voice_gen import generate_scene_audio
    plan = json.loads((ROOT / 'plan.json').read_text())
    for scene in plan['scenes']:
        dest = ROOT / scene.get('audio_source_path', scene['audio_path'])
        settings = speech_settings(scene, plan['meta'])
        digest = settings_digest(settings)
        stamp = dest.with_suffix('.json')
        if dest.exists() and stamp.exists() and json.loads(stamp.read_text()).get('sha256') == digest:
            print('cached', scene['id'], flush=True)
            continue
        start = time.time()
        generate_scene_audio(scene, project_dir=ROOT, voice=settings['voice'], speed=settings['speed'],
                             tts_provider='elevenlabs', elevenlabs_model_id=settings['model'],
                             elevenlabs_stability=settings['stability'],
                             elevenlabs_similarity_boost=settings['similarity_boost'],
                             elevenlabs_style=settings['style'],
                             elevenlabs_use_speaker_boost=settings['use_speaker_boost'])
        if not dest.exists():
            raise RuntimeError('Expected scene audio missing')
        stamp.write_text(json.dumps({'sha256': digest, 'settings': settings}, indent=2) + '\n')
        print('audio', scene['id'], round(time.time()-start, 1), 'seconds', flush=True)


if __name__ == '__main__':
    main()
