"""Render the frozen local research results without changing its protocol."""
from datetime import datetime, timezone
from statistics import mean

import research as r


def fmt(v):
    return '—' if v is None else f'{v:+.3f}'


def main():
    first = r.read('stage1_markouts.json')
    second = r.read('stage2_controls.json')
    third = r.read('stage3_hypotheses.json')
    grid = r.read('stage3_actor_free_grid.json')
    coverage = r.read('coverage.json')
    fills = r.read('fills.json.gz')
    fee = r.read('fee_audit.json')
    paired = r.pair_rows(fills, r.read('matches.json')['primary'])
    actor = [f for f in fills if f['actor']]
    lines = ['# BTC15 maker fiyat avantajı — üç adımın sonucu', '',
        '**Karar: Bosona’ya ait sağlam, kopyalanabilir kısa vadeli fiyat avantajı kanıtlanmadı.** '
        'Diğer makerlara göre küçük bir fark var; tek piyasa ve az sayıda zaman eşleşmesi taşıyor. '
        'Sınanan iki önbilgi kuralı bunu güvenilir biçimde açıklamıyor. Mevcut aday korunmalı; '
        'bu çalışmadan yeni ekonomik shadow adayı çıkmıyor.', '',
        '## Kapsam ve ölçüm', '',
        f'21 Eylül 2026’nın önceden atanmış sekiz BTC15 penceresi: altısı kullanılabilir. '
        f'{len(fills):,} zincir-doğrulanmış maker BUY parçası; Bosona {len(actor)} dolum / '
        f'{len({f["parent"] for f in actor})} parent / {len({f["market"] for f in actor})} işlemli piyasa. '
        'Bir uygun piyasada Bosona dolumu yok. Tek gün ve görülmüş veri; kör test değil.', '',
        '| Başlangıç UTC | Veri durumu | Tüm maker BUY | Bosona dolum / parent |',
        '|---|---|---:|---:|']
    for c in coverage:
        date = datetime.fromtimestamp(c['start'], timezone.utc).strftime('%H:%M')
        status = 'Sonradan uzlaştırıldı' if c['offline_status'] == 'RECONCILED_LATER' else ('Uygun' if c['replay_eligible'] else 'Eksik; dışarıda')
        lines.append(f'| {date} | {status} | {c.get("buy_fills", "—")} | {c.get("actor_fills", "—")} / {c.get("actor_parents", "—")} |')
    lines += ['',
        '21:00 bağlantı boşluğu ve 22:15 eksik WS işlemi sıfır sonuca çevrilmedi. '
        '23:00’ın ilk başarısız API kapısı değiştirilmedi; sonraki tam uzlaşma ayrı etiket. '
        'Sözleşmeler Gamma başlangıç/bitiş, token kimliği ve Chainlink TWAP60 kuralıyla doğrulandı.', '',
        '**Markout = gelecekteki orta fiyat − gerçek maker dolum fiyatı**, sent/pay. '
        'Ana saat kamu dolum mesajının ilk alınması; gerçek eşleşme veya emir yerleştirme saati değil. '
        'Defter sonradan gelen örnekle doldurulmaz: hedef saate kadar alınan son durum kullanılır. '
        'İki token hazır/taze (≤3sn), bid<ask ve tamamlayıcı miktarlar eşit olmalı. '
        'Eksik/boş defter ve kapanış sonrası ufuklar null. '
        'Orta fiyattan satış yapılabildiği, kuyrukta dolum alınabildiği veya rebate kazanıldığı varsayılmıyor.', '',
        'Ana ağırlık: parent içindeki dolumlar eşit, piyasa içindeki parentlar eşit, piyasalar eşit. '
        'Dolum parçalanması sahte örnek büyüklüğü yaratmaz. Pay ağırlığı ayrıca verilir. '
        'Piyasa çıkarma aralığı güven aralığı değildir; aynı gün içi bağımlılık sürer.', '',
        '## 1. Dolumdan sonra fiyat ne yapıyor?', '',
        '| Ufuk | Bosona markout | Pay ağırlıklı | Mesaj anındaki fark | Sonraki fiyat hareketi |',
        '|---|---:|---:|---:|---:|']
    for h in (1000, 5000, 10000):
        d = first['0:actor:all']['horizons'][str(h)]
        lines.append(f'| {h//1000} sn | {fmt(d["markout"]["equal_market"])} | {fmt(d["markout"]["share_weighted"])} | {fmt(d["arrival_gap"]["equal_market"])} | {fmt(d["drift"]["equal_market"])} |')
    lines += ['',
        'Bosona’nın 22 dolumunda üç ufuk da ölçülebildi. Mesaj ulaştığında orta fiyatın altında '
        'bir dolum fiyatı görülüyor; sonraki hareket bu farkı siliyor. Bu, tek başına gelecekteki '
        'yönü iyi tahmin ettiğini desteklemiyor. Diğer makerların ham ortalaması farklı koşulları '
        'karıştırdığı için asıl karşılaştırma aşağıdaki eşleştirilmiş gruptur.', '',
        '## 2. Benzer koşullarda başka makerlarla karşılaştırma', '',
        'Ana kural sonuç hesaplanmadan sabitlendi: aynı piyasa/token, ≤2¢ fiyat, ≤30sn zaman, '
        'farklı transaction. Normalize zaman+fiyat uzaklığıyla tek en yakın dolum; sonuç/gelecek '
        'fiyatı kullanılmaz. Kontrol tekrar seçilebilir ve eksik sonucu varsa değiştirilmez. '
        '22/22 dolum eşleşti; 17 kontrol parentı / 11 cüzdan; en fazla iki kez parent kullanımı. '
        'Ortanca fiyat farkı 0¢, zaman farkı 442ms. Baştan sabit 5¢/60sn kontrolü aynı çiftleri seçti.', '',
        '| Saat varsayımı | 1sn fark | 5sn fark | 10sn fark | 10sn pay ağırlıklı fark |',
        '|---|---:|---:|---:|---:|']
    for shift in (0, -500):
        d = second['primary']['effects']
        vals = [fmt(d[f'{shift}:{h}:markout']['equal_market']) for h in (1000, 5000, 10000)]
        lines.append(f'| {"Mesaj alındı" if shift == 0 else "Alınma−500ms duyarlılığı"} | '+ ' | '.join(vals)+f' | {fmt(d[f"{shift}:10000:markout"]["share_weighted"])} |')
    d = second['primary']['effects']
    loo = second['primary']['leave_one_parent_out'].values()
    lines += ['',
        f'10sn ana farkın {fmt(d["0:10000:arrival_gap"]["equal_market"])} senti mesaj anındaki '
        f'fiyat farkı, {fmt(d["0:10000:drift"]["equal_market"])} senti sonraki göreli harekettir. '
        f'Tek parent çıkarıldığında fark {fmt(min(loo))}…{fmt(max(loo))} sent aralığına geliyor. '
        '500ms kaydırma eşleşmenin gerçek saati için doğrulanmış sınır değil; saat duyarlılığıdır.', '',
        '| Piyasa UTC | Bosona 10sn | Kontrole göre 10sn fark | 500ms kaydırılmış fark |',
        '|---|---:|---:|---:|---:|']
    for m, v in d['0:10000:markout']['by_market'].items():
        lines.append(f'| {datetime.fromtimestamp(int(m), timezone.utc).strftime("%H:%M")} | {fmt(first["0:actor:all"]["horizons"]["10000"]["markout"]["by_market"][m])} | {fmt(v)} | {fmt(d["-500:10000:markout"]["by_market"][m])} |')
    lines += ['',
        '22:00 piyasası ana göreli fark toplamının yaklaşık %93’ünü taşıyor. Bu piyasa '
        'çıkarılınca fark +0,090¢; 500ms saat duyarlılığında −0,208¢. '
        'Aynı agresör eşleşmesindeki 13 Bosona dolumu için diğer makerlarla fark +0,167¢; '
        'gelecek fiyat hareketi farkı tam 0. Aynı token ve aynı saat bunu zaten gerektirir; '
        'bu kontrol yön tahmini kanıtı değil, fiyat farkı/kimlik denetimidir.', '',
        '**Karşı örnekler (sonuç görüldükten sonra seçilmiş açıklayıcı örnekler):**', '',
        '| Piyasa / yaş | Token ve resmî sonuç | Bosona fiyat / 10sn | Kontrol yaş / fiyat / 10sn | Fark |',
        '|---|---|---:|---:|---:|']
    wanted = [(1790028000, 823), (1790028000, 741), (1790023500, 660), (1790031600, 305)]
    for market, age in wanted:
        x = next(f for f in paired if f['market'] == market and int(f['rcv']/1000-market) == age)
        c = x['control']
        lines.append(f'| {datetime.fromtimestamp(market, timezone.utc).strftime("%H:%M")} / {x["rcv"]/1000-market:.3f}sn | {"Up" if x["side"] == 0 else "Down"} / {"kazandı" if x["won"] else "kaybetti"} | {100*x["price"]:.2f}¢ / {fmt(r.metric(x))}¢ | {c["rcv"]/1000-market:.3f}sn / {100*c["price"]:.2f}¢ / {fmt(r.metric(c))}¢ | {fmt(r.difference(x, 10000, "markout", 0))}¢ |')
    lines += ['',
        'En büyük +38¢ göreli fark, Bosona’nın para kazandığı bir alım değil: kendi 10sn '
        'markoutu −0,5¢ ve token sonunda kaybediyor. 8,741sn sonraki kontrol çok daha sert '
        'düşüşü yaşıyor. −16¢ örneğinde ise Bosona’nın tokenı sonunda kazanıyor. '
        'Bunlar kısa ufuk farkını resmî sonuç kârıyla karıştırmamak ve zaman eşleştirmesinin '
        'hızlı hareketlerde sınırlı olduğunu görmek için önemli. Bütün çiftler matches.json’da.', '',
        '## 3. En fazla iki önbilgi açıklaması', '',
        'H1: önceki 5sn’de token orta fiyatı yükseliyorsa o yönde pasif alışa izin ver. '
        'H2: önceki 5sn kamu agresör hacmi token lehine net pozitifse izin ver. '
        'Eşik her ikisinde sıfır; nötr ayrı. İkisi birleştirilmedi, eşik taranmadı. '
        'Bilgi son noktası dolum mesajından 1sn ve ayrı duyarlılıkta 5sn öncesi. '
        'Bu, kendi alınma saatimiz açısından nedensel; Bosona’nın emir gönderiminden önce '
        'bilindiğini kanıtlamaz.', '',
        '| Hipotez / bilgi koruması | Bosona + / nötr / − | Pozitif grupta Bosona 10sn markout | Dolumdan bağımsız pozitif sinyalde 10sn fiyat hareketi |',
        '|---|---:|---:|---:|']
    for hyp in ('H1', 'H2'):
        for guard in (1000, 5000):
            v = third[f'0:{guard}:{hyp}']['filled_context']['actor']
            counts = ' / '.join(str(v[k]['raw_fills']) for k in ('positive', 'neutral', 'negative'))
            lines.append(f'| {hyp} / {guard//1000}sn | {counts} | {fmt(v["positive"]["markout"]["equal_market"])} | {fmt(grid[f"{guard}:{hyp}"]["positive"]["equal_market"])} |')
    lines += ['',
        '**H1: zayıf ve zamana duyarlı ipucu.** Aktörsüz ızgarada +0,235¢ hareket '
        '5sn korumayla +0,018¢’e düşüyor; ikinci durumda tek piyasa çıkarma aralığı '
        '−0,075…+0,183¢. Bosona pozitif H1 dolumlarında da negatif markout taşıyor. '
        'Bir kayıp karşı örnek: 20:45 piyasası Down, yaş 696,354sn, fiyat 26¢; '
        'önceki fiyat hareketi +1¢ ve akış +6,68 pay iken sonraki markout −4,5¢. '
        'Basit fiyat devamlılığı Bosona’nın avantajını açıklamış sayılmıyor.', '',
        '**H2: bu yöndeki açıklama desteklenmedi.** 22 dolumun 15’i aleyhte akış '
        'sonrasında geliyor. Aktörsüz pozitif akışta 10sn hareket iki korumada da '
        'yaklaşık −0,03¢. 22:00 piyasası Up, yaş 842,393sn: önceki akış −529,60 pay '
        'olmasına rağmen 94¢ dolumun 10sn markoutu +4,5¢. '
        'Ters işaretli yeni strateji bu sonucu görünce üretilmedi.', '',
        'H1 lehine kalan gözlem de saklandı: aynı piyasa içindeki pozitif eksi negatif '
        'özellik gruplarında sonraki fiyat hareketi farkı 1sn korumada +3,375¢ '
        '(yalnız iki ortak piyasa), 5sn korumada +1,000¢ (tek ortak piyasa). '
        'Bu alt gruplar ve toplam markout farklı ölçülerdir; tek başına kârlı seçim '
        'anlamına gelmez. Eşleştirilmiş kontrole göre pozitif H1 görülme farkı '
        'eşit piyasa ağırlığıyla yalnız −1,67 / +1,67 yüzde puan. H2 için '
        'aynı piyasa hareket farkı iki korumada da negatif. Aynı koşuldaki '
        'diğer makerların da taşıdığı özellikler Bosona’ya özgü bir kuralı tanımlamıyor.', '',
        'Seçici `research.py:features()` yalnız defter/kamu akışından H1/H2 işaretini '
        'üretir; pozitif işaret ilgili hipotezin izin koşuludur. Her saniye iki token için '
        '10.548 sabit bağlam çalıştırıldı; tamamlayıcı tokenlar bağımsız iki gözlem '
        'değildir, ufuklar da örtüşür. Eksik defter/özellik null olarak durur. '
        'Bu ızgara kotasyon veya dolum varsaymaz; markout/PnL backtest’i değildir. '
        'Olumlu/olumsuz/nötr, aynı özellikli çiftler, ortak piyasadaki işaret farkları '
        've iki saat kaydırması bütün JSON çıktılarında saklandı.', '',
        '**Yanlışlanma/kabul:** H1 için daha eski bilgiyle etkinin kaybolması, H2 için '
        'pozitif akışın daha iyi sonraki hareket vermemesi bu kesitte karşı kanıttır. '
        'Bunlar Bosona’nın bütün stratejisini çürütmez. İlerlemek için değişmeyen '
        'kuralla farklı günlerde, parent/piyasa kümeleriyle aynı yönün korunması '
        've kendi uygulanabilir dolum modelinde maliyet sonrası sonuç gerekir. '
        'Bu koşullar karşılanmadı; iki hipotezden hiçbiri mevcut adayın yerini almıyor.', '',
        '## Kontroller, düzeltme ve sınırlar', '',
        f'Rol, ücret imzasından değil OrdersMatched/OrderFilled zincir ilişkisinden geliyor. '
        f'Kontrol havuzunda {fee["maker_with_nonzero_fee"]} maker parçasında toplam '
        f'{fee["total_fee_units"]/r.UNIT:.5f}$ ücret var ({fee["owners"]} cüzdan); Bosona’da ve '
        'seçilen kontrol dolumlarında sıfır. İlk kontrol testindeki “bütün maker ücretleri '
        'sıfırdır” varsayımı bu gerçek karşı örnekle kaldırıldı; sınıflandırıcı veya '
        'veri değiştirilmedi. Bu yüzden salt ücretle genel rol çıkarmak güvenli değil. '
        '[Resmî V2 kaynak kodu maker ücretini ayrı parametre olarak destekliyor.]'
        '(https://github.com/Polymarket/ctf-exchange-v2/blob/main/src/exchange/mixins/Trading.sol)', '',
        'Kamu defter ve işlem olaylarının alanları '
        '[resmî akış belgesinde](https://docs.polymarket.com/market-data/realtime-data) '
        'ayrı tanımlı. Fiziksel eşleşme saati, emir yerleştirme/iptalleri, dolmayan '
        'emirler, gerçek kuyruk yeri ve diğer makerların portföy riski bilinmiyor. '
        'Aynı fiyat/zaman bu gizli koşulları eşitlemez. Bu çalışma yalnız dolmuş '
        'emirler üzerindeki ilişkiyi ölçer, hangi emirlerin dolacağını açıklamaz.', '',
        'Kimlik/fiyat/rol, parent ağırlığı, eksik ve kapanış sansürü, sonuçtan bağımsız '
        'eşleştirme, public akış çokluğu ve 48 gerçek bağlamda geleceği silme kontrolleri '
        '`verification.json` içinde. Ham kaynaklar delivery manifestleriyle salt okunur '
        'doğrulanır; ağ bağlantısı analiz sırasında engellenir. Aynı hashli tekrar '
        '`reproducibility.json`, çıktı manifesti `delivery_manifest.json` içindedir.', '',
        '## Tekrar çalıştırma', '', '```bash',
        'P=/home/taygun/Masaüstü/KararAtlas/base1/bin/python3',
        f'D={r.HERE}',
        '$P "$D/research.py" all', '$P "$D/check.py"', '$P "$D/report.py"',
        '$P -m ruff check "$D/research.py" "$D/check.py" "$D/report.py"', '```', '',
        'Aday, eşikler, eski protokoller, ana repo, Londra ve çalışan kaydediciler '
        'değiştirilmedi. Araştırma hesabı tamamlandı; ekonomik avantajın doğrulanması açık.', '']
    (r.HERE/'RAPOR.md').write_text('\n'.join(lines))
    assert abs(mean(d['0:10000:markout']['by_market'].values())-d['0:10000:markout']['equal_market']) < 1e-10


if __name__ == '__main__':
    main()
