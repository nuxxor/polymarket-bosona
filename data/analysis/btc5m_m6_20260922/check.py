"""One executable check for receipt-time causality, ambiguity and all 12 controls."""
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256

from diagnose import BASE, OUT, depth_at, level_path, matching_decrements, read

order = dict(send_ms=1100, ack_ms=1150, terminal_observed_ms=1200,
             tokens=['up','down'], oi=0, price=.5)
events = [dict(rcv=900,k='book',p=dict(asset_id=t,timestamp='890',
          bids=[dict(price='.5',size='20')],asks=[dict(price='.5',size='20')]))
          for t in order['tokens']]
for received, source, size in [(1120,1110,'25'),(1190,1170,'5'),(1250,1200,'25')]:
    events.append(dict(rcv=received,k='price_change',p=dict(timestamp=str(source),price_changes=[
        dict(asset_id='up',side='BUY',price='.5',size=size),
        dict(asset_id='down',side='SELL',price='.5',size=size)])))
path = level_path(events,order)
assert depth_at(path,1100)==20_000_000 and depth_at(path,1150)==25_000_000
assert depth_at(path,1190)==5_000_000  # source time cannot make the 1250 receipt visible
assert depth_at(level_path(events[:-1],order),1190)==depth_at(path,1190)
bad = deepcopy(events)
bad[-1]['p']['price_changes'][1]['size']='24'
try:
    level_path(bad,order)
except AssertionError:
    pass
else:
    raise AssertionError('Unreconciled mirror depth was accepted')
ambiguous = [dict(source_ms=t,received_ms=t+10,quantity_units=q)
             for t,q in [(100,10),(200,5),(300,10),(400,5)]]
assert len(matching_decrements(ambiguous,dict(obs_lo=500),5))==2
assert matching_decrements(ambiguous,dict(obs_lo=150),5)==[]

report, baseline = read(OUT/'report.json'), read(BASE/'report.json')
rows = report['rows']
assert len(rows)==len({r['oid'] for r in rows})==12
for r,b in zip(rows,baseline['rows']):
    assert (r['oid'],r['actual'],r['baseline_static'])==(b['oid'],b['actual'],b['static_queue'])
    assert r['calibrated_prediction'] is None
    assert sum(f['quantity_units'] for f in r['own_fills'])==Decimal(str(r['actual']))*1_000_000
    assert all(a['received_ms']<b['received_ms'] for a,b in zip(r['level_path'],r['level_path'][1:]))
assert report['summary']['baseline_mismatches']==4
assert report['summary']['arrival_sensitivity_mismatches']==2
assert report['summary']['clock_nulls']==1
assert rows[0]['initial_depth']==dict(pre100=0,send=5,ack=321.99)
assert rows[2]['initial_depth']==dict(pre100=0,send=28.53,ack=341.52)
assert all(rows[i]['ack_depth_sensitivity']==[0,0] for i in (0,2))
assert all(rows[i]['actual']==5 and rows[i]['ack_depth_sensitivity']==[0,0] for i in (5,11))
assert rows[3]['actual']==0 and rows[3]['ack_depth_sensitivity']==[0,5]  # adverse control
assert rows[5]['depth_min_before_first_public_source']==15
assert rows[5]['own_fills'][0]['decrement_candidates'][0]['public_source_lag_ms']==40
clock = rows[7]['own_fills'][0]
assert 141<clock['source_after_terminal_ms']<142
assert len(clock['decrement_candidates'])==1
assert clock['decrement_candidates'][0]['public_source_lag_ms']==464
assert len(rows[11]['own_fills'][0]['decrement_candidates'])==4  # never choose the convenient one
for name,digest in report['inputs_sha256'].items():
    assert sha256((OUT.parent/name).read_bytes()).hexdigest()==digest,name
assert sha256((OUT/'diagnose.py').read_bytes()).hexdigest()==report['source_sha256']
print('M6: causal levels, mirror rejection, ambiguous clocks, 12 controls and frozen hashes passed')
