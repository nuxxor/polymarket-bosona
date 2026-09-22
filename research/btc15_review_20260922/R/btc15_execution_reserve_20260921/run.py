"""Reuse the frozen public audit; compare one structural cash-reserve change."""
from pathlib import Path
from functools import partial
import importlib.util
import gzip
import json
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
R = HERE.parent
OLD = R/'btc15_ws_expansion_20260921'
sys.path.insert(0,str(OLD))
spec = importlib.util.spec_from_file_location('previous_stage',OLD/'run.py')
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)

a = prior.a
baseline_run = prior.ex.run
ex = a.module('reserve_execution',HERE/'execution.py')
raw_run = ex.run
prior.HERE = HERE
prior.STARTS = (1790027100,1790028000,1790028900)


def protect():
    a.protected()
    for path,digest in a.read(HERE/'protocol.sha256.json').items():
        assert a.sha(HERE/path)==digest,path
    for path,digest in a.read(OLD/'dependencies.json').items():
        assert a.sha(Path(path))==digest,path
    p = HERE/'sources.json'
    if not p.exists():
        files = list(OLD.glob('*.py'))+list((OLD/'results').glob('*.json'))+[OLD/'RAPOR.md']
        files += [R/'candidate.py',R/'protocol.json']
        a.save(p,{str(x):a.sha(x) for x in files})
    for path,digest in a.read(p).items():
        assert a.sha(Path(path))==digest,path


def fetch():
    protect()
    for start in prior.STARTS:
        prior.select(start)
        status = a.read(a.PILOT/'status.json')
        if status['received_ms']<a.CUT:
            a.save(a.HERE/'pending.json',dict(status='WAITING' if status['running'] else 'MISSING_TAPE_TAIL',
                   required_cutoff_ms=a.CUT,recorder=status))
            print('Pending',start,flush=True)
            continue
        if not (a.HERE/'raw/confirmation.json').exists():
            a.fetch()
            a.confirm()
        a.verify_inputs()
        market = a.read(a.HERE/'raw/market_start.json')['data']
        a.public.cached(a.HERE/'raw/clob_configuration.json',
            'https://clob.polymarket.com/clob-markets/'+market['conditionId'])
        p = a.HERE/'clob_manifest.json'
        if not p.exists():
            a.save(p,{'raw/clob_configuration.json':a.sha(a.HERE/'raw/clob_configuration.json')})
        for name,digest in a.read(p).items():
            assert a.sha(a.HERE/name)==digest
    protect()


def freeze_prices():
    p = HERE/'raw/chainlink_manifest.json'
    if p.exists():
        return
    info = {}
    for source in sorted(Path('/home/taygun/Masaüstü/polymarket/data/tape_cl_direct').glob('cld_20260921_2[12].jsonl.gz')):
        copy = HERE/'raw'/source.name
        copy.parent.mkdir(exist_ok=True,parents=True)
        with source.open('rb') as f:
            copy.write_bytes(f.read(source.stat().st_size))
        last,tail = 0,False
        try:
            with gzip.open(copy,'rt') as f:
                for line in f:
                    last = max(last,json.loads(line)['rcv'])
        except EOFError:
            tail = True
        info[str(copy.relative_to(HERE))] = dict(source=str(source),sha256=a.sha(copy),last_received_ms=last,open_tail=tail)
    assert max(x['last_received_ms'] for x in info.values())>=(prior.STARTS[-1]+840)*1000
    a.save(p,info)


def compare():
    protect()
    freeze_prices()
    selected = prior.STARTS
    ready = tuple(s for s in selected if (HERE/'markets'/str(s)/'raw/confirmation.json').exists())
    for start in ready:
        root = HERE/'markets'/str(start)
        for name,digest in a.read(root/'clob_manifest.json').items():
            assert a.sha(root/name)==digest
        config = a.read(root/'raw/clob_configuration.json')['data']
        market = a.read(root/'raw/market_start.json')['data']
        assert config['c']==market['conditionId']
        assert config['fd']==dict(r=.07,e=1,to=True)
        assert {x['t'] for x in config['t']}==set(json.loads(market['clobTokenIds']))
    prior.STARTS = ready
    prior.analyze()
    prior.ex = ex
    for funded in (False,True):
        ex.run = partial(raw_run,fund_hedge=funded)
        prior.replay()
        data = a.read(HERE/'results/replay.json')
        data['assigned_starts'] = selected
        data['missing_starts'] = sorted(set(selected)-set(ready))
        data['fund_hedge'] = funded
        a.save(HERE/'results'/('funded.json' if funded else 'baseline.json'),data)
    prior.STARTS = selected
    protect()


def review():
    root = R/'fable_review_20260921/agents/gap_candidate_replay_lookahead_fix'
    files = [root/'code/candidate_fixed.py',root/'results/candidate_scenario_rows_fixed.json']
    manifest = HERE/'raw/fable_review_manifest.json'
    if not manifest.exists():
        a.save(manifest,{str(p):a.sha(p) for p in files})
    for path,digest in a.read(manifest).items():
        assert a.sha(Path(path))==digest
    entries = [dict(slug=row['slug'],**e) for row in a.read(files[1])
               if row['entry']=='discount' and row['slip']==0 and row['arm']=='managed'
               for e in row['events'] if e['kind']=='first']
    assert len(entries)==180
    a.save(HERE/'results/fable_price_limit_review.json',dict(
        entries=len(entries),executed_over_55c=sum(e['price']>.55 for e in entries),
        max_execution_price=max(e['price'] for e in entries),rows=entries,
        interpretation='Decision ceiling retained; execution ceiling removed for first/add. '
                       'This is a different price-protection contract, not validation of unchanged P0.'))
    source = a.PILOT/'events_20260921_22.jsonl.gz'
    digest = a.read(a.PILOT/'closed_hashes.json')[source.name]
    assert a.sha(source)==digest
    tx = '0x38653423aa33191fa36714e9463daed61a437d5043c4325bd38f46a064f90003'
    with gzip.open(source,'rt') as stream:
        found = [json.loads(line) for line in stream if tx in line]
    a.save(HERE/'results/missing_flow_check.json',dict(tx=tx,global_tape=str(source),
        tape_sha256=digest,global_ws_messages_for_tx=len(found),messages=found,
        interpretation='No source match timestamp for this chain trade; do not insert it at block time or treat it as zero volume.'))


def repeat():
    hashes = []
    for _ in range(2):
        compare()
        review()
        for script in ('telemetry.py','check.py'):
            subprocess.run([sys.executable,'-B',str(HERE/script)],check=True,stdout=subprocess.DEVNULL)
        files = list((HERE/'results').glob('*.json'))+list((HERE/'markets').glob('*/results/*.json'))
        hashes.append({str(p.relative_to(HERE)):a.sha(p) for p in files if p.name!='reproducibility.json'})
    assert hashes[0]==hashes[1]
    a.save(HERE/'results/reproducibility.json',dict(identical=True,artifacts=len(hashes[0]),sha256=hashes[0]))


if __name__=='__main__':
    {'fetch':fetch,'compare':compare,'review':review,'repeat':repeat}[sys.argv[1]]()
