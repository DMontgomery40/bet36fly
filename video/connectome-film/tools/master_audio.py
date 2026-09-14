"""Local mastering of approved voiceover, retaining untouched provider recordings."""
from pathlib import Path
import json,subprocess,hashlib,math
ROOT=Path(__file__).resolve().parents[1];p=json.loads((ROOT/'plan.json').read_text())
settings='atempo=1.0,loudnorm=I=-18:TP=-1.5:LRA=11,adelay=180:all=1,apad=pad_dur=0.32'
for s in p['scenes']:
    raw=s.get('audio_source_path',s['audio_path']);s['audio_source_path']=raw
    out=f'audio/mastered/scene_{s["id"]:03d}.wav';dest=ROOT/out;dest.parent.mkdir(exist_ok=True)
    fingerprint=hashlib.sha256((hashlib.sha256((ROOT/raw).read_bytes()).hexdigest()+settings).encode()).hexdigest();stamp=dest.with_suffix('.json')
    if not (dest.exists() and stamp.exists() and json.loads(stamp.read_text())['fingerprint']==fingerprint):
        subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-i',str(ROOT/raw),'-af',settings,'-ar','48000','-ac','2',str(dest)],check=True)
        stamp.write_text(json.dumps({'fingerprint':fingerprint,'filters':settings,'source':raw},indent=2)+'\n')
    s['audio_path']=out
    s['duration_seconds']=float(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(dest)],text=True))
    s['start_seconds']=sum(x.get('duration_seconds',0) for x in p['scenes'][:s['id']])
p['meta']['duration_seconds']=sum(x['duration_seconds'] for x in p['scenes']);p['meta']['audio_mastering']=settings
assert 480<=p['meta']['duration_seconds']<=720
(ROOT/'plan.json').write_text(json.dumps(p,indent=2)+'\n')
print('Mastered runtime:',p['meta']['duration_seconds'])
