#!/usr/bin/env python3
"""Odenen Chainlink Data Streams WS'ini DOGRUDAN kaydeder (Polymarket relay'ini atlar).
Calisan tape'e dokunmaz; ayri dosyaya yazar. Sadece kayit."""
import asyncio, hmac, hashlib, time, json, os, sys, gzip
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cl_client, websockets
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'
FEEDS={'spot':'0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8',
       'twap30':'0x0002e6b03af5a87b65f4c5c0c8eaf6027e4156f467cd16bdcf8a5b4347f9c087',
       'twap60':'0x0002ee6757e8822c00d273bc340fc24c9cafe123a4ff2ea1dbdb31944bc7d95f'}
R={v:k for k,v in FEEDS.items()}
OUT='/home/taygun/Masaüstü/polymarket/data/tape_cl_direct'
os.makedirs(OUT, exist_ok=True)
def i192(x):
    v=int(x,16); return v-(1<<256) if v>=(1<<255) else v
def dec(b):
    h=b[2:] if b.startswith('0x') else b
    w=[h[i:i+64] for i in range(0,len(h),64)]; x=w[int(w[3],16)//32+1:]
    return '0x'+x[0], int(x[2],16), i192(x[6])/1e18
def hdrs(path):
    cid,sec=cl_client._creds()
    ts=str(int(time.time()*1000)); bh=hashlib.sha256(b'').hexdigest()
    sig=hmac.new(sec.encode(), f"GET {path} {bh} {cid} {ts}".encode(), hashlib.sha256).hexdigest()
    return {'Authorization':cid,'X-Authorization-Timestamp':ts,'X-Authorization-Signature-SHA256':sig,'User-Agent':UA}
async def run():
    path="/api/v1/ws?feedIDs="+",".join(FEEDS.values())
    fh=None; cur=None
    while True:
        try:
            async with websockets.connect("wss://ws.dataengine.chain.link"+path,
                                          additional_headers=hdrs(path), open_timeout=25,
                                          ping_interval=20, ping_timeout=20) as ws:
                async for m in ws:
                    rcv=int(time.time()*1000)
                    try:
                        d=json.loads(m); rp=d.get('report') or d
                        fr=rp.get('fullReport')
                        if not fr: continue
                        fid,obs,px=dec(fr)
                    except Exception: continue
                    hr=time.strftime('%Y%m%d_%H', time.gmtime(rcv/1000))
                    if hr!=cur:
                        if fh: fh.close()
                        fh=gzip.open(f'{OUT}/cld_{hr}.jsonl.gz','at'); cur=hr
                    fh.write(json.dumps({'f':R.get(fid,fid),'obs':obs,'px':px,'rcv':rcv})+'\n')
                    fh.flush()   # 09-19 19:40Z: her yazimda flush (eski kural rastgele/garantisizdi, 5+ dk diske inmiyordu)
        except Exception as e:
            print('yeniden baglaniyor:', str(e)[:120], flush=True)
            await asyncio.sleep(3)
asyncio.run(run())
