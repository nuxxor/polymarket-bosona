import gzip,glob,json,sys
# saniye basina 1 BTC mid ornegi
out={}
for f in sorted(glob.glob('data/tape/tape_20260918_*.jsonl.gz')):
    if f[-13:-11] < '10': continue
    try:
        with gzip.open(f,'rt') as fh:
            for ln in fh:
                if '"k":"fbt"' not in ln: continue
                try: d=json.loads(ln)
                except Exception: continue
                p=d.get('p') or {}
                b=p.get('b'); a=p.get('a')
                if not b or not a: continue
                s=int(d['src']//1000)
                if s in out: continue
                out[s]=(float(b)+float(a))/2.0
    except EOFError: pass
    print(f,len(out),file=sys.stderr)
json.dump(out,open('/tmp/claude-1000/-home-taygun-Masa-st--polymarket/b4197893-bd19-4ee9-9e9a-ddd5e06151af/scratchpad/btc_sn.json','w'))
print("saniye:",len(out),file=sys.stderr)
