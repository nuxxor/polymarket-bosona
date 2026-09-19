#!/usr/bin/env python3
"""PENCERE ONCESI DEFTER KAYDEDICISI — erken kotasyon deneyinin eksik verisi.

SORUN: Londra kaydi pencereden yalnizca 5 dakika once basliyor (270/270 pencere).
       Diger arsiv 6-24 saat kapsiyor ama YALNIZ ilk 5 seviye.
       Bu yuzden "1 saat once emir koysak ne olurdu" sorusu mevcut veriyle
       TAM DERINLIKLE cevaplanamiyor.

COZUM: Her pencereyi T-2 SAAT'ten T+0'a kadar, TAM DERINLIKLE, dakikada bir kaydet.
       Calisan tape'e DOKUNMAZ; ayri dizine yazar.

Cikti: data/tape_preopen/preopen_YYYYMMDD_HH.jsonl.gz
Satir: {"S":pencere, "tok":"Up"/"Down", "rcv":ms, "t_rel":saniye(negatif=oncesi),
        "bids":[[fiyat,pay],...], "asks":[[...]]}
"""
import json, time, gzip, os, urllib.request, urllib.error

ONCE_SN = 2*3600          # 2 saat oncesinden izle
DONGU_SN = 60             # her pencereyi dakikada bir ornekle
OUT = '/home/taygun/Masaüstü/polymarket/data/tape_preopen'
GAMMA = "https://gamma-api.polymarket.com/events?slug=btc-updown-5m-{}"
BOOK = "https://clob.polymarket.com/book?token_id={}"
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) Chrome/140.0'}
os.makedirs(OUT, exist_ok=True)

tok_cache = {}
fh, cur_hr = None, None


def jget(url, timeout=12):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def tokens(S):
    if S in tok_cache:
        return tok_cache[S]
    try:
        ev = jget(GAMMA.format(S))
        for e in ev:
            for m in e.get('markets', []):
                t = dict(zip(json.loads(m['outcomes']), json.loads(m['clobTokenIds'])))
                tok_cache[S] = t
                return t
    except Exception:
        pass
    tok_cache[S] = None
    return None


def yaz(obj):
    global fh, cur_hr
    hr = time.strftime('%Y%m%d_%H', time.gmtime())
    if hr != cur_hr:
        if fh: fh.close()
        fh = gzip.open(f'{OUT}/preopen_{hr}.jsonl.gz', 'at')
        cur_hr = hr
    fh.write(json.dumps(obj, separators=(',', ':')) + '\n')


print(f"pencere-oncesi kaydedici basladi | T-{ONCE_SN//3600}sa .. T+0 | {DONGU_SN}sn cevrim", flush=True)
son = {}
n = 0
while True:
    try:
        now = time.time()
        S0 = int(now // 300 * 300)
        # izlenecek pencereler: simdiki + gelecek ONCE_SN icindekiler
        hedefler = [S0 + k*300 for k in range(0, ONCE_SN//300 + 1)]
        for S in hedefler:
            if now - son.get(S, 0) < DONGU_SN:
                continue
            t = tokens(S)
            if not t:
                son[S] = now; continue
            for nm, tid in t.items():
                try:
                    b = jget(BOOK.format(tid))
                except Exception:
                    continue
                yaz({'S': S, 'tok': nm, 'rcv': int(time.time()*1000),
                     't_rel': int(time.time() - S),
                     'bids': [[float(x['price']), float(x['size'])] for x in b.get('bids', [])],
                     'asks': [[float(x['price']), float(x['size'])] for x in b.get('asks', [])]})
                n += 1
            son[S] = now
        # eski pencereleri temizle
        for S in [s for s in list(son) if s < S0 - 600]:
            son.pop(S, None); tok_cache.pop(S, None)
        if fh: fh.flush()
        if n and n % 200 < 2:
            print(f"  {time.strftime('%H:%M:%S')} kayit={n} izlenen={len(hedefler)}", flush=True)
        time.sleep(2)
    except KeyboardInterrupt:
        break
    except Exception as ex:
        print('hata:', str(ex)[:90], flush=True)
        time.sleep(5)
