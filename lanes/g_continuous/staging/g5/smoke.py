"""Real public books, two isolated dry arms, synthetic inventory; no wallet/client."""
import json
from pathlib import Path
import sys
import threading
import time

from check import BOT, load, order

HERE = Path(__file__).resolve().parent


def main():
    seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    assert 20 <= seconds <= 300
    b0 = load(BOT/'ab.py')
    S = int(time.time())//300*300
    market = [m for e in b0.jget(b0.GAMMA.format('btc', S)) for m in e.get('markets', [])
              if m.get('slug') == f'btc-updown-5m-{S}'][0]
    tokens = dict(enumerate(json.loads(market['clobTokenIds'])))
    journal = b0.emir_iz.baslat(HERE/'smoke_telemetry.jsonl', 'DRY_PUBLIC_SYNTHETIC_INVENTORY', BOT/'ab.py')
    engines = {label: load(BOT/'ab.py') for label in ('G5', 'G4_FIXED')}
    modules, results, errors = list(engines.values()), {}, []
    def run(label):
        b = engines[label]
        b.g5_arm = lambda _: label
        assert not b.LIVE and b.client is None
        b.KESICI = -100
        b.MUTABAKAT_OK = True
        b.state_kaydet = lambda: None
        b.STOP = str(HERE/'SMOKE_STOP')
        events = []
        b.log = lambda event, **fields: events.append(dict(k=event, **fields))
        w = dict(emir=[order(0, 5)], klip=5, kol='G', cozuldu=False)
        b.pen = {('btc', S): w}
        posts, cancels = [], []
        old_post, old_cancel = b.koy_toplu, b.iptal
        def post(rows):
            assert not b.LIVE and b.client is None
            replies = old_post(rows)
            assert all(x[2].startswith('KURU-') for x in replies)
            posts.extend(replies)
            return replies
        def cancel(oid):
            assert not b.LIVE and oid.startswith('KURU-')
            cancels.append(oid)
            return old_cancel(oid)
        b.koy_toplu, b.iptal = post, cancel
        def maintain():
            while not b.DURDUR:
                b.denge_koru(('btc', S), w)
                time.sleep(.2)
        maintenance = threading.Thread(target=maintain)
        maintenance.start()
        try:
            b.taze_izle(('btc', S), w, tokens)
            assert not any(e['k'].endswith('KARAR_HATA') for e in events)
            assert not any(e['k'] == 'DENGE_SINIRI' for e in events)
            assert all(o['pay'] == 0 for o in w['emir'][1:])
            results[label] = dict(dry_posts=len(posts), dry_cancels=len(cancels),
                                 synthetic_start_up=5, real_orders=0, real_fills=0,
                                 ws_reconnects=sum(e['k'] == 'taze_ws_hata' for e in events))
        except Exception as error:
            errors.append(type(error).__name__)
        finally:
            b.DURDUR = True
            maintenance.join(3)
            assert not maintenance.is_alive()
    threads = [threading.Thread(target=run, args=(label,)) for label in ('G5', 'G4_FIXED')]
    for thread in threads:
        thread.start()
    deadline = time.monotonic()+seconds
    while time.monotonic() < deadline and any(t.is_alive() for t in threads):
        time.sleep(.2)
    for b in modules:
        b.DURDUR = True
    for thread in threads:
        thread.join(10)
        assert not thread.is_alive()
    journal.yaz('session_end')
    assert len(results) == 2 and not errors and not journal.errors, (results, errors)
    records = [json.loads(line) for line in (HERE/'smoke_telemetry.jsonl').read_text().splitlines()]
    records = [r for r in records if r['session'] == journal.session]
    assert any(r['event'] == 'g5_quote' for r in records)
    proof = dict(status='PASS', market=S, duration_requested_s=seconds, arms=results,
                 quotes=sum(r['event'] == 'g5_quote' for r in records), sdk_errors=journal.errors,
                 economic_result=None, live_activation=False)
    (HERE/'smoke.json').write_text(json.dumps(proof, indent=2)+'\n')
    print(json.dumps(proof))


if __name__ == '__main__':
    main()
