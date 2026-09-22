"""First G1 pilot: exact terminal economics and two private-stream fill reconciliations."""
from collections import Counter, defaultdict
from decimal import Decimal as D
from hashlib import sha256
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
FINAL = HERE.parents[2]/'g/validation/final_20260922'


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    result = json.loads((FINAL/'complete/result.json').read_text())
    state = json.loads((FINAL/'complete/reconciled_state.json').read_text())
    orders, windows = {}, []
    for item in result['windows']:
        w = state['pen'][item['key']]
        quantity, cash = [D(0), D(0)], D(0)
        for order in w['emir']:
            q = D(str(order.get('pay', 0)))
            quantity[order['oi']] += q
            cash += q*D(str(order['p']))+D(str(order.get('ucret', 0)))
            if order.get('oid'):
                assert order['oid'] not in orders
                orders[order['oid']] = order
        floor = min(quantity)-cash
        pnl = quantity[w['kazanan']]-cash
        assert abs(pnl-D(str(item['pnl']))) < D('.000001')
        windows.append(dict(key=item['key'], winner=w['kazanan'], quantity=quantity, cash=cash,
                            pnl=pnl, final_inventory_floor=floor, payout_above_floor=pnl-floor))
    streams, ledgers, receipts = {}, {}, {}
    for lane in ('A', 'B'):
        events = rows(HERE/f'{lane}_private.jsonl')
        trades, timing, statuses = {}, {}, Counter()
        for e in events:
            m = e.get('payload', {})
            if m.get('event_type') != 'trade':
                continue
            statuses[m['status']] += 1
            own = defaultdict(lambda: D(0))
            for maker in m['maker_orders']:
                oid = maker['order_id']
                if oid in orders:
                    assert m['trader_side'] == 'MAKER'
                    # Two observed partial-fill prices differ from the limit by less than $0.000001/share.
                    assert abs(D(maker['price'])-D(str(orders[oid]['p']))) < D('.000001')
                    own[oid] += D(maker['matched_amount'])
            assert own, 'Unattributed account trade'
            for oid, q in own.items():
                key = (m['id'], oid)
                assert key not in trades or trades[key] == q
                trades[key] = q
                if m['status'] == 'MATCHED':
                    timing[key] = min(timing.get(key, e['received']['mono_ns']), e['received']['mono_ns'])
        quantities = {oid: D(0) for oid in orders}
        for (_, oid), q in trades.items():
            quantities[oid] += q
        assert all(abs(quantities[oid]-D(str(o.get('pay', 0)))) < D('.000001') for oid, o in orders.items())
        streams[lane] = dict(unique_trade_parent_pairs=len(trades),
                             filled_parents=sum(q > 0 for q in quantities.values()),
                             all_accepted_parents_reconciled=len(orders), statuses=statuses,
                             rejected_messages=sum(e['event'] == 'rejected' for e in events),
                             total_shares=sum(quantities.values()))
        ledgers[lane], receipts[lane] = trades, timing
    assert ledgers['A'] == ledgers['B']
    telemetry = rows(FINAL/'original/LOG_g_emir_iz.jsonl')
    requests = {e['attempt']: e for e in telemetry if e['event'] == 'request'}
    post_ms = []
    for e in telemetry:
        if e['event'] == 'response' and e['op'] == 'post_batch':
            assert requests[e['attempt']]['meta']['post_only'] is True
            if any(x.get('success') for x in e.get('reply', {}).get('items', [])):
                post_ms.append(e['duration_ns']/1e6)
    private_times = defaultdict(list)
    for key, q in ledgers['A'].items():
        private_times[key[1]].append((min(receipts[lane][key] for lane in ('A', 'B')), q))
    observed_lag = []
    for e in telemetry:
        if e['event'] != 'fill_observed':
            continue
        cumulative = D(0)
        for observed_ns, q in sorted(private_times[e['oid']]):
            cumulative += q
            if cumulative+D('.000001') >= D(str(e['total'])):
                observed_lag.append((e['mono_ns']-observed_ns)/1e6)
                break
        else:
            raise AssertionError('Local fill not supported by private trades')
    total = {k: sum(w[k] for w in windows) for k in ('cash', 'pnl', 'final_inventory_floor', 'payout_above_floor')}
    assert total['pnl'] == total['final_inventory_floor']+total['payout_above_floor']
    assert abs(total['pnl']-D(str(result['settled_pilot_pnl']))) < D('.000001')
    report = dict(windows=windows, totals=total, streams=streams,
                  accepted_parent_count=len(orders), filled_parent_count=sum(o.get('pay', 0)>0 for o in orders.values()),
                  sdk_fill_observations=len(observed_lag), successful_post_median_ms=median(post_ms),
                  polling_vs_first_private_receipt_ms=dict(median=median(observed_lag), min=min(observed_lag), max=max(observed_lag)),
                  limitations=['Fixed final inventory payoff floor is not a counterfactual trading policy or FIFO attribution.',
                               'Private order-hash matches establish maker fills, not queue priority or Bosona policy equality.',
                               'Six rejected messages per recorder remain unidentified; event completeness is not established.',
                               'Six markets, five Up outcomes; no durable profitability inference.'],
                  sources={str(p): sha256(p.read_bytes()).hexdigest() for p in
                           [FINAL/'complete/result.json', FINAL/'complete/reconciled_state.json',
                            FINAL/'original/LOG_g_emir_iz.jsonl', HERE/'A_private.jsonl', HERE/'B_private.jsonl']})
    (HERE/'analysis.json').write_text(json.dumps(report, default=str, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('sources', 'windows', 'limitations')}, default=str))


if __name__ == '__main__':
    main()
