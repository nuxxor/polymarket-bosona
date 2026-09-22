"""240-second public control using the alternative asyncio I/O implementation."""
import asyncio
import hashlib
import json
from pathlib import Path
import resource
import time

from websockets.asyncio.client import connect

ROOT=Path('/home/ubuntu/polymarket-bosona-m7-transport/run1')


async def main():
    roster=ROOT/'roster.json'
    markets=json.loads(roster.read_text())
    result=dict(started_utc_ns=time.time_ns(),seconds=240,roster_sha256=hashlib.sha256(roster.read_bytes()).hexdigest(),
                connections=0,frames=0,bytes=0,pong=0,closes=[])
    (ROOT/'async_start.json').write_text(json.dumps(result,indent=2)+'\n')
    started=time.monotonic()
    while time.monotonic()-started<240:
        result['connections']+=1
        try:
            async with connect('wss://ws-subscriptions-clob.polymarket.com/ws/market',
                open_timeout=8,close_timeout=2,max_queue=4096,max_size=2**20,ping_interval=None) as ws:
                await ws.send(json.dumps(dict(type='market',assets_ids=[t for m in markets for t in m['tokens']])))
                ping=time.monotonic()-10
                while time.monotonic()-started<240:
                    if time.monotonic()-ping>=10:
                        await ws.send('PING')
                        ping=time.monotonic()
                    try:raw=await asyncio.wait_for(ws.recv(),timeout=.5)
                    except TimeoutError:continue
                    if raw=='PONG':result['pong']+=1
                    else:
                        result['frames']+=1
                        result['bytes']+=len(raw)
        except Exception as error:
            close=getattr(error,'rcvd',None)
            reason=getattr(close,'reason','').lower().replace('_',' ').replace('-',' ')
            result['closes'].append(dict(utc_ns=time.time_ns(),code=getattr(close,'code',None),
                error_type=type(error).__name__,slow_consumer='slow consumer' in reason))
            await asyncio.sleep(.5)
    usage=resource.getrusage(resource.RUSAGE_SELF)
    result.update(ended_utc_ns=time.time_ns(),elapsed=time.monotonic()-started,cpu_seconds=usage.ru_utime+usage.ru_stime)
    (ROOT/'async_result.json').write_text(json.dumps(result,indent=2)+'\n')
    assert result['frames']>0 and result['pong']>0 and result['elapsed']>=240
    print(json.dumps(result))


if __name__=='__main__':
    asyncio.run(main())
