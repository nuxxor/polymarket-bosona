import json,statistics as ist,random
SP='/tmp/claude-1000/-home-taygun-Masa-st--polymarket/b4197893-bd19-4ee9-9e9a-ddd5e06151af/scratchpad'
B={int(k):v for k,v in json.load(open(SP+'/btc_sn.json')).items()}
def rej(S):
    s=[B[t] for t in range(S,S+301) if t in B]
    if len(s)<200: return None
    rng=max(s)-min(s)
    if rng<=0: return None
    return (abs(s[-1]-s[0])/rng, 1e4*rng/s[0])
k=[json.loads(l) for l in open('data/analysis/pm_merdiven_ab_20260918_v5/LOG_ab.jsonl') if l.strip().startswith('{')]
c=[x for x in k if x['k']=='COZULDU' and x.get('kol')]
W=[]
for r in c:
    o=rej(r['S']-300)
    if not o: continue
    W.append(dict(kol=r['kol'],pnl=r['pnl'],pay=sum(e['pay'] for e in r['emirler']),onc_oyn=o[1]))
mo=ist.median(x['onc_oyn'] for x in W)
print(f"### ONCEKI PENCERE OYNAKLIGI kapisi (medyan {mo:.1f} bps) — oynaklik %79 kalici, yani ONDEN BILINEBILIR\n")
def oz(ad,S):
    if not S: print(f"  {ad:34s}  yok"); return
    p=[x['pnl'] for x in S]; s=sum(x['pay'] for x in S)
    r2=random.Random(5); bp=sorted(sum(p[r2.randrange(len(p))] for _ in p) for _ in range(4000))
    print(f"  {ad:34s} {len(S):3d} pen {sum(p):+7.2f}$ {100*sum(p)/max(1e-9,s):+6.2f} kr/pay  %{100*sum(1 for y in p if y>0)/len(p):.0f} artida  GA95[{bp[100]:+.0f},{bp[3900]:+.0f}]")
for kol in ('A','B'):
    K=[x for x in W if x['kol']==kol]
    oz(f"{kol}  TUMU",K)
    oz(f"{kol}  onceki SAKIN  (<{mo:.0f}bps)",[x for x in K if x['onc_oyn']<mo])
    oz(f"{kol}  onceki OYNAK (>={mo:.0f}bps)",[x for x in K if x['onc_oyn']>=mo])
    print()
print("### KAPILI KARMA STRATEJI (onceki oynaksa A, sakinse B)")
mix=[x for x in W if (x['kol']=='A' and x['onc_oyn']>=mo) or (x['kol']=='B' and x['onc_oyn']<mo)]
oz("  A@oynak + B@sakin",mix)
oz("  TERSI (A@sakin + B@oynak)",[x for x in W if (x['kol']=='A' and x['onc_oyn']<mo) or (x['kol']=='B' and x['onc_oyn']>=mo)])
