#!/usr/bin/env python3
"""Salt-okunur pencere muhasebesi. Kimlik dosyasi okumaz, emir gondermez.

python3 muhasebe.py --adres <public-proxy> --baslangic <unix-sn> --api --out /tmp/rapor.json
API olmadan kasette satir bulunmamasi SIFIR DOLUM olarak yorumlanmaz.
"""
import argparse
import collections
from decimal import Decimal
import gzip
import hashlib
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request


def jsonl(path):
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt') as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)  # Bozuk/yarim veri sessizce atlanmaz.


def get(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'python-urllib/3'})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def key(row):
    return tuple(str(row.get(k, '')) for k in
                 ('transactionHash', 'proxyWallet', 'asset', 'side', 'size', 'price'))


def totals(rows, winner):
    quantities = [Decimal(0), Decimal(0)]
    cost = Decimal(0)
    levels = collections.defaultdict(Decimal)
    for r in rows:
        q, p = Decimal(str(r['size'])), Decimal(str(r['price']))
        oi = int(r['outcomeIndex'])
        if not q.is_finite() or not p.is_finite() or q <= 0 or not 0 <= p <= 1 or oi not in (0, 1) or r['side'] not in ('BUY', 'SELL'):
            raise ValueError('Gecersiz dolum')
        signed = q if r['side'] == 'BUY' else -q
        quantities[oi] += signed
        cost += signed * p
        # API fiyatinda USDC yuvarlamasindan ~1e-7 oynama olabiliyor.
        # Yalniz karsilastirma anahtari; maliyet HER ZAMAN ham fiyattan.
        levels[f'{oi}|{p.quantize(Decimal("0.000001")).normalize()}'] += signed
    return dict(q=list(map(float, quantities)), maliyet=float(cost),
                pnl=float(quantities[winner] - cost) if winner is not None else None,
                seviyeler={k: float(v) for k, v in sorted(levels.items())})


def api_trades(address, start, end):
    rows = {}
    for offset in range(0, 10001, 500):
        query = urllib.parse.urlencode(dict(user=address, takerOnly='false', limit=500,
                                           offset=offset, start=max(0, start-600), end=end))
        batch = get('https://data-api.polymarket.com/trades?' + query)
        if not isinstance(batch, list):
            raise ValueError('API islem cevabi liste degil')
        for row in batch:
            if row['proxyWallet'].lower() != address:
                raise ValueError('API yanlis cuzdan dondurdu')
            rows[key(row)] = row
        if len(batch) < 500:
            return list(rows.values())
        time.sleep(0.6)
    raise ValueError('Sayfa sinirina ulasildi; dar zaman araligi gerekli')


def winner_api(slug):
    events = get('https://gamma-api.polymarket.com/events?' + urllib.parse.urlencode({'slug': slug}))
    for event in events:
        for market in event.get('markets', []):
            if market.get('slug') != slug or not market.get('closed'):
                continue
            names = json.loads(market['outcomes'])
            prices = list(map(Decimal, json.loads(market['outcomePrices'])))
            if sorted(prices) == [0, 1]:
                return {'Up': 0, 'Down': 1}[names[prices.index(1)]]
    return None


