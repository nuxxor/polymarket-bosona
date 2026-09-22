"""Read-only audit of the frozen M4v2 end snapshot; no account access."""
import json
from collections import Counter
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT / name).read_text())


def lines(name):
    return [json.loads(s) for s in (ROOT / name).read_text().splitlines()]


trace = lines('LOG_f_emir_iz.jsonl')
logs = lines('LOG_f.jsonl')
account = lines('account.jsonl')
runtime = read('runtime.json')
assert not runtime['pids'] and account[0]['open_orders'] == 0
assert logs[-1]['k'] == 'bitti' and logs[-1]['sebep'] == 'sure'
assert trace[-1]['event'] == 'session_end'
assert [r['seq'] for r in trace] == list(range(1, len(trace) + 1))
requests = Counter(r['attempt'] for r in trace if r['event'] == 'request')
responses = [r for r in trace if r['event'] == 'response']
assert requests == Counter(r['attempt'] for r in responses)
assert all(v == 1 for v in requests.values())
assert all(r['errors'] == 0 and r['event'] != 'exception' for r in trace)
accepted = {v['oid'] for r in responses if r['op'] == 'post_batch'
            for v in r['reply']['items'] if v.get('oid')}
orders = [o for w in read('STATE_f.json')['pen'].values()
          for o in w['emir'] if o.get('oid') in accepted]
assert len(orders) == len(accepted) == 12
assert all(o['durum'] == 'kapali' for o in orders)
assert Counter(o['borsa_durum'] for o in orders) == {'MATCHED': 4, 'CANCELED': 8}
fills = [r for r in logs if r['k'] == 'dolum']
assert len(fills) == 4 and sum(r['yeni'] for r in fills) == 20
pairs = []
for start in sorted({r['S'] for r in fills}):
    part = [r for r in fills if r['S'] == start]
    q = [sum(r['yeni'] for r in part if r['oi'] == side) for side in (0, 1)]
    assert q == [5, 5]
    cost = sum(r['p'] * r['yeni'] for r in part)
    assert abs(cost - 4.9) < 1e-8
    pairs.append({'start': start, 'up': q[0], 'down': q[1], 'cost': cost,
                  'terminal_pnl_before_other_costs': min(q) - cost})
assert abs(account[-1]['local'] - account[-1]['public']) < 0.0002
assert abs(account[-1]['new_local'] - 0.1) < 0.0002
summary = dict(stopped=True, stop_reason='sure', open_orders=0, accepted=12,
               filled_orders=4, filled_shares=20, pairs=pairs,
               settled_delta=account[-1]['new_local'], pending_windows=account[-1]['pending'],
               telemetry_requests=len(requests), websocket_errors=sum(r['k'] == 'taze_ws_hata' for r in logs),
               sdk_median_ms={op: median(r['duration_ns'] / 1e6 for r in responses if r['op'] == op)
                              for op in ('post_batch', 'cancel', 'get_order')})
(ROOT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary))
