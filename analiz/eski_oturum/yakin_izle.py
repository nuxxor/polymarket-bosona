import json,urllib.request,time,os,sys
D='/home/taygun/Masaüstü/polymarket/data/analysis/pm_merdiven_ab_20260918_v5'
UA={'User-Agent':'python-urllib/3'}
BOS='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
def jget(u,t=20):
    with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t) as r: return json.loads(r.read())
def logk():
    return [json.loads(l) for l in open(f'{D}/LOG_ab.jsonl') if l.strip().startswith('{')]
def vol(S):
    try:
        K={int(c[0]//1000):(float(c[1]),float(c[2]),float(c[3]))
           for c in jget("https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=1m&limit=60")}
        m=[K[t] for t in range(S-300,S,60) if t in K]
        return 1e4*(max(x[1] for x in m)-min(x[2] for x in m))/m[0][0] if len(m)==5 else None
    except Exception: return None
def bosona(S):
    """S penceresindeki bosona dolumlari. Kamu akisi gecikmeli -> gec cagir."""
    try:
        tr=[];off=0
        while off<=1500:
            d=jget(f"https://data-api.polymarket.com/trades?user={BOS}&limit=500&offset={off}")
            if not d: break
            tr+=d
            if len(d)<500 or min(x['timestamp'] for x in d)<S-60: break
            off+=500; time.sleep(0.4)
        return [x for x in tr if x.get('slug')==f'btc-updown-5m-{S}']
    except Exception as e: return None
def taraf(q,co,kaz):
    m=min(q[0],q[1]); pay=q[0]+q[1]
    cm=(sum((co[oi]/q[oi])*m for oi in (0,1) if q[oi]>0)*2/(2*m)) if m>0 else None
    fz=0 if q[0]>q[1] else 1; nf=abs(q[0]-q[1])
    uf=(co[fz]/q[fz]) if (nf>0 and q[fz]>0) else None
    pnl=q[kaz]-(co[0]+co[1])
    return m,cm,nf,uf,('Up' if fz==0 else 'Down'),pnl,pay

gor=set(); N=int(sys.argv[1]) if len(sys.argv)>1 else 8; done=0
bas=time.time()
while done<N and time.time()-bas<4200:
    try:
        k=logk()
        KAPI={x['S']:x for x in k if x['k']=='KAPI'}
        for r in [x for x in k if x['k']=='COZULDU' and x.get('kol')]:
            S=r['S']
            if S in gor or S<1789755300: continue
            gor.add(S); done+=1
            q={0:0.0,1:0.0}; co={0:0.0,1:0.0}; dt=[]
            for e in r['emirler']:
                if e['pay']>0:
                    q[e['oi']]+=e['pay']; co[e['oi']]+=e['pay']*e['p']
                    dt.append(('Up' if e['oi']==0 else 'Dn')+f"{e['pay']:.0f}@{e['p']:.2f}")
            m,cm,nf,uf,fz,pnl,pay=taraf(q,co,r['kazanan'])
            g=KAPI.get(S,{})
            kz='Up' if r['kazanan']==0 else 'Down'
            print(f"--- S={S} {time.strftime('%H:%M',time.gmtime(S))}Z  vol={g.get('bps','?')}bps KAPI->{r['kol']}  kazanan={kz}")
            print(f"    BIZ    {pay:5.0f} pay | cift {2*m:4.0f}@{(cm or 0):.3f} | essiz {nf:4.0f} {fz}@{(uf or 0):.3f} | PnL {pnl:+6.2f}$ ({100*pnl/pay if pay else 0:+5.1f} kr/pay)")
            print(f"           dolumlar: {' '.join(dt) if dt else 'YOK'}")
            # bosona: 2 pencere geriden
            Sb=S-600
            bt=bosona(Sb)
            if bt is None: print(f"    BOSONA S={Sb}: akis alinamadi")
            elif not bt: print(f"    BOSONA S={Sb}: gorunur dolum yok")
            else:
                KAZ={x['S']:x['kazanan'] for x in k if x['k']=='COZULDU'}
                bq={0:0.0,1:0.0}; bc={0:0.0,1:0.0}
                for x in bt:
                    oi=x['outcomeIndex']; sz=x['size']*(1 if x['side']=='BUY' else -1)
                    bq[oi]+=sz; bc[oi]+=sz*x['price']
                if Sb in KAZ and bq[0]+bq[1]>0:
                    bm,bcm,bnf,buf,bfz,bpnl,bpay=taraf(bq,bc,KAZ[Sb])
                    print(f"    BOSONA {bpay:5.0f} pay | cift {2*bm:4.0f}@{(bcm or 0):.3f} | essiz {bnf:4.0f} {bfz}@{(buf or 0):.3f} | PnL {bpnl:+7.2f}$ ({100*bpnl/bpay:+5.1f} kr/pay)  [{len(bt)} islem]")
                else: print(f"    BOSONA S={Sb}: {len(bt)} islem, pencere sonucu yok")
    except Exception as e:
        print("[izleyici hata]",str(e)[:90])
    time.sleep(20)
print(f"=== 8 PENCERE TAMAM ({done} pencere izlendi) ===")
