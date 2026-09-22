"""Offline 10-day parent/role sample; no API calls, receipts, orders, or PnL inputs."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json


def select(universe, slices, start, end):
    assert start % 86400 == end % 86400 == 0 and end > start, 'full UTC days required'
    assert all(r.get('proxyWallet', '').lower() == '0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
               for s in slices for r in s['rows']), 'wrong wallet activity'
    intervals = sorted((s['start'], s['end']+1) for s in slices if s.get('complete') is True)
    cursor = start
    for low, high in intervals:
        if low <= cursor:
            cursor = max(cursor, high)
    assert cursor >= end, 'MISSING_DATA: complete wallet activity does not cover every second'
    traded = {r['slug'] for s in slices if s.get('complete') is True for r in s['rows']
              if r.get('type') == 'TRADE'}
    markets = [u for u in universe if u.get('group') == 'btc_15m' and start <= u['S'] < end]
    assert len({m['slug'] for m in markets}) == len(markets), 'duplicate official market'
    days = []
    for day in range(start, end, 86400):
        group = sorted((u for u in markets if day <= u['S'] < day+86400), key=lambda u: u['S'])
        assert [u['S'] for u in group] == list(range(day, day+86400, 900)), 'MISSING_DATA: not 96 official slots'
        assert all(u['end']-u['S'] == 900 and u['mechanism'] == 'chainlink_twap60'
                   for u in group), 'wrong contract duration/mechanism'
        active = [u['slug'] for u in group if u['slug'] in traded]
        active.sort(key=lambda slug: (sha256(('btc15-parent-v1:'+slug).encode()).hexdigest(), slug))
        days.append(dict(day=datetime.fromtimestamp(day, timezone.utc).date().isoformat(),
            slots=96, traded=len(active), observed_no_trade=96-len(active), selected=active[:4],
            universe=[dict(slug=u['slug'], activity_present=u['slug'] in traded) for u in group]))
    n = sum(len(day['selected']) for day in days)
    return dict(status='READY_FOR_RECEIPTS' if len(days) >= 10 and n >= 40 else 'UNDERPOWERED',
                protocol='btc15-parent-v1', start=start, end_exclusive=end, min_full_days=10,
                days=days, selected_markets=n, selection_uses_pnl_or_outcome=False,
                scope='Manifest only; fetch all selected-market activity and receipts before role inference.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--universe', type=Path, required=True)
    parser.add_argument('--activity-dir', type=Path, required=True)
    parser.add_argument('--start', required=True, help='inclusive UTC YYYY-MM-DD')
    parser.add_argument('--end', required=True, help='exclusive UTC YYYY-MM-DD')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    paths = [args.universe, *sorted(args.activity_dir.glob('*.json'))]
    inputs = [json.loads(path.read_text()) for path in paths]
    start, end = [int(datetime.fromisoformat(date).replace(tzinfo=timezone.utc).timestamp())
                  for date in (args.start, args.end)]
    try:
        result = select(inputs[0], inputs[1:], start, end)
    except AssertionError as exc:
        result = dict(status='MISSING_DATA', error=str(exc), missing_is_zero_trade=False)
    result['source_sha256'] = {str(p): sha256(p.read_bytes()).hexdigest() for p in paths}
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['days','source_sha256']}, indent=2))
    if result['status'] == 'MISSING_DATA':
        raise SystemExit(2)


if __name__ == '__main__':
    main()
