"""Fixed exploratory sign tests, never a replay of later actor actions."""
from collections import defaultdict
from decimal import Decimal as D
from hashlib import sha256
import json
from pathlib import Path
import random
from statistics import median

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
UNIT = 1_000_000


def read(path):
    return json.loads(path.read_text())


def terminal(cash, up, down, winner):
    return cash + (up if winner == 0 else down)


def close_delta(quantity, cash_cost, held_wins):
    return quantity - cash_cost - quantity * held_wins


def check():
    # Historical entry cash cancels; closing cannot create reverse risk.
    for old_cash in (D('-17.35'), D('-100')):
        for winner in (0, 1):
            before = terminal(old_cash, D(20), D(15), winner)
            after = terminal(old_cash-D('4.95'), D(20), D(20), winner)
            assert after-before == close_delta(D(5), D('4.95'), winner == 0)
    assert terminal(D('-17.35'), D(20), D(15), 1) == D('-2.35')
    assert terminal(D('-22.30'), D(20), D(20), 1) == D('-2.30')
    # Merge preserves terminal wealth but releases operational cash.
    for winner in (0, 1):
        assert terminal(D(-10), D(12), D(8), winner) == terminal(D(-2), D(4), D(0), winner)
    assert close_delta(D(5), D(3), False) == D(2)
    assert close_delta(D(5), D(3), True) == D(-3)


def group_name(row):
    if row['kind'] == 'control':
        return 'no_reducing_fill_controls' if row['no_observed_reduction'] else 'other_fixed_controls'
    return row['role'] + '_' + row['kind']


def sign_test(rows, lag, field):
    available = [r for r in rows if r[lag].get(field) is not None]
    stable = [r for r in available if not r[lag]['inventory_changed_since_cut']]
    return dict(available=len(available), negative=sum(r[lag][field] < -1e-9 for r in available),
                stable_available=len(stable),
                stable_negative=sum(r[lag][field] < -1e-9 for r in stable),
                days=len({r['day'] for r in available}))


def economic_summary(rows):
    days = defaultdict(float)
    for r in rows:
        days[r['day']] += r['delta']
    rng = random.Random(20260922)
    samples = sorted(sum(rng.choices(list(days.values()), k=len(days))) for _ in range(10000)) if days else []
    return dict(n=len(rows), markets=len({r['S'] for r in rows}), days=dict(days),
                delta=sum(r['delta'] for r in rows),
                ex_top3=sum(sorted((r['delta'] for r in rows), reverse=True)[3:]),
                positive=sum(r['delta'] > 0 for r in rows),
                day_bootstrap95=[samples[250], samples[9750]] if samples else None,
                leave_one_day_out={d: sum(days.values())-v for d, v in days.items()})


