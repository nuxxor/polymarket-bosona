#!/usr/bin/env python3
"""Cache public data for BTC15m markets recorded in F/raw/books_72h that have already ended.

Per market: Gamma metadata (with closed/outcomePrices), Bosona /activity (market-filtered, paginated),
market-wide /trades (takerOnly=true and false, paginated). Rate limited; never overwrites a cached file.
Writes only under MY/raw/new_period/. No orders, no keys.
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

R = Path('/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921')
SRC = R/'btc15_followup/raw/books_72h/markets'
OUT = R/'fable_review_20260921/raw/new_period'
WALLET = '0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'


def get(url):
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 5:
                time.sleep(20)
                continue
            raise
        except OSError:
            if attempt == 5:
                raise
            time.sleep(3)


def cached(path, url):
    if path.exists():
        return json.load(open(path))['data']
    data = get(url)
    time.sleep(1.1)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(dict(url=url, fetched_ms=round(time.time()*1000), data=data)))
    tmp.replace(path)
    return data


def paged(path, base_query, endpoint):
    if path.exists():
        return json.load(open(path))['pages']
    pages = []
    for offset in range(0, 20001, 500):
        q = dict(base_query, limit=500, offset=offset)
        url = f'https://data-api.polymarket.com/{endpoint}?'+urllib.parse.urlencode(q)
        d = get(url)
        time.sleep(1.1)
        pages.append(dict(url=url, fetched_ms=round(time.time()*1000), n=len(d), rows=d))
        if len(d) < 500:
            break
    else:
        raise ValueError('pagination exhausted')
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(dict(pages=pages)))
    tmp.replace(path)
    return pages


def main():
    now = time.time()
    done = []
    for mf in sorted(SRC.glob('btc-updown-15m-*.json')):
        slug = mf.stem
        S = int(slug.rsplit('-', 1)[1])
        if S+900 > now-120:
            continue
        m = cached(OUT/'markets'/(slug+'.json'), 'https://gamma-api.polymarket.com/markets/slug/'+slug)
        if not m.get('closed'):
            # refresh once if not yet closed at cache time
            p = OUT/'markets'/(slug+'.json')
            age = now*1000-json.load(open(p))['fetched_ms']
            if age > 5*60*1000:
                p.unlink()
                m = cached(p, 'https://gamma-api.polymarket.com/markets/slug/'+slug)
        cond = m['conditionId']
        paged(OUT/'activity'/(slug+'.json'), dict(user=WALLET, market=cond, sortBy='TIMESTAMP', sortDirection='ASC'), 'activity')
        for mode in ('true', 'false'):
            paged(OUT/'market_trades'/f'{slug}_taker{mode}.json', dict(market=cond, takerOnly=mode), 'trades')
        done.append(dict(slug=slug, closed=bool(m.get('closed'))))
        print(slug, 'closed' if m.get('closed') else 'OPEN', flush=True)
    (OUT/'fetch_manifest.json').write_text(json.dumps(dict(fetched_ms=round(time.time()*1000), markets=done), indent=1))


if __name__ == '__main__':
    main()