def compare(local, public):
    """Eski emir logu 2 ondalik: yuvarlamayi eksik bir 5-pay dolumdan ayir."""
    if local is None:
        return 'YEREL_SONUC_YOK'
    levels = collections.defaultdict(float)
    tolerance = collections.defaultdict(float)
    for order in local['emirler']:
        k = f"{order['oi']}|{Decimal(str(order['p'])).normalize()}"
        levels[k] += order['pay']
        tolerance[k] += 0.000001 if order.get('oid') else 0.005
    differences = {k: public['seviyeler'].get(k, 0) - levels.get(k, 0)
                   for k in set(levels) | set(public['seviyeler'])}
    if any(abs(v) > tolerance.get(k, 0) + 1e-6 for k, v in differences.items()):
        return 'FARK'
    if public['pnl'] is not None and abs(public['pnl'] - local['pnl']) > 0.005001:
        return 'FARK'
    return 'YUVARLAMA' if any(abs(v) > 1e-6 for v in differences.values()) else 'UYUMLU'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--adres', required=True)
    parser.add_argument('--baslangic', type=int, default=0)
    parser.add_argument('--api', action='store_true')
    parser.add_argument('--snapshot', type=Path, help='Onceden kaydedilen API/sonuc kaynagi; agsiz tekrar')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.api and args.snapshot:
        parser.error('--api ve --snapshot birlikte kullanilamaz')
    verified = args.api or bool(args.snapshot)
    address = args.adres.lower()
    if len(address) != 42 or not address.startswith('0x') or any(c not in '0123456789abcdef' for c in address[2:]):
        parser.error('adres 0x + 40 hex karakter olmali')
    events = list(jsonl(args.root / 'bot/LOG_ab.jsonl'))
    assigned, closed, versions = {}, {}, {}
    sha = 'legacy'
    for event in events:
        if event['k'] == 'SURUM':
            sha = event['kaynak_sha']
        if event.get('S', 0) < args.baslangic:
            continue
        s = event.get('S')
        if event['k'] in ('pencere', 'GERI_CEKILDI'):
            assigned[s] = event
            versions[s] = sha
        if event['k'] == 'COZULDU':
            closed[s] = event
    slugs = {f"{e.get('sym','btc')}-updown-5m-{s}": s for s, e in assigned.items()}
    tape = {}
    for path in sorted((args.root / 'data/tape_fills').glob('fills_*.jsonl*')):
        for row in jsonl(path):
            if row.get('proxyWallet', '').lower() == address and row.get('slug') in slugs:
                tape[key(row)] = row
    end = max(events[-1]['utc_ms'] // 1000 + 3600, max(assigned, default=0) + 3900)
    snapshot = json.loads(args.snapshot.read_text()) if args.snapshot else {}
    fingerprint = hashlib.sha256(address.encode()).hexdigest()
    if snapshot and snapshot['cuzdan_sha256'] != fingerprint:
        raise ValueError('Snapshot farkli cuzdanin')
    fetched = (api_trades(address, min(assigned, default=args.baslangic), end) if args.api
               else snapshot.get('islemler', []))
    api = {key(r): r for r in fetched if r.get('slug') in slugs}
    grouped = {}
    for label, rows in (('kaset', tape.values()), ('api', api.values())):
        buckets = collections.defaultdict(list)
        for row in rows:
            buckets[slugs[row['slug']]].append(row)
        grouped[label] = buckets
    results = []
    outcomes = {}
    for slug, s in sorted(slugs.items(), key=lambda pair: pair[1]):
        local = closed.get(s)
        winner = local.get('kazanan') if local else None
        if verified:
            official = winner_api(slug) if args.api else snapshot['sonuclar'][slug]
            if winner is not None and official is not None and winner != official:
                raise ValueError(f'Sonuc uyusmazligi: {slug}')
            winner = official  # Sonuc dogrulanamazsa gecmis logu resmi diye sunma.
            outcomes[slug] = official
        sources = {label: totals(rows[s], winner) for label, rows in grouped.items()}
        reference = sources['api'] if verified else sources['kaset']
        status = compare(local, reference)
        if not verified and not grouped['kaset'][s]:
            status = 'KASETTE_YOK'
        if verified and not grouped['api'][s] and not grouped['kaset'][s] and local and local['pay'] == 0:
            status = 'SIFIR_DOLUM'
        sources['api'] = sources['api'] if verified else None
        local_q = ([sum(r['pay'] for r in local['emirler'] if r['oi'] == oi) for oi in (0, 1)]
                   if local else None)
        delta = (dict(q=[reference['q'][i]-local_q[i] for i in (0, 1)],
                      maliyet=reference['maliyet']-local['maliyet'],
                      pnl=reference['pnl']-local['pnl'] if reference['pnl'] is not None else None)
                 if local else None)
        results.append(dict(S=s, kol=assigned[s]['kol'], kaynak_sha=versions[s], durum=status,
                            kazanan=winner, yerel_pnl=local.get('pnl') if local else None,
                            yerel_q=local_q, fark=delta,
                            geri_cekildi=assigned[s]['k'] == 'GERI_CEKILDI', **sources))
    state = json.loads((args.root / 'bot/STATE_ab.json').read_text())
    by_arm = {}
    for arm in ('A', 'B', 'C'):
        rows = [r for r in results if r['kol'] == arm]
        ref = 'api' if verified else 'kaset'
        known = [r for r in rows if r[ref]['pnl'] is not None and r['durum'] != 'KASETTE_YOK']
        pnl = sum(r[ref]['pnl'] for r in known)
        by_arm[arm] = dict(atanan=len(rows), sonucu_bilinen=len(known), islem_pnl=pnl,
                           usd_atanan_pencere=pnl/len(rows) if rows and len(known) == len(rows) else None)
    report = dict(kapsam_baslangic=args.baslangic, log_son_utc_ms=events[-1]['utc_ms'],
                  kaynak_sha256=hashlib.sha256((args.root / 'bot/ab.py').read_bytes()).hexdigest(),
                  cuzdan_sha256=fingerprint,
                  api_okundu=verified, api_sadece_kayit=len(set(api)-set(tape)) if verified else None,
                  kaset_sadece_kayit=len(set(tape)-set(api)) if verified else None,
                  state_pencere=state['st']['pencere'], log_pencere=events[-1].get('pencere'),
                  kapsam='Islem PnL: alis/satis + sonuc odemesi; rebate, taker ucreti ve sabit gider HARIC.',
                  durumlar=dict(collections.Counter(r['durum'] for r in results)), kollar=by_arm,
                  pencereler=results)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if args.api:
        fields = ('proxyWallet', 'transactionHash', 'asset', 'slug', 'outcomeIndex',
                  'side', 'size', 'price', 'timestamp')
        snapshot = dict(cuzdan_sha256=fingerprint, baslangic=min(assigned), son=end,
                        islemler=[{k: r[k] for k in fields} for r in api.values()], sonuclar=outcomes)
        args.out.with_suffix('.kaynak.json').write_text(json.dumps(snapshot, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'pencereler'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
