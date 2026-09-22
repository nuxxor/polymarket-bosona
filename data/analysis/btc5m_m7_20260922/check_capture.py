"""Check a completed capture; quiet authenticated stream is not fill validation."""
from collections import Counter,defaultdict
from hashlib import sha256
import gzip
import json
from pathlib import Path
import sys


def check(path,summary_path):
    summary = json.loads(summary_path.read_text())
    assert not summary['full_calibration']
    assert not summary['writer_failed'] and not summary['reader_alive']
    counts = defaultdict(Counter)
    last_received,ready,activity = {},set(),Counter()
    lag,clock_offsets = [],[]
    seq = 0
    digest = sha256()
    opener = gzip.open if path.suffix=='.gz' else open
    with opener(path,'rb') as file:
        for raw in file:
            digest.update(raw)
            row = json.loads(raw)
            if row['event']=='session_start':
                assert seq==0 and row['session']==summary['session']
                assert row['source_sha256']==summary['source_sha256']
                continue
            if row['event']=='session_end':
                assert row['stats']==summary['stats']
                continue
            seq += 1
            assert row['seq']==seq and row['session']==summary['session']
            received,written = row['received'],row['written']
            assert written['mono_ns']>=received['mono_ns']
            key = row['channel'],row['connection']
            assert received['mono_ns']>=last_received.get(key,0)
            last_received[key] = received['mono_ns']
            lag.append((written['mono_ns']-received['mono_ns'])/1e6)
            clock_offsets.append(received['utc_ns']-received['mono_ns'])
            counts[row['channel']][row['event']] += 1
            if row['event']!='data':
                continue
            payload = row['payload']
            counts[row['channel']][payload['event_type']] += 1
            def no_private_fields(value):
                if isinstance(value,dict):
                    assert not set(value)&{'owner','order_owner','trade_owner','auth','apiKey','secret','passphrase','signature'}
                    for v in value.values():
                        no_private_fields(v)
                elif isinstance(value,list):
                    for v in value:
                        no_private_fields(v)
            no_private_fields(payload)
            if row['channel']=='market':
                if payload['event_type']=='book':
                    ready.add((row['connection'],payload['asset_id']))
                if payload['event_type']=='price_change':
                    assert all((row['connection'],c['asset_id']) in ready for c in payload['price_changes'])
                market, = [m for m in summary['markets'] if m['market']==payload['market']]
                if market['S']*10**9<=received['utc_ns']<(market['S']+300)*10**9:
                    activity[market['S']] += 1
    assert row['event']=='session_end' and seq==summary['rows']
    for ch,stats in summary['stats'].items():
        for key in ('book','price_change','last_trade_price','tick_size_change','order','trade','pong'):
            assert counts[ch][key]==stats.get(key,0),(ch,key)
    assert all(counts['market'][k]>0 for k in ('book','price_change','last_trade_price'))
    assert all(counts[ch]['pong']>0 for ch in ('market','user'))
    lag.sort()
    return dict(session=summary['session'],transport_ok=summary['transport_ok'],rollover_observed=len(activity)>=2,
        elapsed_seconds=(summary['ended']['mono_ns']-summary['started']['mono_ns'])/1e9,
        rows=seq,counts={k:dict(v) for k,v in counts.items()},current_window_activity=dict(activity),
        max_write_delay_ms=max(lag),p99_write_delay_ms=lag[int((len(lag)-1)*.99)],
        utc_minus_monotonic_spread_ms=(max(clock_offsets)-min(clock_offsets))/1e6,
        raw_sha256=digest.hexdigest(),user_events_observed=summary['user_events_observed'],full_calibration=False)


if __name__=='__main__':
    result = check(Path(sys.argv[1]),Path(sys.argv[2]))
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['transport_ok'] and result['rollover_observed'] else 1)
