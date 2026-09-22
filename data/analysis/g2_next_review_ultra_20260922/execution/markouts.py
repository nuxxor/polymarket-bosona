"""Own-fill receipt-clock markouts from existing 1 Hz G_KARAR quotes; no new data."""
from collections import defaultdict
from decimal import Decimal as D
from hashlib import sha256
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FINAL = ROOT / 'lanes/g/validation/final_20260922'
PRIVATE = ROOT / 'lanes/g_continuous/validation/g1_first_pilot'


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    state = json.loads((FINAL / 'complete/reconciled_state.json').read_text())
    windows = json.loads((FINAL / 'complete/result.json').read_text())['windows']
    orders = {}
    for item in windows:
        start = int(item['key'].split('|')[1])
        for order in state['pen'][item['key']]['emir']:
            if order.get('oid'):
                orders[order['oid']] = (start, order)
    quotes = defaultdict(list)
    for e in rows(FINAL / 'original/LOG_g.jsonl'):
        if e['k'] == 'G_KARAR':
            quotes[(e['S'], e['oi'])].append(e)
    fills = {}
    for lane in ('A', 'B'):
        for e in rows(PRIVATE / f'{lane}_private.jsonl'):
            p = e.get('payload', {})
            if p.get('event_type') != 'trade' or p['status'] != 'MATCHED':
                continue
            for maker in p['maker_orders']:
                oid = maker['order_id']
                if oid not in orders:
                    continue
                assert p['trader_side'] == 'MAKER'
                key = (p['id'], oid)
                value = dict(S=orders[oid][0], oi=orders[oid][1]['oi'], oid=oid,
                             trade=p['id'], q=D(maker['matched_amount']), price=D(maker['price']),
                             first_received_ns=e['received']['utc_ns'],
                             reported_match_second=int(p['match_time']))
                if key in fills:
                    old = fills[key]
                    assert (old['q'], old['price']) == (value['q'], value['price'])
                    value['first_received_ns'] = min(old['first_received_ns'], value['first_received_ns'])
                fills[key] = value
    assert len(fills) == 40
    for oid, (_, order) in orders.items():
        assert abs(sum(v['q'] for v in fills.values() if v['oid'] == oid) - D(str(order['pay']))) < D('.000001')

    def quote_at(fill, horizon):
        target = fill['first_received_ns'] / 1e6 + horizon * 1000
        if target >= (fill['S'] + 300) * 1000:
            return None
        eligible = [q for q in quotes[(fill['S'], fill['oi'])] if q['karar_ms'] <= target]
        if not eligible:
            return None
        q = eligible[-1]
        # Latest logged decision must itself be recent, and contain a usable book.
        if not (0 <= target - q['karar_ms'] <= 1500 and 0 <= q['defter_yasi'] <= 3
                and q['bb'] is not None and q['ba'] is not None and 0 < q['bb'] < q['ba'] <= 1):
            return None
        source_age_ms = target - q['karar_ms'] + q['defter_yasi'] * 1000
        if source_age_ms > 3000:
            return None
        return dict(quote_decision_ms=q['karar_ms'], distance_to_target_ms=target-q['karar_ms'],
                    source_age_ms=source_age_ms, mid=(D(str(q['bb']))+D(str(q['ba'])))/2,
                    bid=D(str(q['bb'])), ask=D(str(q['ba'])))

    output = []
    for fill in fills.values():
        before = quote_at(fill, -.001)
        item = dict(fill, before_receipt=before, horizons={})
        for horizon in (5, 10, 30):
            after = quote_at(fill, horizon)
            item['horizons'][horizon] = None if after is None else dict(
                after, mid_minus_paid=after['mid']-fill['price'],
                bid_minus_paid=after['bid']-fill['price'],
                mid_change_from_before_receipt=None if before is None else after['mid']-before['mid'])
        output.append(item)
    summary = {}
    for horizon in (5, 10, 30):
        known = [r for r in output if r['horizons'][horizon] is not None]
        paired = [r for r in known if r['before_receipt'] is not None]
        quantity = sum(r['q'] for r in known)
        paired_quantity = sum(r['q'] for r in paired)
        summary[horizon] = dict(fills=len(known), parents=len({r['oid'] for r in known}),
                                shares=quantity,
                                share_weighted_mid_minus_paid=sum(r['q']*r['horizons'][horizon]['mid_minus_paid'] for r in known)/quantity,
                                share_weighted_bid_minus_paid=sum(r['q']*r['horizons'][horizon]['bid_minus_paid'] for r in known)/quantity,
                                pre_and_post_fills=len(paired),
                                pre_and_post_shares=paired_quantity,
                                share_weighted_mid_change_from_before_receipt=sum(r['q']*r['horizons'][horizon]['mid_change_from_before_receipt'] for r in paired)/paired_quantity,
                                negative_mid_vs_paid_shares=sum(r['q'] for r in known if r['horizons'][horizon]['mid_minus_paid'] < 0),
                                quote_target_gap_median_ms=median(r['horizons'][horizon]['distance_to_target_ms'] for r in known))
    by_window = {start: {horizon: sum(r['q']*r['horizons'][horizon]['mid_minus_paid']
                                    for r in output if r['S'] == start and r['horizons'][horizon] is not None)
                         for horizon in (5, 10, 30)} for start in sorted({r['S'] for r in output})}
    result = dict(summary=summary, rows=output, window_markout_dollars=by_window,
                  accepted_parents=len(orders), quote_rows=sum(map(len, quotes.values())),
                  total_fill_parent_pairs=len(fills),
                  clock='Earliest A/B received MATCHED trade UTC ns; not exact execution clock. Quote data logged at approximately 1 Hz.',
                  limitations=['before_receipt may already be after execution; not a causal pre-execution markout.',
                               'Latest decision quote <= target; log age <=1.5s and source age <=3s; missing/stale cases excluded explicitly.',
                               'Mid is a diagnostic, bid lacks depth and taker fees, neither is guaranteed liquidation value.',
                               'All observations first G1 six-market pilot; no matched Bosona clock or G2 economic test.',
                               'Negative markouts support execution-quality concern but do not identify optimal cancel/exit policy.'],
                  input_sha256={str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in (
                      FINAL/'complete/reconciled_state.json', FINAL/'complete/result.json', FINAL/'original/LOG_g.jsonl',
                      PRIVATE/'A_private.jsonl', PRIVATE/'B_private.jsonl')})
    (HERE/'markouts.json').write_text(json.dumps(result, default=str, indent=2)+'\n')
    print(json.dumps(summary, default=str, indent=2))


if __name__ == '__main__':
    main()
