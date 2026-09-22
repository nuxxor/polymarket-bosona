"""Finite M7 transport diagnosis, unchanged recorder plus public drain control."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import threading
import time

SECONDS = 900
SOURCE = Path('/home/ubuntu/polymarket-bosona-m7-v3')


class Meter:
    """One connection; only timing/counts, never message/auth contents."""
    def __init__(self,ws,channel,connection,file):
        self.ws,self.channel,self.connection,self.file = ws,channel,connection,file
        self.bucket = None
        self.last_return = None

    def log(self,event,**fields):
        self.file.write(json.dumps(dict(event=event,utc_ns=time.time_ns(),channel=self.channel,
            connection=self.connection,**fields),separators=(',',':'))+'\n')
        self.file.flush()

    def flush(self):
        if self.bucket:
            self.log('sample',**self.bucket)
            self.bucket = None

    def send(self,message):
        return self.ws.send(message)

    def recv(self,timeout):
        start = time.monotonic_ns()
        second = start//10**9
        if self.bucket and self.bucket['mono_second']!=second:
            self.flush()
        if self.bucket is None:
            self.bucket = dict(mono_second=second,calls=0,frames=0,timeouts=0,bytes=0,
                queue_max=0,paused_samples=0,caller_max_ns=0,recv_max_ns=0)
        b = self.bucket
        b['calls'] += 1
        if self.last_return is not None:
            b['caller_max_ns'] = max(b['caller_max_ns'],start-self.last_return)
        # ponytail: diagnostic-only internals pinned to websockets 17.1; no transport knobs changed.
        b['queue_max'] = max(b['queue_max'],self.ws.recv_messages.frames.qsize())
        b['paused_samples'] += int(self.ws.recv_messages.paused)
        try:
            raw = self.ws.recv(timeout=timeout)
        except TimeoutError:
            b['timeouts'] += 1
            raise
        except Exception as error:
            close = getattr(error,'rcvd',None)
            reason = getattr(close,'reason','').lower().replace('_',' ').replace('-',' ')
            self.log('close',code=getattr(close,'code',None),error_type=type(error).__name__,
                     slow_consumer='slow consumer' in reason,reason_length=len(reason))
            raise
        else:
            b['frames'] += 1
            b['bytes'] += len(raw)
            return raw
        finally:
            self.last_return = time.monotonic_ns()
            b['recv_max_ns'] = max(b['recv_max_ns'],self.last_return-start)
            b['queue_max'] = max(b['queue_max'],self.ws.recv_messages.frames.qsize())
            b['paused_samples'] += int(self.ws.recv_messages.paused)


def connector(root,label):
    from websockets.sync.client import connect
    counts = {}
    @contextmanager
    def open_socket(url,**kwargs):
        channel = url.rsplit('/',1)[1]
        counts[channel] = counts.get(channel,0)+1
        with (root/f'{label}_{channel}.jsonl').open('a') as file:
            with connect(url,**kwargs) as ws:
                meter = Meter(ws,channel,counts[channel],file)
                meter.log('connected',queue_high=ws.recv_messages.high,
                          queue_low=ws.recv_messages.low)
                try:
                    yield meter
                finally:
                    meter.flush()
                    meter.log('connection_end')
    return open_socket


def drain(root,markets,stop):
    started = time.monotonic()
    counts = dict(frames=0,bytes=0,pong=0,connections=0,gaps=0)
    connect = connector(root,'drain')
    while not stop.is_set() and time.monotonic()-started<SECONDS:
        counts['connections'] += 1
        try:
            with connect('wss://ws-subscriptions-clob.polymarket.com/ws/market',
                         open_timeout=8,close_timeout=2,max_queue=4096,
                         max_size=2**20,ping_interval=None) as ws:
                ws.send(json.dumps(dict(type='market',assets_ids=[t for m in markets for t in m['tokens']])))
                ping = time.monotonic()-10
                while not stop.is_set() and time.monotonic()-started<SECONDS:
                    if (root/'STOP_PROBE').exists():
                        stop.set()
                        break
                    if time.monotonic()-ping>=10:
                        ws.send('PING')
                        ping = time.monotonic()
                    try:
                        raw = ws.recv(timeout=.5)
                    except TimeoutError:
                        continue
                    if raw=='PONG':counts['pong'] += 1
                    else:
                        counts['frames'] += 1
                        counts['bytes'] += len(raw)
        except Exception:
            counts['gaps'] += 1
            stop.wait(.5)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    counts.update(cpu_seconds=usage.ru_utime+usage.ru_stime,elapsed=time.monotonic()-started)
    (root/'drain.json').write_text(json.dumps(counts,indent=2)+'\n')
    assert counts['frames']>0 and counts['pong']>0


def main():
    import websockets
    assert websockets.__version__=='17.1'
    os.umask(0o077)
    root = Path(sys.argv[2])
    stop = threading.Event()
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:stop.set())
    if sys.argv[1]=='drain':
        drain(root,json.loads((root/'roster.json').read_text()),stop)
        return
    sys.path.insert(0,str(SOURCE))
    from stream_iz import capture,credentials,roster
    root.mkdir(parents=True,exist_ok=False)
    print('PROBE_STAGE: roster',flush=True)
    markets = roster(SECONDS)
    (root/'roster.json').write_text(json.dumps(markets))
    expected = json.loads((Path(__file__).parent/'protocol.json').read_text())['source_sha256']
    actual = {name:hashlib.sha256((SOURCE/name).read_bytes()).hexdigest() for name in expected}
    assert actual==expected
    print('PROBE_STAGE: account_get',flush=True)
    auth,count = credentials(Path('/home/taygun/Masaüstü/polymarket/.env.live'))
    child = subprocess.Popen([sys.executable,__file__,'drain',str(root)])
    print('PROBE_STAGE: capture',flush=True)
    try:
        _,summary = capture(root/'capture',markets,auth,SECONDS,count,stop,connector(root,'recorder'))
    finally:
        (root/'STOP_PROBE').touch()
        code = child.wait(timeout=20)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    result = dict(recorder_session=summary['session'],recorder_stats=summary['stats'],
        recorder_cpu_seconds=usage.ru_utime+usage.ru_stime,drain_exit=code,
        full_calibration=False,transport_ok=summary['transport_ok'],source_sha256=actual)
    (root/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    assert code==0
    print(json.dumps(result))


def self_test():
    import io
    from types import SimpleNamespace
    from unittest.mock import patch
    secret = 'never-log-this-secret'
    close = RuntimeError(secret)
    close.rcvd = SimpleNamespace(code=1013,reason='slow_consumer: '+secret)
    frames = iter(['PONG',secret,TimeoutError(),close])
    def recv(timeout):
        v = next(frames)
        if isinstance(v,Exception):raise v
        return v
    ws = SimpleNamespace(recv=recv,send=lambda _:None,
        recv_messages=SimpleNamespace(frames=SimpleNamespace(qsize=lambda:4200),paused=True))
    file = io.StringIO()
    meter = Meter(ws,'market',1,file)
    with patch('time.monotonic_ns',side_effect=[100,110,120,130,140,150,160,170]):
        assert meter.recv(.5)=='PONG'
        assert meter.recv(.5)==secret
        for error in (TimeoutError,RuntimeError):
            try:meter.recv(.5)
            except error:pass
            else:raise AssertionError('Missing failure')
    meter.flush()
    assert secret not in file.getvalue()
    rows = [json.loads(x) for x in file.getvalue().splitlines()]
    assert rows[0]['code']==1013 and rows[0]['slow_consumer']
    assert rows[1]['queue_max']==4200 and rows[1]['paused_samples']==8
    assert rows[1]['frames']==2 and rows[1]['timeouts']==1 and rows[1]['caller_max_ns']==10
    print('Probe timing, backlog, exception and secret-redaction checks passed')


if __name__=='__main__':
    if sys.argv[1]=='--self-test':self_test()
    else:
        try:main()
        except Exception as error:
            print('PROBE_FAILED: '+type(error).__name__)
            raise SystemExit(1) from None
