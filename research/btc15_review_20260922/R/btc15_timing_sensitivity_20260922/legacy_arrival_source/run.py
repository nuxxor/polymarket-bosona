"""Finite, offline timing sensitivity. Prior candidates and raw artifacts are read-only."""
from decimal import Decimal as D
from pathlib import Path
from unittest.mock import patch
import gzip
import json
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
R = HERE.parent
W = R/'btc15_ws_validation_20260921'
E = R/'btc15_ws_expansion_20260921'
Z = R/'btc15_execution_reserve_20260921'
N = R/'btc15_feed_integrity_20260922'
sys.path.insert(0,str(W))
import study as a  # noqa: E402
prior = a.module('timing_prior_helpers',E/'run.py')
ex = a.module('timing_execution',HERE/'execution.py')
legacy = a.module('timing_legacy_execution',Z/'execution.py')
PROTOCOL = a.read(HERE/'protocol.json')
ARMS = [('M1_bid',D(0),False,False),('M1_bid_minus_cent',D('.01'),False,False),
        ('M2_bid',D(0),True,False),('M2_reserved',D(0),True,True)]


def source(start):
    if start==1790023500:
        return W
    if start==1790031600:
        return N/'market'
    return (E if start<1790027100 else Z)/'markets'/str(start)


def protect():
    a.protected()
    assert a.sha(HERE/'protocol.json')==(HERE/'protocol.sha256').read_text().strip()
    for root in (Z,N):
        for name,digest in a.read(root/'delivery_manifest.json')['sha256'].items():
            assert a.sha(root/name)==digest,str(root/name)
    for name,digest in a.read(E/'dependencies.json').items():
        assert a.sha(Path(name))==digest,name
    path = HERE/'sources.json'
    if not path.exists():
        paths = [R/'candidate.py',R/'protocol.json',W/'study.py',E/'run.py',Z/'execution.py',
                 Z/'delivery_manifest.json',N/'delivery_manifest.json',E/'dependencies.json']
        a.save(path,{str(p):a.sha(p) for p in paths})
    for name,digest in a.read(path).items():
        assert a.sha(Path(name))==digest,name


def prepare():
    protect()
    path = HERE/'raw/chainlink.jsonl.gz'
    if not path.exists():
        # Closed byte prefix only; no writes to the running price recorder.
        src = Path('/home/taygun/Masaüstü/polymarket/data/tape_cl_direct/cld_20260921_23.jsonl.gz')
        tmp = HERE/'raw/cld_source_prefix.gz'
        tmp.parent.mkdir(parents=True,exist_ok=True)
        with src.open('rb') as f:
            tmp.write_bytes(f.read(src.stat().st_size))
        rows,open_tail = [],False
        try:
            with gzip.open(tmp,'rt') as f:
                for line in f:
                    row = json.loads(line)
                    if row['rcv']<=1790032620000:
                        rows.append(row)
        except EOFError:
            open_tail = True
        path.write_bytes(gzip.compress(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows).encode(),mtime=0))
        a.save(HERE/'raw/chainlink_manifest.json',dict(source=str(src),prefix_sha256=a.sha(tmp),
            normalized_sha256=a.sha(path),rows=len(rows),open_tail=open_tail,max_received_ms=max(r['rcv'] for r in rows)))
    a.public.cached(HERE/'raw/market_result_1790031600.json',
                    'https://gamma-api.polymarket.com/markets/slug/btc-updown-15m-1790031600')
    p = HERE/'raw/manifest.json'
    if not p.exists():
        a.save(p,{str(f.relative_to(HERE)):a.sha(f) for f in (HERE/'raw').glob('*') if f.is_file()})
    protect()


