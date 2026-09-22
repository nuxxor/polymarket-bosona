"""Independent raw streams versus public receipts; never an execution/PnL replay."""
from collections import Counter,defaultdict
from decimal import Decimal as D
import gzip
import json
from pathlib import Path
import sys
from unittest.mock import patch

import record as rec
from common import module

HERE, ROOT = rec.HERE, rec.ROOT
W = ROOT/'btc15_ws_validation_20260921'
OLD = ROOT/'btc15_execution_reserve_20260921'
MAIN = Path('/home/taygun/Masaüstü/polymarket-bosona')
a = module('frozen_feed_audit',W/'study.py')
write = a.save
a.HERE = HERE/'market'
a.START,a.END,a.CUT = rec.START,rec.START+900,rec.CUT*1000
a.SLUG = f'btc-updown-15m-{a.START}'
DUAL = HERE/'raw/dual'


def protect():
    a.protected()
    assert a.sha(HERE/'protocol.json')==(HERE/'protocol.sha256').read_text().strip()
    for name,digest in a.read(OLD/'delivery_manifest.json')['sha256'].items():
        assert a.sha(OLD/name)==digest
    p = HERE/'sources.json'
    if not p.exists():
        files = [W/'study.py',ROOT/'btc15_reconciled_v1_20260921/record_ws.py',*a.SOURCES]
        files += [MAIN/f'data/analysis/btc5m_m6_20260922/{n}' for n in ('diagnose.py','report.json','check.py')]
        files += [MAIN/f'data/analysis/btc5m_m5_20260922/{n}' for n in ('orders.json','report.json','clock_qualification.json')]
        write(p,{str(f):a.sha(f) for f in files})
    for name,digest in a.read(p).items():
        assert a.sha(Path(name))==digest,name


def decode(rows, market):
    """Retain errors alongside raw evidence; never silently accept an unknown frame."""
    events,issues,seq,last_mono,last_rcv = [],[],0,-1,-1
    tokens = set(json.loads(market['clobTokenIds']))
    counts = Counter()
    for row in rows:
        assert row['seq']==seq+1 and row['monotonic_ns']>=last_mono,'raw sequence/monotonic discontinuity'
        seq,last_mono = row['seq'],row['monotonic_ns']
        if row['received_ms']<last_rcv:
            issues.append(dict(seq=seq,kind='wall_clock_backwards',rcv=row['received_ms']))
        last_rcv = row['received_ms']
        counts[row['kind']] += 1
        if row['received_ms']>a.CUT:
            continue
        if row['kind'] in ('connect','gap'):
            events.append(dict(k=row['kind'],rcv=row['received_ms'],p=row))
        elif row['kind']=='frame':
            raw = row.get('raw')
            if raw=='PONG':
                counts['pong'] += 1
                continue
            try:
                data = json.loads(raw)
                data = data if isinstance(data,list) else [data]
            except (ValueError,TypeError):
                issues.append(dict(seq=seq,kind='unparsed_frame',rcv=row['received_ms']))
                continue
            for event in data:
                kind = event.get('event_type') if isinstance(event,dict) else None
                if kind not in ('book','price_change','last_trade_price','tick_size_change','market_resolved'):
                    issues.append(dict(seq=seq,kind='unknown_event',rcv=row['received_ms']))
                    continue
                try:
                    assets = [x.get('asset_id') for x in event['price_changes']] if kind=='price_change' else [event.get('asset_id')] if 'asset_id' in event else event.get('assets_ids',[])
                    assert int(event['timestamp'])>=0
                    if kind=='last_trade_price':
                        assert event['side'] in ('BUY','SELL') and event['transaction_hash']
                        assert 0<=D(event['price'])<=1 and a.m1.units(event['size'])>0
                    if kind=='book':
                        assert isinstance(event['bids'],list) and isinstance(event['asks'],list)
                except (AssertionError,KeyError,TypeError,ValueError,AttributeError,ArithmeticError):
                    issues.append(dict(seq=seq,kind='invalid_event_schema',rcv=row['received_ms']))
                    continue
                if event.get('market')!=market['conditionId'] or not assets or not set(assets)<=tokens:
                    issues.append(dict(seq=seq,kind='wrong_identity',rcv=row['received_ms']))
                    continue
                events.append(dict(k=kind,rcv=row['received_ms'],mono=row['monotonic_ns'],p=event))
    return events,dict(counts=counts,issues=issues,rows=seq,last_received_ms=last_rcv)


