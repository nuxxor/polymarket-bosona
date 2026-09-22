"""One executable check: raw persistence, finite shutdown, then data audit checks."""
import gzip
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import time
from unittest.mock import patch

import record
import audit


def capture_check(byte_limit=record.MAX_BYTES):
    class Socket:
        def __init__(self):
            self.frames = iter(['PONG','{broken',json.dumps([dict(event_type='new_unknown'),dict(event_type='book')]),b'\xff'])
        def send(self, _):
            pass
        def settimeout(self, _):
            pass
        def recv(self):
            time.sleep(.01)
            try:
                return next(self.frames)
            except StopIteration:
                raise record.websocket.WebSocketTimeoutException() from None
        def close(self):
            pass
    market = dict(clobTokenIds='["a","b"]')
    fake_start = int(time.time())+20
    meta = dict(group='btc_15m',S=fake_start,end=fake_start+900,mechanism='chainlink_twap60')
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(record,'HERE',Path(tmp)),patch.object(record,'START',fake_start),patch.object(record,'CUT',time.time()-9.6),patch.object(record,'MAX_BYTES',byte_limit),patch.object(record.accounting.ref.base,'get',return_value=market),patch.object(record.accounting.ref,'classify',return_value=meta),patch.object(record.websocket,'create_connection',side_effect=lambda *a,**kw:Socket()):
            record.main()
        root = Path(tmp)/'raw/dual'
        status = json.loads((root/'status.json').read_text())
        assert not status['running']
        if byte_limit==1:
            assert status['reason']=='storage_limit' and status['raw_bytes']<=1
            return 'combined size guard ends both local reader loops without extending budget'
        assert status['reason']=='duration_complete'
        hashes = json.loads((root/'closed_hashes.json').read_text())
        for name,digest in hashes.items():
            assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
            rows = [json.loads(s) for s in gzip.open(root/name,'rt')]
            assert [r['seq'] for r in rows]==list(range(1,len(rows)+1))
            assert rows[-1]['kind']=='end'
            assert sum(r.get('raw')=='{broken' for r in rows)==1
            assert any(r.get('binary_b64')=='/w==' for r in rows)
            assert any('new_unknown' in r.get('raw','') for r in rows)
            assert all(a['monotonic_ns']<=b['monotonic_ns'] for a,b in zip(rows,rows[1:]))
        assert len(hashes)==2 and all(v['frames']==4 for v in status['channels'].values())
    return 'two readers retain malformed/unknown/binary frames, sequence clocks and finite close hashes'


def main():
    checks = [capture_check(),capture_check(1)]
    market = dict(conditionId='m',clobTokenIds='["a","b"]')
    good = dict(event_type='last_trade_price',market='m',asset_id='a',timestamp='999',
                price='.4',size='5',side='BUY',transaction_hash='tx')
    bodies = [json.dumps([good,dict(event_type='unknown')]),'{bad',json.dumps(dict(good,asset_id='wrong')),
              json.dumps(dict(good,price='NaN'))]
    rows = [dict(seq=i+1,monotonic_ns=1000+i,received_ms=1000+i,kind='frame',raw=body) for i,body in enumerate(bodies)]
    ee,q = audit.decode(rows,market)
    assert len(ee)==1 and len(q['issues'])==4 and q['rows']==4
    checks.append('unknown, malformed and wrong-token messages remain explicit coverage failures')
    broken = copy.deepcopy(rows)
    broken[1]['seq'] += 1
    try:
        audit.decode(broken,market)
    except AssertionError:
        pass
    else:
        raise AssertionError('raw sequence gap accepted')
    checks.append('sequence gap is rejected rather than becoming zero events')
    evidence = audit.a.read(audit.HERE/'results/existing_evidence.json')
    pairs = evidence['distinct_equal_summary_matches']
    e = evidence['captured_public_messages'][0]
    second = copy.deepcopy(e)
    second['p']['transaction_hash'] = pairs[0]['tx']
    groups = {g['tx']:[g] for g in pairs}
    tokens = list({g['active']['token'] for g in pairs}|{m['token'] for g in pairs for m in g['makers']})
    flows,errors,metrics = audit.a.m1.trade_flows([e,e,second],groups,tokens)
    assert not errors and metrics['repeat_messages']==1 and metrics['matches']==2
    assert sum(audit.a.m1.units(f['qty']) for f in flows)==15666668
    checks.append('two genuine equal-summary trades survive; repeated same-log WS message adds no volume')
    assert any(float(x['public_after_matched_ms'])>100 and x['private_exchange_match_ms'] is None for x in evidence['public_clocks'])
    checks.append('public clock after observed MATCHED remains a calibration counterexample')
    chain_path = audit.HERE/'results/independent_chain.json'
    if chain_path.exists():
        chain = audit.a.read(chain_path)
        victim = chain['match_logs'][0]
        key = victim['transactionHash'],victim['logIndex']
        cache = audit.a.rpc_cache
        captured = {}
        def omit(method_path,method,params,endpoints=None):
            value = cache(method_path,method,params,endpoints)
            return [e for e in value if (e['transactionHash'],e['logIndex'])!=key] if method=='eth_getLogs' else value
        with patch.object(audit.a,'rpc_cache',side_effect=omit),patch.object(audit,'write',side_effect=lambda p,v:captured.update({p.name:v})):
            audit.scan()
        changed = captured['independent_chain.json']
        assert changed['known_receipts_absent_from_scan']==[(key[0],int(key[1],16))]
        assert changed['matched_market_logs']==chain['matched_market_logs']-1
        checks.append('a missing cached RPC log is detected against independently fetched receipts without changing raw files')
    current = audit.HERE/'results/comparison.json'
    if current.exists():
        result = audit.a.read(current)
        assert result['economic_pnl'] is None and not result['execution_calibrated']
        assert set(result['channels'])=={'A','B'}
        for c,x in result['channels'].items():
            assert x['report']['start']==record.START and x['report']['cutoff_ms']==record.CUT*1000
            if x['data_gate']=='PASS_OBSERVED_FLOW_GATE':
                assert not x['reasons'] and not x['parse']['issues']
                assert x['report']['valid_book_samples']>=.95*901
                assert not any(m['in_window_by_block_clock'] for m in x['report']['chain_matches_without_ws'])
        checks.append('real streams are gated separately and no public completeness test claims calibrated fills')
    audit.write(audit.HERE/'results/checks.json',dict(passed=True,checks=checks))
    audit.protect()
    print(len(checks),'checks passed')


if __name__=='__main__':
    main()