def analyze(events):
    groups = defaultdict(list)
    for r in events:
        groups[group_name(r)].append(r)
    fields = ('held_bid_change10', 'held_bid_change30', 'held_spot_minus_ref', 'held_twap60_minus_ref')
    signs = {lag: {g: {field: sign_test(rr, lag, field) for field in fields}
                   for g, rr in groups.items()} for lag in ('lag5', 'lag10')}
    inventories = {}
    for g, rr in groups.items():
        vals = [abs(r['net_before_units']) / UNIT for r in rr]
        inventories[g] = dict(n=len(rr), net_min=min(vals), net_median=median(vals), net_max=max(vals),
                              age_median=median(r['age'] for r in rr),
                              at_or_after240=sum(r['age'] >= 240 for r in rr),
                              before10millishares=sum(abs(r['net_before_units']) < 10000 for r in rr))
    execution_rows, fixed = [], {}
    for lag in ('lag5', 'lag10'):
        for age in (120, 240):
            probes = [r for r in events if r['kind'] == 'control' and r['age'] == age]
            usable = []
            for r in probes:
                c = r[lag]
                q = c.get('execution250', {}).get('opposite_buy_5')
                if abs(c['net_at_cutoff_units']) < 5*UNIT or q is None:
                    continue
                assert q['quantity'] == 5
                held_wins = c['held_side'] == r['outcome_label']['winner']
                record = dict(S=r['S'], day=r['day'], nominal_age=age, lag=lag,
                              signal_ms=c['now_ms'], execution_ms=c['execution250']['target_ms'],
                              cash=q['cash'], fee=q['fee'],
                              delta=close_delta(5, q['cash'], held_wins),
                              no_observed_reduction=r['no_observed_reduction'],
                              bid_falling=c.get('held_bid_change10'),
                              spot_against=c.get('held_spot_minus_ref'))
                assert record['execution_ms'] == record['signal_ms'] + 250
                usable.append(record)
            # Two fixed signs, no fitted threshold or combination search.
            fixed[f'{lag}_nominal{age}'] = dict(total_probes=len(probes),
                five_share_quote_available=len(usable),
                all_close=economic_summary(usable),
                bid_falling=economic_summary([r for r in usable if r['bid_falling'] is not None and r['bid_falling'] < -1e-9]),
                spot_against=economic_summary([r for r in usable if r['spot_against'] is not None and r['spot_against'] < -1e-9]))
            execution_rows.extend(usable)
    takers = groups['taker_reduce']
    parity = {}
    for lag in ('lag5', 'lag10'):
        vals = [r[lag].get('opposite_buy_advantage_5') for r in takers]
        vals = [v for v in vals if v is not None]
        parity[lag] = dict(n=len(vals), near_equal=sum(abs(v) <= .00002 for v in vals),
                           min=min(vals) if vals else None, max=max(vals) if vals else None)
    return dict(signs=signs, inventory=inventories, fixed_probe_economics=fixed,
                five_share_buy_vs_sell=parity, execution_rows=execution_rows)


def main():
    check()
    events = read(OUT/'context/events.json')
    assert len(events) == 390 and sum(r['kind'] == 'control' for r in events) == 128
    for r in events:
        for lag in ('lag5', 'lag10'):
            c = r[lag]
            assert c['now_ms'] == (r['ts']-int(lag[3:]))*1000
            for field in ('reference', 'spot', 'twap60'):
                if c.get(field):
                    assert c[field]['received_ms'] <= c['now_ms']
                    assert c[field]['observed_ms'] <= c['now_ms']
            if c.get('book'):
                assert c['book']['snapshot_ms'] <= c['now_ms']
                for b in c['book']['books']:
                    if b is None:
                        continue
                    assert 0 <= c['now_ms']-b['received_ms'] <= 3000
                    assert 0 <= c['now_ms']-b['observed_ms'] <= 3000
    result = analyze(events)
    # Flipping settlement labels cannot change any causal mechanism feature.
    flipped = json.loads(json.dumps(events))
    for r in flipped:
        r['outcome_label']['winner'] = 1-r['outcome_label']['winner']
    alternate = analyze(flipped)
    for name in ('signs', 'inventory', 'five_share_buy_vs_sell'):
        assert result[name] == alternate[name]
    result.update(mode='EXPLORATORY_SAME_POSITION_DIAGNOSTIC_NOT_INDEPENDENT_STRATEGY',
                  limits=['Initial actor inventory is retrospective; no future actor actions are replayed.',
                          '128 fixed probes preserve all64 markets, not only observed closes.',
                          'Nominal120/240 uses signal115/235 at lag5 and110/230 at lag10.',
                          'Each age/lag is a separate comparison, not one combined PnL.',
                          '250ms later depth is a quote-based taker assumption, not guaranteed fills/cancel acknowledgement.',
                          'Public inventory timestamp is not authenticated actor receipt time.',
                          'Rebates and fixed costs excluded; five-share slice does not reproduce actor scale.'],
                  source_sha256={name: sha256((OUT/name).read_bytes()).hexdigest()
                                 for name in ('context/events.json', 'mechanism_protocol.json', 'mechanisms.py')})
    (OUT/'mechanisms.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k in ('fixed_probe_economics', 'five_share_buy_vs_sell')}, indent=2))


if __name__ == '__main__':
    main()
