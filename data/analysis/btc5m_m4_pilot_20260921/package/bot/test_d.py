"""python3 test_d.py — sahte borsa; ag/kimlik/gercek emir YOK."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
from unittest.mock import patch


def load(path, args=()):
    spec = importlib.util.spec_from_file_location('test_' + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    with patch.object(sys, 'argv', [str(path), *args]):
        spec.loader.exec_module(module)
    return module


def main():
    b = load(Path(__file__).with_name('ab.py'), ['--lane-d'])
    assert b.LANE_D and not b.LIVE and b.KESICI == -10
    assert b.kol_ata('btc', 1) == 'D'
    assert b.LOG.endswith('/LOG_d_kuru.jsonl') and b.STOP.endswith('/STOP_D_KURU')
    repo = '/tmp/polymarket-bosona'
    for args, cwd, expected in [
        (['python3', repo+'/bot/ab.py', '--live'], '/tmp', True),
        (['python3', repo+'-d/bot/d.py', '--live'], '/tmp', True),
        (['python3', 'bot/ab.py', '--live'], repo, True),
        (['python3', 'ab.py', '--live'], repo+'/bot', True),
        (['python3', '-m', 'bot.ab', '--live'], repo, True),
        (['python3', 'ab.py', '--live'], '/tmp/polymarket/data/analysis/pm_merdiven_ab_20260918_v5', True),
        (['python3', '-c', 'pass', '--live'], repo, True),
        (['python3', repo+'-d/bot/d_olcum.py'], '/tmp', False),
        (['python3', repo+'-d/bot/d.py'], '/tmp', False),
        (['python3', '/tmp/other/app.py', '--live'], repo, False),
        (['python3', '-m', 'other', '--live'], '/tmp/other', False),
        (['python3', '/tmp/polymarket-bosonax/bot/ab.py', '--live'], '/tmp', False),
    ]:
        assert b.d_baska_yazici(args, cwd) == expected, (args, cwd)
    assert b.taze_hedef(.75, .76, .01, 10, 0, 5, ort_diger=.20) is None
    assert b.taze_hedef(.75, .76, .01, 10, 0, 5, ort_diger=.20, tamamlayici_bant=True) == .75
    assert b.taze_hedef(.75, .76, .01, 10, 0, 0, tamamlayici_bant=True) is None
    assert b.taze_hedef(.75, .76, .01, 31, 0, 5, ort_diger=.20, tamamlayici_bant=True) is None
    assert b.taze_hedef(.80, .81, .01, 10, 0, 5, ort_diger=.205, tamamlayici_bant=True) == .77

    def order(oi, price, size=5, paid=0, status='kapali', oid=''):
        return dict(oi=oi, p=price, boy=size, pay=paid, durum=status, oid=oid,
                    ofset=price, hedef_ofset=price, bb=price, ack_ms=0,
                    dolumlar=[dict(q=paid, p=price, ms=1)] if paid else [])

    w = dict(emir=[order(0, .20, paid=5)], klip=5, cozuldu=False)
    assert b.d_miktar(w, 1) == 5 and b.d_ort(w, 0) == .20
    w['emir'].append(order(1, .75, paid=2))
    assert b.d_miktar(w, 1) == 3 < b.MIN_EMIR
    w['emir'].append(order(1, .75, size=3, status='belirsiz'))
    assert b.d_miktar(w, 1) == 0
    assert b.d_miktar(w, 1, haric=[w['emir'][-1]]) == 3
    # Eski ucuz cift, yeni pahali tamamlamaya butce olamaz.
    w = dict(emir=[order(0, .30, paid=5), order(1, .60, paid=5), order(0, .60, paid=5)], klip=5)
    w['emir'][-1]['dolumlar'][0]['ms'] = 3
    assert b.d_ort(w, 0) == .60
    assert b.taze_hedef(.53, .54, .01, 10, 5, 10, ort_diger=b.d_ort(w, 0), tamamlayici_bant=True) == .38

    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        b.STATE, b.LOG, b.STOP = map(str, (p/'state.json', p/'log.jsonl', p/'STOP'))
        b.log = lambda event, **kw: None
        # Sunucu degisirken teyitsiz eski emir yeni pencereye tasinamaz.
        inherited = dict(emir=[order(1,.46,status='belirsiz',oid='old')],klip=5,cozuldu=False)
        b.pen[('btc', 1)] = inherited
        with patch.object(b, 'dolum_oku', lambda oid: (None, '')):
            assert not b.d_gecmis_dogrula()
            assert b.pencere_risk(inherited) > 0
        with patch.object(b, 'dolum_oku', lambda oid: (5, 'MATCHED')):
            assert b.d_gecmis_dogrula() and b.d_gecmis_dogrula()
        assert inherited['emir'][0]['pay'] == 5
        assert len(inherited['emir'][0]['dolumlar']) == 1
        assert json.loads(Path(b.STATE).read_text())['pen']['btc|1']['emir'][0]['pay'] == 5
        b.pen.clear()
        b.st['pnl'] = b.st['pnl_yerel'] = -9
        assert b.kesici_asilir(1) and not b.kesici_asilir(.99)
        w = dict(emir=[order(0, .40, status='belirsiz')], klip=5)
        b.pen[('btc', 1)] = w
        assert b.kesici_asilir()  # -9 gerceklesen, 2 belirsiz rezerv.
        b.pen.clear()
        b.st['pnl'] = b.st['pnl_yerel'] = -10
        b.st['durdu'] = 'kesici'
        b.state_kaydet()
        b.st['pnl'] = b.st['pnl_yerel'] = 0
        b.st['durdu'] = None
        b.state_yukle()
        b.D_STATE_HAZIR = True
        assert b.kesici_asilir() and b.st['durdu'] == 'kesici'
        b.st['pnl'] = b.st['pnl_yerel'] = 0
        b.st['durdu'] = None

        # POST calisirken niyet diskte olmali; gec kabul STOP sonrasi kapanmali.
        k = ('btc', 1000)
        w = dict(emir=[], klip=5, cozuldu=False)
        b.pen[k] = w
        entered, release = threading.Event(), threading.Event()
        closed = []
        def post(_):
            state = json.loads(Path(b.STATE).read_text())
            assert state['pen']['btc|1000']['emir'][0]['durum'] == 'belirsiz'
            entered.set()
            assert release.wait(8)
            return [(0, .2, 'D1', 'KABUL')]
        def close(r, reason, key):
            closed.append(r['oid'])
            r['durum'] = 'kapali'
            return True
        b.koy_toplu = post
        b.kapat = close
        b.cozumle = lambda *a, **kw: None
        thread = threading.Thread(target=b.d_koy, args=(k,w,0,'token',.2,5,.19,.21,10))
        b.TAZE_IS[k] = thread
        thread.start()
        assert entered.wait(2)
        stopper = threading.Thread(target=b.d_durdur)
        stopper.start()
        time.sleep(4.2)  # Eski dort saniyelik join bu POST'u kacirirdi.
        assert stopper.is_alive()  # Bekleyen POST atlanmiyor.
        release.set()
        thread.join(3)
        stopper.join(3)
        assert not thread.is_alive() and not stopper.is_alive()
        assert 'D1' in closed and w['emir'][0]['durum'] == 'kapali'
        assert b.d_koy(k,w,0,'token',.2,5,.19,.21,10) is None

        # Baska bota ait emir ne kabul edilir ne de iptal supurmesine katilir.
        b.acik_emirler = lambda: [dict(id='foreign')]
        assert not b.d_acik_kontrol()
        b.acik_emirler = lambda: [dict(id='D1')]
        assert b.d_acik_kontrol()
        b.DURDUR = False
        b.koy_toplu = lambda _: [(1,.3,'','BILINMEYEN')]
        result = b.d_koy(k,w,1,'token2',.3,5,.29,.31,10)
        assert result['durum'] == 'belirsiz' and b.DURDUR and b.pencere_risk(w) > 0

    # Gercek taze_izle -> karar -> kalici niyet -> POST yolu, sahte WS ile.
    b = load(Path(__file__).with_name('ab.py'), ['--lane-d'])
    b.log = lambda *args, **kw: None
    b.tick = lambda _: .01
    b.state_kaydet = lambda: None
    b.STOP = '/__olmayan_d_test_stop__'
    submitted = []
    def post_complete(requests):
        submitted.extend(requests)
        b.DURDUR = True
        return [(1, .75, 'KURU-D-COMPLETE', 'KABUL')]
    b.koy_toplu = post_complete
    class Book:
        def __enter__(self):
            return self
        def __exit__(self, *_):
            return False
        def send(self, _):
            pass
        def recv(self, timeout):
            time.sleep(.01)
            return json.dumps([dict(event_type='book', asset_id=token,
                                    bids=[dict(price=bid,size=10)], asks=[dict(price=ask,size=10)])
                               for token,bid,ask in [('u',.20,.21),('d',.75,.76)]])
    k = ('btc', int(time.time())-10)
    w = dict(emir=[order(0,.20,paid=5)], klip=5, cozuldu=False)
    b.pen[k] = w
    with patch('websockets.sync.client.connect', lambda *a, **kw: Book()):
        worker = threading.Thread(target=b.taze_izle,args=(k,w,{0:'u',1:'d'}),daemon=True)
        worker.start()
        worker.join(3)
        assert not worker.is_alive()
    assert submitted == [(1,'d',.75,5)]

    # Acilis hatasinin finally yolu bozuk state'i sifir muhasebeyle EZEMEZ.
    with tempfile.TemporaryDirectory() as td:
        b.STATE = str(Path(td)/'broken.json')
        Path(b.STATE).write_text('{broken')
        b.D_STATE_HAZIR = False
        b.d_durdur()
        assert Path(b.STATE).read_text() == '{broken'

    obs = load(Path(__file__).with_name('d_olcum.py'))
    rows = obs.prices(dict(topic='crypto_prices_twap_sixty', type='update', timestamp=1789910000120,
                          payload=dict(symbol='btc/usd', timestamp=1789910000000,
                                       full_accuracy_value='65000500000000000000000')), 1789910000200)
    assert rows[0]['price'] == '65000.5'
    assert rows[0]['observed_ms'] < rows[0]['published_ms'] < rows[0]['received_ms']
    assert obs.prices(dict(topic='crypto_prices', payload=dict(symbol='ethusdt')), 1) == []
    assert obs.prices(dict(topic='crypto_prices', type='subscribe',
                          payload=dict(symbol='btc/usd', data=[])), 1) == []
    spot = obs.prices(dict(topic='crypto_prices', type='update',
                          payload=dict(symbol='btcusdt', timestamp=1789910000000,
                                       value=80600.12, full_accuracy_value='80600.12')), 1789910000200)
    assert spot[0]['price'] == '80600.12' and spot[0]['parser_version'] == 2
    print('D GECTI: yazici ayrimi, bant, FIFO, kismi dolum, rezerv, $10/restart, gec POST/STOP, yabanci emir, olcum zamanlari.')


if __name__ == '__main__':
    main()
