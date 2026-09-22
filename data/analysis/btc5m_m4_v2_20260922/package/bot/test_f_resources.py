"""Gercek SQLite; normal/hata yollarinda baglanti kapanir. Ag/emir yok."""
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from unittest.mock import patch


def main():
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name('f_model.py')
    spec = importlib.util.spec_from_file_location('checked_model', source)
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    connect = sqlite3.connect
    leaked = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        db, bad, latest = root/'prices.db', root/'empty.db', root/'latest.json'
        latest.write_text(json.dumps({'connected': True}))
        con = connect(db)
        con.execute('CREATE TABLE prices(received_ms, observed_ms, source, price)')
        con.executemany('INSERT INTO prices VALUES(?,?,?,?)',
                        [(ms, ms, s, 80000 + i % 7) for i in range(61)
                         for ms in [1000000 + i * 1000]
                         for s in ('crypto_prices_chainlink', 'crypto_prices_twap_sixty')])
        con.commit()
        con.close()
        connect(bad).close()
        for fn in ('start', 'signal'):
            for broken in (False, True):
                connections = []

                def track(*args, **kwargs):
                    con = connect(*args, **kwargs)
                    connections.append(con)
                    return con

                try:
                    with patch.object(model.sqlite3, 'connect', track):
                        path = bad if broken else db
                        if fn == 'start':
                            model.read_start_report(path, 1000, 1060000)
                        else:
                            model.read_signal(path, latest,
                                              dict(features=model.FEATURES, coef=[0]*4, intercept=0),
                                              dict(S=1000, received_ms=1000000, price=80000), 1000, 1060000)
                except sqlite3.OperationalError:
                    assert broken
                else:
                    assert not broken
                assert len(connections) == 1
                try:
                    connections[0].execute('SELECT 1')
                except sqlite3.ProgrammingError:
                    pass
                else:
                    connections[0].close()
                    leaked.append((fn, broken))
    assert not leaked, ('SQLite baglantisi acik kaldi', leaked)
    print('F kaynak omru GECTI: iki okuyucuda normal/SQL hata yollarinda baglanti kapali.')


if __name__ == '__main__':
    main()
