import json,urllib.request,collections,os
UA={'User-Agent':'Mozilla/5.0'}
A='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
def g(u,t=25):
    with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t) as r: return json.loads(r.read())
if os.path.exists('bos_tr.json'): tr=json.load(open('bos_tr.json'))
else:
    tr=[];off=0
    while off<6000:
        b=g(f"https://data-api.polymarket.com/trades?user={A}&limit=500&offset={off}&takerOnly=false")
        if not b: break
        tr+=b; off+=len(b)
        if len(b)<500: break
    json.dump(tr,open('bos_tr.json','w'))
W=collections.defaultdict(list)
for x in tr:
    s=x.get('slug') or ''
    if '-updown-5m-' not in s: continue
    S=int(s.rsplit('-',1)[1])
    W[s].append({'S':S,'t':int(x.get('timestamp') or 0)-S,'oi':int(x['outcomeIndex']),
                 'side':x.get('side'),'p':float(x['price']),'q':float(x['size'])})
for s in W: W[s].sort(key=lambda z:z['t'])

# 1) Zaman x fiyat dagilimi: ALIMLAR
kova=collections.Counter(); hac=collections.Counter()
for s,v in W.items():
    for x in v:
        if x['side']!='BUY': continue
        tb = 'erken 0-60' if x['t']<60 else ('orta 60-200' if x['t']<200 else ('gec 200-270' if x['t']<270 else 'SON 270-300'))
        pb = '<0.50' if x['p']<0.5 else ('0.50-0.70' if x['p']<0.7 else ('0.70-0.90' if x['p']<0.9 else '>=0.90'))
        kova[(tb,pb)]+=1; hac[(tb,pb)]+=x['q']
print("BOSONA ALIMLARI — zaman x fiyat (adet / pay)")
tbs=['erken 0-60','orta 60-200','gec 200-270','SON 270-300']; pbs=['<0.50','0.50-0.70','0.70-0.90','>=0.90']
print(f"{'':14}"+"".join(f"{p:>18}" for p in pbs))
for tb in tbs:
    print(f"{tb:14}"+"".join(f"{kova[(tb,p)]:>8} / {hac[(tb,p)]:>7.0f}" for p in pbs))

# 2) GEC PAHALI ALIM = cift tamamlama mi?
print("\nGEC (t>=200) ve PAHALI (p>=0.65) ALIMLAR — o ana kadarki envantere gore")
tam=0; ekle=0; yeni=0; det=[]
for s,v in W.items():
    env={0:0.0,1:0.0}
    for x in v:
        if x['t']>=200 and x['p']>=0.65 and x['side']=='BUY':
            oth=1-x['oi']
            if env[oth]>env[x['oi']]+1e-9:
                tam+=1; tip='CIFT_TAMAMLAMA'
            elif env[x['oi']]>0: ekle+=1; tip='ayni tarafa ekle'
            else: yeni+=1; tip='sifirdan yeni'
            det.append((s,x['t'],x['oi'],x['p'],x['q'],dict(env),tip))
        q=x['q'] if x['side']=='BUY' else -x['q']
        env[x['oi']]+=q
print(f"  cift tamamlama : {tam}")
print(f"  ayni tarafa ekle: {ekle}")
print(f"  sifirdan yeni  : {yeni}")
json.dump([[d[0],d[1],d[2],d[3],d[4],{str(k):w for k,w in d[5].items()},d[6]] for d in det],open('bos_gec.json','w'))
print("\nornek 12:")
for d in det[:12]:
    print(f"  {d[0][-14:]} t={d[1]:3}s oi={d[2]} p={d[3]:.2f} pay={d[4]:6.1f} envanter={d[5]} -> {d[6]}")
