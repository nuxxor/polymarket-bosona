from pathlib import Path
import sys
import json
import time
import subprocess
root=Path('/home/ubuntu/polymarket-bosona-participation-v1')
sys.path.insert(0,str(root/'analiz/izleme'))
import bosona_inventory_shadow as inv  # noqa: E402
out=root/'data/participation'
m=json.loads((out/'watch_manifest.json').read_text())
assert m['participation'] is True and m['source_sha256']==inv.hashes()
es=[json.loads(line) for line in (out/'shadow.jsonl').read_text().splitlines()]
ds={(e['S'],e['age']):e for e in es if e['kind']=='decision'}
markets={e['S']:e['market'] for e in es if e['kind']=='market'}
assert len(ds)==sum(e['kind']=='decision' for e in es)
positions={}
first={}
for e in es:
    if e['kind']!='execution':
        continue
    d=ds[e['S'],e['age']]
    assert e['request_ms']>=d['decision_ms']+(250 if e['speed']=='250' else 0)
    for lane,f in e['fills'].items():
        history=positions.setdefault((e['S'],lane),[])
        intent=d['intents'][lane]
        expected=inv.execute(intent,history,e['books'],markets[e['S']],f['age'])
        assert expected==f
        for k in ('observed_ms','received_ms'):
            assert 0<=e['execution_ms']-e['books'][f['side']][k]<=3000
        if f['kind']=='first':
            assert not history
            first[e['S'],lane]=dict(age=f['age'],side=f['side'],qty=f['qty'],cost=f['cost'],signal_side=d['entry_side'],context_gap=d['context_gap'])
        history.append(f)
        p=inv.position(history)
        assert p['cash']<=15+1e-8 and p['floor']>=-5-1e-8 and abs(p['qty'][0]-p['qty'][1])<=10+1e-8
assert all((m['start_S'],lane) in first for lane in inv.LANES), 'first-window entry not yet filled'
pid=subprocess.check_output(['tmux','display-message','-p','-t','bosona-participation','#{pane_pid} #{pane_dead}']).decode().strip()
print(json.dumps(dict(captured_ms=round(time.time()*1000),manifest=m,pid=pid,first=[dict(S=s,lane=lane,**v) for (s,lane),v in first.items()],decisions=len(ds),gaps=[e for e in es if e['kind']=='gap'],validation='PASS: actual paper entries, fresh executable quotes, fees, risk, delayed request, frozen source, one initial entry per lane/window')))
