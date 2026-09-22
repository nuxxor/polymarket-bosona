"""Finite public drain control versus the unmodified recorder; no orders."""
import json
from pathlib import Path
import resource
import subprocess
import sys
import threading
import time

SECONDS = 120


def drain(markets, output):
    from websockets.sync.client import connect
    started = time.monotonic()
    counts = dict(frames=0,bytes=0,pong=0,connections=0,gaps=[])
    while time.monotonic()-started<SECONDS:
        counts['connections'] += 1
        try:
            with connect('wss://ws-subscriptions-clob.polymarket.com/ws/market',
                         open_timeout=8,close_timeout=2,max_queue=4096,
                         max_size=2**20,ping_interval=None) as ws:
                ws.send(json.dumps(dict(type='market',assets_ids=[t for m in markets for t in m['tokens']])))
                ping = time.monotonic()-10
                while time.monotonic()-started<SECONDS:
                    if time.monotonic()-ping>=10:
                        ws.send('PING')
                        ping = time.monotonic()
                    try:
                        raw = ws.recv(timeout=.5)
                    except TimeoutError:
                        continue
                    if raw=='PONG':
                        counts['pong'] += 1
                    else:
                        counts['frames'] += 1
                        counts['bytes'] += len(raw)
        except Exception as error:
            close = getattr(error,'rcvd',None)
            reason = getattr(close,'reason','').lower()
            counts['gaps'].append(dict(elapsed=time.monotonic()-started,
                code=getattr(close,'code',None),error_type=type(error).__name__,
                slow_consumer='slow consumer' in reason))
            time.sleep(.5)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    counts.update(cpu_seconds=usage.ru_utime+usage.ru_stime,elapsed=time.monotonic()-started)
    assert counts['frames']>0 and counts['pong']>0
    output.write_text(json.dumps(counts,indent=2)+'\n')


if __name__=='__main__':
    root = Path(sys.argv[2])
    if sys.argv[1]=='drain':
        drain(json.loads((root/'roster.json').read_text()),root/'drain.json')
    else:
        sys.path.insert(0,'/home/ubuntu/polymarket-bosona-m7-v3')
        from stream_iz import capture,credentials,roster
        root.mkdir(parents=True,exist_ok=False)
        markets = roster(SECONDS)
        (root/'roster.json').write_text(json.dumps(markets))
        auth,count = credentials(Path('/home/taygun/Masaüstü/polymarket/.env.live'))
        child = subprocess.Popen([sys.executable,__file__,'drain',str(root)])
        _,summary = capture(root/'capture',markets,auth,SECONDS,count,threading.Event())
        code = child.wait(timeout=20)
        usage = resource.getrusage(resource.RUSAGE_SELF)
        (root/'comparison.json').write_text(json.dumps(dict(
            recorder_session=summary['session'],recorder_stats=summary['stats'],
            recorder_cpu_seconds=usage.ru_utime+usage.ru_stime,drain_exit=code,
            limitation='Concurrent two connections; not proof of server or network root cause.'),indent=2)+'\n')
        assert code==0
        print(json.dumps(dict(recorder_stats=summary['stats'],drain=json.loads((root/'drain.json').read_text()))))
