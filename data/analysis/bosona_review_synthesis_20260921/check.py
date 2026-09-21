"""Read-only synthesis checks; no orders, network calls or runtime changes.

The costly historical reproduction reuses the adjacent independent review's
check.py. Its isolated output is calculations.json; this check verifies that
output and adds the four PRO cases and two narrowly scoped diagnostics.
"""
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent
DATA = ROOT / 'data/analysis'


def main():
    original = DATA / 'bosona_independent_review_20260921/calculations.json'
    reproduced = OUT / 'calculations.json'
    assert json.loads(original.read_text()) == json.loads(reproduced.read_text())
    calc = json.loads(reproduced.read_text())
    assert calc['raw_multiplicity']['pnl'] == '8313.228464'
    assert calc['execution_roles']['counts'] == {
        'opposite_token_BUY_fee_False': 3599,
        'same_token_BUY_fee_True': 316, 'same_token_SELL_fee_False': 416}
    activity_path = DATA / 'bosona_gec_20260921/activity.json'
    activity = json.loads(activity_path.read_text())
    cases = {}
    for start, winner, expected, count in (
        (1789852200, 1, '76.359200', 3),
        (1789852800, 0, '-30.15236', 6),
        (1789853400, 1, '4.7405', 3),
        (1789853700, 0, '-210.225162', 14),
    ):
        buys = [r for r in activity if r.get('slug') == f'btc-updown-5m-{start}'
                and r['type'] == 'TRADE']
        assert len(buys) == count and all(r['side'] == 'BUY' for r in buys)
        cash = sum(D(str(r['usdcSize'])) for r in buys)
        payout = sum(D(str(r['size'])) for r in buys if r['outcomeIndex'] == winner)
        assert payout - cash == D(expected)
        cases[str(start)] = dict(records=count, cash=str(cash), pnl=str(payout-cash))
    assert D('38.77') * (1-D('.959')) == D('1.58957')
    snapshot_path = DATA / 'btc5m_status_20260921_1740/snapshot.json'
    snapshot = json.loads(snapshot_path.read_text())
    for profile in snapshot['profiles'].values():
        assert profile['hashes'] == profile['manifest']['source_sha256']
        assert not profile['partial_last']

    # Reproduce the request/receipt boundary defect without querying Binance.
    source = ROOT / 'analiz/izleme/bosona_rebound_shadow.py'
    sys.path.insert(0, str(source.parent))
    spec = importlib.util.spec_from_file_location('synthesis_rebound', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    start = 22 * 60000
    rows = [[i*60000, '1', '1', '1', '1', '0', (i+1)*60000-1]
            for i in range(23)]
    with patch.object(module, 'now_ms', side_effect=[start+59500, start+62200]), \
            patch.object(module.base, 'get', return_value=rows):
        result = module.bars()
    assert result['rows'][-1][6] > result['request_ms']
    sd_drop = 1 - 110.755 / 137.451
    variance_drop = 1 - (110.755 / 137.451)**2
    assert .194 < sd_drop < .195 and .350 < variance_drop < .351
    evidence = dict(
        ultra_reproduction='exact JSON equality', pro_cases=cases,
        pro_local_exit_contribution='1.58957',
        runtime_hashes_match_at_ms=snapshot['captured_ms'],
        request_boundary_defect_reproduced=True,
        fable_reported_table_sd_drop=sd_drop,
        fable_reported_table_variance_drop=variance_drop,
        limits='Archival diagnostics; no parent order/onchain role proof or whole-policy causal PnL.',
        input_sha256={str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
                      for p in (original, reproduced, activity_path, snapshot_path, source)},
    )
    (OUT / 'verification.json').write_text(json.dumps(evidence, indent=2)+'\n')
    print('PASS: Ultra output, four PRO paths, runtime hashes, candle-boundary reproduction, SD arithmetic')


if __name__ == '__main__':
    main()
