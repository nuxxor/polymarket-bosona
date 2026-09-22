"""Real quote/maintenance loops, mocked venue; never initializes an authenticated client."""
from hashlib import sha256
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
BOT = HERE/'bot'
ROOT = HERE.parents[3]
BASE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT/'.git/g4-publication-20260922/lanes/g_continuous/bot'
sys.path.insert(0, str(BOT))
import g_policy as g  # noqa: E402


def load(path):
    spec = importlib.util.spec_from_file_location('g5_checked_engine', path)
    b = importlib.util.module_from_spec(spec)
    with patch.object(sys, 'argv', [str(path), '--lane-g']):
        spec.loader.exec_module(b)
    assert not b.LIVE and b.client is None
    return b


def order(side, qty=0, price=.39, oid='held', status='dolu'):
    return dict(oi=side, pay=qty, boy=5, p=price, oid=oid, durum=status,
                dolumlar=[dict(q=qty, p=price, ms=1)] if qty else [])


def scenario(path, label, start=185, end=197, held=5, existing=None,
             bid=.40, cancel_pending=False, gate=False, stale=False, budget=False, journal_error=False):
    b = load(path)
    S = 1790100000
    clock = [float(S+start)]
    b.g5_arm = lambda _: label
    posts, cancels, events, audit, statuses = [], [], [], [], {}
    w = dict(emir=[order(0 if held >= 0 else 1, abs(held))] if held else [],
             klip=5, kol='G', cozuldu=False)
    if existing is not None:
        w['emir'].append(existing)
        statuses[existing['oid']] = 'LIVE'
    b.STOP = '/__g5_test_no_stop__'
    b.pen = {('btc', S): w}
    b.MUTABAKAT_OK = not gate
    b.LIVE = True  # No initialization; all financial methods below are mocked.
    b.healthy = lambda _: True
    b.tick = lambda _: .01
    b.state_kaydet = lambda: None
    b.log = lambda event, **kw: events.append((event, kw))
    b.kesici_asilir = lambda *args: budget
    def post(rows):
        posts.extend(rows)
        oid = f'mock{len(posts)}'
        statuses[oid] = 'LIVE'
        return [(side, p, oid, 'KABUL') for side, token, p, q in rows]
    def cancel(oid):
        cancels.append(oid)
        if not cancel_pending:
            statuses[oid] = 'CANCELED'
        return not cancel_pending, 'pending' if cancel_pending else 'canceled'
    b.koy_toplu = post
    b.iptal = cancel
    b.iptal_toplu = lambda ids: {oid: cancel(oid) for oid in ids}
    b.dolum_oku = lambda oid: (next((r['pay'] for r in w['emir'] if r['oid'] == oid), 0), statuses.get(oid, 'MATCHED'))
    journal = SimpleNamespace(errors=0)
    def record(event, **fields):
        audit.append((event, fields))
        if journal_error:
            journal.errors = 1
    journal.yaz = record
    def sleep(seconds):
        clock[0] += seconds
        time.sleep(.005)
        if clock[0] >= S+end:
            b.DURDUR = True
    b.time = SimpleNamespace(time=lambda: clock[0], sleep=sleep, monotonic=time.monotonic,
                             monotonic_ns=time.monotonic_ns, time_ns=lambda: round(clock[0]*1e9))
    drained = threading.Event()
    class Book:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def send(self, value): pass
        def recv(self, timeout):
            time.sleep(.001)
            frames = [dict(event_type='book', asset_id=token, timestamp=str(round((clock[0]-(4 if stale else 0))*1000)),
                           bids=[dict(price=str(p), size='20')], asks=[dict(price=str(p+.01), size='20')])
                      for token, p in [('up', bid), ('down', .99-bid)]]
            drained.set()
            return json.dumps(frames)
    def maintenance():
        last = -1
        while not b.DURDUR:
            if clock[0]-last >= .5:
                b.denge_koru(('btc', S), w)
                last = clock[0]
            time.sleep(.002)
    threads = []
    real_start = threading.Thread.start
    def start(thread):
        threads.append(thread)
        real_start(thread)
        if thread.name.startswith('taze-ws-'):
            assert drained.wait(2)
            time.sleep(.01)
    with patch('websockets.sync.client.connect', lambda *a, **kw: Book()), \
            patch.object(threading.Thread, 'start', start), patch.object(b.emir_iz, 'aktif', journal):
        worker = threading.Thread(target=maintenance, name='g5-maintenance')
        worker.start()
        try:
            b.taze_izle(('btc', S), w, {0: 'up', 1: 'down'})
        finally:
            b.DURDUR = True
        for thread in threads:
            thread.join(2)
            assert not thread.is_alive()
    assert not any(e.endswith('KARAR_HATA') for e, f in events), events
    return dict(posts=len(posts), cancels=len(cancels),
                maintenance_cancels=sum(e == 'DENGE_SINIRI' for e, f in events),
                stopped=b.st['durdu'], states=[r['durum'] for r in w['emir']],
                original_canceled='original' in cancels, roles=[r.get('g5', {}).get('role') for r in w['emir']],
                intents=sum(e == 'g5_intent' for e, f in audit),
                post_results=sum(e == 'g5_post_result' for e, f in audit))


