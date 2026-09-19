#!/usr/bin/env python3
"""4.910 settlement penceresinin S-60..S+300 araligini iki feed icin ceker."""
import sys, os, time, duckdb, pandas as pd, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch import page, FEEDS
H = '/home/taygun/Masaüstü/polymarket/data/analysis/btc5m_top_actor_hunt_20260902_v1'
D = os.path.dirname(os.path.abspath(__file__))
now = int(time.time())
W = duckdb.connect().execute(f"""select distinct start_ts from read_parquet('{H}/SETTLEMENT_DEFS.parquet')
 where ref_twap60 is not null and start_ts > {now-28*86400} order by 1""").fetchdf()
S = [int(x) for x in W.start_ts]
pages = sorted({p for s in S for p in range(((s-90)//100)*100, s+300+100, 100)})
print(f"{len(S)} pencere, {len(pages)} sayfa/feed", flush=True)
for name in ('twap60', 'spot'):
    out = f'{D}/HIST_{name}.parquet'
    if os.path.exists(out):
        print("atlandi (var):", out, flush=True); continue
    rows, done, t0 = [], 0, time.time()
    with cf.ThreadPoolExecutor(6) as ex:
        for res in ex.map(lambda p: page(p, FEEDS[name]), pages):
            rows += res; done += 1
            if done % 1000 == 0:
                print(f"  {name} {done}/{len(pages)} {len(rows)} satir {time.time()-t0:.0f}s", flush=True)
    pd.DataFrame(rows, columns=['ts','price','bid','ask']).drop_duplicates('ts').sort_values('ts').to_parquet(out, index=False)
    print(f"BITTI {out} ({time.time()-t0:.0f}s)", flush=True)
