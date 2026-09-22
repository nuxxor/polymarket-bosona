"""Unlimited time does not reset money; recorder rotation retains actual events."""
import ast
import gzip
import json
import math
from pathlib import Path
import tempfile
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch

import f_budget
import g_guard
import observer
import pilot
import stream_iz as stream
from test_stream_iz import Wire, MARKETS, ORDER, TRADE, SECRET, main as old_stream_checks


def main():
    old_stream_checks()
    source = Path(__file__).with_name('ab.py')
    tree = ast.parse(source.read_text())
    expiry = next(n.test for n in ast.walk(tree) if isinstance(n, ast.If)
                  and 'MAX_SAAT is not None' in ast.unparse(n.test))
    code = compile(ast.Expression(expiry), str(source), 'eval')
    state = dict(st=dict(pnl=-6.02858, pnl_yerel=-6.02858), pen={})
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root/'STOP_G').touch()
        budget = pilot.activate_files(root, state, dict(checked_ms=1000), 1000)
        assert budget['cutoff'] == budget['anchor']-10 and budget['end_ms'] is None
        assert f_budget.read_budget(root/'BUDGET_G.json', allow_unlimited=True) == budget
        try:
            f_budget.read_budget(root/'BUDGET_G.json')
        except ValueError:
            pass
        else:
            raise AssertionError('F accepted unlimited budget')
        for name in g_guard.REQUIRED:
            (root/name).parent.mkdir(parents=True, exist_ok=True)
            (root/name).write_text('{}')
        (root/'protocol.json').write_text(json.dumps(dict(continuous=True)))
        manifest = {n: pilot.sha(root/n) for n in g_guard.REQUIRED}
        (root/'G_RELEASE.json').write_text(json.dumps(manifest))
        g_guard.verify(root, budget)
        original_budget = (root/'BUDGET_G.json').read_bytes()
        original_run = (root/'RUN_G.json').read_bytes()
        resumed = json.loads((root/'STATE_g.json').read_text())
        resumed['st'].update(pnl=-7, pnl_yerel=-7)
        pilot.resume_files(root, resumed, dict(checked_ms=1000), budget, 1001)
        assert (root/'BUDGET_G.json').read_bytes() == original_budget
        assert (root/'RUN_G.json').read_bytes() == original_run
        assert json.loads((root/'STATE_g.json').read_text())['st']['pnl'] == -7
        resumed['st'].update(pnl=budget['cutoff'], pnl_yerel=budget['cutoff'])
        try:
            pilot.resume_files(root, resumed, dict(checked_ms=1000), budget, 1002)
        except ValueError:
            pass
        else:
            raise AssertionError('Exhausted budget resumed')
        clock = SimpleNamespace(time=lambda: 100*365*86400)
        assert not eval(code, dict(MAX_SAAT=None, time=clock, t0=0, F_BUDGET=budget))
        assert eval(code, dict(MAX_SAAT=12, time=clock, t0=0, F_BUDGET=None))
        assert eval(code, dict(MAX_SAAT=None, time=clock, t0=0, F_BUDGET=dict(end_ms=1)))
        (root/'protocol.json').write_text('{}')
        try:
            g_guard.verify(root, budget)
        except ValueError:
            pass
        else:
            raise AssertionError('Unlimited without frozen protocol')

    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name=='acilis_maruziyeti')
    env = dict(LIVE=True, LANE_D=True, math=math, pen={}, DIS_RISK=7, MUTABAKAT_OK=True,
               adres=lambda: 'test', log=lambda *a, **kw: None, time=SimpleNamespace(sleep=lambda _: None))
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), env)
    calls = []
    def read(*args):
        calls.append(args)
        if len(calls)<3:
            raise OSError('temporary')
        assert env['MUTABAKAT_OK'] is False
        return []
    env['jget'] = read
    assert env['acilis_maruziyeti']()==0 and len(calls)==3 and not env['MUTABAKAT_OK']
    calls.clear()
    def unavailable(*args):
        calls.append(args)
        raise OSError('persistent')
    env.update(jget=unavailable, DIS_RISK=7, MUTABAKAT_OK=True)
    assert env['acilis_maruziyeti']() is None and len(calls)==3 and env['DIS_RISK']==7
    assert not env['MUTABAKAT_OK']

    # London /tmp is a small tmpfs; exercise the recorder on its actual filesystem.
    with tempfile.TemporaryDirectory(dir=source.parent) as td:
        root = Path(td)
        def connect(url, **kwargs):
            return Wire(['PONG', json.dumps([ORDER, TRADE, TRADE])] if url.endswith('/user') else ['PONG'])
        health = root/'health.json'
        result = []
        def capture():
            result.append(stream.capture(root/'chunk', MARKETS, {}, 1.4, 0, threading.Event(),
                                         connect, compressed=True, health_path=health))
        thread = threading.Thread(target=capture)
        thread.start()
        deadline = time.monotonic()+3
        while not health.exists() and time.monotonic()<deadline:
            time.sleep(.02)
        active = json.loads(health.read_text())
        assert active['status']=='active' and all(active['pongs'].values())
        thread.join(3)
        assert not thread.is_alive()
        path, summary = result[0]
        with gzip.open(path, 'rt') as file:
            text = file.read()
        rows = [json.loads(line) for line in text.splitlines()]
        assert SECRET not in text and summary['transport_ok']
        assert len([r for r in rows if r.get('payload', {}).get('event_type')=='trade'])==2
        assert json.loads(health.read_text())['status']=='ended'
        stop = root/'STOP_OBSERVER'
        stop.touch()
        _, summary = stream.capture(root/'stopped', MARKETS, {}, 100, 0, threading.Event(),
                                    connect, compressed=True, stop_path=stop)
        assert not summary['reader_alive'] and not summary['writer_failed']
        with patch.object(stream.shutil, 'disk_usage', return_value=SimpleNamespace(free=0)):
            assert not observer.healthy(root)
            try:
                stream.capture(root/'full', MARKETS, {}, 2, 0, threading.Event(),
                               connect, compressed=True, health_path=health)
            except OSError:
                pass
            else:
                raise AssertionError('Recorder ignored low disk')
        assert json.loads(health.read_text())['status']=='failed'
        run = root/'measurement/run1'
        run.mkdir(parents=True)
        row = dict(pid=123, status='active', at_ns=time.time_ns(),
                   pongs=dict(market=time.time_ns(), user=time.time_ns()), rejected=6, queue_overflow=0)
        observer.write(run/'A.health.json', row)
        with patch.object(Path, 'read_bytes', return_value=str(root/'observer.py').encode()+b'\0A\0'):
            assert observer.healthy(root)  # Existing G1 availability semantics; no completeness claim.
            observer.write(run/'A.health.json', dict(row, queue_overflow=1))
            assert not observer.healthy(root)
            observer.write(run/'A.health.json', dict(row, status='ended'))
            assert not observer.healthy(root)

    for lane, expected in [('A', [900,900]), ('B', [1200,900])]:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            durations, rosters = [], []
            def capture(output, markets, auth, seconds, *args, **kwargs):
                durations.append(seconds)
                if len(durations)==2:
                    (root/'STOP_OBSERVER').touch()
                return None, dict(writer_failed=False, reader_alive=False,
                                  stats={'user': dict(rejected=6, queue_overflow=0)})
            with patch.object(observer, 'HERE', root), \
                    patch.object(stream, 'credentials', return_value=({},0)) as auth, \
                    patch.object(stream, 'roster', side_effect=lambda n: rosters.append(n) or MARKETS), \
                    patch.object(stream, 'capture', capture):
                observer.worker(lane, dict(chunk_seconds=900, first_b_extra_seconds=300))
            assert durations==expected and rosters==[n+30 for n in expected]
            assert auth.call_count==1
    print('PASS: new $10, preserved history, unlimited clock, guard, gzip/multiplicity, PONG health, STOP, low disk, staggered rosters')


if __name__=='__main__':
    main()