def select(start):
    root = source(start)
    a.HERE,a.START,a.END,a.CUT = root,start,start+900,(start+1020)*1000
    a.SLUG = f'btc-updown-15m-{start}'
    a.verify_inputs()
    special = start==1790031600
    report = a.read((N/'channels/A' if special else root)/'results/report.json')
    gatepath = root/'results/eligibility.json'
    gate = a.read(gatepath)['data_gate'] if gatepath.exists() else report['data_gate']
    reasons = []
    if gate!='PASS_OBSERVED_FLOW_GATE':
        reasons.append('frozen_data_gate_failed')
    if special:
        chain = a.read(N/'results/independent_chain.json')
        comparison = a.read(N/'results/comparison.json')
        diag = a.read(N/'results/api_diagnostic.json')['rows']
        assert not chain['new_to_api_ws_universe'] and not chain['known_receipts_absent_from_scan']
        assert not comparison['only_a'] and not comparison['only_b']
        assert all(x['only_missing_row_added'] for x in diag)
        # First gate remains failed; subsequent exact reconciliation is a new offline label.
        confirmed = a.read(N/'channels/A/results/api_reconciliation.json')
        assert len(confirmed['true_confirmed']['differences'])==1 and not confirmed['false']['differences']
        assert report['api_differences']==dict(true_initial=1,true_confirmed=1,false=0)
        reasons = ['LATER_RECONCILED_API_ONLY']
    eligible = gate=='PASS_OBSERVED_FLOW_GATE' or reasons==['LATER_RECONCILED_API_ONLY']
    return root,dict(start=start,frozen_data_gate=gate,offline_status='RECONCILED_LATER' if special else gate,
                     replay_eligible=eligible,reasons=reasons,economic_pnl=None)


def ticks_with_initial(events,tokens,checkpoints,initial):
    """A received pre-window metadata observation seeds tick state; future values cannot."""
    when=initial.get('received_ms')
    tick=initial['data'].get('orderPriceMinTickSize')
    seed=[]
    if when is not None and tick is not None:
        assert D(str(tick)) in (D('.1'),D('.01'),D('.001'),D('.0001'))
        # Internal tick-only input to the existing helper, never a fabricated raw book.
        seed=[dict(k='book',rcv=when,p=dict(asset_id=t,timestamp=str(when),tick_size=str(tick))) for t in tokens]
    return prior.ticks_at(sorted(seed+events,key=lambda e:e['rcv']),tokens,checkpoints)


def load(start):
    root,row = select(start)
    if not row['replay_eligible']:
        return row,None
    path = N/'channels/A/events.jsonl.gz' if start==1790031600 else root/'raw/events.jsonl.gz'
    with gzip.open(path,'rt') as f:
        events = [json.loads(line) for line in f]
    initial = a.read(root/'raw/market_start.json')
    market = initial['data']
    tokens = json.loads(market['clobTokenIds'])
    events,origin = prior.book_events(events,tokens)
    checks = [(start+n)*1000 for n in range(30,841)]
    client,issues = a.m1.books_at(events,tokens,checks)
    assert not issues.get('future_source_clock') and not issues.get('out_of_order_book')
    ct = ticks_with_initial(events,tokens,checks,initial)
    # Offline venue reconstruction only. Policies never receive this stream.
    published = sorted([dict(e,rcv=int(e['p']['timestamp'])) for e in events
                        if e['k'] in ('book','price_change','tick_size_change')],key=lambda e:e['rcv'])
    venue,vt = {},{}
    for delay in (250,750):
        times = [t+delay for t in checks]
        venue[delay],_ = a.m1.books_at(published,tokens,times)
        vt[delay] = ticks_with_initial(published,tokens,times,initial)
    groups = {p.stem:a.m1.matches(a.read(p)['data']) for p in (root/'raw/receipts').glob('*.json')}
    flows,errors,_ = a.m1.trade_flows(events,groups,tokens)
    assert not errors
    makers = {(tx,m['log_index']):m for tx,gg in groups.items() for g in gg for m in g['makers']}
    prints = []
    for f in flows:
        m = makers[f['tx'],f['log_index']]
        gross = m['cash_cost']-m['fee'] if m['side']==0 else -m['cash_cost']+m['fee']
        cash = gross if m['side']==0 else m['qty']-gross
        assert f['obs_lo']==f['obs_hi'] and f['received']>=f['obs_lo']
        prints.append(dict(side=f['side'],qty=D(m['qty'])/ex.UNIT,gross=D(cash)/ex.UNIT,
            obs=f['obs_lo'],rcv=f['received'],tx=f['tx'],log=f['log_index']))
    rp = HERE/'raw/market_result_1790031600.json' if start==1790031600 else root/'raw/market_result.json'
    result = a.read(rp)['data']
    for m in (market,result):
        meta = a.accounting.ref.classify(m)
        assert (meta['group'],meta['S'],meta['end'],meta['mechanism'])==('btc_15m',start,start+900,'chainlink_twap60')
        assert json.loads(m['clobTokenIds'])==tokens
        assert m['feesEnabled'] and D(str(m['feeSchedule']['rate']))==D('.07') and m['feeSchedule']['exponent']==1
    row.update(winner=a.accounting.ref.base.outcome(result),book_origin_ms=origin,prints=len(prints),
               initial_metadata_received_ms=initial.get('received_ms'),
               initial_metadata_tick=market.get('orderPriceMinTickSize'),
               resolution_received_ms=a.read(rp).get('fetched_ms'),arms={},control={})
    return row,dict(client=client,venue=venue,ct=ct,vt=vt,prints=prints,market=market,result=result)


