#!/usr/bin/env python3
"""Chainlink Streams tape okuyucu: cok-uyeli / yarim kesilmis gz dosyalarini toleransli okur.
Kullanim: cl_oku.py <dosya.gz> [--son N]  ->  JSON satirlari (f, obs, px, rcv)."""
import sys,zlib,json
def oku(p):
    raw=open(p,'rb').read(); pos=0; out=b''
    while pos<len(raw):
        d=zlib.decompressobj(16+zlib.MAX_WBITS)
        try: out+=d.decompress(raw[pos:])
        except zlib.error:
            # yarim uye: bu uyenin cozulebilen kismini al, sonraki gzip basligina (1f 8b) atla
            d2=zlib.decompressobj(16+zlib.MAX_WBITS); buf=b''
            for i in range(pos,len(raw),4096):
                try: buf+=d2.decompress(raw[i:i+4096])
                except zlib.error: break
            out+=buf
            nxt=raw.find(b'\x1f\x8b',pos+2)
            if nxt<0: break
            pos=nxt; continue
        if not d.unused_data: break
        pos=len(raw)-len(d.unused_data)
        nxt=raw.find(b'\x1f\x8b',pos)
        if nxt<0: break
        pos=nxt
    rows=[]
    for l in out.decode('utf-8','ignore').split('\n'):
        if not l.strip(): continue
        try: rows.append(json.loads(l))
        except Exception: pass
    return rows
if __name__=='__main__':
    rows=oku(sys.argv[1]); n=int(sys.argv[sys.argv.index('--son')+1]) if '--son' in sys.argv else None
    for r in (rows[-n:] if n else rows): print(json.dumps(r))
