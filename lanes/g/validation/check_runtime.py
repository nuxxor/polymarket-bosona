"""Recheck archived G2 dry runtime; no credentials, network or orders."""
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    archive = HERE/'runtime_v2'
    proof = json.loads((archive/'runtime_final.json').read_text())
    manifest = json.loads((HERE.parent/'bot/G_RELEASE.json').read_text())
    assert proof['sources'] == manifest
    assert proof['original_financial_unchanged'] and proof['open_orders'] == 0
    assert not proof['live_processes'] and not proof['g_processes']
    assert proof['parked'] and not any(proof['financial_files'].values())
    remote = json.loads((archive/'validation_remote.json').read_text())
    assert set(remote) == {'test_g.py', 'test_g_pilot.py', 'test_g_stream.py', 'pilot.py'}
    assert all(x['returncode'] == 0 for x in remote.values())
    rows = [json.loads(line) for line in (archive/'bot/LOG_g_kuru.jsonl').read_text().splitlines()]
    assert all(a['utc_ms'] <= b['utc_ms'] for a, b in zip(rows, rows[1:]))
    first = next(x for x in rows if x['k'] == 'SURUM')
    assert first['kaynak_sha'] == manifest['ab.py'][:12]
    ready = next(x for x in rows if x['k'] == 'hazir')
    assert ready['mod'] == 'KURU' and ready['lane'] == 'G'
    last = rows[-1]
    assert last['k'] == 'bitti' and last['sebep'] == 'sure' and last['risk'] == last['pnl'] == 0
    duration = (last['utc_ms']-first['utc_ms'])/1000
    assert 480 <= duration <= 500
    placements = [x for x in rows if x['k'] == 'taze_koy']
    by_window = Counter(x['S'] for x in placements)
    assert len(by_window) == 2 and all(0 < n <= 60 for n in by_window.values())
    for row in placements:
        assert row['boy'] == 5 and row['kol'] == 'G' and row['oid'].startswith('KURU-')
        assert Decimal(str(row['bb']))-Decimal(str(row['p'])) == Decimal('.01')
        assert row['p'] < row['bb'] < row['ba']
        assert 3 <= row['utc_ms']/1000-row['S'] < 240
    endings = [x for x in rows if x['k'] == 'taze_bitti']
    assert len(endings) == 2 and all(x['dolan'] == 0 and x['ws_hata'] == 0 for x in endings)
    assert any(x['k'] == 'G_KALITE' and x['neden'] == 'time_limit' for x in rows)
    assert not [x for x in rows if 'HATA' in x['k'] or x['k'] in ('state_hata', 'gamma_err', 'dolum')]
    assert proof['dry_state']['pay'] == 0 and proof['dry_state']['order_states'] == ['kapali']
    proof['dry_checks'] = dict(duration_s=duration, windows=len(by_window), intents=len(placements),
                              actual_fills=0, price_qty_time_checks=True, normal_end=True,
                              events=dict(Counter(x['k'] for x in rows)))
    proof['archive_sha256'] = hashlib.sha256((HERE/'validation_final.tar').read_bytes()).hexdigest()
    (HERE/'runtime_final.json').write_text(json.dumps(proof, indent=2)+'\n')
    print(json.dumps(proof['dry_checks']))


if __name__ == '__main__':
    main()
