"""Offline G2-source audit and matched-window G1/Bosona reconstruction.

Run with python -B; no network or credential access, writes only beside this file.
"""
from collections import defaultdict
from decimal import Decimal as D
from hashlib import sha256
import json
from pathlib import Path
from statistics import median
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RECENT = ROOT / 'data/analysis/g1_comparison_20260922'
BOT = ROOT / 'lanes/g_continuous/identity_fix/bot'


def read(path):
    return json.loads(path.read_text())


def block(event, args):
    if event in ('socket.connect', 'socket.bind'):
        raise RuntimeError('offline audit attempted network access')
    if event == 'open' and isinstance(args[0], (str, bytes)):
        name = str(args[0]).lower()
        if '.env' in name or name.endswith(('.session', '.pem', '.key')):
            raise RuntimeError('credential access prohibited')


sys.addaudithook(block)
sys.dont_write_bytecode = True
sys.path.insert(0, str(RECENT))
import study  # noqa: E402


def metrics(rows, market, start, ledger, execution):
    tokens = json.loads(market['clobTokenIds'])
    buys = [r for r in rows if r['type'] == 'TRADE' and r['side'] == 'BUY']
    assert all(r['timestamp'] >= start for r in buys), 'unexpected pre-window inventory'
    qty = sum(D(str(r['size'])) for r in buys)
    cash = sum(D(str(r['usdcSize'])) for r in buys)
    winner = ledger['winner']
    bought = [sum(D(str(r['size'])) for r in buys if r['asset'] == token) for token in tokens]
    pnl = None if winner is None else bought[winner] - cash
    # Independent direct BUY payout agrees with transfer-aware ledger on this cohort.
    assert not any(r['type'] == 'TRADE' and r['side'] == 'SELL' for r in rows)
    assert pnl is None or abs(pnl - ledger['pnl']) < D('.00005')
    peak, area, net, at = D(0), D(0), D(0), 0
    changes = defaultdict(lambda: [D(0), D(0)])
    for r in buys:
        changes[int(r['timestamp']) - start][tokens.index(r['asset'])] += D(str(r['size']))
    crosses = opens = reopens = mixed = 0
    first_time = min(changes, default=None)
    first_price = None
    if first_time is not None:
        first = [r for r in buys if r['timestamp'] == start + first_time]
        first_price = sum(D(str(r['usdcSize'])) for r in first) / sum(D(str(r['size'])) for r in first)
    for age, amounts in sorted(changes.items()):
        if age >= 300:
            continue
        area += abs(net) * (age - at)
        after = net + amounts[0] - amounts[1]
        if all(amounts):
            mixed += 1
        if net * after < 0:
            crosses += 1  # Endpoint crossing, not necessarily one order/decision.
        if net == 0 and after != 0:
            opens += 1
            reopens += int(opens > 1)
        net, at = after, age
        peak = max(peak, abs(net))
    area += abs(net) * (300 - at)
    assert execution['complete']
    parents = defaultdict(list)
    for fill in execution['rows']:
        parents[fill['order_hash']].append(fill)
    late_new = late_cont = 0
    for group in parents.values():
        times = [t - start for f in group for t in f['public_seconds']]
        late_new += int(min(times) >= 240)
        late_cont += int(min(times) < 240 <= max(times))
    return dict(buy_records=len(buys), bought_shares=qty, cash=cash, pnl=pnl,
                first_age=first_time, first_cash_price=first_price,
                first_sides=ledger['first_sides'], filled_parents=len(parents),
                parent_median_shares=median(execution['parent_shares']) if parents else None,
                taker_shares=execution['taker_shares'], maker_shares=execution['maker_shares'],
                peak_abs_net=peak, final_net=net, open_share_seconds=area,
                normalized_5shares_pnl=None if pnl is None or qty == 0 else pnl * 5 / qty,
                normalized_5shares_floor=None if qty == 0 else (min(bought) - cash) * 5 / qty,
                normalized_5shares_abs_net=None if qty == 0 else abs(net) * 5 / qty,
                normalized_5shares_exposure_seconds=None if qty == 0 else area * 5 / qty,
                crossings=crosses, exact_flat_reopens=reopens, mixed_seconds=mixed,
                late_first_filled_parents=late_new, late_continuing_parents=late_cont)


def aggregate(records):
    result = {}
    for actor in ('G', 'Bosona'):
        vals = [r['actors'][actor] for r in records]
        traded = [v for v in vals if v['bought_shares'] > 0]
        result[actor] = dict(windows=len(vals), traded_windows=len(traded),
                            records=sum(v['buy_records'] for v in vals),
                            shares=sum(v['bought_shares'] for v in vals),
                            filled_parents=sum(v['filled_parents'] for v in vals),
                            taker_shares=sum(v['taker_shares'] for v in vals),
                            first_age_median=median(v['first_age'] for v in traded),
                            first_cash_price_median=median(v['first_cash_price'] for v in traded),
                            raw_pnl=sum(v['pnl'] for v in vals),
                            normalized_5shares_sum=sum(v['normalized_5shares_pnl'] for v in traded),
                            normalized_exposure_seconds_median=median(v['normalized_5shares_exposure_seconds'] for v in traded),
                            late_first_filled_parents=sum(v['late_first_filled_parents'] for v in vals),
                            late_continuing_parents=sum(v['late_continuing_parents'] for v in vals),
                            crossings=sum(v['crossings'] for v in vals),
                            exact_flat_reopens=sum(v['exact_flat_reopens'] for v in vals))
    comparable = [r for r in records if all(len(r['actors'][a]['first_sides']) == 1 for a in ('G', 'Bosona'))]
    result['first_side_comparison'] = dict(n=len(comparable), same=sum(r['actors']['G']['first_sides'] == r['actors']['Bosona']['first_sides'] for r in comparable))
    return result


