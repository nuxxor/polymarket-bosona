#!/usr/bin/env python3
"""BOSONA SUREKLI KAYIT — /activity ucundan (TRADE + MERGE + REDEEM + REBATE).
/trades DEGIL: o yalnizca BUY/SELL gosterir, merge ve rebate gorunmez.
Tekrarlari eler, JSONL'e ekler. ~300 sn kamu gecikmesi var, o degismez."""
import json,time,os,urllib.request,sys
BOS='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
OUT='/home/taygun/Masaüstü/polymarket/data/bosona_canli/activity.jsonl'
SEEN='/home/taygun/Masaüstü/polymarket/data/bosona_canli/.gorulen'
gor=set()
if os.path.exists(SEEN):
    gor=set(x.strip() for x in open(SEEN) if x.strip())
def jget(u,t=20):
    r=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
    return json.load(urllib.request.urlopen(r,timeout=t))
def anahtar(a):
    return "|".join(str(a.get(k,'')) for k in
                    ('transactionHash','timestamp','type','asset','side','size','price'))
hata=0
while True:
    try:
        n=0
        for off in (0,500):
            ac=jget(f"https://data-api.polymarket.com/activity?user={BOS}&limit=500&offset={off}")
            if not ac: break
            with open(OUT,'a') as f:
                for a in ac:
                    k=anahtar(a)
                    if k in gor: continue
                    gor.add(k); f.write(json.dumps(a,separators=(',',':'))+"\n"); n+=1
            if len(ac)<500: break
        if n:
            with open(SEEN,'w') as f:
                for k in list(gor)[-60000:]: f.write(k+"\n")
            print(f"[{time.strftime('%H:%M:%S')}] +{n} yeni olay (toplam takip {len(gor)})",flush=True)
        hata=0
    except Exception as e:
        hata+=1
        print(f"[{time.strftime('%H:%M:%S')}] HATA {type(e).__name__}: {str(e)[:60]} (ust uste {hata})",flush=True)
        if hata>=10: time.sleep(120)
    time.sleep(45)
