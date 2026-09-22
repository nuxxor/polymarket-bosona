"""Run read-only on London via SSH; stdout is a bounded, sanitized gzip snapshot."""
from hashlib import sha256
import gzip
import io
import json
from pathlib import Path
import sys
import time

ROOT=Path('/home/ubuntu/polymarket-bosona-g-continuous/bot')
START=1790082300  # Frozen complete market starts: 22 Sep 13:05 <= S < 13:25 UTC.
END=1790083500
SOURCE='a5cd853493a6f01ab395495574150bf31c6dec7201783dfb563e98a6e2fa3ca7'


def prefix(path):
    with path.open('rb') as f:return f.read(path.stat().st_size)


def main():
    assert sha256((ROOT/'ab.py').read_bytes()).hexdigest()==SOURCE
    snapshot_ns=time.time_ns();inputs={}
    def jsonl(name):
        raw=prefix(ROOT/name);inputs[name]={'bytes':len(raw),'sha256':sha256(raw).hexdigest()}
        return [json.loads(line) for line in raw.splitlines(keepends=True) if line.endswith(b'\n')]
    log=jsonl('LOG_g.jsonl');telemetry=jsonl('LOG_g_emir_iz.jsonl')
    accepted={x['oid']:x for x in log if x.get('k')=='taze_koy' and START<=x['S']<END}
    assert accepted
    requests={x['attempt']:x for x in telemetry if x['event']=='request'}
    tokens={};attempts=set()
    for e in telemetry:
        if e['event']!='response' or e.get('op')!='post_batch':continue
        req=requests[e['attempt']]
        for order,item in zip(req['meta']['orders'],e.get('reply',{}).get('items') or []):
            if item.get('oid') in accepted:
                tokens[(accepted[item['oid']]['S'],order['oi'])]=order['token'];attempts.add(e['attempt'])
    for attempt,req in requests.items():
        if any(oid in accepted for oid in req.get('meta',{}).get('oids',[])):attempts.add(attempt)
    selected=[x for x in log if START<=x.get('S',-1)<END]
    points=[]
    for index,e in enumerate(selected[:-1]):
        if e['k']!='G_KARAR':continue
        q=selected[index+1]
        if q['k']!='G_KALITE' or (q['S'],q['oi'])!=(e['S'],e['oi']):continue
        token=tokens.get((e['S'],e['oi']))
        if token:points.append((q['utc_ms']*1000000,token))
    points=sorted(set(points));assets=set(tokens.values());meta=[]
    with gzip.GzipFile(fileobj=sys.stdout.buffer,mode='wb',mtime=0) as output:
        def emit(kind,**fields):output.write((json.dumps({'kind':kind,**fields},separators=(',',':'))+'\n').encode())
        emit('capture_start',at_ns=snapshot_ns,start_S=START,end_S_exclusive=END,source_sha256=SOURCE,
             budget_sha256=sha256((ROOT/'BUDGET_G.json').read_bytes()).hexdigest(),
             boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),tokens=[{'S':s,'oi':i,'asset':v} for (s,i),v in tokens.items()])
        for row in selected:emit('bot',row=row)
        for row in telemetry:
            if row.get('attempt') in attempts or row.get('oid') in accepted:emit('sdk',row=row)
        for path in sorted((ROOT/'measurement/run1').glob('*/*/*.jsonl.gz')):
            blob=prefix(path);name=str(path.relative_to(ROOT));lane=path.parents[1].name
            inputs[name]={'bytes':len(blob),'sha256':sha256(blob).hexdigest(),'prefix_snapshot':True}
            quotes={};ready=set();at=0;count=0;truncated=False
            def flush(until):
                nonlocal at
                while at<len(points) and points[at][0]<until:
                    stamp,token=points[at];quote=quotes.get(token)
                    if quote:emit('book_sample',lane=lane,file=name,decision_ns=stamp,asset=token,**quote)
                    at+=1
            try:
                with gzip.GzipFile(fileobj=io.BytesIO(blob)) as stream:
                    for raw in stream:
                        if not raw.endswith(b'\n'):
                            truncated=True;break
                        e=json.loads(raw);count+=1
                        if e.get('event')=='session_start':
                            meta.append({'file':name,**{k:e[k] for k in ('session','boot_id','started','source_sha256') if k in e}})
                            continue
                        received=e.get('received',{});when=received.get('utc_ns')
                        if when is None:continue
                        flush(when)
                        if e.get('channel')=='user' and e.get('event')=='data':
                            pay=e['payload'];oid=pay.get('id')
                            if oid in accepted or any(m['order_id'] in accepted for m in pay.get('maker_orders',[])):
                                emit('private',lane=lane,file=name,row=e)
                        if e.get('channel')!='market':continue
                        if e.get('event') in ('gap','connection_end','subscription_sent'):
                            quotes.clear();ready.clear();continue
                        pay=e.get('payload',{});source=int(float(pay.get('timestamp',0))*1000000)
                        changes=[]
                        if pay.get('event_type')=='book' and pay['asset_id'] in assets:
                            token=pay['asset_id'];ready.add(token)
                            bid=max((float(x['price']) for x in pay['bids'] if float(x['size'])>0),default=None)
                            ask=min((float(x['price']) for x in pay['asks'] if float(x['size'])>0),default=None)
                            changes=[(token,bid,ask)]
                        elif pay.get('event_type')=='price_change':
                            changes=[(x['asset_id'],x.get('best_bid'),x.get('best_ask')) for x in pay['price_changes'] if x['asset_id'] in ready]
                        for token,bid,ask in changes:
                            bid=float(bid) if bid is not None else None
                            ask=float(ask) if ask is not None else None
                            if source>when+100000000 or source<quotes.get(token,{}).get('source_ns',0):
                                ready.discard(token);quotes.pop(token,None);continue
                            if bid is None or ask is None or not 0<bid<ask<=1:
                                quotes.pop(token,None);continue
                            quotes[token]={'bid':bid,'ask':ask,'source_ns':source,'received':received}
            except (EOFError,gzip.BadGzipFile):truncated=True
            flush(snapshot_ns+1)
            emit('recording_end',file=name,rows=count,truncated_active_prefix=truncated)
        emit('capture_end',inputs=inputs,recordings=meta,accepted_parents=len(accepted),decision_points=len(points),
             source_unchanged=sha256((ROOT/'ab.py').read_bytes()).hexdigest()==SOURCE)


if __name__=='__main__':main()
