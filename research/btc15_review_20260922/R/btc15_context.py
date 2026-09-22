#!/usr/bin/env python3
"""Read existing BTC price tapes for 15-minute contracts only; no new recorder."""
from collections import Counter, defaultdict
import bisect
import gzip
import hashlib
import math
import shutil

import research as r


def build():
    r.base.OUT = r.REPO/'data/analysis/bosona_gec_20260921'
    streams, _, excluded = r.base.load_prices()
    records = {name:[(rcv,*v) for rcv,v in zip(times,values)] for name,(times,values) in streams.items()}
    sources = {}
    for p in sorted((r.REPO/'data/tape_cl_direct').glob('cld_202609*.gz')):
        if not 'cld_20260920_23'<=p.name[:15]<'cld_20260921_12':
            continue
        frozen = r.RAW/'btc_price_extension'/p.name
        if not frozen.exists():
            frozen.parent.mkdir(exist_ok=True)
            shutil.copyfile(p,frozen)
        with gzip.open(frozen,'rt') as stream:
            part = [r.json.loads(line) for line in stream]
        for x in part:
            if x['f'] in records and x['obs']*1000<=x['rcv']:
                records[x['f']].append((x['rcv'],x['obs']*1000,float(x['px'])))
        sources[str(frozen)] = hashlib.sha256(frozen.read_bytes()).hexdigest()
    for p in sorted((r.REPO/'data/analysis/bosona_derin_20260921/recovered_prices').glob('*.gz')):
        sources[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
        with gzip.open(p,'rt') as stream:
            for w,rcv,obs,px in r.json.load(stream):
                if obs<=rcv:
                    records['spot' if w==0 else 'twap60'].append((rcv,obs,float(px)))
    for p in sorted((r.base.OUT/'price_snapshot').glob('*.gz')):
        sources[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    starts = {}
    for name,seq in records.items():
        times,values,last = [],[],-1
        for rcv,obs,px in sorted(set(seq)):
            if obs<last:
                continue
            last = obs
            times.append(rcv)
            values.append((obs,float(px)))
            if name=='twap60' and obs%900000==0:
                starts.setdefault(obs//1000,(rcv,float(px)))
        streams[name] = times,values
    universe = [w for w in r.read(r.OUT/'universe.json') if w['group']=='btc_15m']
    fills = [f for f in r.read(r.OUT/'fills.json') if f['group']=='btc_15m']
    requests = defaultdict(set)
    for w in universe:
        requests[w['S']].update(range(w['S']+120,w['end'],30))
    for f in fills:
        requests[f['S']].update([f['ts']-5,f['ts']-10])
    def price(name,when):
        times,values = streams[name]
        i = bisect.bisect_right(times,when*1000)-1
        if i<0 or not 0<=when*1000-times[i]<=3000 or not 0<=when*1000-values[i][0]<=3000:
            raise ValueError('stale_or_missing_'+name)
        return values[i][1]
    output,failures = {},Counter()
    for w in universe:
        s = w['S']
        m = r.read(r.RAW/'markets'/(w['slug']+'.json'))
        meta = next(e['eventMetadata'] for e in m['events'] if e['slug']==w['slug'])
        for now in sorted(requests[s]):
            try:
                if s not in starts:
                    raise ValueError('no_recorded_reference')
                rcv,ref = starts[s]
                if rcv>now*1000 or not 0<now-s<900:
                    raise ValueError('reference_or_time_not_available')
                if abs(ref-float(meta['priceToBeat']))>1e-6:
                    raise ValueError('reference_mismatch')
                spot,twap = price('spot',now),price('twap60',now)
                hist = [price('spot',now-i*5) for i in range(13)]
                sigma = math.sqrt(sum((a-b)**2 for a,b in zip(hist,hist[1:]))/60)
                if sigma<1e-8:
                    raise ValueError('zero_volatility')
                f = dict(S=s,now=now,ref=ref,reference_received_ms=rcv,spot=spot,twap=twap,sigma=sigma,
                         momentum10=(hist[0]-hist[2])/(sigma*math.sqrt(10)),
                         distance=(spot-ref)/(sigma*math.sqrt(900-(now-s))))
                # The reusable function depends only on end=S+300. Map that end to the 15m end.
                f.update(r.deep.fair_twap(streams,w['end']-300,now*1000,f))
                output[f'{s}:{now}'] = f
            except (ValueError,KeyError) as e:
                failures[str(e)] += 1
    r.save(r.RAW/'btc15_context.json',output)
    r.save(r.RAW/'btc15_context_manifest.json',dict(records=len(output),requested=sum(map(len,requests.values())),
          failures=dict(failures),source_hashes=sources,excluded=excluded))
    print('BTC15 recorded Chainlink contexts',len(output),'gaps',dict(failures),flush=True)


if __name__=='__main__':
    build()
