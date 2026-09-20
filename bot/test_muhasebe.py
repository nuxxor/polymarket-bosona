"""Emir gondermeden muhasebe regresyonlari: python3 bot/test_muhasebe.py."""
import copy
import importlib.util
import json
import tempfile
from pathlib import Path
from unittest.mock import patch


def yukle():
    spec = importlib.util.spec_from_file_location('bosona_test', Path(__file__).with_name('ab.py'))
    bot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bot)
    bot.log = lambda *args, **kwargs: None
    bot.state_kaydet = lambda: None
    return bot


def main():
    b = yukle()
    k = ('btc', 1000)
    events = []
    b.log = lambda event, **kw: events.append((event, kw))
    b.resmi_sonuc = lambda *args: 1
    r = dict(oi=0, p=0.3, pay=0.0, durum='kapali', oid='O1',
             ofset=0.3, hedef_ofset=0.3, bb=0.31, ack_ms=0)
    w = dict(cozuldu=False, emir=[r], per=300, kol='C')
    b.pen[k] = w
    b.dolum_oku = lambda oid: (0.0, 'CANCELED')
    b.cozumle(k, w)
    assert w['cozuldu'] and b.st['pnl_yerel'] == 0
    b.dolum_oku = lambda oid: (4.999123, 'MATCHED')
    b.cozumle(k, w, tekrar=True)
    assert abs(b.st['pnl_yerel'] + 1.499737) < 1e-6
    assert b.st['pay'] == 4.999123 and b.st['dolum'] == 1
    once = copy.deepcopy(b.st)
    b.cozumle(k, w, tekrar=True)
    assert b.st == once
    assert sum(e == 'MUHASEBE_DUZELTME' for e, _ in events) == 1
    assert [d for e, d in events if e == 'COZULDU'][-1]['emirler'][0]['pay'] == 4.999123

    for oid in ('', 'O2'):
        w2 = dict(cozuldu=False, emir=[dict(r, oid=oid, pay=0.0, durum='belirsiz')])
        b.cozumle(('btc', 1), w2)
        assert not w2['cozuldu'] and b.pencere_risk(w2) > 0
    w3 = dict(cozuldu=False, emir=[dict(r, pay=0.0)])
    b.dolum_oku = lambda oid: (None, '')
    b.cozumle(k, w3)
    assert not w3['cozuldu'] and w3['emir'][0]['durum'] == 'belirsiz'

    # Restart ayni dolumu bir daha kazanc/zarar yazmaz; acik emir kaybolmaz.
    with tempfile.TemporaryDirectory() as td:
        b.STATE = str(Path(td) / 'state.json')
        Path(b.STATE).write_text(json.dumps({'st': b.st, 'pen': {'btc|1000': w}}))
        b.pen.clear()
        b.state_yukle()
        b.dolum_oku = lambda oid: (4.999123, 'MATCHED')
        b.cozumle(k, b.pen[k], tekrar=True)
        assert b.st == once
        w['cozuldu'] = False
        w['emir'][0]['durum'] = 'acik'
        Path(b.STATE).write_text(json.dumps({'st': b.st, 'pen': {'btc|1000': w}}))
        b.state_yukle()
        assert b.pen[k]['emir'][0]['durum'] == 'belirsiz'
        b.LOG = str(Path(td) / 'log.jsonl')
        Path(b.LOG).write_text(json.dumps({'k': 'bitti', 'pencere': b.st['pencere']+1})+'\n')
        b.LIVE = True
        try:
            b.state_yukle()
            raise AssertionError('Eski state ile acilis engellenmedi')
        except SystemExit as exc:
            assert exc.code == 3

    b = yukle()
    b.LIVE = True  # Sahte client: kimlik/SDK/ag erisimi YOK.
    b.adres = lambda: 'test-wallet'
    b.resmi_sonuc = lambda *args: 1
    b.st['pencereler'] = [list(k)]
    trade = dict(transactionHash='tx', asset='token', outcomeIndex=0, side='BUY',
                 size=5.0, price=0.3, timestamp=1100, slug='btc-updown-5m-1000')
    b.jget = lambda *args: [trade, trade]
    with patch.object(b.time, 'sleep', lambda _: None):
        assert abs(b.mutabakat() + 1.5) < 1e-9  # Tekrarlanan sayfa/satir tek sayilir.
        once = copy.deepcopy(b.st)
        b.jget = lambda *args: []
        assert b.mutabakat() is None and not b.MUTABAKAT_OK
        assert b.st['pnl'] == once['pnl'] and b.st['gorulen_tx'] == once['gorulen_tx']
        b.jget = lambda *args: [trade, dict(trade, price=0.4)]
        assert abs(b.mutabakat() + 3.5) < 1e-9  # Ayni tx/miktar, farkli fiyat kaybolmaz.
        b.jget = lambda *args: [trade]
        assert b.mutabakat() is None and b.st['pnl'] == -3.5
        b.st['gorulen_tx'] = []
        b.st['gorulen_islem'] = []
        b.jget = lambda *args: [trade] * 500
        assert b.mutabakat() is None  # Sayfa tavani tamamlanmis gecmis degildir.
        b.jget = lambda *args: {'error': 'no data'}
        assert b.mutabakat() is None

    b = yukle()
    b.LIVE = True
    class Client:
        def get_open_orders(self):
            return {'error': 'invalid'}

        def get_order(self, oid):
            return {'status': 'CANCELED'}  # Eksik miktar, sifir miktar degildir.
    b.client = Client()
    assert b.acik_emirler() is None
    assert b.dolum_oku('O1') == (None, '')
    b = yukle()
    b.LIVE = True
    b.adres = lambda: 'test-wallet'
    b.resmi_sonuc = lambda *args: 1
    b.st['pencereler'] = [list(k)]
    w = dict(cozuldu=True, kazanan=1, emir=[dict(r, pay=0.0, durum='kapali')])
    w['hesap'] = b.pencere_hesabi(w, 1)
    b.pen[k] = w
    b.jget = lambda *args: [trade]
    b.dolum_oku = lambda oid: (5.0, 'MATCHED')
    with patch.object(b.time, 'sleep', lambda _: None):
        assert b.mutabakat() == -1.5
        assert b.st['pnl_yerel'] == -1.5 and b.MUTABAKAT_OK
        assert b.mutabakat() == -1.5 and b.st['pay'] == 5.0
        w['emir'][0]['durum'] = 'belirsiz'
        b.dolum_oku = lambda oid: (None, '')
        assert b.mutabakat() is None and not b.MUTABAKAT_OK
    assert b.pencere_risk(dict(cozuldu=True, emir=[dict(r, pay=2, durum='belirsiz')])) > 0
    # Gercek API'deki mikro fiyat farki maliyette korunur, sahte dolum farki uretmez.
    path = Path(__file__).resolve().parents[1] / 'analiz/izleme/muhasebe.py'
    spec = importlib.util.spec_from_file_location('audit_test', path)
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    local = dict(pnl=-1.5, emirler=[dict(oi=0, p=0.3, pay=5.0)])
    public = audit.totals([dict(size=4.999999, price=0.30000001, outcomeIndex=0, side='BUY')], 1)
    assert audit.compare(local, public) in ('UYUMLU', 'YUVARLAMA')
    missing = audit.totals([dict(size=10, price=0.3, outcomeIndex=0, side='BUY')], 1)
    assert audit.compare(local, missing) == 'FARK'
    print('Muhasebe regresyonlari: GECTI (gec/tekrarli/eksik dolum, restart, rezerv, sayfalama).')


if __name__ == '__main__':
    main()
