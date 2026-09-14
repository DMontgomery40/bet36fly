"""Align the approved ElevenLabs narration at the same approved provider."""
from pathlib import Path
import os,json,hashlib,requests
from dotenv import load_dotenv
ROOT=Path(__file__).resolve().parents[1]
load_dotenv('/Users/davidmontgomery/local-explainer-video/.env',override=False)
headers={'xi-api-key':os.environ['ELEVENLABS_API_KEY']}
p=json.loads((ROOT/'plan.json').read_text());dest=ROOT/'qa/alignments';dest.mkdir(exist_ok=True)
for s in p['scenes']:
    out=dest/f'{s["id"]:02d}.json';audio=ROOT/s['audio_path']
    fingerprint=hashlib.sha256(audio.read_bytes()+s['narration'].encode()).hexdigest()
    if out.exists() and json.loads(out.read_text()).get('fingerprint')==fingerprint:continue
    with audio.open('rb') as f:
        r=requests.post('https://api.elevenlabs.io/v1/forced-alignment',headers=headers,files={'file':(audio.name,f,'audio/wav')},data={'text':s['narration']},timeout=(15,180))
    if r.status_code!=200:raise RuntimeError(f'Alignment HTTP {r.status_code}: {r.text[:200]}')
    result=r.json();result['fingerprint']=fingerprint
    assert result.get('words'), 'No aligned words'
    out.write_text(json.dumps(result,indent=2)+'\n')
    print('aligned',s['id'],len(result['words']),'words',flush=True)
