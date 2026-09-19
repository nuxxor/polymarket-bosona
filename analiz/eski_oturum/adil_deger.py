#!/usr/bin/env python3
"""ADIL DEGER MODELI — "yonu bilmek" degil, KALAN SUREYE GORE OLASILIK.

Uzlasma:  Up  <=>  TWAP60(S+300) >= TWAP60(S)
t aninda bilinen:  marj(t) = TWAP60(t) - TWAP60(S)
Kalan belirsizlik: S+300'deki TWAP60, son 60 sn'nin ortalamasi. t<240 iken
  o pencerenin bir kismi HENUZ OLUSMADI -> kalan oynaklik onemli.

Adil deger:  P(Up) = Phi( marj / sigma_kalan )
  sigma_kalan: BTC vadelinin kalan surede TWAP60'i ne kadar oynatabilecegi.
  Ampirik olarak KALIBRE edilir (teorik formul yerine gercek dagilim).

Sonra: adil deger PIYASA FIYATINDAN daha iyi kalibre mi?
Bu, "kenar var mi" sorusunun dogru hali.
"""
import json,gzip,glob,collections,statistics as ist,math,random
T=[60,90,120,150,180,210,240,270]
CL=collections.defaultdict(list)
for f in sorted(glob.glob('/home/taygun/Masaüstü/polymarket/data/tape/tape_2026091[3-8]_*.jsonl.gz')):
    try:
        with gzip.open(f,'rt') as fh:
            for ln in fh:
                if '"k":"cl"' not in ln: continue
                try: d=json.loads(ln)
                except Exception: continue
                p=d.get('p') or {}
                if p.get('w')!=60: continue
                CL[int(d['src']//1000)].append(float(p['px']))
    except EOFError: pass
S60={s:ist.median(v) for s,v in CL.items()}
print(f"TWAP60 saniye: {len(S60)}",flush=True)
def at(t):
    for d in range(4):
        if t-d in S60: return S60[t-d]
    return None
lo,hi=min(S60),max(S60)
W=[]
for S in range((lo//300+1)*300,(hi//300)*300,300):
    b=at(S); e=at(S+300)
    if b is None or e is None: continue
    m={}
    for t in T:
        v=at(S+t)
        m[t]=None if v is None else (v-b)/b*1e4
    if all(m[t] is not None for t in T): W.append((S,1 if e>=b else 0,m))
print(f"tam pencere: {len(W)}\n")
# 1) her t icin: marj -> sonuc dagilimi. sigma_kalan'i AMPIRIK kalibre et.
print("### ADIL DEGER KALIBRASYONU (yariya bol: 1. yari kalibre, 2. yari TEST)")
n=len(W); A=W[:n//2]; B=W[n//2:]
print(f"  kalibrasyon {len(A)} pencere | test {len(B)} pencere\n")
def norm(x): return 0.5*(1+math.erf(x/math.sqrt(2)))
for t in T:
    # kalibrasyon: sonuc=Up olanlarin marj dagiliminden sigma tahmini
    mar=[m[t] for _,_,m in A]
    s=ist.pstdev([m[t] for _,k,m in A if True]) or 1.0
    # en iyi sigma'yi log-skor ile ara
    en=None
    for sg in [s*x for x in (0.3,0.5,0.7,0.9,1.1,1.4,1.8,2.5,3.5)]:
        ll=0.0
        for _,k,m in A:
            p=min(max(norm(m[t]/sg),1e-6),1-1e-6)
            ll+= math.log(p) if k==1 else math.log(1-p)
        if en is None or ll>en[1]: en=(sg,ll)
    sg=en[0]
    # TEST yarisinda kalibrasyon: tahmin kovalarina gore gercek oran
    kova=collections.defaultdict(lambda:[0,0])
    for _,k,m in B:
        p=norm(m[t]/sg)
        kv=min(int(p*10),9)
        kova[kv][0]+=1; kova[kv][1]+=k
    sat=f"  t={t:>3} sigma={sg:>6.2f}bp | "
    for kv in range(10):
        c,w=kova[kv]
        sat+=f"{(100*w/c if c>=20 else -1):>5.0f}" if c>=20 else "    ."
    print(sat)
print("        tahmin kovasi:   5%   15%   25%   35%   45%   55%   65%   75%   85%   95%")
print("        (satirlar gercek kazanma % — kalibre ise artan ve kova ile uyumlu olmali)")
