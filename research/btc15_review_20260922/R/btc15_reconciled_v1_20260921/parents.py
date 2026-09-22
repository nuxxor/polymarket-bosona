"""Reuse cached receipts and actor-filtered decoder; preserve sample coverage."""
from collections import Counter, defaultdict
from decimal import Decimal as D
import json

from common import FABLE, R, S, INPUTS, module, read, roles, save

BASE = FABLE/'agents/D3_order_identity'
decoder = module('frozen_public_decoder', BASE/'code/decode_receipts.py')
ACTOR = '0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'


def main():
    scope = read(BASE/'raw/scope_activity.json')['activity']
    by = defaultdict(list)
    for row in scope:
        assert row['proxyWallet'].lower() == ACTOR and row['type'] == 'TRADE'
        by[row['transactionHash']].append(row)
    fills = read(R/'btc15_reconciled_v1_20260921/results/fills.json')
    fixed = defaultdict(list)
    for f in fills:
        fixed[(f['tx'], f['token'])].append(f)
    out, excluded, parent = [], Counter(), defaultdict(list)
    for tx, aa in sorted(by.items()):
        receipt = read(BASE/'raw/receipts'/f'{tx}.json')
        decoded = decoder.decode(receipt, ACTOR)
        assert len(decoded) == len(aa)
        unused = list(sorted(decoded, key=lambda x:x['log_index']))
        for a in aa:
            candidates = [x for x in unused if x['token'] == a['asset']
                          and abs(D(x['qty'])-D(str(a['size']))*1000000) <= 1
                          and abs(D(x['cash_cost'])-D(str(a['usdcSize']))*1000000) <= 1]
            assert candidates, 'API quantity/cash cannot be paired to receipt'
            d = candidates[0]
            unused.remove(d)
            path = R/'raw/markets'/f'{a["slug"]}.json'
            if path.exists():
                market = read(path)
            else:
                market = read(S/'raw/new_period_markets'/f'{a["slug"]}.json')['data']
            # Official metadata excludes the hourly contract in Fable's 34-market scope.
            import research
            meta = research.classify(market)
            if meta['group'] != 'btc_15m':
                excluded[meta['group']] += 1
                continue
            assert a['conditionId'] == market['conditionId']
            assert a['asset'] == json.loads(market['clobTokenIds'])[a['outcomeIndex']]
            fee_role = roles.role(float(a['price']), float(a['usdcSize'])/float(a['size']),
                                  float(a['size']), market['feeSchedule']['rate'])
            assert fee_role == d['role']
            linked = [x for x in fixed[(tx, a['asset'])]
                      if abs(D(x['qty'])-D(str(a['size']))) < D('.000001')]
            item = dict(slug=a['slug'], condition=a['conditionId'], token=a['asset'],
                exchange=decoder.EXCHANGE, tx=tx, log_index=d['log_index'],
                order_hash=d['order_hash'], role=d['role'], qty=a['size'], cash=a['usdcSize'],
                block_number=int(receipt['blockNumber'], 16),
                transaction_index=int(receipt['transactionIndex'], 16),
                block_second=a['timestamp'], S=meta['S'], age=a['timestamp']-meta['S'],
                matched_ms=None, first_submit_ms=None,
                corrected_historical_phase=linked[0]['phase'] if len(linked) == 1 else None,
                phase_link_ambiguous=len(linked) > 1)
            out.append(item)
            parent[(decoder.EXCHANGE, a['conditionId'], d['order_hash'])].append(item)
        assert not unused
    parents = []
    for identity, rows in sorted(parent.items()):
        rows.sort(key=lambda x:(x['block_number'], x['transaction_index'], x['log_index']))
        parents.append(dict(exchange=identity[0], condition=identity[1], order_hash=identity[2],
            slug=rows[0]['slug'], observed_fills=len(rows), roles=sorted({x['role'] for x in rows}),
            first_age=rows[0]['age'], last_age=rows[-1]['age'],
            public_fill_span=rows[-1]['block_second']-rows[0]['block_second'],
            qty=sum(D(str(x['qty'])) for x in rows),
            note='Observed sample only; no claim that first fill equals order submission.'))
    represented = Counter(x['slug'] for x in out)
    historical = Counter(x['slug'] for x in fills if x['group'] == 'btc_15m')
    coverage = {slug:dict(decoded=n, historical_total=historical.get(slug),
                         historical_complete=(n == historical[slug]) if slug in historical else None)
                for slug,n in sorted(represented.items())}
    summary = dict(source_rows=len(scope), btc15_rows=len(out), markets=len(represented),
        excluded_other_official_groups=dict(excluded), roles=dict(Counter(x['role'] for x in out)),
        parents=len(parents), matched_clock_available=0,
        first_submit_clock_available=0, historical_complete=sum(
            x['historical_complete'] is True for x in coverage.values()),
        note='Selected diagnostic cohort, not population maker/parent frequency estimate.')
    save('results/parent_fills.json', out)
    save('results/parents.json', dict(summary=summary, parents=parents, coverage=coverage))
    save('results/parent_inputs.json', INPUTS)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
