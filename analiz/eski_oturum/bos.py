import json,urllib.request,collections,time
UA={'User-Agent':'Mozilla/5.0'}
A='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
def g(u,t=25):
    with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t) as r: return json.loads(r.read())
tr=[];off=0
while off<6000:
    b=g(f"https://data-api.polymarket.com/trades?user={A}&limit=500&offset={off}&takerOnly=false")
    if not b: break
    tr+=b; off+=len(b)
    if len(b)<500: break
print("toplam islem:",len(tr))
# sadece 5m updown
w=collections.defaultdict(list)
for x in tr:
    s=x.get('slug') or ''
    if '-updown-5m-' not in s: continue
    try: S=int(s.rsplit('-',1)[1])
    except: continue
    w[s].append({'S':S,'t':int(x.get('timestamp') or 0)-S,'oi':int(x['outcomeIndex']),
                 'side':x.get('side'),'p':float(x['price']),'q':float(x['size'])})
print("5m pencere:",len(w))
lastS=max(v[0]['S'] for v in w.values())
print("en son pencere:",lastS, time.strftime('%Y-%m-%d %H:%M UTC',time.gmtime(lastS)))
