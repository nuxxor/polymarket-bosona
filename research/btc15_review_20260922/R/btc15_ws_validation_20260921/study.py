"""Finite public BTC15 feed/receipt audit. No orders, credentials or recorder changes."""
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal as D
import gzip
import hashlib
import io
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
R = HERE.parent
V = R/'btc15_reconciled_v1_20260921'
sys.path.insert(0, str(V))
from common import accounting, module, protected  # noqa: E402

MAIN = Path('/home/taygun/Masaüstü/polymarket-bosona')
M1PATH = MAIN/'data/analysis/btc5m_maker_feasibility_20260921/replay.py'
m1 = module('existing_market_decoder', M1PATH)
public = module('existing_public_fetch', R/'fable_review_20260921/code/fetch_new_period.py')
PILOT = V/'raw/ws_pilot_v1'
START, END, CUT = 1790023500, 1790024400, 1790024520000
SLUG = f'btc-updown-15m-{START}'
SOURCES = [M1PATH, Path(m1.SPEC.origin), Path(public.__file__), V/'common.py']


def read(path):
    return json.loads(path.read_bytes())


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, indent=2, default=str)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def events():
    with gzip.open(HERE/'raw/events.jsonl.gz', 'rt') as stream:
        return [json.loads(line) for line in stream]


def freeze():
    protected()
    if (HERE/'raw/freeze.json').exists():
        return
    status = read(PILOT/'status.json')
    assert status['received_ms'] >= CUT, 'fixed cutoff not recorded yet'
    assert sha(V/'record_ws.py') == status['source_sha256']
    market = read(PILOT/'markets'/f'{SLUG}.json')
    meta = accounting.ref.classify(market['data'])
    assert meta['group'] == 'btc_15m' and meta['S'] == START and meta['end'] == END
    assert meta['mechanism'] == 'chainlink_twap60'
    save(HERE/'raw/market_start.json', market)
    save(HERE/'raw/recorder_status.json', status)
    target, source_info, lines, crossed, tail = market['data']['conditionId'], {}, [], False, False
    for path in sorted(PILOT.glob('events_*.jsonl.gz')):
        # Freeze a byte prefix; a still-open gzip member need not have a trailer.
        size = path.stat().st_size
        with path.open('rb') as stream:
            raw = stream.read(size)
        copy = HERE/'raw'/('source_'+path.name)
        copy.write_bytes(raw)
        source_info[path.name] = dict(bytes=size, sha256=sha(copy))
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
                for rawline in stream:
                    row = json.loads(rawline)
                    if row['received_ms'] > CUT:
                        crossed = True
                        break
                    if row['kind'] != 'events':
                        lines.append(dict(k=row['kind'], rcv=row['received_ms'], p=row))
                    else:
                        lines.extend(dict(k=e['event_type'], rcv=row['received_ms'],
                            mono=row['monotonic_ns'], p=e) for e in row['data'] if e['market'] == target)
        except EOFError:
            tail = True
        if crossed:
            break
    assert crossed and lines, 'prefix does not fully cover fixed cutoff'
    payload = ''.join(json.dumps(x, separators=(',', ':'))+'\n' for x in lines).encode()
    (HERE/'raw/events.jsonl.gz').write_bytes(gzip.compress(payload, mtime=0))
    save(HERE/'raw/freeze.json', dict(start=START, end=END, received_cutoff_ms=CUT,
        source_prefixes=source_info, open_gzip_tail_encountered=tail,
        retained_events=len(lines), crossed_cutoff=True, events_sha256=sha(HERE/'raw/events.jsonl.gz'),
        collector_sha256=sha(Path(__file__)), sources={str(p):sha(p) for p in SOURCES}))
    print('Frozen', len(lines), 'events', flush=True)


def rpc_cache(name, method, params, endpoints=None):
    path = HERE/'raw'/name
    if path.exists():
        return read(path)['data']
    attempts = []
    for url in endpoints or m1.probe.RPCS:
        requested = round(time.time()*1000)
        try:
            data = m1.probe.rpc(url, method, params)
            save(path, dict(url=url, method=method, params=params, requested_ms=requested,
                 received_ms=round(time.time()*1000), prior_failures=attempts, data=data))
            return data
        except (OSError, ValueError, AssertionError) as exc:
            attempts.append(dict(url=url, error=type(exc).__name__, detail=str(exc)[:180]))
    raise ValueError(str(attempts))


