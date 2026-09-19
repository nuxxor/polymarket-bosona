#!/usr/bin/env python3
"""bosona'nin MAKER alim dolumlari + bizim tape penceremizle kesisimi."""
import json, urllib.request, collections, os, glob
UA={'User-Agent':'Mozilla/5.0'}
A='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
def g(u,t=30):
    with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t) as r: return json.loads(r.read())
def cek(to,n=6000):
    tr=[];off=0
    while off<n:
        b=g(f"https://data-api.polymarket.com/trades?user={A}&limit=500&offset={off}&takerOnly={to}")
        if not b: break
        tr+=b; off+=len(b)
        if len(b)<500: break
    return tr
if os.path.exists('bos_tum.json'):
    tum=json.load(open('bos_tum.json')); tak=json.load(open('bos_tak.json'))
else:
    tum=cek('false'); tak=cek('true')
    json.dump(tum,open('bos_tum.json','w')); json.dump(tak,open('bos_tak.json','w'))
ana=lambda x:(x.get('transactionHash'),str(x.get('outcomeIndex')),x.get('side'),str(x.get('size')))
takset={ana(x) for x in tak}
print(f"tum {len(tum)}, taker {len(tak)}")

EVk=set()
for f in glob.glob('/home/taygun/Masaüstü/polymarket/data/analysis/pm_delta_tarama_20260916_v1/ev/*.json'):
    EVk |= set(json.load(open(f)).keys())
print(f"tape penceresi: {len(EVk)}")

out=collections.defaultdict(list)
n_m=n_t=0
for x in tum:
    s=x.get('slug') or ''
    if '-updown-5m-' not in s: continue
    parc=s.split('-'); sym=parc[0]; S=parc[-1]
    an=f"{sym}|{S}"
    if an not in EVk: continue
    maker = ana(x) not in takset
    if x.get('side')!='BUY': continue
    if maker: n_m+=1
    else: n_t+=1
    out[an].append({'oi':int(x['outcomeIndex']),'p':float(x['price']),'q':float(x['size']),
                    't':int(x.get('timestamp') or 0)-int(S),'maker':maker})
json.dump(out,open('BOSONA_DOLUM.json','w'))
print(f"kesisen pencere: {len(out)} | bosona ALIM dolumu: maker {n_m}, taker {n_t}")
pay_m=sum(d['q'] for v in out.values() for d in v if d['maker'])
pay_t=sum(d['q'] for v in out.values() for d in v if not d['maker'])
print(f"pay: maker {pay_m:,.0f} (%{100*pay_m/max(pay_m+pay_t,1):.1f}) | taker {pay_t:,.0f}")
