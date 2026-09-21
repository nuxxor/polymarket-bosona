#!/usr/bin/env python3
"""Read-only checkpoint of the frozen London shadows; no inference or order calls."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import time

import bosona_gec_arastirma as base
import bosona_latency as latency

OUT = base.ROOT/'data/analysis/shadow_status_20260921_1016'
RAW = OUT/'raw'
PATHS = dict(baseline='polymarket-bosona-research/data/bosona_gec_forward',
             rebound='polymarket-bosona-rebound/data/forward',
             latency='polymarket-bosona-rebound/data/latency',
             jev='polymarket-bosona-jev/data/jev_shadow')


def read(name):
    filename = 'events.jsonl' if name=='jev' else 'quotes.jsonl' if name=='latency' else 'shadow.jsonl'
    return [json.loads(s) for s in (RAW/PATHS[name]/filename).read_text().splitlines()]


def fetch():
    starts = sorted({r['S'] for name in ('baseline','rebound','jev') for r in read(name)
                     if r['kind'] in ('decision','execution','DECISION','SETTLED')})
    def one(S):
        path=OUT/'markets'/f'{S}.json'
        if path.exists():
            return
        m=base.get(f'https://gamma-api.polymarket.com/markets/slug/btc-updown-5m-{S}?snapshot={int(time.time())//30}')
        assert m['slug']==f'btc-updown-5m-{S}' and json.loads(m['outcomes'])==['Up','Down']
        base.save(path,m)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(one,starts))
    print('fresh public market checks',len(starts))


def pnl(side,cost,winner):
    return 0. if side is None else 5.*(side==winner)-cost


def stats(rows):
    resolved=[r for r in rows if r['winner'] is not None]
    trades=[r for r in resolved if r['side'] is not None]
    values=[pnl(r['side'],r['cost'],r['winner']) for r in resolved]
    running=peak=dd=0.
    for value in values:
        running+=value
        peak=max(peak,running)
        dd=max(dd,peak-running)
    return dict(eligible=len(rows),resolved_eligible=len(resolved),trades=len(trades),
                wins=sum(r['side']==r['winner'] for r in trades),
                losses=sum(r['side']!=r['winner'] for r in trades),
                no_signal=sum(r['side'] is None for r in resolved),
                pending_selected=sum(r['side'] is not None and r['winner'] is None for r in rows),
                pnl=sum(values) if resolved else None,
                cost=sum(r['cost'] for r in trades),fees=sum(r['fee'] for r in trades),
                max_drawdown=dd if resolved else None,
                ex_top3=sum(values)-sum(sorted(values,reverse=True)[:3]) if resolved else None)


def analyze():
    logs={name:read(name) for name in PATHS}
    cutoff=min(max(r['recorded_ms'] for r in logs[name]) for name in ('baseline','rebound'))//300000*300
    markets={int(p.stem):json.loads(p.read_text()) for p in (OUT/'markets').glob('*.json')}
    winners={}
    for S,m in markets.items():
        if S+300<=cutoff:
            try:
                winners[S]=base.outcome(m)
            except ValueError:
                pass
    for name in ('baseline','rebound','jev'):
        for r in logs[name]:
            if r['kind'] in ('resolution','SETTLED') and r['S'] in winners:
                recorded=(0 if r['up_won'] else 1) if name=='jev' else r['winner']
                assert recorded==winners[r['S']],(name,r['S'])
    result=dict(cutoff=cutoff,cutoff_utc=datetime.fromtimestamp(cutoff,timezone.utc).isoformat(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),shadows={},jev={})
    all_rows={}
    for name in ('baseline','rebound'):
        rows=logs[name]
        manifest=json.loads((RAW/PATHS[name]/'watch_manifest.json').read_text())
        assigned=list(range(manifest['start_S'],min(cutoff,manifest['end_S']),300))
        decisions={(r['S'],r['age']):r for r in rows if r['kind']=='decision' and r['S'] in assigned}
        assert len(decisions)==sum(r['kind']=='decision' and r['S'] in assigned for r in rows)
        executions=decisions if name=='baseline' else {(r['S'],r['age']):r for r in rows if r['kind']=='execution' and r['S'] in assigned}
        rules=['favorite','aligned','buffer'] if name=='baseline' else ['rebound','favorite']
        report=dict(start_S=manifest['start_S'],end_S=manifest['end_S'],assigned=len(assigned),
                    duration_hours=(cutoff-manifest['start_S'])/3600,by_age={})
        for age in manifest['slots']:
            es=[r for (S,a),r in sorted(executions.items()) if a==age]
            gaps=[r for r in rows if r['kind']=='gap' and r['age']==age and r['S'] in assigned]
            events={r['S'] for r in es}|{r['S'] for r in gaps}
            entry=dict(assigned=len(assigned),eligible=len(es),gaps=len(gaps),missing_attempts=len(set(assigned)-events),
                       gap_reasons=dict(Counter(r['reason'] for r in gaps)),rules={})
            assert len(set(assigned)-events)==0,(name,age)
            for rule in rules:
                rr=[]
                for r in es:
                    side=(r['side'] if r['selected'][rule] else None) if name=='baseline' else r[rule]
                    cost=(r['cost']+r['fee'] if name=='baseline' else sum(r['costs'][side])) if side is not None else 0.
                    fee=(r['fee'] if name=='baseline' else r['costs'][side][1]) if side is not None else 0.
                    rr.append(dict(S=r['S'],age=age,rule=rule,side=side,cost=cost,fee=fee,winner=winners.get(r['S'])))
                    if name=='baseline':
                        c,f=base.ask_cost(r['execution_book'],markets[r['S']])
                        assert abs(c-r['cost'])<1e-8 and abs(f-r['fee'])<1e-8
                    else:
                        for b,paircost in zip(r['execution_books'],r['costs']):
                            c,f=base.ask_cost(b,markets[r['S']])
                            assert abs(c-paircost[0])<1e-8 and abs(f-paircost[1])<1e-8
                entry['rules'][rule]=stats(rr)
                all_rows[f'{name}_{age}_{rule}']=rr
            report['by_age'][str(age)]=entry
        result['shadows'][name]=report
    rr=logs['jev']
    cfg=next(r for r in rr if r['kind']=='CONFIG')
    version=next(r for r in rr if r['kind']=='VERSION' and r['version']==2)
    finals=[r for r in rr if r['kind']=='DECISION' and r.get('version')==2 and r['final']]
    assert len({r['S'] for r in finals})==len(finals)
    jr=result['jev']
    jr.update(start_ms=cfg['ts_ms'],end_ms=cfg['end_ms'],stop_ms=[r['ts_ms'] for r in rr if r['kind']=='STOP'][-1],
              v2_first_S=version['first_S'],v2_assigned=len(range(version['first_S'],cfg['end_ms']//1000,300)),
              final_predictions=len(finals),missing_final=0,models={},by_horizon={})
    jr['missing_final']=jr['v2_assigned']-len(finals)
    for model in ('full','technical','market'):
        records=[]
        for r in finals:
            assert r['on_time'] and r['decision_ms']<=(r['S']+240)*1000
            position=r['position'] if model=='full' else r['baselines'].get(model)
            if position is None:
                continue
            side=int(position['side']=='DOWN')
            assert position['quote_ms']>=r['decision_ms']
            assert abs(position['cost']-position['gross_cost']-position['fee'])<1e-8
            records.append(dict(S=r['S'],side=side,cost=position['cost'],fee=position['fee'],winner=winners.get(r['S'])))
        jr['models'][model]=stats(records)
        all_rows['jev_v2_'+model]=records
    v1=[r for r in rr if r['kind']=='DECISION' and r.get('version',1)==1 and r['position']]
    jr['v1']=stats([dict(S=r['S'],side=int(r['position']['side']=='DOWN'),cost=r['position']['cost'],
                         fee=r['position']['fee'],winner=winners.get(r['S'])) for r in v1])
    v2=[r for r in rr if r.get('version')==2]
    for slot in range(30,241,30):
        ds=[r for r in v2 if r['kind']=='DECISION' and r['slot']==slot and r['on_time'] and r['S'] in winners]
        if not ds:
            continue
        score={}
        for model in ('full','technical','market'):
            ps=[r['market_p_up'] if model=='market' else r['views'][model]['p_up'] for r in ds]
            sides=[int(p<.5) if model=='market' else int(r['views'][model]['side']=='DOWN') for p,r in zip(ps,ds)]
            score[model]=dict(correct=sum(side==winners[r['S']] for side,r in zip(sides,ds)),
                             brier=statistics.mean((p-(winners[r['S']]==0))**2 for p,r in zip(ps,ds)))
        jr['by_horizon'][str(slot)]=dict(n=len(ds),scores=score)
    responses=[r for r in rr if r['kind']=='RESPONSE']
    jr['api_cost_all_versions']=sum(r['cost_usd'] for r in responses)+333*cfg['rate_per_million']/1e6
    jr['api_errors']=sum(r['kind']=='API_ERROR' for r in rr)
    jr['median_v2_api_ms']=statistics.median(r['latency_ms'] for r in v2 if r['kind']=='RESPONSE')
    jr['direction_changes']=sum(r.get('direction_changes',0) for r in v2 if r['kind']=='SETTLED')
    for s in [r for r in rr if r['kind']=='SETTLED']:
        if s['position']:
            assert abs(pnl(int(s['position']['side']=='DOWN'),s['position']['cost'],winners[s['S']])-s['paper_pnl'])<1e-8
    lm=json.loads((RAW/PATHS['latency']/'watch_manifest.json').read_text())
    originals=[r for r in logs['rebound'] if r.get('S',cutoff)+300<=cutoff and r['recorded_ms']>=lm['started_ms']]
    fast=[r for r in logs['latency'] if r.get('S',cutoff)+300<=cutoff or r['kind'] not in ('fast_quote','gap')]
    result['latency']=latency.compare(originals,fast)
    for age in (240,270,280):
        es=[r for r in originals if r['kind']=='execution' and r['age']==age]
        fs={(r['S'],r['age']):r for r in fast if r['kind']=='fast_quote'}
        for rule in ('rebound','favorite'):
            common=[r for r in es if (r['S'],r['age']) in fs]
            fast_rows=[dict(S=r['S'],side=r[rule],winner=winners.get(r['S']),
                           cost=sum(fs[r['S'],age]['costs'][r[rule]]) if r[rule] is not None else 0.,
                           fee=fs[r['S'],age]['costs'][r[rule]][1] if r[rule] is not None else 0.) for r in common]
            result['latency'][f'{age}_{rule}_fast']=stats(fast_rows)
    # Diagnose the observed late-slot bar bug from the logged inputs, without replaying missing trades.
    candle=None
    failures=[]
    for r in logs['rebound']:
        if r['kind']=='bars':
            candle=r['bars']
        if r['kind']=='gap' and r['reason']=='incomplete or stale context':
            age_ms=r['recorded_ms']-candle['rows'][-1][6]
            failures.append(dict(S=r['S'],age=r['age'],bar_age_ms=age_ms,stale=age_ms>62000,
                                 bar_fetch_age_s=candle['received_ms']/1000-r['S']))
    result['context_gaps']=failures
    # Compare only identical windows, never the non-overlapping Jev/rebound pilots.
    jset={r['S'] for r in all_rows['jev_v2_full']}
    bset={r['S'] for r in all_rows['baseline_240_favorite']}
    result['overlap']=dict(jev_baseline_final=sorted(jset&bset),jev_rebound=sorted(jset&{r['S'] for r in all_rows['rebound_240_rebound']}))
    base.save(OUT/'trade_rows.json',all_rows)
    base.save(OUT/'score.json',result)
    base.save(OUT/'source_manifest.json',{str(p.relative_to(RAW)):hashlib.sha256(p.read_bytes()).hexdigest() for p in RAW.rglob('*') if p.is_file()})
    print(json.dumps({k:v for k,v in result.items() if k not in ('context_gaps','latency')},indent=2))
    print('latency',json.dumps({k:v for k,v in result['latency'].items() if k!='rows'}))


def check():
    assert pnl(0,1.25,0)==3.75 and pnl(0,1.25,1)==-1.25 and pnl(None,0.,0)==0.
    rows=[dict(S=0,side=0,cost=1.25,fee=.05,winner=0),dict(S=300,side=None,cost=0.,fee=0.,winner=1),
          dict(S=600,side=1,cost=2.,fee=.07,winner=None)]
    s=stats(rows)
    assert (s['pnl'],s['trades'],s['no_signal'],s['pending_selected'])==(3.75,1,1,1)
    assert stats([])['pnl'] is None  # No valid test must not be reported as zero profit.
    print('Fees, wins/losses, no-signal, missing/pending and empty-test checks passed')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['fetch','analyze','check'])
    globals()[p.parse_args().action]()
