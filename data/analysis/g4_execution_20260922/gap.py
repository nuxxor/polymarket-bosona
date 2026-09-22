"""Fixed-clock gap diagnosis; reuses archived prices/books, never fetches or trades."""
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT/'analiz/izleme'))
import bosona_derin as d  # noqa: E402

AGES = (60, 120, 180, 210, 240, 270, 280, 290)
CUTS = (5, 10, 20)  # bps, fixed before outcomes; no threshold search.


def summarize(rows):
    priced = [r for r in rows if r['cost5'] is not None]
    daily = defaultdict(float)
    for r in priced:
        daily[datetime.fromtimestamp(r['S'], timezone.utc).strftime('%Y-%m-%d')] += 5*r['win']-r['cost5']
    pnl = sum(daily.values())
    contributions = sorted((5*r['win']-r['cost5'] for r in priced), reverse=True)
    return dict(n=len(rows), wins=sum(r['win'] for r in rows),
                win_rate=statistics.mean(r['win'] for r in rows) if rows else None,
                priced=len(priced), priced_wins=sum(r['win'] for r in priced),
                mean_cost=statistics.mean(r['cost5']/5 for r in priced) if priced else None,
                pnl=pnl if priced else None, ex_top3=pnl-sum(contributions[:3]) if priced else None,
                daily=dict(daily))


def main():
    protocol = dict(ages=AGES, primary_age=180, gap_bps_cuts=CUTS, z_cuts=(1, 2, 3),
                    execution_lag_ms=250, quote_max_grid_age_ms=1250,
                    source_max_age_ms=3000, clip=5, study='descriptive_existing_history',
                    no_actor_fill_selection=True, no_live_change=True,
                    additional_measure='Received official TWAP60 gap, same clocks/bins, separately from spot')
    (HERE/'gap_protocol.json').write_text(json.dumps(protocol, indent=2)+'\n')
    markets = d.markets()
    streams, starts, excluded = d.deep_prices()
    print('prices loaded', len(markets), len(starts), flush=True)
    snaps, _, _ = d.load_snapshots()
    print('books loaded', len(snaps), flush=True)
    rows, missing = [], Counter()
    for S in range(d.base.START, d.base.END, 300):
        m = markets.get(S)
        if m is None:
            missing['market'] += 1
            continue
        if 'btc-usd-twap-60s-streams' not in m.get('description', ''):
            missing['settlement_rule'] += 1
            continue
        try:
            winner = d.base.outcome(m)
        except ValueError:
            missing['outcome'] += 1
            continue
        for age in AGES:
            now = (S+age)*1000
            if S not in starts or starts[S][0] > now:
                missing[f'{age}:reference'] += 1
                continue
            ref = float(starts[S][1])
            try:
                spot = d.spot_at(streams, now)
            except ValueError:
                missing[f'{age}:spot'] += 1
                continue
            if not ref > 0 or spot == ref:
                missing[f'{age}:invalid_or_tie'] += 1
                continue
            sigma = z = None
            try:
                hist = [d.spot_at(streams, now-i*5000) for i in range(13)]
                sigma = math.sqrt(sum((a-b)**2 for a, b in zip(hist, hist[1:]))/60)
                if sigma > 1e-8:
                    z = abs(spot-ref)/(sigma*math.sqrt(300-age))
            except ValueError:
                pass  # Missing volatility must not erase the raw-gap observation.
            side = 0 if spot > ref else 1
            pair = d.quote_at(snaps, S, now+250)
            cost = None
            if pair and pair[side][6] is not None and pair[side][7] is not None:
                cost = pair[side][6]+pair[side][7]
            rows.append(dict(S=S, age=age, remaining=300-age, side=side, winner=winner,
                             spot=spot, ref=ref, bps=abs(spot-ref)/ref*10000,
                             sigma=sigma, z=z, win=side == winner, cost5=cost,
                             reference_received_ms=starts[S][0]))
            try:
                twap = d.spot_at({'spot': streams['twap60']}, now)
                twap_side = 0 if twap > ref else 1
                twap_cost = pair[twap_side][6]+pair[twap_side][7] if pair and pair[twap_side][6] is not None and pair[twap_side][7] is not None else None
                if twap != ref:
                    rows[-1]['twap'] = dict(price=twap, bps=abs(twap-ref)/ref*10000,
                                           side=twap_side, win=twap_side == winner, cost5=twap_cost)
            except ValueError:
                pass
    assert len({(r['S'], r['age']) for r in rows}) == len(rows)
    assert all(r['reference_received_ms'] <= (r['S']+r['age'])*1000 for r in rows)
    assert summarize([dict(S=0, win=True, cost5=4.99), dict(S=300, win=False, cost5=4.99)])['pnl'] < 0
    groups = {}
    for age in AGES:
        rr = [r for r in rows if r['age'] == age]
        groups[str(age)] = dict(all=summarize(rr), gap={}, z={}, gap_by_z={})
        for i, label in enumerate(('0-5', '5-10', '10-20', '20+')):
            bb = [r for r in rr if bisect_right(CUTS, r['bps']) == i]
            groups[str(age)]['gap'][label] = summarize(bb)
            groups[str(age)]['gap_by_z'][label] = {
                zlab: summarize([r for r in bb if r['z'] is not None and bisect_right((1, 2, 3), r['z']) == j])
                for j, zlab in enumerate(('0-1', '1-2', '2-3', '3+'))}
        for i, label in enumerate(('0-1', '1-2', '2-3', '3+')):
            groups[str(age)]['z'][label] = summarize([r for r in rr if r['z'] is not None and bisect_right((1, 2, 3), r['z']) == i])
    twap_groups = {}
    for age in AGES:
        rr = [dict(S=r['S'], **r['twap']) for r in rows if r['age'] == age and 'twap' in r]
        twap_groups[str(age)] = {label: summarize([r for r in rr if bisect_right(CUTS, r['bps']) == i])
                                for i, label in enumerate(('0-5', '5-10', '10-20', '20+'))}
    result = dict(protocol=protocol, calendar_slots=(d.base.END-d.base.START)//300,
                  start=d.base.START, end=d.base.END, rows=len(rows),
                  markets=len({r['S'] for r in rows}), missing=dict(missing), excluded_prices=excluded,
                  groups=groups, twap_groups=twap_groups, source_hash=sha256(Path(__file__).read_bytes()).hexdigest(),
                  helper_hashes={p.name: sha256(p.read_bytes()).hexdigest() for p in (Path(d.__file__), Path(d.base.__file__))},
                  limitations=['Explored historical days, no clean holdout or calibrated odds.',
                               'Price context may be missing non-randomly; do not count missing as zero.',
                               '250ms is a paper execution scenario, not measured submit latency.',
                               'Z uses past spot volatility and sqrt(time); not official TWAP odds.',
                               'No early bid-depth archive: raw-gap counts and priced counts differ.'])
    (HERE/'gap_rows.json').write_text(json.dumps(rows, sort_keys=True)+'\n')
    (HERE/'gap_results.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k: v['gap'] for k, v in groups.items()}, indent=2))


if __name__ == '__main__':
    main()
