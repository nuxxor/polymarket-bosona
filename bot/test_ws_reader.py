"""Actual reader loop with burst/reconnect frames; no credentials or orders."""
import importlib.util
import json
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch


def scenario(path, kind):
    spec = importlib.util.spec_from_file_location('ws_test_bot', path)
    b = importlib.util.module_from_spec(spec)
    with patch.object(sys, 'argv', [str(path)]):
        spec.loader.exec_module(b)
    now = time.time()
    clock = [0.0]
    b.time = SimpleNamespace(time=time.time, sleep=time.sleep, monotonic=lambda: clock[0])
    sent, seen, errors = [], [], []
    b.tick = lambda _: .01
    b.log = lambda event, **kw: errors.append(event) if event.endswith('HATA') else None
    b.state_kaydet = lambda: None
    b.MUTABAKAT_OK = False
    b.C_T_MIN = 0
    b.C_T_MAX = 12
    b.STOP = '/__ws_test_no_stop__'
    def no_order(*args, **kwargs):
        raise AssertionError('Reader test must never submit an order')
    b.koy_toplu = no_order
    def target(bb, ba, *args, **kwargs):
        seen.append((bb, ba))
        b.DURDUR = True
        return None
    b.taze_hedef = target
    def book(token, price, age=0):
        return dict(event_type='book', asset_id=token, timestamp=str(round((now-age)*1000)),
                    bids=[dict(price=str(price), size='10')], asks=[dict(price=str(price+.01), size='10')])
    frames = [json.dumps([book('u', .4), book('d', .59)])]
    if kind == 'burst':
        frames.append(json.dumps([book('u', .55), book('d', .44)]))
    elif kind == 'mixed':
        frames.append(json.dumps([book('u', .55), dict(event_type='tick_size_change', asset_id='d', new_tick_size='0.001'), book('d', .44)]))
    elif kind == 'old':
        frames.extend([json.dumps(book('u', .55)), json.dumps(book('u', .2, age=8))])
    elif kind == 'delta_before_snapshot':
        frames = [json.dumps(dict(event_type='price_change', timestamp=str(round(now*1000)),
                  price_changes=[dict(asset_id='u', price='.55', size='10', side='BUY', best_ask='.56')]))]
    elif kind == 'reconnect':
        b.C_T_MAX = 14
        frames.extend([OSError('simulated disconnect'), json.dumps([book('u', .55), book('d', .44)])])
    drained = threading.Event()
    class Book:
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def send(self, value): sent.append(value)
        def recv(self, timeout):
            if frames:
                clock[0] += 11
                value = frames.pop(0)
                if isinstance(value, Exception):
                    raise value
                return value
            drained.set()
            time.sleep(.01)
            raise TimeoutError
    original_start = threading.Thread.start
    threads = []
    def start(thread):
        threads.append(thread)
        original_start(thread)
        assert drained.wait(2)
    with patch('websockets.sync.client.connect', lambda *a, **kw: Book()), \
            patch.object(threading.Thread, 'start', start):
        b.taze_izle(('btc', int(now)-10), dict(emir=[], klip=5, cozuldu=False), {0:'u', 1:'d'})
    for thread in threads:
        thread.join(2)
        assert not thread.is_alive()
    assert not errors, errors
    expected = (None, None) if kind == 'delta_before_snapshot' else (.55, .56)
    if kind == 'delta_before_snapshot' and not seen:
        pass  # Main C rejects an uninitialized book before asking for a target.
    else:
        assert seen[0] == expected, (kind, seen, expected)
    assert json.loads(sent[0]) == dict(type='market', assets_ids=['u', 'd'])
    assert 'PING' in sent


if __name__ == '__main__':
    path = Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('ab.py')
    for kind in ('burst', 'mixed', 'old', 'delta_before_snapshot', 'reconnect'):
        scenario(path, kind)
    print('WS reader: burst, mixed frame, old snapshot, initial delta, reconnect, heartbeat and stop checks passed')
