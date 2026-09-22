#!/usr/bin/env python3
"""Finite offline BTC15 selection audit; no fitting, threshold search or writes to R."""
import bisect
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics as st

HERE = Path(__file__).resolve().parent
R = Path('/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921')
INPUTS = {}


def read(path):
    raw = path.read_bytes()
    INPUTS[str(path)] = hashlib.sha256(raw).hexdigest()
    return json.loads(raw)


def at(history, now):
    i = bisect.bisect_right([x['t'] for x in history], now)-1
    if i < 0 or not 0 <= now-history[i]['t'] <= 75:
        return None
    price = float(history[i]['p'])
    return (price, now-history[i]['t']) if 0 < price < 1 else None


def stats(values):
    if not values:
        return dict(n=0)
    return dict(n=len(values), median=st.median(values), mean=st.mean(values),
                minimum=min(values), maximum=max(values))


def summary(rows):
    joint = [x for x in rows if x['context'] and x['price']]
    return dict(markets=len(rows), context=sum(x['context'] for x in rows),
                price=sum(x['price'] for x in rows), joint=len(joint),
                sigma=stats([x['sigma'] for x in joint]),
                sigma_bp_per_sqrt_second=stats([x['sigma_bp'] for x in joint]),
                up_price=stats([x['up_price'] for x in joint]),
                cheaper_price=stats([x['cheaper_price'] for x in joint]),
                absolute_price_imbalance=stats([x['price_imbalance'] for x in joint]),
                price_age=stats([x['price_age'] for x in joint]))


