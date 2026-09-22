"""Finite London public-data test of the actual reader; order paths disabled."""
from collections import Counter
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import threading
import time
from unittest.mock import patch

import requests


def main():
    path = Path(sys.argv[1])
    duration = int(sys.argv[2]) if len(sys.argv)>2 else 120
    spec = importlib.util.spec_from_file_location('smoke_bot', path)
    b = importlib.util.module_from_spec(spec)
    with patch.object(sys, 'argv', [str(path)]):
        spec.loader.exec_module(b)
    assert not b.LIVE
    start = int(time.time())//300*300
    m = requests.get('https://gamma-api.polymarket.com/markets', params={'slug':f'btc-updown-5m-{start}'}, timeout=15).json()[0]
    tokens = json.loads(m['clobTokenIds'])
    events, decisions = [], []
    b.tick = lambda _: .01
    b.C_T_MIN = 0
    b.C_T_MAX = time.time()-start+duration
    b.state_kaydet = lambda: None
    b.log = lambda event, **kw: events.append(dict(event=event, **kw))
    def no_order(*args, **kwargs):
        raise AssertionError('Financial method reached by public smoke')
    b.koy_toplu = b.kapat = no_order
    def target(bb, ba, *args, **kwargs):
        decisions.append(dict(ms=round(time.time()*1000), bb=bb, ba=ba))
        return None
    b.taze_hedef = target
    window = dict(emir=[], klip=5, cozuldu=False)
    began = time.time()
    b.taze_izle(('btc', start), window, dict(enumerate(tokens)))
    for thread in threading.enumerate():
        if thread.name == f'taze-ws-{start}':
            thread.join(4)
            assert not thread.is_alive()
    assert not window['emir']
    result = dict(started_ms=round(began*1000), ended_ms=round(time.time()*1000),
        source_sha256=sha256(path.read_bytes()).hexdigest(), S=start, decisions=len(decisions),
        quoted=sum(r['bb'] is not None and r['ba'] is not None for r in decisions),
        events=events, kinds=dict(Counter(e['event'] for e in events)), orders=0)
    Path(sys.argv[3]).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
