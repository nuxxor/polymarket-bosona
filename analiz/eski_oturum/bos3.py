import json,collections
tr=json.load(open('bos_tr.json')); K=json.load(open('win_cache.json'))
W=collections.defaultdict(list)
for x in tr:
    s=x.get('slug') or ''
    if '-updown-5m-' not in s or K.get(s) is None: continue
    S=int(s.rsplit('-',1)[1])
    W[s].append({'t':int(x.get('timestamp') or 0)-S,'oi':int(x['outcomeIndex']),
                 'side':x.get('side'),'p':float(x['price']),'q':float(x['size'])})
for s in W: W[s].sort(key=lambda z:z['t'])
def pnl(s,x):
    w=K[s]; v=(1.0 if x['oi']==w else 0.0)-x['p']
    return x['q']*(v if x['side']=='BUY' else -v)
tot=sum(pnl(s,x) for s,v in W.items() for x in v)
pay=sum(x['q'] for s,v in W.items() for x in v)
print(f"BOSONA {len(W)} pencere, {pay:,.0f} pay, TOPLAM PnL ${tot:+,.0f} = {100*tot/pay:+.2f} kr/pay\n")

tbs=[('erken 0-60',0,60),('orta 60-200',60,200),('gec 200-270',200,270),('SON 270-300',270,10**9)]
pbs=[('<0.50',0,.5),('0.50-0.70',.5,.7),('0.70-0.90',.7,.9),('>=0.90',.9,2)]
agg=collections.defaultdict(lambda:[0.0,0.0,0])
for s,v in W.items():
    for x in v:
        if x['side']!='BUY': continue
        tb=next(n for n,a,b in tbs if a<=x['t']<b); pb=next(n for n,a,b in pbs if a<=x['p']<b)
        a=agg[(tb,pb)]; a[0]+=pnl(s,x); a[1]+=x['q']; a[2]+=1
print("ALIMLARIN KENARI (kurus/pay) — zaman x fiyat   [pay adedi]")
print(f"{'':14}"+"".join(f"{p:>20}" for p,_,_ in pbs))
for tb,_,_ in tbs:
    row=f"{tb:14}"
    for pb,_,_ in pbs:
        a=agg[(tb,pb)]
        row+= f"{100*a[0]/a[1]:>+9.2f} [{a[1]:>7.0f}]" if a[1]>0 else f"{'-':>20}"
    print(row)

print("\nGEC+PAHALI (t>=200, p>=0.65) ALIMLAR — tipe gore")
typ=collections.defaultdict(lambda:[0.0,0.0,0,0])
for s,v in W.items():
    env={0:0.0,1:0.0}
    for x in v:
        if x['t']>=200 and x['p']>=0.65 and x['side']=='BUY':
            oth=1-x['oi']
            tip=('CIFT TAMAMLAMA' if env[oth]>env[x['oi']]+1e-9 else
                 ('ayni tarafa ekle' if env[x['oi']]>0 else 'sifirdan yeni'))
            a=typ[tip]; a[0]+=pnl(s,x); a[1]+=x['q']; a[2]+=1; a[3]+= (1 if x['oi']==K[s] else 0)
        env[x['oi']] += x['q'] if x['side']=='BUY' else -x['q']
for tip,a in sorted(typ.items()):
    print(f"  {tip:18} {a[2]:4} islem  {a[1]:8.0f} pay  ${a[0]:+9.2f}  {100*a[0]/a[1]:+6.2f} kr/pay  kazanan tarafi tutturma %{100*a[3]/a[2]:.0f}")

print("\nTEK TARAFLI KALAN ENVANTER — bosona pencere sonunda ne yapiyor?")
dek=collections.Counter(); kaz_=collections.Counter()
for s,v in W.items():
    env={0:0.0,1:0.0}
    for x in v: env[x['oi']] += x['q'] if x['side']=='BUY' else -x['q']
    fz=env[0]-env[1]
    if abs(fz)<1: dek['DENGE (cift tam)']+=1; continue
    at=0 if fz>0 else 1
    dek['artan var']+=1
    if at==K[s]: kaz_['artan KAZANDI']+=1
    else: kaz_['artan KAYBETTI']+=1
print(" ",dict(dek)," ",dict(kaz_))
n=sum(kaz_.values())
if n: print(f"  -> artan envanterin kazanma orani: %{100*kaz_['artan KAZANDI']/n:.1f}  (bizimki 0/4)")