def run_one(data,profile,mode,tie,arm,trace=False):
    name,offset,hedge,funded = arm
    return ex.run(data['client'],data['venue'][profile['accept']],data['prints'],data['market'],mode,offset,
        hedge,profile['accept'],profile['learn'],data['ct'],data['vt'][profile['accept']],funded,
        cancel_delay=profile['cancel'],trade_shift=profile['shift'],tie_order=tie,trace=trace)


def run_all():
    protect()
    for name,digest in a.read(HERE/'raw/manifest.json').items():
        assert a.sha(HERE/name)==digest
    clpaths = [HERE/'raw/chainlink.jsonl.gz']
    for stage in (E,Z):
        manifest = a.read(stage/'raw/chainlink_manifest.json')
        for name,info in manifest.items():
            assert a.sha(stage/name)==info['sha256']
            clpaths.append(stage/name)
    streams,refs = ex.engine.old.chainlink_streams(clpaths)
    rows = []
    for start in PROTOCOL['starts']:
        row,data = load(start)
        if data is None:
            rows.append(row)
            continue
        # Neither final winner nor later reference validation can change a decision.
        row['reference_matches_afterward'] = any(e.get('eventMetadata',{}).get('priceToBeat') is not None
            and start in refs and abs(float(e['eventMetadata']['priceToBeat'])-refs[start][1])<1e-6
            for e in data['result'].get('events',[]))
        for delay in (250,750):
            p0 = prior.candidate(data['client'],data['venue'][delay],data['market'],streams,refs,delay)
            p0['conditional_pnl'] = D(str(p0['state']['q'][row['winner']]))-D(str(p0['state']['cash'])) if row['winner'] in (0,1) and not p0['gaps'] else None
            row['control'][str(delay)] = p0
        for profile in PROTOCOL['profiles']:
            for mode in PROTOCOL['queues']:
                for tie in PROTOCOL['ties']:
                    for arm in ARMS:
                        v = run_one(data,profile,mode,tie,arm)
                        v['conditional_pnl'] = v['actual']['q'][row['winner']]-v['actual']['cash'] if row['winner'] in (0,1) and not v['unknown'] else None
                        v['economic_pnl'] = None
                        key = ':'.join((arm[0],profile['name'],mode,tie))
                        row['arms'][key] = v
        a.save(HERE/'results/markets'/f'{start}.json',row)
        # Keep a compact table in RAM; complete per-path audit stays in market file.
        rows.append({**row,'arms':{k:{kk:v[kk] for kk in ('conditional_pnl','unknown','max_cash','max_net','min_worst','lifecycle','max_funding')} for k,v in row['arms'].items()}})
        print('Replayed',start,len(row['arms']),flush=True)
    a.save(HERE/'results/cohort.json',dict(markets=rows,status='CONDITIONAL_TIMING_SENSITIVITY',economic_pnl=None))
    summary(rows)
    protect()


