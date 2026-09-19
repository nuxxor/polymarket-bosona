import json,urllib.request,concurrent.futures as cf
UA={'User-Agent':'Mozilla/5.0'}
cache=json.load(open('win_cache.json'))
todo=[s for s,v in cache.items() if v is None]
print("eksik:",len(todo))
def kaz(s):
    sym,_,kad,S=s.split('-')
    for u in (f"https://gamma-api.polymarket.com/events?slug={sym}-updown-{kad}-{S}",
              f"https://gamma-api.polymarket.com/markets?slug={s}"):
        try:
            d=json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=20).read())
            ms=[m for e in d for m in e.get('markets',[])] if u.endswith(S) else d
            for m in ms:
                if m.get('slug')!=s: continue
                op=[float(z) for z in json.loads(m.get('outcomePrices') or '[]')]
                if op==[1.0,0.0]: return s,0
                if op==[0.0,1.0]: return s,1
        except Exception as ex: pass
    return s,None
with cf.ThreadPoolExecutor(10) as ex:
    for s,k in ex.map(kaz,todo): cache[s]=k
json.dump(cache,open('win_cache.json','w'))
print("etiketli:",sum(1 for v in cache.values() if v is not None),"/",len(cache))
