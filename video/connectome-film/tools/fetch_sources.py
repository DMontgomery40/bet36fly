"""Fetch a bounded set of public project source files for this film's attribution."""
from pathlib import Path
import json, hashlib, urllib.request
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'sources/raw';DEST.mkdir(parents=True,exist_ok=True)
repos={'doomfly':'nftechie/doomfly','flyvis':'TuragaLab/flyvis','flybody':'TuragaLab/flybody','shiu':'philshiu/Drosophila_brain_model'}
record=[]
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'connectome-film-source-check'})
    with urllib.request.urlopen(req,timeout=40) as r:return r.read()
for name,repo in repos.items():
    info=json.loads(get(f'https://api.github.com/repos/{repo}/commits?per_page=1'))[0]
    sha=info['sha']
    tree=json.loads(get(f'https://api.github.com/repos/{repo}/git/trees/{sha}?recursive=1'))['tree']
    files=[x['path'] for x in tree if x['type']=='blob']
    readmes=[f for f in files if '/' not in f and f.lower()=='readme.md']
    selected=readmes[:1]
    if name=='doomfly':selected += [f for f in files if f in ['doom/run.py','doom/runner.py','doom/env.py','doom/neural.py','doom/decoder.py','doom/connectome.py','doom/main.py','doom/model.py']][:4]
    if name=='flyvis':selected += [f for f in files if f=='flyvis/network/network.py']
    if name=='flybody':selected += [f for f in files if f=='flybody/fly_envs.py']
    if name=='shiu':selected += [f for f in files if f=='model.py']
    local=[]
    for f in selected:
        b=get(f'https://raw.githubusercontent.com/{repo}/{sha}/{f}')
        dest=DEST/(name+'--'+f.replace('/','__'));dest.write_bytes(b)
        local.append({'path':f,'local':str(dest.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest()})
    record.append({'project':name,'repository':f'https://github.com/{repo}','commit':sha,'commit_date':info['commit']['committer']['date'],'files':local})
    print(name,sha,len(selected),flush=True)
(ROOT/'sources/repository-snapshots.json').write_text(json.dumps(record,indent=2)+'\n')
