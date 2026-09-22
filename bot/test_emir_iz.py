"""Sahte SDK, gercek bot fonksiyonlari. Emir/ag/kimlik dosyasi erisimi yok."""
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
from unittest.mock import patch

import emir_iz as iz

OID = ['0x' + f'{i:064x}' for i in range(1, 4)]
CANARY = 'TEST_ONLY_DO_NOT_LOG_THIS_TEXT'


class SDK:
    def create_order(self, args):
        return {'signature': CANARY, 'private_key': CANARY}

    def post_orders(self, args, post_only):
        assert post_only
        return [{'orderID': oid, 'success': True, 'headers': CANARY} for oid in OID[:len(args)]]

    def post_order(self, order, kind):
        return {'orderID': OID[2], 'success': True, 'signature': CANARY}

    def cancel_order(self, payload):
        return {'canceled': [payload.orderID], 'headers': CANARY}

    def cancel_orders(self, ids):
        return {'canceled': [ids[0]], 'not_canceled': {ids[1]: CANARY}}

    def get_order(self, oid):
        return {'id': oid, 'size_matched': '2.5', 'status': 'LIVE', 'secret': CANARY}

    def get_open_orders(self):
        return [self.get_order(OID[0])]


def check(bot_path, output, args=()):
    assert not output.exists(), 'Use a fresh smoke output path'
    spec = importlib.util.spec_from_file_location('telemetry_smoke_bot', bot_path)
    b = importlib.util.module_from_spec(spec)
    with patch.object(sys, 'argv', [str(bot_path), *args]), \
            patch.object(sys, 'path', [str(bot_path.parent), *sys.path]):
        spec.loader.exec_module(b)  # LIVE yok; credentials dalina girmez.
    g = iz.Gunluk(output, 'MOCK', bot_path)
    b.LIVE, b.client, b.log = True, SDK(), lambda *a, **kw: None
    b.OrderArgs = b.PostOrdersV2Args = b.OrderPayload = SimpleNamespace
    b.OrderType, b.BUY = SimpleNamespace(GTC='GTC', FAK='FAK'), 'BUY'
    with patch.object(iz, 'aktif', g):
        got = b.koy_toplu([(0, '123', .4, 5), (1, '456', .5, 5)])
        assert got == [(0, .4, OID[0], 'KABUL'), (1, .5, OID[1], 'KABUL')]
        canceled = b.iptal_toplu(OID[:2])
        assert canceled[OID[0]][0] and not canceled[OID[1]][0]
        assert b.dolum_oku(OID[0]) == (2.5, 'LIVE')
        r = dict(oid=OID[0], oi=0, p=.4, pay=0, durum='acik')
        b.kapat(r, 'test')  # Canceled cevabina ragmen LIVE: kapanmis sayilamaz.
        assert r['durum'] == 'belirsiz' and r['pay'] == 2.5
        assert not b.pay_ekle(r, 2.5, 'duplicate')
        assert b.pay_ekle(r, 5, 'poll')
        assert len(b.acik_emirler()) == 1
        b.TAMAMLA_ACIK, b.state_kaydet = True, lambda: None
        b.TOK[('btc', 1)] = ['123', '456']
        b.defter = lambda *a: ([], [(.4, 10)])
        w = {'emir': [dict(oi=0, p=.2, pay=5, dolum_ms=1, durum='kapali')]}
        b.tamamla(('btc', 1), w)
        assert w['emir'][-1]['oid'] == OID[2] and w['emir'][-1]['pay'] == 2.5
        reply = {'orderID': OID[2], 'success': True, 'signature': CANARY}

        # POST devam ederken iptal cevabi gelebilir: iki farkli deneme/saat cifti.
        entered, release = threading.Event(), threading.Event()
        original = b.client.post_orders

        def delayed(*args, **kwargs):
            entered.set()
            assert release.wait(3)
            return original(*args, **kwargs)

        with patch.object(b.client, 'post_orders', delayed), ThreadPoolExecutor(2) as pool:
            future = pool.submit(b.koy_toplu, [(0, '123', .4, 5)])
            assert entered.wait(3)
            assert b.iptal(OID[1])[0]
            release.set()
            assert future.result()[0][2] == OID[0]
        with ThreadPoolExecutor(4) as pool:
            assert list(pool.map(b.dolum_oku, [OID[0]] * 20)) == [(2.5, 'LIVE')] * 20

        with patch.object(b.client, 'post_orders', side_effect=[TimeoutError(CANARY),
                          [{'orderID': OID[0], 'success': True}]]):
            assert b.koy_toplu([(0, '123', .4, 5)])[0][3] == 'BILINMEYEN'
            assert b.koy_toplu([(0, '123', .4, 5)])[0][3] == 'KABUL'

        ex = TimeoutError(CANARY)

        def fail():
            raise ex

        try:
            iz.cagir('post', {}, fail)
            raise AssertionError('exception lost')
        except TimeoutError as got:
            assert got is ex

        # Bozuk yanit sifir dolum veya basarili iptal diye kaydedilemez.
        for op, result, meta in [('get_order', {'size_matched': 'NaN'}, {}),
                                 ('cancel', {}, {'oids': [OID[0]]}),
                                 ('post_batch', {}, {})]:
            assert iz.cagir(op, meta, lambda: result) is result
        # Duvar saati geriye sicrasa da SDK suresi monotonic kalir.
        times = iter(range(100000, 0, -1))
        with patch.object(iz.time, 'time_ns', lambda: next(times)):
            b.dolum_oku(OID[0])
        g.yaz('session_end')

    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert CANARY not in output.read_text()
    assert [r['seq'] for r in rows] == list(range(1, len(rows)+1))
    assert not any(r['errors'] for r in rows)
    requests = {r['attempt']: r for r in rows if r['event'] == 'request'}
    responses = {r['attempt']: r for r in rows if r['event'] in ('response', 'error')}
    assert requests.keys() == responses.keys()
    assert len(requests) == sum(r['event'] == 'request' for r in rows)
    for aid, req in requests.items():
        res = responses[aid]
        assert req['mono_ns'] <= res['begin']['mono_ns'] <= res['end']['mono_ns'] <= res['mono_ns']
        assert res['duration_ns'] == res['end']['mono_ns'] - res['begin']['mono_ns']
    fills = [r for r in rows if r['event'] == 'fill_observed']
    assert [r['delta'] for r in fills] == [2.5, 2.5, 2.5]
    assert [r['oid'] for r in fills] == [OID[0], OID[0], OID[2]]
    assert all(r['exchange_ns'] is None for r in fills)
    cancel = next(r for r in responses.values() if r['op'] == 'cancel_batch')
    assert cancel['reply']['items'][1] == dict(oid=OID[1], canceled=False, not_canceled=True)
    unknown = [r for r in responses.values() if r['op'] == 'cancel'][-1]
    assert unknown['reply']['items'][0]['canceled'] is None
    jumped = list(responses.values())[-1]
    assert jumped['end']['utc_ns'] < jumped['begin']['utc_ns'] and jumped['duration_ns'] >= 0

    # Dosya dolu/izin yok: kabul cevabi ve asil SDK istisnasi aynen korunur.
    damaged = iz.Gunluk(output.with_suffix('.damaged.jsonl'), 'MOCK', bot_path)
    with patch.object(iz, 'aktif', damaged):
        with patch.object(Path, 'open', side_effect=OSError(CANARY)):
            assert iz.cagir('post', {}, lambda: reply) is reply
            try:
                iz.cagir('post', {}, fail)
                raise AssertionError('original exception lost')
            except TimeoutError as got:
                assert got is ex
        damaged.yaz('session_end')
    assert damaged.errors == 4
    bad_rows = [json.loads(s) for s in damaged.path.read_text().splitlines()]
    assert bad_rows[-1]['errors'] == 4 and bad_rows[-1]['seq'] == 6
    assert CANARY not in damaged.path.read_text()
    return dict(source=str(bot_path), events=len(rows), attempts=len(requests),
                fill_observations=len(fills), mode='MOCK', lane_args=list(args), healthy=True,
                failure_session_detected=True)


def main():
    bot = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name('ab.py')
    args = sys.argv[3:]
    assert args in ([], ['--lane-d'], ['--lane-e'], ['--lane-f'])
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(tmp)/'smoke.jsonl'
        # Herhangi bir yanlislikla gercek borsaya erisim denemesi testi dusurur.
        with patch('socket.socket', side_effect=AssertionError('network forbidden')):
            result = check(bot, out, args)
        print(json.dumps(result))


if __name__ == '__main__':
    main()