def summary(rows):
    good = [r for r in rows if r['replay_eligible']]
    tables = {}
    for key in sorted({k for r in good for k in r['arms']}):
        values = [r['arms'][key]['conditional_pnl'] for r in good]
        complete = all(v is not None for v in values)
        vv = [D(v) for v in values if v is not None]
        tables[key] = dict(per_market=values,complete=len(vv),conditional_total=sum(vv,D(0)) if complete else None,
            without_best=sum(vv,D(0))-max(vv) if complete else None,all_assigned_total=None)
    pairs = {}
    for name in ('M2_bid','M2_reserved'):
        for profile in PROTOCOL['profiles']:
            for mode in PROTOCOL['queues']:
                for tie in PROTOCOL['ties']:
                    suffix=':'.join((profile['name'],mode,tie))
                    one,two = tables['M1_bid:'+suffix],tables[name+':'+suffix]
                    pairs[name+':'+suffix] = (D(two['conditional_total'])-D(one['conditional_total'])) if one['conditional_total'] is not None and two['conditional_total'] is not None else None
    a.save(HERE/'results/summary.json',dict(assigned=len(rows),eligible_starts=[r['start'] for r in good],
        excluded_starts=[r['start'] for r in rows if not r['replay_eligible']],scenarios=tables,hedge_minus_passive=pairs,
        economic_pnl=None,warning='Observed scenario extrema are not mathematical PnL bounds. One already-seen UTC day.'))


def repeat():
    hashes=[]
    with patch.object(a.public,'get',side_effect=AssertionError('offline HTTP')),patch.object(a.m1.probe,'rpc',side_effect=AssertionError('offline RPC')):
        for _ in range(2):
            run_all()
            hashes.append({str(p.relative_to(HERE)):a.sha(p) for p in (HERE/'results').rglob('*.json') if p.name not in ('reproducibility.json','checks.json')})
    assert hashes[0]==hashes[1]
    a.save(HERE/'results/reproducibility.json',dict(identical=True,sha256=hashes[0]))


def diagnose():
    """Explain conservative nulls; do not turn a failed execution gate into profit."""
    protect()
    output=[]
    rows=a.read(HERE/'results/cohort.json')['markets']
    for row in rows:
        keys=[k for k,v in row.get('arms',{}).items() if v['unknown']]
        if not keys:
            continue
        _,data=load(row['start'])
        # Equal tie variants have the same missing-book cause; inspect one per profile/arm/queue.
        for key in keys:
            arm_name,profile_name,mode,tie=key.split(':')
            if tie!='lifecycle_first':
                continue
            profile=next(p for p in PROTOCOL['profiles'] if p['name']==profile_name)
            arm=next(x for x in ARMS if x[0]==arm_name)
            failed=[]
            original=ex.engine.quote
            def quote(book,now):
                value=original(book,now)
                if value is None and now%1000:
                    bids,asks,stamp=book
                    failed.append(dict(now=now,age_ms=now-stamp,bid=bids[0][0] if bids else None,
                                       ask=asks[0][0] if asks else None))
                return value
            with patch.object(ex.engine,'quote',side_effect=quote):
                value=run_one(data,profile,mode,tie,arm)
            output.append(dict(start=row['start'],key=key,unknown=value['unknown'],failed_acceptance_checks=failed))
    a.save(HERE/'null_diagnostic.json',output)
    protect()


if __name__=='__main__':
    {'prepare':prepare,'run':run_all,'repeat':repeat,'diagnose':diagnose}[sys.argv[1]]()
