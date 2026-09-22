"""Two bounded, unauthenticated raw market streams; no trading/account imports."""
import gzip
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import threading
import time

import websocket

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.dont_write_bytecode = True
sys.path.insert(0,str(ROOT/'btc15_reconciled_v1_20260921'))
from common import accounting  # noqa: E402

START = 1790031600
CUT = START+1020
ENDPOINT = 'wss://ws-subscriptions-clob.polymarket.com/ws/market'
MAX_BYTES = 512*1024**2


def save(path, data):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')
    tmp.replace(path)


def stamp():
    return dict(received_ms=time.time_ns()//1000000,monotonic_ns=time.monotonic_ns())


def line(seq, connection, kind, **data):
    return json.dumps(dict(seq=seq,connection=connection,kind=kind,**data),separators=(',',':'))+'\n'


def main():
    out = HERE/'raw/dual'
    out.mkdir(parents=True,exist_ok=False)
    begun = time.time()
    assert begun<START, 'assigned market must not silently start with missing prefix'
    assert 0<CUT+10-begun<=1800
    slug = f'btc-updown-15m-{START}'
    before = stamp()
    url = 'https://gamma-api.polymarket.com/markets/slug/'+slug
    market = accounting.ref.base.get(url,timeout=5,attempts=1)
    meta = accounting.ref.classify(market)
    assert (meta['group'],meta['S'],meta['end'],meta['mechanism'])==('btc_15m',START,START+900,'chainlink_twap60')
    tokens = json.loads(market['clobTokenIds'])
    assert len(tokens)==len(set(tokens))==2
    save(out/'market.json',dict(url=url,request=before,**stamp(),data=market))
    deadline = time.monotonic()+max(0,CUT+10-time.time())
    state = dict(pid=os.getpid(),start_ms=round(begun*1000),stop_ms=(CUT+10)*1000,
        assigned_start=START,cutoff_ms=CUT*1000,max_raw_bytes=MAX_BYTES,min_free_bytes=2*1024**3,
        endpoint=ENDPOINT,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        raw_bytes=0,running=True,reason='duration_complete',channels={c:dict(frames=0,gaps=0,connections=0) for c in ('A','B')})
    save(out/'run.json',state)
    stop,lock = threading.Event(),threading.Lock()

    def listen(channel):
        seq,connection,ping = 0,0,0
        socket = None
        with gzip.open(out/f'{channel}.jsonl.gz','wt',compresslevel=1) as sink:
            def emit(kind, **data):
                nonlocal seq
                seq += 1
                payload = line(seq,connection,kind,**data)
                with lock:
                    size = len(payload.encode())
                    if state['raw_bytes']+size>MAX_BYTES:
                        state['reason'] = 'storage_limit'
                        stop.set()
                        return False
                    state['raw_bytes'] += size
                sink.write(payload)
                return True
            try:
                while not stop.is_set() and time.monotonic()<deadline:
                    try:
                        if socket is None:
                            socket = websocket.create_connection(ENDPOINT,timeout=5)
                            connection += 1
                            subscription = dict(assets_ids=tokens,type='market')
                            socket.send(json.dumps(subscription))
                            socket.settimeout(1)
                            emit('connect',**stamp(),subscription=subscription)
                            with lock:
                                state['channels'][channel]['connections'] += 1
                            ping = 0
                        if time.monotonic()-ping>=10:
                            socket.send('PING')
                            emit('ping',**stamp())
                            sink.flush()
                            ping = time.monotonic()
                        try:
                            raw = socket.recv()
                        except websocket.WebSocketTimeoutException:
                            emit('timeout',**stamp())
                            continue
                        timing = stamp()
                        if not raw:
                            raise OSError('websocket closed')
                        # Persist raw text first; unknown schemas and malformed JSON survive.
                        payload = dict(binary_b64=base64.b64encode(raw).decode()) if isinstance(raw,bytes) else dict(raw=raw)
                        if not emit('frame',**timing,**payload):
                            break
                        with lock:
                            state['channels'][channel]['frames'] += 1
                    except (OSError,ValueError,websocket.WebSocketException) as exc:
                        emit('gap',**stamp(),error_type=type(exc).__name__)
                        with lock:
                            state['channels'][channel]['gaps'] += 1
                        if socket:
                            socket.close()
                        socket = None
                        stop.wait(min(2,max(0,deadline-time.monotonic())))
            except Exception as exc:
                with lock:
                    state['reason'] = 'writer_error_'+type(exc).__name__
                stop.set()
                raise
            finally:
                if socket:
                    socket.close()
                emit('end',**stamp())

    workers = [threading.Thread(target=listen,args=(c,)) for c in ('A','B')]
    for worker in workers:
        worker.start()
    while any(t.is_alive() for t in workers):
        with lock:
            if shutil.disk_usage(out).free<state['min_free_bytes']:
                state['reason'] = 'free_space_limit'
                stop.set()
            save(out/'status.json',dict(state,**stamp()))
        stop.wait(1)
        if stop.is_set():
            for worker in workers:
                worker.join(timeout=1)
    state['running'] = False
    save(out/'status.json',dict(state,**stamp()))
    save(out/'closed_hashes.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.jsonl.gz')})


if __name__=='__main__':
    main()