def freeze():
    protect()
    if (a.HERE/'raw/freeze.json').exists():
        return
    status = a.read(DUAL/'status.json')
    assert not status['running'], 'freeze only after bounded recorder closes'
    assert a.sha(HERE/'record.py')==status['source_sha256']
    hashes = a.read(DUAL/'closed_hashes.json')
    market = a.read(DUAL/'market.json')
    write(a.HERE/'raw/market_start.json',market)
    all_trades,manifest = [],{}
    for channel in ('A','B'):
        path = DUAL/f'{channel}.jsonl.gz'
        assert a.sha(path)==hashes[path.name]
        with gzip.open(path,'rt') as stream:
            ee,quality = decode((json.loads(s) for s in stream),market['data'])
        out = HERE/'channels'/channel/'events.jsonl.gz'
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_bytes(gzip.compress(''.join(json.dumps(e,separators=(',',':'))+'\n' for e in ee).encode(),mtime=0))
        write(out.parent/'parse.json',quality)
        manifest[str(out.relative_to(HERE))] = a.sha(out)
        manifest[str((out.parent/'parse.json').relative_to(HERE))] = a.sha(out.parent/'parse.json')
        all_trades.extend(e for e in ee if e['k']=='last_trade_price')
    # This union is ONLY transaction discovery for the shared receipt downloader.
    # Independent A/B books are never interleaved for analysis or pretend fills.
    merged = a.HERE/'raw/events.jsonl.gz'
    merged.write_bytes(gzip.compress(''.join(json.dumps(e)+'\n' for e in all_trades).encode(),mtime=0))
    write(a.HERE/'raw/freeze.json',dict(start=a.START,end=a.END,received_cutoff_ms=a.CUT,
        events_sha256=a.sha(merged),sources=a.read(HERE/'sources.json'),purpose='receipt discovery only'))
    write(HERE/'raw/streams_manifest.json',dict(files=manifest,raw_hashes=hashes,recorder=status))


def fetch():
    freeze()
    a.freeze = freeze
    a.fetch()
    a.confirm()
    a.verify_inputs()