def run():
    assert at([dict(t=100, p=.4), dict(t=200, p=.8)], 150) == (.4, 50)
    assert at([dict(t=100, p=.4)], 99) is None
    assert at([dict(t=100, p=.4)], 176) is None
    universe = [x for x in read(R/'results/universe.json') if x['group'] == 'btc_15m']
    windows = {x['slug']: x for x in read(R/'results/windows.json') if x['group'] == 'btc_15m'}
    contexts = read(R/'raw/btc15_context.json')
    tokens = {x['slug']: json.loads(read(R/'raw/markets'/f"{x['slug']}.json")['clobTokenIds']) for x in universe}
    wanted = {t for pair in tokens.values() for t in pair}
    histories = {}
    for path in sorted((R/'raw/histories').glob('*.json')):
        for token, history in read(path)['response']['history'].items():
            if token in wanted:
                if token in histories:
                    assert histories[token] == history
                histories[token] = history
    rows = []
    for w in sorted(universe, key=lambda x: x['S']):
        day = datetime.fromtimestamp(w['S'], timezone.utc).strftime('%Y-%m-%d')
        hour = datetime.fromtimestamp(w['S'], timezone.utc).hour
        owned = windows.get(w['slug'])
        first_age = owned['first_age'] if owned else None
        state = ('no_observed_trade' if first_age is None else 'entered_by180' if first_age <= 180
                 else 'first_at_or_after_end' if first_age >= 900 else 'later_first_entry')
        when = w['S']+180
        context = contexts.get(f"{w['S']}:{when}")
        prices = [at(histories.get(t, []), when) for t in tokens[w['slug']]]
        available = all(x is not None for x in prices)
        x = dict(slug=w['slug'], S=w['S'], day=day, hour=hour, traded=bool(owned),
                 first_age=first_age, state_at180=state, context=bool(context), price=available)
        if context:
            assert context['now'] == when and context['reference_received_ms'] <= when*1000
            x.update(sigma=context['sigma'], sigma_bp=context['sigma']/context['spot']*10000)
        if available:
            p0, p1 = [v[0] for v in prices]
            x.update(up_price=p0, cheaper_price=min(p0, p1),
                     price_imbalance=abs(p0-p1), price_age=max(v[1] for v in prices))
        rows.append(x)
    by_day = defaultdict(list)
    for x in rows:
        by_day[x['day']].append(x)
    assert len(rows) == 816 and sum(x['traded'] for x in rows) == 598
    full_days = sorted(day for day, values in by_day.items() if len(values) == 96)
    assert len(full_days) == 8
    full = [x for x in rows if x['day'] in full_days]
    assert len(full) == 768
    days = {}
    for day, rr in sorted(by_day.items()):
        hours = {str(h): dict(n=len(v), traded=sum(x['traded'] for x in v),
                             rate=sum(x['traded'] for x in v)/len(v))
                 for h in sorted({x['hour'] for x in rr}) if (v := [x for x in rr if x['hour'] == h])}
        assert all(v['n'] == 4 for v in hours.values())
        days[day] = dict(n=len(rr), traded=sum(x['traded'] for x in rr),
                        rate=sum(x['traded'] for x in rr)/len(rr), full=day in full_days,
                        by_hour=hours, context=summary(rr))
    hours = {}
    for h in range(24):
        vv = [x for x in full if x['hour'] == h]
        rates = {day: days[day]['by_hour'][str(h)]['rate'] for day in full_days}
        loo = {day: sum(x['traded'] for x in vv if x['day'] != day)/28 for day in full_days}
        hours[str(h)] = dict(n=len(vv), traded=sum(x['traded'] for x in vv),
                            rate=sum(x['traded'] for x in vv)/len(vv), by_day=rates,
                            day_range=max(rates.values())-min(rates.values()),
                            leave_one_day=loo, loo_range=max(loo.values())-min(loo.values()))
    loo_all = {day: sum(x['traded'] for x in full if x['day'] != day)/672 for day in full_days}
    comparison = {}
    for label, rr in [('full_days', full), ('including_update', rows)]:
        comparison[label] = dict(
            traded=summary([x for x in rr if x['traded']]),
            no_observed_trade=summary([x for x in rr if not x['traded']]),
            at180={state: summary([x for x in rr if x['state_at180'] == state])
                   for state in ('entered_by180', 'later_first_entry', 'first_at_or_after_end', 'no_observed_trade')})
    byday_context = {day: {label: summary([x for x in rr if x['traded'] == flag])
                           for label, flag in [('traded', True), ('no_observed_trade', False)]}
                     for day, rr in sorted(by_day.items())}
    result = dict(scope='BTC15 UTC start-hour bins; descriptive, no fitted model/threshold search',
                  total=816, traded=598, full_day_total=768, full_day_traded=sum(x['traded'] for x in full),
                  days=days, hours=hours, leave_one_day=loo_all,
                  comparison=comparison, byday_context=byday_context,
                  states=dict(Counter(x['state_at180'] for x in rows)), rows=rows, input_sha256=INPUTS)
    (HERE/'selection_audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    report = ['# BTC15 piyasa seçimi ve saat: küçük bağımsız ek', '',
        'Bu inceleme yalnız resmî BTC15 evrenini ve karar öncesi arşiv girdilerini okur; model öğrenmez, eşik aramaz. Saat UTC sözleşme başlangıcıdır. Etiket kamu dolumu gözlenmesidir; emir gönderme/iptal veya fırsat yokluğu anlamına gelmez.', '',
        '## Takvim ve saat', '', '| UTC gün | Resmî pencere | İşlemli | Oran | Tam gün |', '|---|---:|---:|---:|---|']
    for day, info in days.items():
        report.append(f"| {day} | {info['n']} | {info['traded']} | {100*info['rate']:.2f}% | {info['full']} |")
    report += ['', f"**DOĞRULANDI:** sekiz tam gün 768 pencerenin {result['full_day_traded']}'inde işlem var; 21 Eylül 00–12 UTC ayrı 48 pencere, işlem yok. Yarım gün tam günlerin saat oranına katılmadı. Bir tam gün çıkarılınca genel işlem oranı %{100*min(loo_all.values()):.2f}…%{100*max(loo_all.values()):.2f}.", '',
        '| UTC saat | İşlemli /32 | Günler arası oran min–max | Bir gün çıkarılmış oran min–max |', '|---|---:|---:|---:|']
    for hour, info in hours.items():
        report.append(f"| {hour.zfill(2)} | {info['traded']}/32 | %{100*min(info['by_day'].values()):.0f}–%{100*max(info['by_day'].values()):.0f} | %{100*min(info['leave_one_day'].values()):.1f}–%{100*max(info['leave_one_day'].values()):.1f} |")
    report += ['', '**GÖZLEMSEL DESTEK / SINIR:** her saat-gün hücresi yalnız dört sözleşmedir. Tam saat tablosu ve gün bırakma oynaklığı, tek bir saati seçerek kural ilan etmeyi desteklemez. Saat ilişkisi gün/rejim, mevcut envanter, defter veya dolmamış emir etkilerini ayırmaz.', '',
        '## t180 fiyat/oynaklık: gözlenebilirlik paydası', '',
        'Eski btc15_context t180 sigma değeri USD/√sn; normalize değer sigma/spot×10000. Bu girdinin geçmiş örnek erişim kusuru ana raporda ayrıca düzeltildi; bu ek eski sürümü açıkça sabit tutar. Tarihsel iki token fiyatı t180 veya daha önceki son örnektir; en çok75sn yaşında, 0<p<1. Sonraki örnek, nihai hacim/likidite veya sonuç özellik yapılmaz. Fiyat kayıtlarının yerel tarihsel alınma zamanı bilinmiyor; bunlar olay-zamanlı kamu fiyatları, bid/ask değildir.', '',
        '| Sekiz tam gün sınıfı | Piyasa | Context / fiyat / ortak | Normalize sigma medyan | Ucuz fiyat medyan | Fiyat yaşı medyan |', '|---|---:|---:|---:|---:|---:|']
    for name, info in comparison['full_days'].items():
        if name == 'at180':
            continue
        report.append(f"| {name} | {info['markets']} | {info['context']}/{info['price']}/{info['joint']} | {info['sigma_bp_per_sqrt_second'].get('median')} | {info['cheaper_price'].get('median')} | {info['price_age'].get('median')} |")
    report += ['', f"t180 sınıfları (816): {result['states']}. t180'den önce zaten girilenlerde aynı andaki sigma/fiyat ilk giriş açıklaması olamaz; piyasa-içi katılım karşılaştırması bile ters zaman yorumuna açıktır. Karar öncesi risk seti için yalnız t180'de henüz girilmemiş sonraki ilk girişler ile gözlenen işlemsizler karşılaştırılabilir. Bitiş sonrası ilk dolumu olan bir piyasa ayrıca ayrıldı.", '',
        '| t180’de henüz girilmemiş tam gün durumu | Piyasa | Ortak veri | Normalize sigma medyan | Ucuz fiyat medyan |', '|---|---:|---:|---:|---:|']
    for name in ('later_first_entry', 'no_observed_trade'):
        info = comparison['full_days']['at180'][name]
        report.append(f"| {name} | {info['markets']} | {info['joint']} | {info['sigma_bp_per_sqrt_second'].get('median')} | {info['cheaper_price'].get('median')} |")
    report += ['', '**KANIT YETERSİZ:** dağılım farkı karar mekanizması veya nedensel seçim etkisi değildir. Veri mevcudiyeti gün ve sınıfa göre farklıdır; `selection_audit.json.byday_context` bütün paydaları verir. Yeni 21 Eylül sıfır işlemli yarım günü eski tam günlerin kontrol grubuna ekleyip rejim etkisini gizlemedim.', '',
        f'Çalıştırma: `PYTHONDONTWRITEBYTECODE=1 python3 {HERE}/selection_audit.py`. Gömülü gelecek/bayat fiyat regresyonu,96-slot gün kontrolü ve816/598 mutabakatı her koşuda çalışır. Kaynak SHA256 JSON içinde; kaynaklar ve önceki result.json değişmez.']
    (HERE/'SELECTION.md').write_text('\n'.join(report)+'\n')
    print(json.dumps({k: result[k] for k in ('total', 'traded', 'full_day_total', 'full_day_traded', 'states', 'leave_one_day', 'comparison')}, ensure_ascii=False))


if __name__ == '__main__':
    run()
