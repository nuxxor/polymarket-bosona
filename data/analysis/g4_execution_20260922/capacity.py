"""First actual order enabled by cap10, from the frozen first-six-window ledger."""
from collections import defaultdict
from decimal import Decimal as D
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def allowed(net_own, reserve, cap):
    target = min(5, -net_own) if net_own < -1e-6 else min(5, max(0, cap-net_own))
    return max(0, target-reserve)


def main():
    rows = [json.loads(line) for line in gzip.open(HERE/'capture.jsonl.gz', 'rt')]
    state = next(r['row'] for r in rows if r['kind'] == 'state')
    orders = {o['oid']: dict(o, S=int(k.split('|')[1])) for k, w in state['windows'].items()
              for o in w['emir'] if o.get('oid')}
    sdk = [r['row'] for r in rows if r['kind'] == 'sdk']
    requests = {r['attempt']: r for r in sdk if r['event'] == 'request'}
    response = {r['attempt']: r for r in sdk if r['event'] == 'response' and r['op'] == 'post_batch'}
    tokens = {}
    for r in response.values():
        for slot, item in zip(requests[r['attempt']]['meta']['orders'], r['reply']['items'], strict=True):
            if item.get('oid') in orders:
                tokens[slot['token']] = orders[item['oid']]['S']
    paid, pending, attempts = defaultdict(float), {}, {}
    inventory_checks = interval_checks = 0
    bounds, opportunities = [], []
    selected = set()
    for r in sdk:
        event = r['event']
        if event == 'fill_observed' and r['oid'] in orders:
            paid[r['oid']] = max(paid[r['oid']], r['total'])
        if event == 'g4_cancel_result' and r['confirmed']:
            pending.pop(r['oid'], None)
        if event == 'response' and r['op'] == 'get_order':
            if r['reply'].get('status') in ('CANCELED', 'MATCHED'):
                pending.pop(r['reply']['oid'], None)
        if event == 'g4_quote':
            S = r['S']
            if str('btc|'+str(S)) not in state['windows']:
                continue
            q = [sum(v for oid, v in paid.items() if orders[oid]['S'] == S and orders[oid]['oi'] == i) for i in (0, 1)]
            assert all(abs(a-b) < 1e-6 for a, b in zip(q, r['inventory'])), (r['seq'], q, r['inventory'])
            inventory_checks += 1
            reserve = [sum(max(0, p['boy']-p['pay']) for p in r['pending'] if p['oi'] == i) for i in (0, 1)]
            low, high = q[0]-q[1]-reserve[1], q[0]-q[1]+reserve[0]
            bounds.append((low, high))
            assert low >= -10-1e-6 and high <= 10+1e-6, (r['seq'], low, high)
            interval_checks += 1
            # Authoritative in-process pending snapshot, excluding fully filled remainders.
            pending = {oid: p for oid, p in pending.items() if p['S'] != S}
            pending.update({p['oid']: dict(p, S=S) for p in r['pending'] if p['oid']})
        if event == 'request' and r['op'] == 'post_batch':
            for i, slot in enumerate(r['meta']['orders']):
                S = tokens.get(slot['token'])
                if S is None:
                    continue
                q = [sum(v for oid, v in paid.items() if orders[oid]['S'] == S and orders[oid]['oi'] == oi) for oi in (0, 1)]
                side = slot['oi']
                net = q[side]-q[1-side]
                reserve = sum(max(0, p['boy']-paid[p['oid']]) for p in pending.values()
                              if p['S'] == S and p['oi'] == side and p['oid'] in orders)
                size5, size10 = allowed(net, reserve, 5), allowed(net, reserve, 10)
                assert slot['size'] <= size10+1e-6, (r['seq'], slot, q, reserve)
                if net > 1e-6 and slot['size'] > size5+1e-6 and S not in selected:
                    reply = response.get(r['attempt'])
                    item = reply['reply']['items'][i] if reply else {}
                    oid = item.get('oid')
                    opportunities.append(dict(S=S, oi=side, oid=oid, attempt=r['attempt'],
                        seq=r['seq'], post_ms=r['utc_ns']/1e6, q_before=q, same_reserve=reserve,
                        cap5_size=size5, cap10_size=size10, size=slot['size'], price=slot['price'],
                        accepted=oid in orders))
                    selected.add(S)
                attempts[(r['attempt'], i)] = dict(S=S, oi=side, boy=slot['size'])
        if event == 'response' and r['op'] == 'post_batch':
            for i, item in enumerate(r['reply']['items']):
                oid = item.get('oid')
                if oid in orders:
                    pending[oid] = dict(attempts[(r['attempt'], i)], oid=oid)
    source = json.loads((HERE/'results.json').read_text())
    fills = source['rows']
    for p in opportunities:
        own = [f for f in fills if f['oid'] == p['oid']]
        w = state['windows']['btc|'+str(p['S'])]
        # The later handoff supplies final outcome only, never the decision state.
        outcome = w.get('kazanan')
        if outcome is None:
            handoff = json.loads((HERE/'runtime_handoff.json').read_text())
            matches = [e for e in handoff['windows'] if e.get('S') == p['S'] and e.get('resolved')]
            outcome = matches[-1]['winner'] if matches else None
        p.update(fills=len(own), filled_qty=sum(f['q'] for f in own), winner=outcome,
                 delta=sum(float(D(str(f['q']))*(D(int(f['oi'] == outcome))-D(str(f['price'])))) for f in own)
                 if outcome is not None else None,
                 actual_fills=own, executable_sell_after={'1': None, '5': None})
    result = dict(status='LOCAL_CONTRIBUTION_NOT_POLICY_PNL', assigned=6,
                  known_inventory_checks=inventory_checks, reachable_interval_checks=interval_checks,
                  min_reachable=min(a for a, b in bounds), max_reachable=max(b for a, b in bounds),
                  opportunities=opportunities, total_delta=sum(p['delta'] for p in opportunities if p['delta'] is not None),
                  days=1, economic_conclusion='INCONCLUSIVE_ONE_DAY',
                  quote_generation_intent='unknown; distinct order ID does not prove distinct economic decision')
    (HERE/'capacity_results.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps({**{k: v for k, v in result.items() if k != 'opportunities'},
                      'opportunities': [{k: v for k, v in p.items() if k != 'actual_fills'} for p in opportunities]}, indent=2))


if __name__ == '__main__':
    main()
