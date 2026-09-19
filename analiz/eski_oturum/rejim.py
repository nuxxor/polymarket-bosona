import json,statistics as ist,random
B=json.load(open('/tmp/claude-1000/-home-taygun-Masa-st--polymarket/b4197893-bd19-4ee9-9e9a-ddd5e06151af/scratchpad/btc_sn.json'))
B={int(k):v for k,v in B.items()}
L='data/analysis/pm_merdiven_ab_20260918_v5/LOG_ab.jsonl'
k=[json.loads(l) for l in open(L) if l.strip().startswith('{')]
c=[x for x in k if x['k']=='COZULDU' and x.get('kol')]

def rejim(S):
    ser=[B[t] for t in range(S,S+301) if t in B]
    if len(ser)<200: return None
    rng=max(ser)-min(ser); net=abs(ser[-1]-ser[0])
    if rng<=0: return None
    return dict(n=len(ser), rng_bps=1e4*rng/ser[0], net_bps=1e4*net/ser[0],
                verim=net/rng, yon=(1 if ser[-1]>ser[0] else -1))

W=[]
for r in c:
    g=rejim(r['S'])
    if not g: continue
    pay=sum(e['pay'] for e in r['emirler'])
    W.append(dict(kol=r['kol'],S=r['S'],pnl=r['pnl'],pay=pay,**g))

print(f"kapsanan pencere: {len(W)}/{len(c)}")
vm=ist.median(x['verim'] for x in W); rm=ist.median(x['rng_bps'] for x in W)
print(f"verim medyan {vm:.2f} | oynaklik medyan {rm:.1f} bps\n")

def oz(ad,L):
    if not L: print(f"  {ad:26s}  yok"); return
    p=[x['pnl'] for x in L]; s=sum(x['pay'] for x in L)
    r2=random.Random(11); bp=sorted(sum(p[r2.randrange(len(p))] for _ in p) for _ in range(4000)) if len(p)>3 else None
    ga=f"GA95[{bp[100]:+.0f},{bp[3900]:+.0f}]" if bp else ""
    print(f"  {ad:26s} {len(L):3d} pen  {sum(p):+7.2f}$  {100*sum(p)/max(1e-9,s):+6.2f} kr/pay  %{100*sum(1 for x in p if x>0)/len(p):.0f} artida  {ga}")

for kol in ('A','B'):
    K=[x for x in W if x['kol']==kol]
    print(f"### KOL {kol}  ({len(K)} pencere)")
    oz("TUMU",K)
    oz(f"GIDIP GELDI (verim<{vm:.2f})",[x for x in K if x['verim']<vm])
    oz(f"TREND      (verim>={vm:.2f})",[x for x in K if x['verim']>=vm])
    oz(f"SAKIN (rng<{rm:.0f}bps)",[x for x in K if x['rng_bps']<rm])
    oz(f"OYNAK (rng>={rm:.0f}bps)",[x for x in K if x['rng_bps']>=rm])
    print()

print("### 4 HUCRE (verim x oynaklik) — kol basina kr/pay")
print(f"  {'hucre':24s} {'A':>18s} {'B':>18s}")
for vlab,vf in (("gidip-geldi",lambda x:x['verim']<vm),("trend",lambda x:x['verim']>=vm)):
    for olab,of in (("sakin",lambda x:x['rng_bps']<rm),("oynak",lambda x:x['rng_bps']>=rm)):
        row=f"  {vlab+' / '+olab:24s}"
        for kol in ('A','B'):
            S=[x for x in W if x['kol']==kol and vf(x) and of(x)]
            s=sum(x['pay'] for x in S)
            row+=f" {(f'{100*sum(x[chr(112)+chr(110)+chr(108)] for x in S)/s:+6.2f} (n{len(S)})' if s>0 else '   -    '):>18s}"
        print(row)