def main():
    results = {}
    old = scenario(BASE/'ab.py', 'G4', start=178, end=242)
    assert old['maintenance_cancels'] >= 10 and old['posts'] >= 20, old
    results['legacy_bug_reproduced'] = old
    for label in ('G5', 'G4_FIXED'):
        new = scenario(BOT/'ab.py', label, start=178, end=242)
        assert new['maintenance_cancels'] == 0 and new['posts'] <= 2, new
        assert new['intents'] == new['post_results'] == new['posts'], new
        results[label+'_boundary'] = new
        for age in (150, 185, 230, 240, 289, 291):
            new = scenario(BOT/'ab.py', label, start=age, end=age+1)
            assert new['posts'] == (2 if age < 240 else (1 if age < 290 else 0)), (label, age, new)
            results[f'{label}_{age}'] = new
    for label in ('G5', 'G4_FIXED'):
        for role, held in (('open', 0), ('add', 5), ('reduce', -5)):
            result = scenario(BOT/'ab.py', label, held=held, existing=order(0, oid='original', status='acik'), bid=.45)
            expected = label == 'G4_FIXED' or role == 'reduce'
            assert result['original_canceled'] == expected, (label, role, result)
            results[label+'_'+role+'_rising'] = result
    for name, opts in {
        'falling': dict(bid=.38), 'time': dict(start=240, end=241),
        'gate': dict(gate=True), 'stale': dict(stale=True), 'budget': dict(budget=True),
        'uncertain_cancel': dict(bid=.38, cancel_pending=True),
        'journal_error': dict(journal_error=True),
    }.items():
        result = scenario(BOT/'ab.py', 'G5', existing=order(0, oid='original', status='acik'), **opts)
        if name == 'journal_error':
            assert result['posts'] == 0 and result['stopped'] == 'emir_kaydi_hata', result
        else:
            assert result['original_canceled'], (name, result)
        if name in ('gate', 'stale', 'budget', 'uncertain_cancel'):
            assert result['posts'] == 0, (name, result)
        results[name] = result
    partial = scenario(BOT/'ab.py', 'G5', held=0, existing=order(0, qty=2, oid='original', status='acik'), bid=.45)
    assert not partial['original_canceled'] and partial['posts'] == 0, partial
    results['partial_not_rounded_or_replaced'] = partial
    b = load(BOT/'ab.py')
    count = 0
    for net, up_pending, down_pending in itertools.product(range(-10, 11), range(6), range(6)):
        if net+up_pending > 10 or net-down_pending < -10:
            continue
        w = dict(emir=[order(0, max(net, 0)), order(1, max(-net, 0)),
                      {**order(0, status='belirsiz'), 'boy': up_pending},
                      {**order(1, status='acik'), 'boy': down_pending}], klip=5)
        for side in (0, 1):
            size = b.d_miktar(w, side)
            lower = net-down_pending-(size if side == 1 else 0)
            upper = net+up_pending+(size if side == 0 else 0)
            assert lower >= -10-1e-9 and upper <= 10+1e-9
            count += 1
    for block in range(1000):
        assert {g.arm(block*600), g.arm(block*600+300)} == {'G5', 'G4_FIXED'}
    assert g.retain(.2, .4, 5, 0, 'G5') and not g.retain(.2, .4, 0, 5, 'G5')
    assert not g.retain(.5, .4, 5, 0, 'G5')
    proof = dict(status='PASS', cases=results, actual_size_interval_cases=count,
                 paired_assignments=1000, source_sha=sha256((BOT/'ab.py').read_bytes()).hexdigest(),
                 financial_api_calls=0, live_activation=False)
    (HERE/'checks.json').write_text(json.dumps(proof, indent=2)+'\n')
    print(json.dumps({k: v for k, v in proof.items() if k != 'cases'}))


if __name__ == '__main__':
    main()
