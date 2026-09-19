#!/usr/bin/env python3
"""CUZDAN ETIKETLI DOLUM TAPE — kripto 5dk pazarlarinin TUM islemleri.

NEDEN: kamu defteri ANONIM (kimin emri oldugu yazmaz), ama /trades her dolumun
proxyWallet'ini verir -> "seviye supuruldugunde KIM doldu" olculebilir.
Kuyruk pozisyonu sorusunun tek dolayli yolu.
takerOnly=false SART: varsayilan true ve 3 ay boyunca akisin ~%18'ini gosterdi.

09-19 17:00Z DUZELTME: ilk surum her yoklamada yalniz en yeni 500 satiri aliyordu.
data-api islemleri ~5 dk gecikmeyle GECMISE ekliyor; o arada pazarda 2.000+ yeni
satir birikince geciken satir hic gorulmuyordu -> olculen kayip %69-72 (3 pencere,
sayfalanmis tam cekimle kiyas). Simdi her pazar offset ile SONUNA KADAR sayfalaniyor.
Kullanim: --once (tek tur, test) ; FILLS_DIR=... (cikti dizini)
"""
import json,os,sys,time,urllib.request,datetime as dt
D=os.environ.get('FILLS_DIR','/home/taygun/Masaüstü/polymarket/data/tape_fills')
ONCE='--once' in sys.argv
SYM=('btc','eth','sol','xrp')
GAMMA="https://gamma-api.polymarket.com/events?slug={}-updown-5m-{}"
SAYFA=500; MAKS_OFFSET=10000
def jget(u,t=15):
    r=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
    return json.load(urllib.request.urlopen(r,timeout=t))
CID={}
def cid_bul(sym,S):
    if (sym,S) in CID: return CID[(sym,S)]
    c=None
    try:
        e=jget(GAMMA.format(sym,S),10)
        if e and e[0].get('markets'): c=e[0]['markets'][0].get('conditionId')
    except Exception: pass
    CID[(sym,S)]=c; return c
def pazar_tam(c):
    """Pazarin TUM satirlari (sayfalanmis). Bir sayfa hata verirse o pazar bu tur atlanir (None)."""
    out=[]; off=0
    while off<=MAKS_OFFSET:
        try:
            tr=jget(f"https://data-api.polymarket.com/trades?market={c}&takerOnly=false&limit={SAYFA}&offset={off}")
        except Exception:
            return None
        if not tr: break
        out+=tr; off+=SAYFA
        if len(tr)<SAYFA: break
        time.sleep(0.25)
    return out
gor=set(); n_tot=0; hata=0
print(f"[{time.strftime('%H:%M:%S')}] basladi (sayfali)",flush=True)
while True:
    try:
        t0=time.time()
        S0=int(time.time())//300*300
        yeni=0; istek=0
        y=f"{D}/fills_{dt.datetime.now(dt.UTC).strftime('%Y%m%d_%H')}.jsonl"
        f=open(y,'a')
        for sym in SYM:
            for S in (S0-600,S0-300,S0):
                c=cid_bul(sym,S)
                if not c: continue
                tr=pazar_tam(c)
                if tr is None:
                    print(f"[{time.strftime('%H:%M:%S')}] {sym} {S} sayfa hatasi, tur atlandi",flush=True)
                    time.sleep(1.0); continue
                istek+=1+len(tr)//SAYFA
                for a in tr:
                    k=f"{a.get('transactionHash')}|{a.get('proxyWallet')}|{a.get('asset')}|{a.get('side')}|{a.get('size')}|{a.get('price')}"
                    if k in gor: continue
                    gor.add(k); a['_sym']=sym; a['_S']=S
                    f.write(json.dumps(a,separators=(',',':'))+"\n"); yeni+=1
                f.flush()
                time.sleep(0.25)
        f.close()
        n_tot+=yeni; hata=0
        print(f"[{time.strftime('%H:%M:%S')}] +{yeni} dolum (toplam {n_tot:,}, takip {len(gor):,}) {istek} istek {time.time()-t0:.0f}sn",flush=True)
        for k in [k for k in CID if k[1]<S0-1800]: CID.pop(k,None)
        if len(gor)>500000: gor=set(list(gor)[-250000:])
    except Exception as e:
        hata+=1
        print(f"[{time.strftime('%H:%M:%S')}] HATA {type(e).__name__}: {str(e)[:60]} ({hata})",flush=True)
        time.sleep(30 if hata<5 else 120)
    if ONCE: break
    time.sleep(10)
