#!/usr/bin/env python3
"""AYNA TESTI: bosona'nin maker alim yaptigi HER (pencere, token, fiyat) noktasina
bizim durust kuyruk motorumuzu koy. Kazanan ayni pencerede AYNI oldugu icin,
kazanma orani farki ancak DOLUM KUMESI farkindan gelebilir.

Uc olasi sonuc:
  - ayni yerlerde doluyoruz ve kenar onlarinkine yakin -> fark FIYAT SECIMINDE, kopyalanabilir
  - dolamiyoruz                                        -> fark KUYRUK POZISYONUNDA
  - doluyoruz ama kaybediyoruz                         -> fark ZAMANLAMADA
"""
import json, glob, collections, statistics as ist
D='/home/taygun/Masaüstü/polymarket/data/analysis/pm_delta_tarama_20260916_v1'
KLIP=5.0; T_REST=2.0; T_IPTAL=297.0
DOL=json.load(open('BOSONA_DOLUM.json'))
KAZ=json.load(open(f'{D}/kazanan.json'))
EV={}
for f in sorted(glob.glob(f'{D}/ev/*.json')): EV.update(json.load(open(f)))

def merdiven(w,oi,t):
    en=None
    for (ts,o,b) in w['snap']:
        if o!=oi or ts>t: continue
        if en is None or ts>en[0]: en=(ts,b)
    if en is None: return None
    lad={round(px,2):sz for px,sz in en[1]}
    for (ts,o,px,sz,sd) in w['pc']:
        if o!=oi or sd!='BUY' or not (en[0]<ts<=t): continue
        px=round(px,2)
        if sz<=0: lad.pop(px,None)
        else: lad[px]=sz
    return lad

def tuket(w,oi,p,t0,t1):
    s=0.0
    for (t,o,px,sz,side) in w['tr']:
        if not (t0<t<=t1): continue
        if o==oi and side=='SELL' and px<=p+1e-9: s+=sz
        elif o!=oi and side=='BUY' and px>=1-p-1e-9: s+=sz
    return s

BQ=BC=BW=0.0            # bosona: pay, maliyet, kazanan pay
UQ=UC=UW=0.0            # bizim ayna
n_nokta=0; n_dolduk=0; atla=collections.Counter()
det=[]
for an,dl in DOL.items():
    w=EV.get(an); kz=KAZ.get(an)
    if not w or kz is None: atla['pencere_yok']+=1; continue
    # bosona'nin maker alimlarini (token, fiyat) noktalarina indir
    nk=collections.defaultdict(float)
    for d in dl:
        if not d['maker']: continue
        nk[(d['oi'],round(d['p'],2))]+=d['q']
    if not nk: continue
    for (oi,p),q in nk.items():
        BQ+=q; BC+=q*p; BW+= q if oi==kz else 0.0
        lad=merdiven(w,oi,T_REST)
        if lad is None: atla['defter_yok']+=1; continue
        n_nokta+=1
        Q=lad.get(p,0.0)
        dol=min(KLIP,max(0.0,tuket(w,oi,p,T_REST,T_IPTAL)-Q))
        if dol>0: n_dolduk+=1
        UQ+=dol; UC+=dol*p; UW+= dol if oi==kz else 0.0
        det.append({'an':an,'oi':oi,'p':p,'bos_q':q,'Q':Q,'biz':dol,'kazandi':int(oi==kz)})
print(f"nokta (pencere x token x fiyat): {n_nokta} | atlanan: {dict(atla)}")
print(f"bu noktalarda bizim dolum oranimiz: {n_dolduk}/{n_nokta} = %{100*n_dolduk/max(n_nokta,1):.1f}\n")
def sat(ad,Q,C,W):
    if Q<=0: print(f"  {ad}: pay yok"); return
    print(f"  {ad:34} pay {Q:8,.0f} | odedigi {100*C/Q:5.2f} kr | kazanma %{100*W/Q:5.2f} | kenar {100*(W/Q-C/Q):+6.2f} kr/pay")
print("AYNI (pencere, token, fiyat) NOKTALARINDA:")
sat("bosona (gercek maker dolumu)",BQ,BC,BW)
sat("BIZ (ayna, motor)",UQ,UC,UW)
json.dump(det,open('AYNA.json','w'))
print()
# kuyrugun rolu
Qs=sorted(d['Q'] for d in det)
print(f"bu noktalardaki kuyruk Q: medyan {ist.median(Qs):.0f} | p25 {Qs[len(Qs)//4]:.0f} | p75 {Qs[3*len(Qs)//4]:.0f}")
dolan=[d for d in det if d['biz']>0]; bos=[d for d in det if d['biz']<=0]
if dolan and bos:
    print(f"dolduklarimizda Q medyan {ist.median([d['Q'] for d in dolan]):.0f}, "
          f"dolmadiklarimizda {ist.median([d['Q'] for d in bos]):.0f}")
    print(f"dolduklarimizin kazanma orani %{100*sum(d['kazandi'] for d in dolan)/len(dolan):.1f} | "
          f"dolmadiklarimizin %{100*sum(d['kazandi'] for d in bos)/len(bos):.1f}")
