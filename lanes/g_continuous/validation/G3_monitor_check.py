"""Recheck the frozen monitoring capture; no network or trading actions."""
from collections import Counter
import gzip
from hashlib import sha256
import json
import math
from pathlib import Path

root = Path(__file__).resolve().parent
capture = root / 'G3_monitor_session_20260922.jsonl.gz'
with gzip.open(capture, 'rt') as stream:
    rows = [json.loads(line) for line in stream]
assert rows[0]['kind'] == 'capture_start' and rows[-1]['kind'] == 'capture_end'
meta = rows[0]
assert meta['hashes']['ab.py'] == 'f1f175671b6f2268f7359732b0e4fd8dfa392cc5262b13406e5fa6af64242a70'
assert meta['hashes']['BUDGET_G.json'] == '16c6ad83210baabde2f272939202e995ca682cd62e168fba435311b7b4402162'
sdk = [x['row'] for x in rows if x['kind'] == 'sdk']
bot = [x['row'] for x in rows if x['kind'] == 'bot']
state = next(x for x in rows if x['kind'] == 'state')
assign = {e['S']: e['arm'] for e in bot if e['k'] == 'G3_ATAMA'}
assert len(assign) == len([e for e in bot if e['k'] == 'G3_ATAMA']) == 7
quotes = [e for e in sdk if e['event'] == 'g3_quote']
for e in quotes:
    arm = 'G3' if sha256(('ULTRA-Q1|' + str(e['S'])).encode()).digest()[0] & 1 else 'G2'
    assert e['arm'] == assign[e['S']] == arm
    assert e['book']['mono_ns'] <= e['decision']['mono_ns'] <= e['mono_ns']
    assert not e['flags']['buffer_cancel'] or (
        arm == 'G3' and e['flags']['buffer_signal']
        and e['inventory'][e['oi']] >= e['inventory'][1-e['oi']] - 1e-6)
assert not any(e['errors'] for e in sdk)
assert sdk[0]['event'] == 'session_start'
assert [e['seq'] for e in sdk] == list(range(1, len(sdk) + 1))
windows = []
for key, window in state['windows'].items():
    start = int(key.split('|')[1])
    qty = [math.fsum(o.get('pay', 0) for o in window['emir'] if o['oi'] == i) for i in (0, 1)]
    cost = math.fsum(o.get('pay', 0)*o['p'] + o.get('ucret', 0) for o in window['emir'])
    pnl = window.get('hesap', {}).get('pnl')
    if window['cozuldu']:
        assert abs(qty[window['kazanan']] - cost - pnl) < 1e-7
    windows.append(dict(S=start, arm=assign[start], resolved=window['cozuldu'], qty=qty,
                        cost=cost, pnl=pnl, payoff_bounds=[min(qty)-cost, max(qty)-cost],
                        accepted=sum(bool(o.get('oid')) for o in window['emir'])))
protected = {o['oid'] for e in bot if e['k'] == 'G3_KORUMA_IPTAL' for o in e['emirler']}
orders = {o['oid']: o for w in state['windows'].values() for o in w['emir'] if o.get('oid')}
assert protected <= orders.keys()
summary = dict(status='MONITORING_COMPLETE_RUNTIME_CONTINUES', session=meta['session'],
               capture_sha256=sha256(capture.read_bytes()).hexdigest(), sdk_rows=len(sdk),
               quotes=len(quotes), quote_arms=dict(Counter(e['arm'] for e in quotes)),
               protection_cancels=len(protected), protection_final=dict(Counter(
                   ('filled' if orders[o].get('pay', 0) else 'no_fill') + '_' + orders[o]['durum']
                   for o in protected)), windows=windows,
               realized_pnl=sum(w['pnl'] for w in windows if w['resolved']), state=state['st'],
               clock_and_role_checks_passed=True, sdk_contiguous_sequence=True, sdk_write_errors=0)
output = root / 'G3_monitor_20260922_summary.json'
output.write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary))
