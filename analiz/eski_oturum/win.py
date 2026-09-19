import json,urllib.request,collections,concurrent.futures as cf,os
UA={'User-Agent':'Mozilla/5.0'}
tr=json.load(open('bos_tr.json'))
slugs=sorted({x['slug'] for x in tr if '-updown-5m-' in (x.get('slug') or '')})
print("pencere:",len(slugs))
cache=json.load(open('win_cache.json')) if os.path.exists('win_cache.json') else {}
def kaz(s):
    if s in cache: return s,cache[s]
    sym,_,kad,S=s.split('-')
    u=f"https://gamma-api.polymarket.com/events?slug={sym}-updown-{kad}-{S}"
    try:
        for e in urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=15).read().decode() and json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=15).read()):
            for m in e.get('markets',[]):
                if m.get('slug')!=s or not m.get('closed'): continue
                op=[float(z) for z in json.loads(m.get('outcomePrices') or '[]')]
                if op==[1.0,0.0]: return s,0
                if op==[0.0,1.0]: return s,1
    except Exception: pass
    return s,None
todo=[s for s in slugs if s not in cache]
with cf.ThreadPoolExecutor(10) as ex:
    for i,(s,k) in enumerate(ex.map(kaz,todo)):
        cache[s]=k
        if i%100==0: print(" ",i,flush=True)
json.dump(cache,open('win_cache.json','w'))
print("etiketli:",sum(1 for v in cache.values() if v is not None),"/",len(slugs))