def maintenance_check():
    sys.path.insert(0, str(HERE / 'test_bot'))
    import test_g
    b = test_g.load()
    calls = []
    b.log = lambda *args, **kwargs: None
    b.state_kaydet = lambda: None
    b.iptal_toplu = lambda ids: calls.append(ids) or {oid: (True, 'test') for oid in ids}
    b.dolum_oku = lambda oid: (2, 'CANCELED')
    sample = dict(emir=[test_g.order(0, .4, 2, 'acik', 'partial')], klip=5)
    import copy
    with patch.object(b.time, 'time', return_value=1179):
        b.denge_koru(('btc', 1000), copy.deepcopy(sample))
    assert not calls
    with patch.object(b.time, 'time', return_value=1180):
        b.denge_koru(('btc', 1000), copy.deepcopy(sample))
    assert calls == [['partial']]
    closed = dict(emir=[test_g.order(0, .4, 2, 'kapali', 'partial')], klip=5)
    capacity = [b.d_miktar(closed, oi) for oi in (0, 1)]
    assert capacity == [3, 2] and all(q < b.MIN_EMIR for q in capacity)
    return dict(at179='kept', at180='canceled', partial_held_shares=2,
                after_cancel_capacity_up_down=capacity,
                after_cancel_both_sides_below_minimum=True,
                scope='actual inherited denge_koru; mocked exchange IO, not new live occurrence')


def main():
    manifest = read(BOT / 'G_RELEASE.json')
    assert all(sha256((BOT / p).read_bytes()).hexdigest() == digest for p, digest in manifest.items())
    latest = read(RECENT / 'latest.json')
    cut = RECENT / 'cuts' / Path(latest['cut']).name
    wallets = read(RECENT / 'protocol.json')['wallets']
    records = []
    for record in latest['rows']:
        start = record['S']
        market = read(cut / f'{start}_market.json')
        out = dict(S=start, cohort=record['cohort'], assigned=record['actors']['G']['assigned_by_bot'], actors={})
        for actor in ('G', 'Bosona'):
            raw = read(cut / f'{start}_{actor}.json')
            assert raw['complete']
            ledger = study.ledger(raw['rows'], market, start)
            actual = json.loads(json.dumps(ledger, default=str))
            assert actual == {k: record['actors'][actor][k] for k in ledger}
            execution = study.roles(raw['rows'], market, wallets[actor], limit=0)
            assert json.loads(json.dumps(execution, default=str)) == record['actors'][actor]['execution']
            out['actors'][actor] = metrics(raw['rows'], market, start, ledger, execution)
        records.append(out)
    resolved = [r for r in records if all(r['actors'][a]['pnl'] is not None for a in ('G', 'Bosona'))]
    paired = [r for r in resolved if all(r['actors'][a]['bought_shares'] for a in ('G', 'Bosona'))]
    pilot = [r for r in resolved if r['S'] <= 1790070900]
    final = ROOT / 'lanes/g/validation/final_20260922/complete'
    summary = read(final / 'result.json')
    state = read(final / 'reconciled_state.json')
    pnls, floors = [], []
    for row in summary['windows']:
        w = state['pen'][row['key']]
        q = [sum(D(str(o['pay'])) for o in w['emir'] if o['oi'] == oi) for oi in (0, 1)]
        cash = sum(D(str(o['pay'])) * D(str(o['p'])) + D(str(o.get('ucret', 0))) for o in w['emir'])
        pnls.append(q[w['kazanan']] - cash)
        floors.append(min(q) - cash)
    assert abs(sum(pnls) - D(str(summary['settled_pilot_pnl']))) < D('.000001')
    report = dict(source_ab_sha=manifest['ab.py'], policy_sha=manifest['g_policy.py'],
                  source_manifest_all_verified=len(manifest), snapshot_collection_start_s=int(cut.name),
                  analysis_asof_ms=latest['as_of_ms'], local_cut_names=sorted(p.name for p in (RECENT / 'cuts').iterdir()),
                  records=records, resolved_all=aggregate(resolved), resolved_both_traded=aggregate(paired),
                  pilot=aggregate(pilot), inherited_maintenance=maintenance_check(),
                  pilot_local_ledger=dict(pnl=sum(pnls), final_floor_sum=sum(floors), payout_above_floor=sum(pnls)-sum(floors)),
                  caveats=['Recent economic data predate the 12:07:30 UTC G2 start.',
                           'Same public-second crossing can combine multiple parents; it is not one reversing decision.',
                           '5-total-bought-share normalization is descriptive, not a feasible same-risk strategy replay.',
                           '11:00 gate anomaly and 11:05 skipped assignment are infrastructure, not policy choices.',
                           'Partial 11:10 market has pending settlement and is excluded from resolved metrics.'])
    paths = [BOT / name for name in manifest] + [RECENT / 'latest.json', RECENT / 'study.py', RECENT / 'identity.py', RECENT / 'protocol.json']
    paths += list(cut.glob('*.json')) + list((RECENT / 'receipts').glob('*.json'))
    report['input_sha256'] = {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    (HERE / 'results.json').write_text(json.dumps(report, indent=2, default=str) + '\n')
    print(json.dumps({k: report[k] for k in ('resolved_all', 'resolved_both_traded', 'pilot', 'pilot_local_ledger', 'inherited_maintenance')}, indent=2, default=str))


if __name__ == '__main__':
    main()
