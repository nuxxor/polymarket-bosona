# G1 / Bosona: aynı piyasa ilk okuma

Kesit: 2026-09-22T11:15:54.136000+00:00

Kamu nakit maliyeti ve sonuç ödemesi; rebate/sabit gider hariç. Açık sonuç null. Saatler TR. İlk pilot, süresiz ilk koşu ve yeniden devam ayrı dönemlerdir.

| Pencere TR | G sonucu $ | Bosona sonucu $ | İlk dolum yaşı G/Bosona | G yerel pay teyidi |
|---|---:|---:|---|---|
| 12:30 | 5.1500 | 247.699360 | 12/195 | True |
| 12:35 | 3.10 | -44.82 | 15/205 | True |
| 12:40 | 0.75 | 14.7072 | 9/163 | True |
| 12:45 | -0.198115 | -25.844600 | 10/34 | True |
| 12:50 | -2.345571 | 0 | 12/None | True |
| 12:55 | 2.75 | 42.771600 | 9/132 | True |
| 13:35 | -2.00 | -27.427784 | 10/3 | True |
| 13:40 | 1.6008 | 0.210029 | 10/75 | True |
| 14:00 | -2.30 | -27.39 | 9/201 | True |
| 14:05 | 0 | -18.550965 | None/82 | None |
| 14:10 | None | None | 9/24 | True |

## Muhasebe ve yorum sınırları

- Her snapshot tek başına tam condition geçmişi sorgular; aynı görünen gerçek satırlar korunur. Sayfalar arası belirsiz tekrar kabul edilmez.
- Nakit ve sonuç hesabı bağımsız trade hesabıyla eşleşir. BUY/SELL miktarları ve nakitleri V2 receipt/log ile doğrulanır; gerçek maker/taker ve parent yalnız bu kapsamda bilinir.
- Boş asset taşıyan REDEEM, geçerli outcomeIndex ile ödeme tarafına bağlanır ve işaretlenir. Kaybeden tokenların zincirde yakılması ve harici transferler ayrıca doğrulanmış değildir; tam zincir bakiyesi denetimi iddiası yok.
- Public API saniyesi emir verme anı değildir. Parent ilk dolum zamanı da ilk emir verme zamanı değildir. Aynı saniyede iki taraf varsa sıra belirsizdir.
- İşlemsiz gözlenen piyasa, hiç emir verilmediğini kanıtlamaz. G tarafından atlanan pencere ileri takvimden çıkarılmaz.
- Yerel state, Gamma ve iki activity yanıtı farklı zamanlarda alınır. Açık pencerede miktar farkı veya Gamma sonucundan önce görülen redeem, tek başına bot muhasebe hatası sayılmaz; sonraki kesitte yeniden kontrol edilir.
- trade_only_floor, gözlenen bütün işlemlerin iki olası sonuçtaki düşük ödemesidir. Kapanışın yarattığı alfa veya alternatif strateji PnL’si değildir.
- İleri evren: 14:05–16:05 TR, 24 slot; araştırma süreç çıkışı 16:20 TR. Worker ilk veri kesitini daha sonra toplar; protokol önceden dondurulmuştur. Bu işlem gönderen shadow değildir.

## Tekrar çalıştırma

```bash
python3 /home/taygun/Masaüstü/polymarket-bosona/data/analysis/g1_comparison_20260922/check.py
python3 /home/taygun/Masaüstü/polymarket-bosona/data/analysis/g1_comparison_20260922/report.py
```
