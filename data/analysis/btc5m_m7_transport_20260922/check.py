"""Reproduce transport diagnosis; failure to see a gap is not a permanent fix."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'btc5m_m7_20260922'))
from check_capture import check as capture_check


def meter_check(path):
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert rows[0]['event']=='connected' and rows[-1]['event']=='connection_end'
    common = {'event','utc_ns','channel','connection'}
    keys = dict(connected={'queue_high','queue_low'},connection_end=set(),
        sample={'mono_second','calls','frames','timeouts','bytes','queue_max','paused_samples','caller_max_ns','recv_max_ns'},
        close={'code','error_type','slow_consumer','reason_length'})
    for row in rows:
        assert set(row)==common|keys[row['event']]
        assert row['channel'] in ('market','user')
    samples = [r for r in rows if r['event']=='sample']
    assert samples
    assert all(r['queue_max']>=0 and r['caller_max_ns']>=0 for r in samples)
    assert all(r['calls']>=r['frames']+r['timeouts'] for r in samples)
    maxes = sorted(r['caller_max_ns']/1e6 for r in samples)
    closes=[]
    for r in rows:
        if r['event']!='close':continue
        previous = [s for s in samples if s['connection']==r['connection'] and
                    0<=r['utc_ns']-s['utc_ns']<=30*10**9]
        closes.append(dict(**r,prior_30s_queue_max=max((s['queue_max'] for s in previous),default=None),
                           prior_30s_paused_samples=sum(s['paused_samples'] for s in previous)))
    return dict(frames=sum(r['frames'] for r in samples),samples=len(samples),
        connections=sum(r['event']=='connected' for r in rows),closes=closes,
        queue_highs=sorted({r['queue_high'] for r in rows if r['event']=='connected'}),
        queue_max=max(r['queue_max'] for r in samples),paused_samples=sum(r['paused_samples'] for r in samples),
        caller_max_ms=max(maxes),p99_secondly_caller_max_ms=maxes[int((len(maxes)-1)*.99)])


def main(root):
    comparison = json.loads((root/'comparison.json').read_text())
    session = comparison['recorder_session']
    capture_root=root/'capture'
    raw=capture_root/(session+'.jsonl')
    if not raw.exists():raw=capture_root/(session+'.jsonl.gz')
    summary_path=capture_root/(session+'.summary.json')
    summary=json.loads(summary_path.read_text())
    capture=capture_check(raw,summary_path)
    protocol=json.loads((HERE/'protocol.json').read_text())
    assert summary['source_sha256']==protocol['source_sha256']==comparison['source_sha256']
    assert comparison['drain_exit']==0
    meters={name:meter_check(root/(name+'.jsonl')) for name in ('drain_market','recorder_market','recorder_user')}
    for ch in ('market','user'):
        stats=summary['stats'][ch]
        m=meters['recorder_'+ch]
        assert m['frames']==stats.get('frames',0)+stats['pong']
        assert m['connections']==stats['connections']
    drain=json.loads((root/'drain.json').read_text())
    assert meters['drain_market']['frames']==drain['frames']+drain['pong']
    assert len(meters['drain_market']['closes'])<=drain['gaps']
    assert summary['full_calibration'] is False
    runtime=json.loads((root/'runtime_sources.json').read_text())
    assert all(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==sha for name,sha in runtime.items())
    state=json.loads((root/'final_state.json').read_text())
    before=json.loads((HERE.parent/'btc5m_m7_20260922/final_state.json').read_text())
    assert state['financial_hashes']==before['m4_v2_hashes']
    assert not state['financial_pids'] and not state['observer_pids'] and state['open_orders']==0
    async_result=json.loads((root/'async_result.json').read_text())
    assert async_result['roster_sha256']==hashlib.sha256((root/'roster.json').read_bytes()).hexdigest()
    assert async_result['elapsed']>=240 and async_result['frames']>0 and async_result['pong']>0
    # Raw public source timestamps measure publication age, not exchange activation.
    delays=[]
    opener=gzip.open if raw.suffix=='.gz' else open
    with opener(raw,'rt') as file:
        for line in file:
            row=json.loads(line)
            if row.get('event')=='data' and row['payload']['event_type']=='price_change':
                delays.append(row['received']['utc_ns']/1e6-float(row['payload']['timestamp']))
    delays.sort()
    assert delays
    return dict(capture=capture,meters=meters,drain=drain,
        recorder_cpu_seconds=comparison['recorder_cpu_seconds'],
        price_change_publication_age_ms=dict(median=delays[len(delays)//2],p99=delays[int((len(delays)-1)*.99)],max=max(delays)),
        transport_gate_passed=bool(capture['transport_ok'] and len(capture['current_window_activity'])>=3 and
                                  capture['elapsed_seconds']>=protocol['seconds']),
        permanent_disconnect_fix_proven=False,full_calibration=False,
        probe_sha256=hashlib.sha256((HERE/'probe.py').read_bytes()).hexdigest(),
        async_control=async_result,connection_overlap=json.loads((root/'connection_overlap.json').read_text()),
        financial_state_unchanged=True,observers_stopped=True,open_orders=0)


if __name__=='__main__':
    result=main(Path(sys.argv[1]))
    print(json.dumps(result,indent=2))
