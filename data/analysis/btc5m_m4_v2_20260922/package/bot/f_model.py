"""F fiyat kalitesi; egitimden bagimsiz stdlib tahmin ve gecmis-zaman girdileri."""
import bisect
from contextlib import closing
import hashlib
import json
import math
from pathlib import Path
import sqlite3

FEATURES = ['spot_z', 'twap_z', 'momentum_10s', 'kalan_oran']


def capture_reference(event, market, S, received_ms, start_report=None):
    slug = 'btc-updown-5m-'+str(S)
    if event['slug'] != slug or market['slug'] != slug or market.get('closed') is True:
        raise ValueError('aktif sozlesme eslesmiyor')
    rule = market['description']
    if 'btc-usd-twap-60s-streams' not in rule or json.loads(market['outcomes']) != ['Up','Down']:
        raise ValueError('desteklenmeyen sonuc kurali')
    raw_price = event.get('eventMetadata',{}).get('priceToBeat')
    source = 'gamma'
    if raw_price is None:
        if not start_report or start_report['observed_ms']!=S*1000 or start_report['received_ms']>received_ms:
            raise ValueError('baslangic TWAP raporu yok')
        raw_price = start_report['price']
        source = 'rtds_twap60_exact_start'
    price = float(raw_price)
    if start_report and abs(price-float(start_report['price']))>1e-6:
        raise ValueError('resmi referans / TWAP farki')
    if not math.isfinite(price) or price <= 0 or received_ms < S*1000:
        raise ValueError('referans degeri/zamani')
    return dict(S=S, price=price, received_ms=received_ms, condition=market['conditionId'],
                rule_sha=hashlib.sha256(rule.encode()).hexdigest(), source=source, start_report=start_report)


def read_start_report(db, S, now_ms):
    with closing(sqlite3.connect(Path(db).resolve().as_uri()+'?mode=ro',uri=True,timeout=.25)) as con:
        rows=list(con.execute('SELECT received_ms,observed_ms,price FROM prices WHERE source=? '
                              'AND received_ms BETWEEN ? AND ? AND observed_ms=? ORDER BY received_ms',
                              ('crypto_prices_twap_sixty',S*1000,now_ms,S*1000)))
    if not rows or any(abs(float(r[2])-float(rows[0][2]))>1e-6 for r in rows):
        raise ValueError('tekil baslangic TWAP raporu yok')
    rcv,obs,price=rows[0]
    return dict(received_ms=rcv,observed_ms=obs,price=price)


def features(streams, reference, S, now_ms):
    """streams: kaynak -> (sirali received_ms listesi, (obs_ms, fiyat) listesi)."""
    if not math.isfinite(reference) or reference <= 0 or not 3 <= now_ms / 1000 - S <= 200:
        raise ValueError('referans/zaman')

    def at(source, at_ms):
        times, values = streams[source]
        i = bisect.bisect_right(times, at_ms) - 1
        if i < 0:
            raise ValueError('gecmis eksik')
        obs, price = values[i]
        if not 0 <= at_ms - times[i] <= 3000 or not 0 <= at_ms - obs <= 3000:
            raise ValueError('bayat fiyat')
        if not math.isfinite(price) or price <= 0:
            raise ValueError('gecersiz fiyat')
        return price, times[i], obs

    spot, rcv, obs = at('spot', now_ms)
    twap, trcv, tobs = at('twap60', now_ms)
    history = [at('spot', now_ms - 5000 * i)[0] for i in range(13)]
    sigma = math.sqrt(math.fsum((a-b)**2 for a,b in zip(history, history[1:])) / 60)
    if sigma <= 1e-8:
        raise ValueError('oynaklik yok')
    remaining = S + 300 - now_ms / 1000
    scale = sigma * math.sqrt(remaining)
    x = [(spot-reference)/scale, (twap-reference)/scale,
         (spot-history[2])/(sigma*math.sqrt(10)), remaining/300]
    x = [max(-8, min(8, v)) for v in x]
    return x, dict(spot=spot, twap60=twap, sigma=sigma, spot_received_ms=rcv,
                   spot_observed_ms=obs, twap_received_ms=trcv, twap_observed_ms=tobs)


def probability(model, x):
    if model.get('features') != FEATURES or len(model['coef']) != len(x):
        raise ValueError('model semasi')
    scale=model.get('calibration_scale',1.)
    if not math.isfinite(scale) or scale<=0:
        raise ValueError('kalibrasyon katsayisi')
    z = (model['intercept'] + math.fsum(a*b for a,b in zip(model['coef'], x))) * scale
    if not math.isfinite(z):
        raise ValueError('model sayisi')
    return 1/(1+math.exp(-max(-40, min(40, z))))


def load_model(path):
    raw = Path(path).read_bytes()
    model = json.loads(raw)
    probability(model, [0]*len(FEATURES))
    return model, hashlib.sha256(raw).hexdigest()


def read_signal(db, latest, model, reference, S, now_ms):
    if reference['received_ms'] > now_ms or reference['S'] != S:
        raise ValueError('referans zamani')
    status = json.loads(Path(latest).read_text())
    if status.get('connected') is not True:
        raise ValueError('akis kopuk')
    sources = {'crypto_prices_chainlink':'spot', 'crypto_prices_twap_sixty':'twap60'}
    streams = {s:([],[]) for s in sources.values()}
    with closing(sqlite3.connect(Path(db).resolve().as_uri()+'?mode=ro', uri=True, timeout=.25)) as con:
        rows = con.execute('SELECT received_ms,observed_ms,source,price FROM prices '
                           'WHERE received_ms BETWEEN ? AND ? ORDER BY received_ms',
                           (now_ms-65000,now_ms))
        for rcv,obs,source,price in rows:
            if source not in sources: continue
            times,values=streams[sources[source]]
            if values and obs < values[-1][0]: continue
            times.append(rcv); values.append((obs,float(price)))
    x,meta = features(streams,float(reference['price']),S,now_ms)
    return dict(p_up=probability(model,x), x=x, karar_ms=now_ms, reference=reference, **meta)
