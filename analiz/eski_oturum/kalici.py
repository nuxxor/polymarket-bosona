import json,statistics as ist,random
SP='/tmp/claude-1000/-home-taygun-Masa-st--polymarket/b4197893-bd19-4ee9-9e9a-ddd5e06151af/scratchpad'
B={int(k):v for k,v in json.load(open(SP+'/btc_sn.json')).items()}
def rej(S):
    s=[B[t] for t in range(S,S+301) if t in B]
    if len(s)<200: return None
    rng=max(s)-min(s); 
    if rng<=0: return None
    return (abs(s[-1]-s[0])/rng, 1e4*rng/s[0])

# 1) rejim KENDI ICINDE kalici mi? (tum 5dk pencereler, bot log'undan bagimsiz)
S0=(min(B)//300+1)*300; SN=(max(B)//300-1)*300
seri=[]
for S in range(S0,SN,300):
    r=rej(S)
    if r: seri.append((S,)+r)
print(f"ardisik pencere: {len(seri)}")
for ad,i in (("verim",1),("oynaklik",2)):
    x=[a[i] for a in seri]
    prev=[(x[j-1],x[j]) for j in range(1,len(x))]
    mx=ist.median(x)
    # ust-ust gecis olasiligi
    uu=sum(1 for p,c in prev if p>=mx and c>=mx); u=sum(1 for p,c in prev if p>=mx)
    aa=sum(1 for p,c in prev if p<mx and c<mx);  a=sum(1 for p,c in prev if p<mx)
    mp=ist.mean(x); sp=ist.pstdev(x)
    rho=sum((p-mp)*(c-mp) for p,c in prev)/len(prev)/(sp*sp) if sp>0 else 0
    print(f"  {ad:9s} medyan {mx:6.2f} | ardisik korelasyon rho={rho:+.3f} | onceki UST->UST %{100*uu/max(1,u):.0f} | onceki ALT->ALT %{100*aa/max(1,a):.0f}  (sans %50)")

# 2) ONCEKI pencereyle kapilama: bot pencerelerinde test
k=[json.loads(l) for l in open('data/analysis/pm_merdiven_ab_20260918_v5/LOG_ab.jsonl') if l.strip().startswith('{')]
c=[x for x in k if x['k']=='COZULDU' and x.get('kol')]
mv=ist.median(a[1] for a in seri)
W=[]
for r in c:
    o=rej(r['S']-300); n=rej(r['S'])
    if not o or not n: continue
    W.append(dict(kol=r['kol'],pnl=r['pnl'],pay=sum(e['pay'] for e in r['emirler']),onceki_verim=o[0],simdi_verim=n[0]))
print(f"\n### ONCEKI PENCEREYE GORE KAPI (n={len(W)}) — gercekten onden bilinebilir sinyal")
for kol in ('A','B'):
    K=[x for x in W if x['kol']==kol]
    for ad,f in ((f"onceki GIDIP-GELDI (<{mv:.2f})",lambda x:x['onceki_verim']<mv),(f"onceki TREND (>={mv:.2f})",lambda x:x['onceki_verim']>=mv)):
        S=[x for x in K if f(x)]; p=sum(x['pay'] for x in S)
        if not S: continue
        print(f"  {kol} {ad:28s} {len(S):3d} pen {sum(x['pnl'] for x in S):+7.2f}$  {100*sum(x['pnl'] for x in S)/max(1e-9,p):+6.2f} kr/pay")
