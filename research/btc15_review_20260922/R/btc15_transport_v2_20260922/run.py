"""Offline BTC15 transport comparison; no trading, strategy change or outcome tuning."""
from collections import defaultdict
from decimal import Decimal as D
from pathlib import Path
from unittest.mock import patch
import gzip
import json
import math
import socket
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
R = HERE.parent
sys.path.insert(0,str(R/'btc15_ws_validation_20260921'))
import study as a  # noqa: E402
T = R/'btc15_timing_sensitivity_20260922'
G = R/'g1_transfer_review_20260922'
old = a.module('transport_frozen_runner',T/'run.py')
ex = a.module('transport_split_engine',HERE/'execution.py')


def protect():
    old.protect()
    for name,digest in a.read(HERE/'sources.json').items():
        assert a.sha(Path(name)) == digest,name
    for name,digest in a.read(T/'delivery_manifest.json')['sha256'].items():
        assert a.sha(T/name) == digest,name


def freeze_profiles():
    protect()
    x = a.read(G/'snapshot.json')
    placements = {e['payload']['id']:e['received']['mono_ns'] for e in x['observers']['A']['user']
                  if e.get('payload',{}).get('type') == 'PLACEMENT'}
    post,cancel = [],[]
    for e in x['telemetry']:
        if e['event'] == 'response' and e['op'] == 'post_batch':
            for item in e['reply']['items']:
                if item.get('oid') in placements:
                    begin,ack = e['begin']['mono_ns'],e['end']['mono_ns']
                    post.append(dict(oid=item['oid'],active_upper=(min(placements[item['oid']],ack)-begin)/1e6,
                                     ack=(ack-begin)/1e6))
    for e in x['observers']['A']['user']:
        if e.get('payload',{}).get('type') != 'CANCELLATION':
            continue
        oid = e['payload']['id']
        requests = [t['mono_ns'] for t in x['telemetry'] if t['event']=='request' and t['op']=='cancel' and oid in t['meta']['oids']]
        replies = [t['end']['mono_ns'] for t in x['telemetry'] if t['event']=='response' and t['op']=='get_order'
                   and t['reply'].get('oid')==oid and t['reply'].get('status')=='CANCELED']
        assert requests and replies
        begin = min(requests)
        known = min(t for t in replies if t>=begin)
        cancel.append(dict(oid=oid,active_upper=(min(known,e['received']['mono_ns'])-begin)/1e6,known=(known-begin)/1e6))
    learning = [t['bot_learned_cumulative_minus_private_ms']-t['public_minus_private_received_ms'] for t in a.read(G/'timing.json')]
    assert len(post)==63 and len(cancel)==27 and len(learning)==40
    profiles = [dict(p) for p in old.PROTOCOL['profiles'] if p['name'] in ('legacy_fast','legacy_slow')]
    def quantile(values,q):
        return math.ceil(sorted(values)[math.ceil(q*len(values))-1])
    for label,q in [('p50',.50),('p95',.95),('max',1.)]:
        profiles.append(dict(name='observed_'+label,accept=quantile([p['active_upper'] for p in post],q),
            post_ack_ms=quantile([p['ack'] for p in post],q),cancel=quantile([p['active_upper'] for p in cancel],q),
            cancel_notice_ms=quantile([p['known'] for p in cancel],q),learn=quantile(learning,q),shift=0))
    value = dict(starts=old.PROTOCOL['starts'],profiles=profiles,queues=old.PROTOCOL['queues'],ties=old.PROTOCOL['ties'],
        arms=[arm[0] for arm in old.ARMS],post_samples=post,cancel_samples=cancel,learning_relative_to_public_ms=learning,
        interpretation='Same-host observed upper bounds / marginal stress points; not venue timestamps, BTC15 calibration, or PnL bounds.',
        policy='Frozen BTC15 rules and risk limits; no G1 strategy parameters transferred.',economic_pnl=None)
    target = HERE/'protocol.json'
    if target.exists():
        assert a.read(target)==value,'protocol cannot be rewritten after results'
    else:
        a.save(target,value)
        (HERE/'protocol.sha256').write_text(a.sha(target)+'\n')
    assert a.sha(target)==(HERE/'protocol.sha256').read_text().strip()
    return value


def load(start,profiles):
    row,data = old.load(start)
    if data is None:
        return row,None
    root = old.source(start)
    path = old.N/'channels/A/events.jsonl.gz' if start==1790031600 else root/'raw/events.jsonl.gz'
    with gzip.open(path,'rt') as stream:
        events = [json.loads(line) for line in stream]
    tokens = json.loads(data['market']['clobTokenIds'])
    events,_ = old.prior.book_events(events,tokens)
    published = sorted([dict(e,rcv=int(e['p']['timestamp'])) for e in events
                        if e['k'] in ('book','price_change','tick_size_change')],key=lambda e:e['rcv'])
    initial = a.read(root/'raw/market_start.json')
    for delay in {p['accept'] for p in profiles}-data['venue'].keys():
        times = [t+delay for t in data['client']]
        data['venue'][delay],_ = a.m1.books_at(published,tokens,times)
        data['vt'][delay] = old.ticks_with_initial(published,tokens,times,initial)
    return row,data


