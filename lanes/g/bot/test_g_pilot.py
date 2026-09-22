"""G operator kapisi: yalniz gecici dosya ve sahte SDK/exec."""
import ast
import copy
import json
import math
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pilot as m4


def positions_check():
    for folder in ('polymarket-bosona-f',):
        path = Path(__file__).with_name('ab.py')
        function = next(n for n in ast.parse(path.read_text()).body
                        if isinstance(n, ast.FunctionDef) and n.name == 'acilis_maruziyeti')
        env = dict(LIVE=True, LANE_D=True, math=math, pen={}, DIS_RISK=8,
                   adres=lambda: 'test', log=lambda *a, **kw: None)
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), 'exec'), env)
        first = [dict(asset=str(i), conditionId='c'+str(i), slug='s'+str(i),
                      size=5, avgPrice=.4, redeemable=True) for i in range(500)]
        extra = dict(asset='extra', conditionId='other', slug='other',
                     size=.01, avgPrice=.4, redeemable=False, outcome='Up')
        calls = []

        def read(url, timeout):
            query = parse_qs(urlsplit(url).query)
            assert query['sizeThreshold'] == ['0'] and query['includeArchived'] == ['true']
            offset = int(query['offset'][0])
            calls.append(offset)
            return first if offset == 0 else [extra]

        env['jget'] = read
        result = env['acilis_maruziyeti']()
        assert calls == [0, 500]
        assert result is None if folder.endswith('-f') else result == .004
        extra['redeemable'] = True
        assert env['acilis_maruziyeti']() == 0
        for bad in (None, {}, [first[0]], [dict(extra, size=float('nan'))],
                    [dict(extra, redeemable='false')], [dict(extra, avgPrice=-1)]):
            env['DIS_RISK'] = 8
            env['jget'] = lambda url, timeout, bad=bad: first if 'offset=0&' in url else bad
            assert env['acilis_maruziyeti']() is None and env['DIS_RISK'] == 8
        env['jget'] = lambda *a: []
        assert env['acilis_maruziyeti']() == 0


def main():
    positions_check()
    from f_budget import read_budget
    client = m4.ReadOnly(SimpleNamespace(get_open_orders=lambda: [], host='test'))
    assert client.get_open_orders() == [] and client.host == 'test'
    for name in ('post_order', 'post_orders', 'cancel_order', 'cancel_orders', 'cancel_all', 'create_order'):
        try:
            getattr(client, name)
        except RuntimeError:
            pass
        else:
            raise AssertionError(name)
    state = {'st': {'pnl': -12.3, 'pnl_yerel': -12.30001, 'emir': 624, 'pencere': 70,
                    'f_budget_id': 'old', 'durdu': 'hata'},
             'pen': {'btc|1': {'cozuldu': True, 'emir': []}}}
    original = copy.deepcopy(state)
    proof = {'checked_ms': 1000000, 'pnl': -12.30001}
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root/'STOP_G').touch()
        budget = m4.activate_files(root, state, proof, 1000000)
        assert state == original
        assert budget['anchor'] == -12.30001 and budget['cutoff'] == -22.30001
        assert budget['end_ms'] == 2800000 and read_budget(root/'BUDGET_G.json') == budget
        loaded = json.loads((root/'STATE_g.json').read_text())
        assert loaded['pen'] == state['pen'] and loaded['st']['emir'] == 624
        assert loaded['st']['pnl_yerel'] == state['st']['pnl_yerel']
        assert loaded['st']['f_budget_id'] == budget['id'] and loaded['st']['durdu'] is None
        assert not (root/'STOP_G').exists() and (root/'STOP_G.operator_once').exists()
        try:
            m4.activate_files(root, state, proof, 1000001)
        except ValueError:
            pass
        else:
            raise AssertionError('Budget reset')
    for case in ('stale', 'future', 'nan', 'nan_local', 'partial', 'no_park'):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            if case != 'no_park':
                (root/'STOP_G').touch()
            s = copy.deepcopy(state)
            now = 1030001 if case == 'stale' else 999999 if case == 'future' else 1000000
            if case == 'nan':
                s['st']['pnl'] = float('nan')
            if case == 'nan_local':
                s['st']['pnl_yerel'] = float('nan')
            if case == 'partial':
                (root/'RUN_G.json').write_text('{}')
            try:
                m4.activate_files(root, s, proof, now)
            except ValueError:
                pass
            else:
                raise AssertionError(case)
            assert not (root/'STATE_g.json').exists()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        protocol = {'minutes': 30, 'loss_limit': 10, 'clip': 5}
        (root/'protocol.json').write_text(json.dumps(protocol))
        for name in m4.REQUIRED-{'protocol.json'}:
            (root/name).parent.mkdir(parents=True, exist_ok=True)
            (root/name).write_text('test fixture')
        (root/'G_RELEASE.json').write_text(json.dumps({name: m4.sha(root/name) for name in m4.REQUIRED}))
        assert m4.verify(root) == protocol
        with patch.object(m4, '__file__', str(root/'m4.py')), \
                patch.object(sys, 'argv', ['m4.py']), \
                patch.object(m4, 'preflight', return_value=(state, proof)), \
                patch.object(m4.os, 'execv', side_effect=AssertionError('Default must not launch')):
            m4.main()
        assert not (root/'RUN_G.json').exists() and not (root/'BUDGET_G.json').exists()
        (root/'protocol.json').write_text('{}')
        try:
            m4.verify(root)
        except ValueError:
            pass
        else:
            raise AssertionError('Modified release')
    print('G GECTI: salt-okunur SDK, varsayilan emir yok, hash, tek kullanim, 30dk/$10, eski muhasebe.')


if __name__ == '__main__':
    main()
