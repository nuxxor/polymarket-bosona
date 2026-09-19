#!/usr/bin/env python3
"""BTC FIYAT TAPE — Binance futures aggTrade + 1s kline, saatlik gz JSONL.
09-19: eski tape.py betigi eski bir oturum klasoruyle silinmisti ve kayit
01:02'de olmustu (13,5 saat defter verisi kalici kayip). Bu onun yerine gecer.
Kapsam BILEREK dar: yalnizca BTCUSDT. Eski tape cok-borsa + tam derinlikti
(~140 GB/gun); bu ~1-2 GB/gun."""
import asyncio, gzip, json, os, time, datetime as dt
import websockets
D='/home/taygun/Masaüstü/polymarket/data/tape_btc'
# 09-19 16:45: fstream (futures WS) baglaniyor ama VERI GONDERMIYOR (14 dk, 0 satir).
# REST futures calisiyor (botun vol kapisi onu kullanir, etkilenmedi). Spot WS calisiyor.
URL="wss://stream.binance.com:9443/stream?streams=btcusdt@aggTrade/btcusdt@kline_1s"
def yol():
    return f"{D}/btc_{dt.datetime.now(dt.UTC).strftime('%Y%m%d_%H')}.jsonl.gz"
async def kos():
    f=None; ad=None; n=0; t0=time.time()
    while True:
        try:
            async with websockets.connect(URL,ping_interval=20,max_queue=4096) as ws:
                print(f"[btc] bagli {dt.datetime.now(dt.UTC):%H:%M:%S}Z",flush=True)
                async for m in ws:
                    y=yol()
                    if y!=ad:
                        if f: f.close()
                        f=gzip.open(y,'at'); ad=y
                    f.write(m+"\n"); n+=1
                    if n%50000==0:
                        f.flush()
                        print(f"[btc] {n:,} olay, {n/(time.time()-t0):.0f}/sn, dosya {os.path.basename(ad)}",flush=True)
        except Exception as e:
            print(f"[btc] KOPTU {type(e).__name__}: {str(e)[:60]} -> 5sn",flush=True)
            await asyncio.sleep(5)
asyncio.run(kos())
