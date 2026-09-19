import sys,json,time
from websockets.sync.client import connect
d=[json.loads(l) for l in open('LOG_ab_kuruL.jsonl') if '"pencere"' in l][-1]
toks=d['tokens']
t0=time.time(); n=0; first=None
with connect("wss://ws-subscriptions-clob.polymarket.com/ws/market",open_timeout=8,close_timeout=2,max_queue=4096) as ws:
    print("baglandi",round((time.time()-t0)*1000),"ms")
    ws.send(json.dumps({"type":"subscribe","channel":"market","assets_ids":toks}))
    while time.time()-t0<8:
        try: raw=ws.recv(timeout=1.0)
        except TimeoutError: continue
        n+=1
        if first is None: first=round((time.time()-t0)*1000)
print("8 sn'de mesaj:",n,"| ilk mesaj",first,"ms")
