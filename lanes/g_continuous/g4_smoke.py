"""G4 with real public books, dry intents only; no authenticated trading client."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
from unittest.mock import patch

import g4_operator as deploy
from test_g4 import materialize


def main():
    seconds = 120
    output = deploy.HERE/'validation'
    with tempfile.TemporaryDirectory(prefix='.g4-public-', dir=output) as directory:
        root = Path(directory)
        materialize(root, deploy.TARGET)
        sys.path.insert(0, str(root))
        spec = importlib.util.spec_from_file_location('g4_public_dry', root/'ab.py')
        b = importlib.util.module_from_spec(spec)
        with patch.object(sys, 'argv', [str(root/'ab.py'), '--lane-g']):
            spec.loader.exec_module(b)
        assert not b.LIVE and b.client is None
        b.KESICI = -100
        b.STATE = str(root/'dry.json')
        journal = b.emir_iz.baslat(output/'G4_smoke_telemetry.jsonl', 'DRY_PUBLIC_ONLY', root/'ab.py')
        events = []
        b.log = lambda event, **fields: events.append(dict(k=event, **fields))
        posted, canceled = [], []
        original_post, original_cancel = b.koy_toplu, b.iptal
        def dry_post(orders):
            assert not b.LIVE
            result = original_post(orders)
            assert all(r[2].startswith('KURU-') for r in result)
            posted.extend(result)
            return result
        def dry_cancel(oid):
            assert not b.LIVE and oid.startswith('KURU-')
            canceled.append(oid)
            return original_cancel(oid)
        b.koy_toplu, b.iptal = dry_post, dry_cancel
        b.MUTABAKAT_OK = True
        def stop():
            b.DURDUR = True
        timer = threading.Timer(seconds, stop)
        timer.start()
        windows = []
        try:
            while not b.DURDUR:
                S = int(time.time())//300*300
                market = [m for e in b.jget(b.GAMMA.format('btc', S)) for m in e.get('markets', [])
                          if m.get('slug') == f'btc-updown-5m-{S}'][0]
                tokens = json.loads(market['clobTokenIds'])
                w = dict(emir=[], klip=5, kol='G', cozuldu=False)
                b.pen = {('btc', S): w}
                windows.append(S)
                b.taze_izle(('btc', S), w, {0: tokens[0], 1: tokens[1]})
        finally:
            b.DURDUR = True
            timer.cancel()
            for thread in threading.enumerate():
                if thread.name.startswith('taze-ws-'):
                    thread.join(5)
            journal.yaz('session_end')
            b.emir_iz.aktif = None
        rows = [json.loads(line) for line in (output/'G4_smoke_telemetry.jsonl').read_text().splitlines()]
        quotes = [r for r in rows if r['session'] == journal.session and r['event'] == 'g4_quote']
        assert quotes and posted and canceled and not journal.errors
        assert all(q['arm'] == 'G4' and q['book']['mono_ns'] <= q['decision']['mono_ns'] <= q['mono_ns'] for q in quotes)
        assert not any(e['k'] == 'G_KARAR_HATA' for e in events)
        assert all(r.get('pay', 0) == 0 for w in b.pen.values() for r in w['emir'])
        (output/'G4_smoke_bot.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
        proof = dict(status='PASS', source_sha=deploy.package()[2]['ab.py'], seconds=seconds,
                     windows=windows, quotes=len(quotes), dry_posts=len(posted), dry_cancels=len(canceled),
                     real_orders=0, real_fills=0, economic_result=None, sdk_errors=journal.errors,
                     ws_reconnections=sum(e['k'] == 'taze_ws_hata' for e in events))
        (output/'G4_smoke.json').write_text(json.dumps(proof, indent=2)+'\n')
        print(json.dumps(proof))


if __name__ == '__main__':
    main()