def fetch():
    freeze()
    market = read(HERE/'raw/market_start.json')['data']
    condition = market['conditionId']
    all_rows = {}
    for mode in ('true', 'false'):
        pages = public.paged(HERE/'raw'/f'trades_{mode}.json', dict(market=condition, takerOnly=mode), 'trades')
        assert pages and len(pages[-1]['rows']) < 500
        rows = [r for page in pages for r in page['rows']]
        assert all(x['conditionId'] == condition for x in rows)
        all_rows[mode] = rows
    public.cached(HERE/'raw/market_result.json', 'https://gamma-api.polymarket.com/markets/slug/'+SLUG)
    public.paged(HERE/'raw/actor_activity.json', dict(user=public.WALLET, market=condition,
        sortBy='TIMESTAMP', sortDirection='ASC'), 'activity')
    transactions = sorted({x['transactionHash'] for x in all_rows['false']} |
                          {e['p']['transaction_hash'] for e in events() if e['k'] == 'last_trade_price'})
    assert len(transactions) <= 1000, 'finite receipt budget exceeded'
    for i, url in enumerate(m1.probe.RPCS):
        assert rpc_cache(f'chain_{i}.json', 'eth_chainId', [], (url,)) == '0x89'
    errors = []
    def receipt(tx):
        result = rpc_cache(f'receipts/{tx}.json', 'eth_getTransactionReceipt', [tx])
        assert result['transactionHash'] == tx and result['status'] == '0x1'
        time.sleep(.15)
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {pool.submit(receipt, tx):tx for tx in transactions}
        for i, job in enumerate(as_completed(jobs), 1):
            try:
                job.result()
            except (OSError, ValueError, AssertionError) as exc:
                errors.append(dict(tx=jobs[job], error=str(exc)))
            if i%50 == 0 or i == len(jobs):
                print(f'Receipts {i}/{len(jobs)}, errors {len(errors)}', flush=True)
    blocks = sorted({read(p)['data']['blockNumber'] for p in (HERE/'raw/receipts').glob('*.json')})
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda n:rpc_cache(f'blocks/{n}.json', 'eth_getBlockByNumber', [n, False]), blocks))
    cross = []
    for tx in transactions[:2]:
        path = HERE/'raw/receipts'/f'{tx}.json'
        if not path.exists():
            continue
        first = read(path)['data']
        second = rpc_cache(f'cross/{tx}.json', 'eth_getTransactionReceipt', [tx], (m1.probe.RPCS[1],))
        assert all(first[k] == second[k] for k in ('transactionHash', 'blockHash', 'status', 'logs'))
        cross.append(tx)
    save(HERE/'raw/fetch.json', dict(transactions=transactions, failures=errors, cross_provider=cross,
        files={str(p.relative_to(HERE)):sha(p) for p in sorted((HERE/'raw').rglob('*.json')) if p.name!='fetch.json'}))


def aggregate_api(rows):
    values = defaultdict(lambda:dict(qty=0, gross=D(0), rows=0))
    for r in rows:
        key = (r['transactionHash'], r['proxyWallet'].lower(), r['asset'], r['side'])
        values[key]['qty'] += m1.units(r['size'])
        values[key]['gross'] += D(str(r['price']))*m1.units(r['size'])
        values[key]['rows'] += 1
    return values


def confirm():
    market = read(HERE/'raw/market_start.json')['data']
    path = HERE/'raw/trades_true_confirmation.json'
    public.paged(path, dict(market=market['conditionId'],takerOnly='true'), 'trades')
    manifest = HERE/'raw/confirmation.json'
    if not manifest.exists():
        save(manifest, dict(reason='Independent repeat of paginated taker history; original retained.',
             files={str(path.relative_to(HERE)):sha(path)}))