def scan():
    """Discover market match logs without using WS or /trades as the tx universe."""
    protect()
    probe = a.m1.probe
    tokens = set(json.loads(a.read(DUAL/'market.json')['data']['clobTokenIds']))
    head = a.rpc_cache('independent/head.json','eth_getBlockByNumber',['latest',False])
    number = int(head['number'],16)
    def header(n):
        return a.rpc_cache(f'independent/headers/{n}.json','eth_getBlockByNumber',[hex(n),False])
    def timestamp(n):
        return int(header(n)['timestamp'],16)
    assert timestamp(number-1000)<a.START<a.CUT//1000<=timestamp(number)
    def boundary(target):
        lo,hi = number-1000,number
        while lo<hi:
            mid = (lo+hi)//2
            if timestamp(mid)<target:
                lo = mid+1
            else:
                hi = mid
        assert timestamp(lo-1)<target<=timestamp(lo)
        return lo
    first,stop = boundary(a.START),boundary(a.CUT//1000)
    assert 0<stop-first<=1000
    hits,segments = [],[]
    for lo in range(first,stop,20):
        hi = min(stop-1,lo+19)
        params = [dict(fromBlock=hex(lo),toBlock=hex(hi),address=probe.EXCHANGE,topics=[probe.MATCHED])]
        logs = a.rpc_cache(f'independent/logs/{lo}.json','eth_getLogs',params)
        assert len(logs)<10000,'potential truncated RPC log response'
        for event in logs:
            assert not event.get('removed',False) and lo<=int(event['blockNumber'],16)<=hi
            assert event['address'].lower()==probe.EXCHANGE and event['topics'][0]==probe.MATCHED
            side,token,making,taking = probe.words(event['data'],4)
            assert side in (0,1)
            if str(token) in tokens:
                hits.append(event)
        segments.append(dict(first=lo,last=hi,logs=len(logs)))
        if lo in (first,first+((stop-first-1)//20)*20):
            other = a.rpc_cache(f'independent/cross/{lo}.json','eth_getLogs',params,(probe.RPCS[1],))
            assert logs==other,'RPC log providers differ'
    keys = [(e['transactionHash'],int(e['logIndex'],16)) for e in hits]
    assert len(set(keys))==len(keys)
    known = {}
    for path in (a.HERE/'raw/receipts').glob('*.json'):
        receipt = a.read(path)['data']
        if first<=int(receipt['blockNumber'],16)<stop:
            known.update({(g['tx'],g['match_log']):g for g in a.m1.matches(receipt)
                          if g['active']['token'] in tokens})
    missing = sorted(set(keys)-known.keys())
    absent = sorted(known.keys()-set(keys))
    for e in hits:
        key = e['transactionHash'],int(e['logIndex'],16)
        if key in known:
            g = known[key]
            side,token,making,taking = probe.words(e['data'],4)
            assert g['active']['token']==str(token) and g['active']['side']==side
            assert g['active']['qty']==(taking if side==0 else making)
    files = {str(p.relative_to(HERE)):a.sha(p) for p in (a.HERE/'raw/independent').rglob('*.json')}
    write(HERE/'raw/independent_manifest.json',files)
    write(HERE/'results/independent_chain.json',dict(first_block=first,stop_block_exclusive=stop,
        start=a.START,cutoff_ms=a.CUT,segments=segments,match_logs=hits,
        matched_market_logs=len(hits),new_to_api_ws_universe=missing,known_receipts_absent_from_scan=absent,
        note='V2 Exchange, two contract tokens, fixed block-time range; not an inferred matching clock.'))


def compare():
    protect()
    a.verify_inputs()
    for name,digest in a.read(HERE/'raw/independent_manifest.json').items():
        assert a.sha(HERE/name)==digest
    independent = a.read(HERE/'results/independent_chain.json')
    manifest = a.read(HERE/'raw/streams_manifest.json')
    for name,digest in manifest['files'].items():
        assert a.sha(HERE/name)==digest
    channels = {}
    for channel in ('A','B'):
        root = HERE/'channels'/channel
        with gzip.open(root/'events.jsonl.gz','rt') as stream:
            events = [json.loads(s) for s in stream]
        a.events = lambda events=events: events
        a.quote_probes = lambda *_: dict(rows=[],status_counts={})
        a.save = lambda path,obj,root=root: write(root/'results'/path.name,obj)
        try:
            a.analyze()
        finally:
            a.save = write
        report = a.read(root/'results/report.json')
        parse = a.read(root/'parse.json')
        reasons = []
        if parse['issues']:
            reasons.append('raw_parser_or_clock_issues')
        if parse['last_received_ms']<=a.CUT or manifest['recorder']['reason']!='duration_complete':
            reasons.append('incomplete_capture')
        if report['data_gate']!='PASS_OBSERVED_FLOW_GATE':
            reasons.append('book_receipt_or_flow_gate')
        if independent['new_to_api_ws_universe']:
            reasons.append('independent_chain_has_unseen_transactions')
        if independent['known_receipts_absent_from_scan']:
            reasons.append('independent_chain_scan_incomplete')
        flows = a.read(root/'results/flows.json')
        channels[channel] = dict(data_gate='MISSING_DATA' if reasons else 'PASS_OBSERVED_FLOW_GATE',
            reasons=reasons,parse=parse,report=report,flows=flows)
    fa,fb = [{(f['tx'],f['log_index']):f for f in channels[c]['flows']} for c in ('A','B')]
    shared = sorted(fa.keys() & fb.keys())
    for key in shared:
        assert (fa[key]['side'],fa[key]['qty'])==(fb[key]['side'],fb[key]['qty'])
    a_only,b_only = sorted(fa.keys()-fb.keys()),sorted(fb.keys()-fa.keys())
    results = dict(channels=channels,shared_maker_fills=len(shared),only_a=a_only,only_b=b_only,
        common_source_clock_differences=[key for key in shared if (fa[key]['obs_lo'],fa[key]['obs_hi'])!=(fb[key]['obs_lo'],fb[key]['obs_hi'])],
        receive_b_minus_a_ms=[fb[k]['received']-fa[k]['received'] for k in shared],
        economic_pnl=None,execution_calibrated=False)
    write(HERE/'results/comparison.json',results)
    protect()


def diagnostic():
    """Attribute the API disagreement without rewriting the original gate."""
    protect()
    diffs = a.read(HERE/'channels/A/results/api_reconciliation.json')['true_confirmed']['differences']
    rows,inputs = [],{}
    condition = a.read(DUAL/'market.json')['data']['conditionId']
    for i,diff in enumerate(diffs):
        tx,owner,token,side = diff['key']
        receipt = a.read(a.HERE/'raw/receipts'/f'{tx}.json')['data']
        name = f'diagnostic/cross_{i}.json'
        other = a.rpc_cache(name,'eth_getTransactionReceipt',[tx],(a.m1.probe.RPCS[1],))
        assert all(receipt[k]==other[k] for k in ('transactionHash','blockHash','status','logs'))
        inputs[str((a.HERE/'raw'/name).relative_to(HERE))] = a.sha(a.HERE/'raw'/name)
        checks = {}
        for mode in ('true','false'):
            path = HERE/'raw/diagnostic'/f'user_{i}_{mode}.json'
            pages = a.public.paged(path,dict(user=owner,market=condition,takerOnly=mode),'trades')
            assert len(pages[-1]['rows'])<500
            checks[mode] = [r for page in pages for r in page['rows'] if r['transactionHash']==tx]
            inputs[str(path.relative_to(HERE))] = a.sha(path)
        path = HERE/'raw/diagnostic/market_true_later.json'
        pages = a.public.paged(path,dict(market=condition,takerOnly='true'),'trades')
        assert len(pages[-1]['rows'])<500
        later_all = [r for page in pages for r in page['rows']]
        later = [r for r in later_all if r['transactionHash']==tx]
        initial = [r for page in a.read(a.HERE/'raw/trades_true_confirmation.json')['pages'] for r in page['rows']]
        only_missing_row_added = a.aggregate_api(later_all)==a.aggregate_api(initial+later)
        later_manifest = HERE/'raw/diagnostic_later_manifest.json'
        digest = {str(path.relative_to(HERE)):a.sha(path)}
        if not later_manifest.exists():
            write(later_manifest,digest)
        assert a.read(later_manifest)==digest
        rows.append(dict(difference=diff,user_filtered=checks,later_market_taker=later,
            later_api_rows=len(later_all),only_missing_row_added=only_missing_row_added,
            receipt=a.m1.matches(receipt),
            inference='Initial and confirmed whole-market taker API differ from exchange logs. '
                      'User-filtered and later queries are separate observations, not replacements for the frozen gate.'))
    manifest = HERE/'raw/diagnostic_manifest.json'
    if not manifest.exists():
        write(manifest,inputs)
    assert a.read(manifest)==inputs
    write(HERE/'results/api_diagnostic.json',dict(rows=rows))


def existing():
    """Two equal economic summaries are distinct real matches, not duplicates."""
    protect()
    raw = OLD/'markets/1790028900/raw'
    missing = '0x38653423aa33191fa36714e9463daed61a437d5043c4325bd38f46a064f90003'
    equal = '0x8a52f8ddce9884442c3f6987005e276139fc6967a3477b091c53046ceba31ce2'
    receipts = [a.read(raw/'receipts'/f'{t}.json')['data'] for t in (missing,equal)]
    for name,digest in a.read(HERE/'existing/manifest.json').items():
        assert a.sha(HERE/name)==digest
    for receipt in receipts:
        other = a.read(HERE/'existing/raw/receipts'/f'{receipt["transactionHash"]}.json')['data']
        assert all(receipt[k]==other[k] for k in ('blockHash','transactionHash','status','logs'))
        scanned = a.read(HERE/'existing/raw/block_matches.json')['data']
        expected = [e for e in receipt['logs'] if e['topics'][0]==a.m1.probe.MATCHED]
        observed = [e for e in scanned if e['transactionHash']==receipt['transactionHash']]
        assert expected==observed
    pairs = [a.m1.matches(x)[0] for x in receipts]
    assert receipts[0]['blockHash']==receipts[1]['blockHash']
    def key(g):
        return g['active']['token'],g['active']['side'],g['active']['qty'],g['gross']
    assert key(pairs[0])==key(pairs[1])
    assert pairs[0]['active']['order_hash']!=pairs[1]['active']['order_hash']
    assert pairs[0]['active']['owner']!=pairs[1]['active']['owner']
    ee = [json.loads(s) for s in gzip.open(raw/'events.jsonl.gz','rt')]
    linked = [e for e in ee if e['k']=='last_trade_price' and e['p'].get('transaction_hash') in (missing,equal)]
    assert len(linked)==1 and linked[0]['p']['transaction_hash']==equal
    report = a.read(MAIN/'data/analysis/btc5m_m6_20260922/report.json')
    m5 = MAIN/'data/analysis/btc5m_m5_20260922'
    inputs = a.read(m5/'input_manifest.json')
    for name in ('orders.json','events.jsonl.gz'):
        assert a.sha(m5/name)==inputs['files'][name]
    own_events = [json.loads(s) for s in gzip.open(m5/'events.jsonl.gz','rt')]
    orders = {o['oid']:o for o in a.read(m5/'orders.json')}
    receipt_manifest = a.read(m5/'receipt_fetch/fetch_manifest.json')['files']
    receipt_manifest.update(a.read(m5/'own_manifest.json'))
    trace = [json.loads(s) for s in (OLD/'raw/orders.jsonl').read_text().splitlines()]
    clocks = []
    for row in report['rows']:
        for f in row['own_fills']:
            path = m5/'receipt_fetch/receipts'/f'{f["tx"]}.json'
            # Public on-chain receipt; no account/state/key file is needed.
            digest = receipt_manifest.get('receipts/'+path.name,receipt_manifest.get('receipt_fetch/receipts/'+path.name))
            assert digest and a.sha(path)==digest
            group = a.m1.matches(a.read(path))
            selected = [e for e in own_events if e['k']=='last_trade_price' and e['p'].get('transaction_hash')==f['tx']]
            actual,errors,_ = a.m1.trade_flows(selected,{f['tx']:group},orders[row['oid']]['tokens'])
            assert not errors
            clock, = [x for x in actual if x['log_index']==f['log_index']]
            maker, = [m for g in group for m in g['makers'] if m['log_index']==f['log_index']]
            assert maker['order_hash']==row['oid'] and maker['qty']==f['quantity_units']
            assert clock['obs_lo']==clock['obs_hi']==f['source_ms']
            confirmed = [x for x in trace if x['event']=='response' and x['op']=='get_order'
                         and x['reply'].get('oid')==row['oid'] and x['reply'].get('status')=='MATCHED']
            assert confirmed
            first = min(x['end']['utc_ns'] for x in confirmed)
            clocks.append(dict(oid=row['oid'],tx=f['tx'],log_index=f['log_index'],
                public_source_ms=f['source_ms'],observed_matched_ns=first,
                public_after_matched_ms=str(D(f['source_ms'])-D(first)/1000000),
                private_exchange_match_ms=None))
    assert len(clocks)==5 and any(D(x['public_after_matched_ms'])>100 for x in clocks)
    write(HERE/'results/existing_evidence.json',dict(distinct_equal_summary_matches=pairs,
        captured_public_messages=linked,public_clocks=clocks,
        conclusion='Missing quantity is real. Equal price/size cannot supply the missing trade identity or time. '
                   'Public source timestamps are not demonstrated venue match timestamps.'))


def collisions():
    """Counterexample to a universal equal-price/quantity message suppression rule."""
    protect()
    sources = [W]+list((ROOT/'btc15_ws_expansion_20260921/markets').iterdir())+list((OLD/'markets').iterdir())
    rows,inputs = [],{}
    for source in sources:
        raw = source/'raw'
        report = a.read(source/'results/report.json')
        tokens = json.loads(a.read(raw/'market_start.json')['data']['clobTokenIds'])
        flows = a.read(source/'results/flows.json')
        seen = {(x['tx'],x['log_index']) for x in flows}
        hashes = a.read(raw/'fetch.json')['files']
        for name in ('results/report.json','results/flows.json','raw/fetch.json'):
            inputs[str(source/name)] = a.sha(source/name)
        assert a.sha(raw/'market_start.json')==hashes['raw/market_start.json']
        groups = defaultdict(list)
        for path in sorted((raw/'receipts').glob('*.json')):
            assert a.sha(path)==hashes[str(path.relative_to(source))]
            receipt = a.read(path)['data']
            header = raw/'blocks'/f'{receipt["blockNumber"]}.json'
            assert a.sha(header)==hashes[str(header.relative_to(source))]
            block = a.read(header)['data']
            assert block['hash']==receipt['blockHash']
            if not report['start']<=int(block['timestamp'],16)<report['end']:
                continue
            for g in a.m1.matches(receipt):
                active = g['active']
                if active['token'] not in tokens:
                    continue
                key = (receipt['blockHash'],active['token'],active['side'],active['qty'],g['gross'])
                groups[key].append(dict(tx=g['tx'],log=g['match_log'],order=active['order_hash'],
                    seen=all((g['tx'],m['log_index']) in seen for m in g['makers'])))
        duplicate = [dict(key=k,matches=v) for k,v in sorted(groups.items()) if len(v)>1]
        rows.append(dict(start=report['start'],groups=sum(len(v) for v in groups.values()),equal_summary_groups=duplicate))
    manifest = HERE/'raw/collision_inputs.json'
    if not manifest.exists():
        write(manifest,inputs)
    assert a.read(manifest)==inputs
    write(HERE/'results/collision_scan.json',dict(scope='seven prior assigned BTC15 windows; block-time groups, no exchange-time imputation',markets=sorted(rows,key=lambda r:r['start'])))


def repeat():
    hashes = []
    with patch.object(a.m1.probe,'rpc',side_effect=AssertionError('offline run attempted network')),patch.object(a.public,'get',side_effect=AssertionError('offline API request')):
        for _ in range(2):
            existing()
            collisions()
            scan()
            compare()
            diagnostic()
            files = list((HERE/'results').glob('*.json'))+list((HERE/'channels').glob('*/results/*.json'))
            hashes.append({str(p.relative_to(HERE)):a.sha(p) for p in files if p.name!='reproducibility.json'})
    assert hashes[0]==hashes[1]
    write(HERE/'results/reproducibility.json',dict(identical=True,sha256=hashes[0]))


if __name__=='__main__':
    {'fetch':fetch,'scan':scan,'compare':compare,'diagnostic':diagnostic,'existing':existing,'collisions':collisions,'repeat':repeat}[sys.argv[1]]()
