#!/usr/bin/env python3
"""Finite public BTC15m full L2 snapshot recorder. No orders or actor trigger."""
import argparse
from collections import Counter
import fcntl
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import time
import urllib.request

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import research as r  # noqa: E402


def validate(books,tokens,condition):
    if not isinstance(books,list) or len(books)!=2 or {b['asset_id'] for b in books}!=set(tokens):
        raise ValueError('missing or wrong token')
    for b in books:
        if b['market']!=condition or int(b['timestamp'])<=0:
            raise ValueError('wrong market/timestamp')
        for x in b['asks']+b['bids']:
            p,q=float(x['price']),float(x['size'])
            if not math.isfinite(p+q) or not 0<=p<=1 or q<=0:
                raise ValueError('invalid level')
    # Preserve empty, crossed or stale books as evidence; replay must reject them.


def record(out,seconds,interval):
    out.mkdir(parents=True,exist_ok=True)
    lock=(out/'record.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    start=time.time()
    deadline=time.monotonic()+seconds
    counts=Counter()
    r.save(out/'run.json',dict(pid=os.getpid(),start_ms=round(start*1000),end_ms=round((start+seconds)*1000),
        interval_seconds=interval,code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        sources=['https://gamma-api.polymarket.com/markets/slug/','https://clob.polymarket.com/books'],
        limitations='REST snapshots, not every update. No assumption of freshness from receipt alone.'))
    market=None
    tape=None
    tape_hour=None
    next_status=0
    try:
        while time.monotonic()<deadline:
            cycle=time.monotonic()
            now=time.time()
            if shutil.disk_usage(out).free<2*1024**3:
                raise OSError('less than 2 GiB free: bounded recorder stops')
            hour=time.strftime('%Y%m%d_%H',time.gmtime(now))
            if hour!=tape_hour:
                if tape:
                    tape.close()
                tape=gzip.open(out/f'books_{hour}.jsonl.gz','at',compresslevel=3)
                tape_hour=hour
            s=int(now)//900*900
            event=dict(requested_ms=round(now*1000),S=s)
            try:
                if market is None or market['slug']!=f'btc-updown-15m-{s}':
                    market=r.base.get(f'https://gamma-api.polymarket.com/markets/slug/btc-updown-15m-{s}',timeout=4,attempts=1)
                    meta=r.classify(market)
                    if meta['group']!='btc_15m' or meta['S']!=s or meta['mechanism']!='chainlink_twap60':
                        raise ValueError('contract rules changed')
                    r.save(out/'markets'/(market['slug']+'.json'),dict(market,captured_ms=round(time.time()*1000)))
                tokens=json.loads(market['clobTokenIds'])
                req=urllib.request.Request('https://clob.polymarket.com/books',
                    data=json.dumps([dict(token_id=t) for t in tokens]).encode(),
                    headers={'Content-Type':'application/json','User-Agent':'public-btc15-research/1'})
                event['requested_ms']=round(time.time()*1000)
                with urllib.request.urlopen(req,timeout=4) as response:
                    books=json.load(response)
                event.update(received_ms=round(time.time()*1000),books=books,kind='books')
                validate(books,tokens,market['conditionId'])
                event['exchange_ages_ms']=[event['received_ms']-int(b['timestamp']) for b in books]
                counts['snapshots']+=1
                counts['both_exchange_age_under_3s']+=all(0<=x<=3000 for x in event['exchange_ages_ms'])
            except (OSError,ValueError,KeyError,TypeError) as e:
                event.update(kind='gap',received_ms=round(time.time()*1000),error=type(e).__name__+': '+str(e))
                counts['gaps']+=1
            tape.write(json.dumps(event,separators=(',',':'))+'\n')
            tape.flush()
            if time.monotonic()>=next_status:
                r.save(out/'status.json',dict(pid=os.getpid(),received_ms=event['received_ms'],S=s,
                    counts=dict(counts),running=True,elapsed_seconds=round(time.time()-start)))
                next_status=time.monotonic()+10
            time.sleep(max(0,min(interval-(time.monotonic()-cycle),deadline-time.monotonic())))
    finally:
        if tape:
            tape.close()
        r.save(out/'status.json',dict(pid=os.getpid(),received_ms=round(time.time()*1000),
            counts=dict(counts),running=False,elapsed_seconds=round(time.time()-start)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seconds',type=int,default=72*3600)
    p.add_argument('--interval',type=float,default=1.)
    a=p.parse_args()
    if not a.out.is_absolute() or not 0<a.seconds<=72*3600 or not 1<=a.interval<=60:
        p.error('absolute output; duration 1..259200 seconds; interval 1..60 seconds')
    record(a.out,a.seconds,a.interval)