def quote_probes(ee, tokens, groups, flows):
    """Independent fixed-lifetime quotes, not a reinvesting M1/M2 strategy."""
    output = []
    for age in (30, 180, 600, 840):
        decision = (START+age)*1000
        activation, cancel = decision+250, decision+1250
        ss, issues = m1.books_at(ee, tokens, (decision,activation,cancel))
        assert not issues
        tick = {}
        for e in ee:
            if e['rcv']>decision:
                break
            if e['k']=='book' and e['p'].get('tick_size'):
                tick[e['p']['asset_id']] = m1.units(e['p']['tick_size'])
            elif e['k']=='tick_size_change':
                tick[e['p']['asset_id']] = m1.units(e['p']['new_tick_size'])
        for side in (0,1):
            for offset in (0,10000):
                row = dict(age=age, side=side, price_offset=offset/m1.UNIT,
                    decision_ms=decision, activation_assumed_ms=activation,
                    cancel_assumed_ms=cancel, economic_pnl=None)
                bb = [ss[t][side] for t in (decision,activation,cancel)]
                if any(not b['ready'] or not 0<=t-b['obs']<=3000 or not 0<=t-b['rcv']<=3000
                       for t,b in zip((decision,activation,cancel),bb)):
                    output.append(dict(row,status='missing_book'))
                    continue
                if not bb[0]['BUY'] or not bb[0]['SELL'] or min(bb[0]['SELL'])-max(bb[0]['BUY'])>30000:
                    output.append(dict(row,status='no_eligible_quote'))
                    continue
                price = max(bb[0]['BUY'])-offset
                if tokens[side] not in tick or price<=0 or price%tick[tokens[side]]:
                    output.append(dict(row,status='invalid_or_unknown_tick'))
                    continue
                if bb[1]['SELL'] and price>=min(bb[1]['SELL']):
                    output.append(dict(row,status='post_only_rejected',price=price/m1.UNIT,
                        arrival_ask=min(bb[1]['SELL'])/m1.UNIT))
                    continue
                # A 100ms boundary guard is inherited from the existing M1 probe.
                eligible = []
                for f in flows:
                    if f['side']!=side or not activation+100<=f['obs_lo']<=f['obs_hi']<=cancel-100:
                        continue
                    if f['min_delay']<0 or f['max_delay']>3000:
                        continue
                    match = next(g for g in groups[f['tx']] if any(m['log_index']==f['log_index'] for m in g['makers']))
                    maker = next(m for m in match['makers'] if m['log_index']==f['log_index'])
                    gross = maker['cash_cost']-maker['fee'] if maker['side']==0 else -maker['cash_cost']+maker['fee']
                    equivalent_cash = gross if maker['side']==0 else maker['qty']-gross
                    # Compare micro-cash, not rounded feed price or a price epsilon.
                    if D(equivalent_cash)-D(price)*maker['qty']/m1.UNIT<=2:
                        eligible.append((f,maker['qty']))
                ahead = max(b['BUY'].get(price,0) for b in bb[:2])
                volume = sum(q for _,q in eligible)
                _, back = m1.queue_fill(ahead,5000000,volume)
                _, front = m1.queue_fill(0,5000000,volume)
                output.append(dict(row,status='conditional',price=price/m1.UNIT,
                    observed_tick=tick[tokens[side]]/m1.UNIT, ahead=ahead/m1.UNIT,
                    eligible_shares=volume/m1.UNIT, queue_back_shares=back/m1.UNIT,
                    queue_front_shares=front/m1.UNIT,
                    flows=[[f['tx'],f['log_index']] for f,_ in eligible]))
    return dict(rows=output, status_counts=dict(Counter(x['status'] for x in output)),
        note='Exploratory execution checks at existing entry/add/last-control times. Outcome already known; '
             'not a new preregistered policy test. Independent quotes, no M2 inventory, no profit claim. '
             '250ms acceptance and 1250ms cancellation are assumptions; queue front/back are scenarios.')


def verify_inputs():
    protected()
    manifest = read(HERE/'raw/freeze.json')
    assert (manifest['start'], manifest['end'], manifest['received_cutoff_ms']) == (START, END, CUT)
    assert sha(HERE/'raw/events.jsonl.gz') == manifest['events_sha256']
    for path, expected in manifest['sources'].items():
        assert sha(Path(path)) == expected, 'source changed: '+path
    for path, expected in read(HERE/'raw/fetch.json')['files'].items():
        assert sha(HERE/path) == expected, 'input changed: '+path
    for path, expected in read(HERE/'raw/confirmation.json')['files'].items():
        assert sha(HERE/path) == expected, 'confirmation changed: '+path