def run_one(data,profile,mode,tie,arm,trace=False):
    _,offset,hedge,funded = arm
    extra = {k:profile[k] for k in ('post_ack_ms','cancel_notice_ms') if k in profile}
    return ex.run(data['client'],data['venue'][profile['accept']],data['prints'],data['market'],mode,offset,
        hedge,profile['accept'],profile['learn'],data['ct'],data['vt'][profile['accept']],funded,
        cancel_delay=profile['cancel'],trade_shift=profile['shift'],tie_order=tie,trace=trace,separate_arrival=True,**extra)


def run_all():
    protocol = freeze_profiles()
    rows,baseline_paths = [],0
    for start in protocol['starts']:
        row,data = load(start,protocol['profiles'])
        if data is None:
            rows.append(row)
            continue
        frozen = a.read(T/'results/markets'/f'{start}.json')
        row['control'] = frozen['control']
        for profile in protocol['profiles']:
            for mode in protocol['queues']:
                for tie in protocol['ties']:
                    for arm in old.ARMS:
                        key = ':'.join((arm[0],profile['name'],mode,tie))
                        v = run_one(data,profile,mode,tie,arm)
                        v['conditional_pnl'] = v['actual']['q'][row['winner']]-v['actual']['cash'] if not v['unknown'] else None
                        v['economic_pnl'] = None
                        if profile['name'].startswith('legacy_'):
                            assert json.loads(json.dumps(v,default=str))==frozen['arms'][key],(start,key)
                            baseline_paths += 1
                        row['arms'][key] = v
        a.save(HERE/'results/markets'/f'{start}.json',row)
        rows.append({**row,'arms':{key:{k:v[k] for k in ('conditional_pnl','unknown','max_cash','max_net','min_worst','lifecycle','max_funding','actual')}
                                 for key,v in row['arms'].items()}})
        print('BTC15',start,len(row['arms']),'paths; baseline identical',flush=True)
    tables = defaultdict(list)
    for row in rows:
        for key,value in row.get('arms',{}).items():
            tables[key].append(value['conditional_pnl'])
    summary = {}
    for key,values in sorted(tables.items()):
        complete = all(v is not None for v in values)
        summary[key] = dict(per_market=values,conditional_total=sum(values,D(0)) if complete else None,
            without_best=sum(values,D(0))-max(values) if complete else None,all_assigned_total=None)
    a.save(HERE/'results/cohort.json',dict(markets=rows,baseline_paths_identical=baseline_paths,economic_pnl=None))
    a.save(HERE/'results/summary.json',dict(assigned=len(rows),eligible=sum(row['replay_eligible'] for row in rows),
        scenarios=summary,economic_pnl=None))
    protect()


def repeat():
    def hashes():
        return {str(p.relative_to(HERE)):a.sha(p) for p in (HERE/'results').rglob('*.json')
                if p.name not in ('checks.json','reproducibility.json')}
    before = hashes()
    assert len(before)==9,'run and challenge must finish before repetition'
    run_all()
    challenge()
    assert before==hashes()
    a.save(HERE/'results/reproducibility.json',dict(identical=True,offline=True,sha256=before))


def challenge():
    """Post-result falsification, not an additional preregistered success test."""
    protocol = freeze_profiles()
    paths = []
    for start in protocol['starts']:
        row,data = load(start,protocol['profiles'])
        if data is None:
            continue
        frozen = a.read(HERE/'results/markets'/f'{start}.json')
        for base in protocol['profiles'][2:]:
            for test in ('earlier_trade','coupled_cancel_notice'):
                profile = dict(base)
                if test=='earlier_trade':
                    profile['shift'] = -500
                else:
                    # Previous motor's effect + acceptance-delay convention; no fitted threshold.
                    profile['cancel_notice_ms'] = profile['cancel']+profile['accept']
                for mode in protocol['queues']:
                    for tie in protocol['ties']:
                        for arm in old.ARMS[:2]:
                            key = ':'.join((arm[0],base['name'],mode,tie))
                            v = run_one(data,profile,mode,tie,arm)
                            v['conditional_pnl'] = v['actual']['q'][row['winner']]-v['actual']['cash'] if not v['unknown'] else None
                            v['economic_pnl'] = None
                            paths.append(dict(start=start,test=test,key=key,profile=profile,
                                baseline_pnl=frozen['arms'][key]['conditional_pnl'],result=v))
        print('Challenged BTC15',start,flush=True)
    groups = defaultdict(list)
    for p in paths:
        groups[p['test']+':'+p['key']].append(p)
    summary = {}
    for key,values in sorted(groups.items()):
        pnl = [v['result']['conditional_pnl'] for v in values]
        complete = all(v is not None for v in pnl)
        summary[key] = dict(per_market=pnl,conditional_total=sum(pnl,D(0)) if complete else None,
            without_best=sum(pnl,D(0))-max(pnl) if complete else None,
            baseline_total=sum((D(v['baseline_pnl']) for v in values),D(0)),economic_pnl=None)
    a.save(HERE/'results/challenges.json',dict(stage='post-result mechanism/falsification diagnostics',paths=paths,summary=summary))
    protect()


if __name__ == '__main__':
    with patch.object(socket.socket,'connect',side_effect=AssertionError('offline only')):
        {'profiles':freeze_profiles,'run':run_all,'repeat':repeat,'challenge':challenge}[sys.argv[1]]()
