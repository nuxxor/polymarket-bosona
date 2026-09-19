---
name: project-breakthrough-review-20260919
description: 2026-09-19 breakthrough review sonucu — BTC5m derin merdiven maker kulvarında pozitif EV mekanizması gösterilemedi; kayıp mekanizması ms düzeyinde ölçüldü (kaskad + bilgili akış); bosona'nın BTC5m kenarı 515 pencerede sıfırdan ayırt edilemiyor, kârı BTC15m'de
metadata:
  type: project
---

# Breakthrough review (2026-09-19 gecesi, Fable 5.1, ~280 ajan)

Rapor: `data/analysis/pm_breakthrough_review_20260918_v1/REPORT.md`; doğrulanmış sayılar `orch/ANCHORS.md` (A-N).
Veri katmanı: tape 09-13..09-18 parquet'e açıldı (`parquet/<kind>/`), bosona tam akış (takerOnly=false, 10.491 satır, offset tavanı ~10,5k) `raw/`, ms-birleşik dolumlar `fills_bosona.parquet` / `fills_us.parquet`, yardımcı `tapelib.py`.

## Yerleşik bulgular
- **bosona BTC5m, 515 olgun pencere (09-16..18):** +0,82 kr/pay GA[−1,16,+2,86] (sıfırı KAPSIYOR); maker −0,15, taker +3,10 (GA sıfırı kapsıyor); satış YOK. Brief'teki 48 pencerelik +5,06 elverişli dilimdi (en yakın yeniden kurulum +2,41 GA[−2,58,+7,35]). Aynı çekimde **BTC15m +3,21 GA[+0,51,+5,87]** (190 pazar) → kâr merkezi BTC5m değil.
- **Kayıp mekanizması (489 dolum, cut1):** 5 payımız medyan 556 paylık seviyede; dolumdan önceki 2 s'de seviye 317'ye iniyor, azalmanın %98'i İPTAL; mid 2 s önce fiyatımızın 5,5 kr üstünde (A 9,5), dolumdan 1 s sonra 4,6 kr altında; 60 s sonrası ve terminal fark ~0. A dolumlarının %23'ü 5 s içinde ≥5 bps aleyhte vadeli hareketinin ardından (tüm taker hacminin ~%3'ü bilgili) → ~7x aşırı maruziyet. Vadeli→PM gecikmesi 250 ms; ≥3 bps hareketten sonra kotasyon p50 134 ms, ilk aynı yön taker p50 116 ms; bizim yol ≥1 s.
- **Markout düzeltmesi düzeltildi:** LOG dolum zamanı keşif zamanı (medyan 0,62 s geç); tape'te pc, ltp'den ~30 ms önce. "Giriş −1,38" artefakt; gerçek: giriş ~0, kayıp dolum sonrası 1 s'de.
- **Hızlı iptal kurtarmıyor:** kalabalık-çekilme tetiği dolumların %94'ünden önce (=ticaret yok); vadeli tetikleri −8..−12 kr/pay kuyruğunu kesiyor ama kalan dolumlar −1,5; medyan etki 0, GA sıfırı kapsıyor.
- **Eşleşme oranı yan ürün** (B %83 eşleşip kaybediyor; simülatör kalibre: %43 vs %42). **Boy testi yapılamaz** (3-5 kr/pay için 550-2.500 pencere; $40 tavan 1-2 pencere). **Rejim kapısı** IPW'de gürültü (+0,70 GA[−3,65,+4,74]).
- **TWAP kilidi gerçek ve kamuya açık:** t=270'te |marj|≥3 bps → 1.006 pencerede 0 hata (%71 kapsam); PM mid@270 hatası %2,2.
- **Geç-favori MAKER negatif** (1.415 pencere, t=270'te mid≥0,80 tarafına 0,85/0,90/0,95 alış): dolan pay başına −15/−13/−10 kr; kaybeden %2,2'de emir HER ZAMAN doluyor. bosona'nın ≥0,95 geç maker alımları +1,75 GA[−0,85,+3,31].
- **Defter dengesizliği** sonucu öngörmüyor (25 hipotez, OOS, AUC farkı ≤0,004). **Toplu iptal hacmi** vadeliye tepki vermiyor ve mid'i öngörmüyor.
- Güç: 1 kr/pay için karma 1.700 pencere (~6 gün), A 5.700, B 649 (cut1 sigma $3,77/pencere).

## OPERATÖR DÜZELTMESİ (09-19 sabah) — 19 günlük zincir defteri (FILL_PARTY_LEDGER, 14 Ağu-2 Eyl)
- bosona BTC5m maker **+1,95 kr/pay GA[+0,96,+2,95]** (1,78M pay), taker +3,53. 2 günlük kamu çekimi bunu ÇÖZEMİYOR (GA kapsıyor). "BTC5m kâr merkezi değil" GERİ ÇEKİLDİ. Maker kârının ~%40'ı ≥0,80 favoriden (0,84-0,96'dan %100 isabetle).
- Tüm maker'lar bant haritası: 0,20-0,40 ≈ +0,5 (GA sıfırı kapsıyor; operatörün kendi tablosu +1,85/+1,48 GA dışlıyor — tanım farkı çözülmedi), 0,60-0,80 −1,0/−1,1 (herkes kaybediyor), 0,80-0,90 +1,07 [+0,01,+2,11], 0,90-1,00 +0,40 [+0,11,+0,68]. Dolum boyu gradyanı 0,20-0,40: <10 pay −0,07 → 250+ +2,39 (kenar = seviyenin kendisi olmak).
- **Geç-favori MAKER verdikti düzeltildi:** negatif olan PM-mid≥0,80 seçicisiydi; Chainlink marj kapısı (≥3 bps @270) ile kaybeden dolum 0/1.006, ama 5 paylık kuyruk-arkası bid pencerelerin %0,5'inde doluyor. 19 gün: tüm maker'lar ≥0,95 son 60 s +0,40 [+0,20,+0,59] (30M pay, boy bağımsız, S+300 sonrası işlem devam ediyor: +0,45 @0,995 %99,9 isabet); bosona +3,78 [+3,60,+3,96] (28k pay, 134 pazar, 0,96'dan %100). KULVAR AÇIK: kilit-kapılı, 50-200 paylık 0,95-0,99 bid; sıradaki test = tape replay (boy 25/100/200, optimistik/pesimistik kuyruk) sonra kâğıt gölge.
- Bizim bantlarımız: <0,45 +0,73 (A −1,74, B +3,37); ≥0,45 −4,39 (hepsi B, hacmin %39'u). 0,20-0,40: A −5,37 (kaskad/bilgili akış), B +7,68. İki mekanizma, kol başına bir: A ucuz bantta seçime kaybediyor, B yanlış bantta duruyor. Operatör PX_TAVAN_MAKER=0,45 koydu; 09-18 replay'i #47 kontrolünü geçmiyor (21 iyi/23 kötü, medyan 0, ilk-3 %85); gerekçe 19 günlük bant haritası.

## REPLAY SONUÇLARI (09-19 öğle)
- **Hacim çeyreği önden bilinemiyor** (5.293 pencere): çeyrek = gidiş-dönüş vekili (Q4 %88 iki taraf da alınmış; gidiş-dönüş +8,0 / tek taraf −29,2); rho ile önceki hacim −0,004, önceki BTC salınımı +0,026, saat +0,008; 4 kapının OOS'u −4,6…−7,0, GA sıfırı dışlıyor (koşulsuz −5,9). KAPANDI. Operatör kendi "+1,85 ucuz bant kenarı"nı geri çekti (pay-ağırlıklı havuz; pencere-eşit −5,28 ≈ A'nın −5,37'si).
- **Kilit-kapılı geç-favori replay** (1.409 pencere): ≥3 bps kapı 0 hata; 0,95-0,97 bid'e arz yok (%0,5-1 pencere); **0,99 bid +1 kr/pay %100 isabet, 130-350 pay/pencere arz** ama 0,99'da medyan 24.000 paylık duvar → t=270'te konan bid pencerelerin %1,2'sinde doluyor. Kenar var, kuyruğun ÖNÜNE ait (defterdeki en büyük cüzdan 4,1M pay +0,56). Başabaş kapı hatası %1 (gözlenen 0/1.006). $540 kulvarı değil; altyapı (ilk olmak, boy, 0,001 tik) sorusu.

## Kalan yönler (para yok)
1. Kilit-kapılı 0,99 kuyruk-önü: ancak WS ile seviyenin açıldığı anda post edebilen altyapıyla; önce kâğıt. 2.
bosona geometrisi (mid−1,6 kr, büyük boy, WS iptal <200 ms) BTC15m'de kâğıt gölge; 200 gölge dolumu öncesi para yok.

## Olay
01:00-01:03 (+03) bellek baskısı: earlyoom 22 GB analiz sürecini kesti; `learningenglish-bot` ve `onchain-trader-tnc-source-v3` öldü, systemd 10 s'de yeniden başlattı. Ticaret süreci yok.

İlgili: [[project-takeronly-hatasi-20260918]], [[project-bosona-cift-maliyeti-cozuldu-20260918]] (o dosyadaki sayılar artık geçersiz), [[project-gec-favori-curudu-20260918]], [[project-rejim-kapisi-20260918]]