def analyze():
    verify_inputs()
    ee = events()
    market = read(HERE/'raw/market_start.json')['data']
    tokens = json.loads(market['clobTokenIds'])
    counts = Counter(e['k'] for e in ee)
    gaps = [e for e in ee if e['k']=='gap' and START*1000<=e['rcv']<=END*1000]
    samples = [(START+age)*1000 for age in range(0, 901)]
    snapshots, issues = m1.books_at(ee, tokens, samples)
    good, missing = [], Counter()
    for t, bb in snapshots.items():
        problems = []
        for b in bb:
            if not b['ready'] or not 0<=t-b['rcv']<=3000 or not 0<=t-b['obs']<=3000:
                problems.append('missing_or_stale_book')
            if b['BUY'] and b['SELL'] and max(b['BUY'])>=min(b['SELL']):
                problems.append('crossed_book')
        for side in (0, 1):
            if bb[side]['BUY'] != {m1.UNIT-p:q for p,q in bb[1-side]['SELL'].items()}:
                problems.append('complement_depth_mismatch')
        if problems:
            missing.update(set(problems))
        else:
            good.append(t)
    groups, failures, block = {}, [], {}
    for path in sorted((HERE/'raw/receipts').glob('*.json')):
        receipt = read(path)['data']
        try:
            groups[path.stem] = m1.matches(receipt)
            header = read(HERE/'raw/blocks'/f'{receipt["blockNumber"]}.json')['data']
            assert header['hash'] == receipt['blockHash']
            block[path.stem] = int(header['timestamp'], 16)*1000
        except (AssertionError, KeyError, ValueError, OSError) as exc:
            failures.append(dict(tx=path.stem, error=str(exc)))
    flows, flow_errors, metrics = m1.trade_flows(ee, groups, tokens)
    bad_flow_clocks = sum(f['min_delay']<0 or f['max_delay']>3000 or f['obs_lo']!=f['obs_hi'] for f in flows)
    # Duplicate feed messages collapse by exchange log; API equal rows retain multiplicity.
    assert len({(x['tx'],x['log_index']) for x in flows}) == len(flows)
    api_checks = {}
    for mode, filename in (('true_initial','trades_true.json'),
                           ('true_confirmed','trades_true_confirmation.json'),('false','trades_false.json')):
        rows = [x for page in read(HERE/'raw'/filename)['pages'] for x in page['rows']]
        api = aggregate_api(rows)
        chain = defaultdict(lambda:dict(qty=0, gross=0, rows=0))
        for tx, matches in groups.items():
            for match in matches:
                for f in [match['active']]+([] if mode.startswith('true') else match['makers']):
                    if f['token'] not in tokens:
                        continue
                    key = (tx,f['owner'],f['token'],'BUY' if f['side']==0 else 'SELL')
                    chain[key]['qty'] += f['qty']
                    chain[key]['gross'] += f['cash_cost']-f['fee'] if f['side']==0 else -f['cash_cost']+f['fee']
                    chain[key]['rows'] += 1
        diffs = []
        for key in sorted(api.keys()|chain.keys()):
            empty = dict(qty=0,gross=0,rows=0)
            a, c = api.get(key,empty), chain.get(key,empty)
            if a['qty']!=c['qty'] or abs(a['gross']-c['gross'])>D(2)*max(a['rows'],c['rows']):
                diffs.append(dict(key=key, api=dict(a), chain=dict(c)))
        api_checks[mode] = dict(rows=len(rows), groups=len(api), differences=diffs)
    messages = [e for e in ee if e['k']=='last_trade_price']
    segments = Counter('before_start' if int(e['p']['timestamp'])<START*1000 else
        'in_window' if int(e['p']['timestamp'])<END*1000 else 'after_end' for e in messages)
    receive_lag = [e['rcv']-int(e['p']['timestamp']) for e in messages]
    block_lag = [block[e['p']['transaction_hash']]-int(e['p']['timestamp'])
                 for e in messages if e['p']['transaction_hash'] in block]
    def distribution(values):
        return dict(n=len(values), min=min(values), median=statistics.median(values), max=max(values)) if values else None
    public_only = sorted(set(groups)-{e['p']['transaction_hash'] for e in messages})
    seen_flows = {(f['tx'], f['log_index']) for f in flows}
    unseen_matches = []
    for tx, matches in groups.items():
        for match in matches:
            if match['active']['token'] in tokens and not all((tx,f['log_index']) in seen_flows for f in match['makers']):
                unseen_matches.append(dict(tx=tx, log=match['match_log'], block_ms=block.get(tx),
                    in_window_by_block_clock=START*1000<=block.get(tx,0)<CUT))
    status = 'PASS_OBSERVED_FLOW_GATE'
    if (gaps or issues.get('future_source_clock') or issues.get('out_of_order_book')
        or len(good)<.95*len(samples) or flow_errors or failures or bad_flow_clocks
        or any(api_checks[k]['differences'] for k in ('true_confirmed','false'))
        or any(x['in_window_by_block_clock'] for x in unseen_matches)):
        status = 'MISSING_DATA'
    probes = quote_probes(ee,tokens,groups,flows) if status=='PASS_OBSERVED_FLOW_GATE' else dict(rows=[],status_counts={})
    save(HERE/'results/quote_probes.json',probes)
    save(HERE/'results/flows.json', flows)
    save(HERE/'results/api_reconciliation.json', api_checks)
    save(HERE/'results/book_samples.json', {str(t):bb for t,bb in snapshots.items()})
    result = dict(slug=SLUG, start=START, end=END, cutoff_ms=CUT, events=dict(counts),
        book_samples=len(samples), valid_book_samples=len(good), invalid_book_reasons=dict(missing),
        book_issues=issues, explicit_gaps=gaps, metrics=metrics, flow_errors=flow_errors,
        bad_flow_clocks=bad_flow_clocks,
        receipt_failures=failures, api_differences={k:len(x['differences']) for k,x in api_checks.items()},
        receive_minus_server_ms=distribution(receive_lag), block_minus_server_ms=distribution(block_lag),
        public_transactions_without_ws=public_only, data_gate=status,
        chain_matches_without_ws=unseen_matches,
        quote_probe_status=probes['status_counts'],
        trade_time_segments=dict(segments),
        economic_pnl=None, economic_status='ONE_MARKET_AND_UNCALIBRATED_EXECUTION',
        source_hashes={str(p):sha(p) for p in SOURCES+[Path(__file__)]},
        note='Observed public flow reconciliation is not order acceptance/cancel calibration or true queue position.')
    save(HERE/'results/report.json', result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_hashes','public_transactions_without_ws',
        'chain_matches_without_ws','explicit_gaps','receipt_failures')},default=str))
    protected()


def repeat():
    names = ('flows', 'api_reconciliation', 'book_samples', 'report', 'quote_probes', 'execution')
    hashes = []
    for _ in range(2):
        analyze()
        subprocess.run([sys.executable, '-B', str(HERE/'execution.py')], check=True, cwd=HERE)
        hashes.append({n:sha(HERE/'results'/f'{n}.json') for n in names})
    assert hashes[0] == hashes[1], 'offline outputs changed'
    subprocess.run([sys.executable, '-B', str(HERE/'check.py')], check=True, cwd=HERE)
    for p in HERE.glob('*.py'):
        compile(p.read_text(), str(p), 'exec')
    subprocess.run([sys.executable, '-m', 'ruff', 'check', '--no-cache', str(HERE)], check=True, cwd=HERE)
    save(HERE/'results/reproduction.json', dict(identical_runs=2, hashes=hashes[0],
         checks_sha256=sha(HERE/'results/checks.json'), syntax='PASS', ruff='PASS',
         sources={str(p):sha(p) for p in HERE.glob('*.py')}))


if __name__ == '__main__':
    action, = sys.argv[1:]
    {'freeze':freeze, 'fetch':fetch, 'confirm':confirm, 'analyze':analyze, 'repeat':repeat}[action]()
