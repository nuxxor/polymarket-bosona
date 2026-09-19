#!/usr/bin/env python3
"""Chainlink Data Streams 1Hz BTC/USD gecmisini ceker -> parquet.
Kullanim: fetch.py <start_unix> <end_unix> <cikti.parquet> [is_parcaci]"""
import sys, os, time, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cl_client, pandas as pd

# DOGRULANDI 2026-09-13: C feed = Polymarket settlement TWAP-60 (tape ile birebir, 18 hane)
FEEDS = {'spot': '0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8',
         'twap30': '0x0002e6b03af5a87b65f4c5c0c8eaf6027e4156f467cd16bdcf8a5b4347f9c087',
         'twap60': '0x0002ee6757e8822c00d273bc340fc24c9cafe123a4ff2ea1dbdb31944bc7d95f'}
BTC = FEEDS['twap60']

def i192(x):
    v = int(x, 16)
    return v - (1 << 256) if v >= (1 << 255) else v

def decode(blob):
    h = blob[2:] if blob.startswith('0x') else blob
    w = [h[i:i+64] for i in range(0, len(h), 64)]
    b = w[int(w[3], 16)//32 + 1:]
    return int(b[2], 16), i192(b[6])/1e18, i192(b[7])/1e18, i192(b[8])/1e18

def page(t0, feed=None):
    fid = feed or BTC
    for a in range(4):
        try:
            r = cl_client.call(f'/api/v1/reports/page?feedID={fid}&startTimestamp={t0}&limit=100')
            return [decode(x['fullReport']) for x in r.get('reports', [])]
        except Exception as e:
            if 'out of bounds' in str(e) or '404' in str(e):
                return []
            time.sleep(1.0 * (a + 1))
    return []

if __name__ == '__main__':
    s, e, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    nw = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    starts = list(range(s, e, 100))
    rows, done, t0 = [], 0, time.time()
    with cf.ThreadPoolExecutor(nw) as ex:
        for res in ex.map(page, starts):
            rows += res; done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(starts)} sayfa, {len(rows)} satir, {time.time()-t0:.0f}s", flush=True)
    df = pd.DataFrame(rows, columns=['ts', 'price', 'bid', 'ask']).drop_duplicates('ts').sort_values('ts')
    df.to_parquet(out, index=False)
    print(f"BITTI {out}: {len(df)} saniye, {df.ts.min()}..{df.ts.max()}, kayip {(e-s)-len(df)}")
