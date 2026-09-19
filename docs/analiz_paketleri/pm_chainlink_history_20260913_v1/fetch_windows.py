#!/usr/bin/env python3
"""Belirli pencerelerin cevresindeki (S-60 .. S+300) Chainlink saniyelerini ceker."""
import sys, os, time, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch import page
import pandas as pd

def fetch_windows(starts, out, nw=6):
    pages = sorted({p for S in starts for p in range(((S-60)//100)*100, S+300+100, 100)})
    rows, done, t0 = [], 0, time.time()
    with cf.ThreadPoolExecutor(nw) as ex:
        for res in ex.map(page, pages):
            rows += res; done += 1
            if done % 200 == 0:
                print(f"  {done}/{len(pages)} sayfa, {len(rows)} satir, {time.time()-t0:.0f}s", flush=True)
    df = pd.DataFrame(rows, columns=['ts','price','bid','ask']).drop_duplicates('ts').sort_values('ts')
    df.to_parquet(out, index=False)
    print(f"BITTI {out}: {len(df)} saniye")
    return df
