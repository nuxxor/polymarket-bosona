"""Read-only review of frozen claims; writes only beside this file."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path('/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921')
FABLE = ROOT / 'fable_review_20260921'
OUT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(FABLE / 'code'))
import role_classifier as rc  # noqa: E402
import test_passive_replay as t  # noqa: E402


def main():
    tracked = [FABLE / 'code' / n for n in (
        'passive_replay.py', 'test_passive_replay.py', 'role_classifier.py',
        's_period_level_age.py')]
    tracked += [ROOT / 'candidate.py', ROOT / 'protocol.json']
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked}
    original = [fn for name, fn in vars(t).items() if name.startswith('test_')]
    for fn in original:
        fn()
    rc._test()
    fills = json.loads((ROOT / 'results/fills.json').read_text())
    btc = [x for x in fills if x['group'] == 'btc_15m']
    roles = Counter(rc.role(x['price'], x['cash_price'], x['qty']) for x in btc)
    assert roles == {'maker': 4387, 'taker': 1054}
    late = [x for x in btc if x['opening_kind'] == 'add' and 600 <= x['age'] < 900]
    late_roles = Counter(rc.role(x['price'], x['cash_price'], x['qty']) for x in late)
    assert late_roles == {'maker': 1099, 'taker': 74}

    # Characterization checks: these assert the observed bugs, not correct behavior.
    through = t.run([t.snap(a, .40, .42, .58, .60, 20.) for a in (30, 31, 32)],
                    t.prints((31, t.UP, .39, 1.)))
    assert through['q'][0] == 5.
    gap = t.run([t.snap(a, .40, .42, .58, .60, 0.) for a in (30, 35)],
                t.prints((32, t.UP, .40, 5.)))
    assert gap['q'][0] == 5.
    hedge = t.run([t.snap(a, .40, .42, .58, .60, 0.) for a in range(30, 50)],
                  t.prints(*[(40+i, t.UP, .40, 5.) for i in range(4)]), hedge=True)
    assert abs(hedge['cash'] - 20.336) < 1e-9

    cached = {}
    for folder in ('replay_s_period', 'replay_after_s'):
        p = FABLE / 'results' / folder / 'replay.json'
        d = json.loads(p.read_text())
        hashes[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
        bad = []
        for m in d['markets']:
            for arm, v in m.get('arms', {}).items():
                if not arm.startswith('P0') and v['cash'] > 15 + 1e-8:
                    bad.append(dict(slug=m['slug'], arm=arm, cash=v['cash']))
        cached[folder] = dict(cash_over_15=bad,
                             distinct_markets=len({x['slug'] for x in bad}),
                             passive_only_cases=sum(x['arm'].startswith('P1') for x in bad),
                             summary=d['summary'])
    assert len(cached['replay_s_period']['cash_over_15']) == 19
    # A price ceiling fixed by the predecision probability can reject future
    # execution prices without changing the already-issued decision.
    c = t.pr.c
    f = dict(spot=101., ref=100., final_up_prob=.70)
    intent = c.decide(c.state(), 180, [.4, .6], f)
    assert intent == dict(side=0, qty=5., kind='first')
    frozen_probability = f['final_up_prob']
    executions = {str(px): px <= .55 and frozen_probability-c.unit_cost(px, .07) >= .05
                  for px in (.4, .8)}
    assert executions == {'0.4': True, '0.8': False}
    baseline = json.loads((ROOT / 'btc15_followup/baseline_hashes.json').read_text())
    for path, expected in baseline.items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected
    for path, expected in hashes.items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected
    result = dict(source_hashes=hashes, existing_tests_passed=len(original),
                  roles=dict(roles), late_roles_before_ultra_phase_fix=dict(late_roles),
                  one_share_print_simulated_fill=through['q'][0],
                  implicit_gap_simulated_fill=gap['q'][0], hedge_cash=hedge['cash'],
                  fixed_intent=intent, fixed_ceiling_execution_acceptance=executions,
                  cached_replays=cached, baseline_hashes_unchanged=True,
                  fable_verification_manifest_exists=(FABLE/'results/audit_verification.json').exists(),
                  scope='Limited claim review. No full study or chain decoder rerun.')
    (OUT / 'checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print('Review checks passed; confirmed counterexamples are recorded in checks.json.')


if __name__ == '__main__':
    main()
