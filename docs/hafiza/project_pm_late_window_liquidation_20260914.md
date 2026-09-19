---
name: project-pm-late-window-liquidation-20260914
description: PM BTC5m kenarı geç-pencere tasfiye akışında — son 35 sn, favori 0,75-0,90, maker alım, +9,58 kr/pay 17 günde iki yarıda da doğrulandı
metadata:
  type: project
---

**2026-09-14.** Aktör kenarının kaynağı bulundu: dalga/ters-seçilim DEĞİL, **zaman**.

Settlement `Up ⟺ TWAP60(S+300) ≥ TWAP60(S)`, ve TWAP60(S+300) = spot'un
[S+240, S+300] ortalaması → settlement penceresi **S+240'ta kilitlenmeye başlar**.
Bu üç faz yaratıyor (17 gün, 4.704 pencere, 19,2M işlem, gün-kümeli GA):

- FAZ1 0-240 sn: maker alım +0,60 kr/pay
- FAZ2 240-265 sn: TWAP kilitlenirken bilgili yeniden fiyatlama → **bizim
  replayimizde her politikada −3…−23 kr/pay** (tehlike bölgesi)
- FAZ3 265-300 sn: yalnız tasfiye akışı → +1,29; **px 0,75-0,90'da +9,58**
  GA [+7,22,+11,52], 1. yarı +10,45 / 2. yarı +8,87 (taranmadan, iki yarı ayrı geçti)

Gerçekçi payımız: 937 küçük cüzdan hacmin %30,3'ünü alıp **+4,88 kr/pay**
kazanıyor. 38 pencere/gün, 50 pay klip → ~$93/gün. $77 sermaye yeter
(0,80×50=$40, 5 dk'da döner).

**Çürütülenler:** dalga-koşullu filtre (1,75'in yalnız 0,30'unu açıklıyor,
gecikmeyle 0,05); `P_model − px ≥ 0,10` kuralı (en iyi 3 gün hariç +0,12).

**Kilitli-TWAP tahmincisi doğrulandı** ama tek başına para etmiyor: S+270'te
%97,7 isabet, piyasa zaten fiyatlıyor, taker yolu ölü. Değerli olan maker kolu.

**Açık risk:** dolumlar gerçekleşmiş dolumlar — sahibi kuyrukta öndeydi.
17 günlük veride defter YOK. Sıradaki: Londra 2 günlük defterinde t≥265'te
0,75-0,90'a gelen süpürmelerin seviyeyi tüketip tüketmediğini ölç.

Kod/rapor: `data/analysis/pm_locked_twap_20260914_v1/` (locked.py, gap.py,
edge.py, oos.py, phase.py, breadth.py, REPORT_TR.md — eşikler mühürlü).
İlgili: [[project-btc5m-top-actor-hunt-20260902]], [[project-operator-a-london-ms-20260910]]

## KUYRUK ÖLÇÜLDÜ (14 Eyl akşam)
Londra 2 günlük tam derinlik defteri, 3.041 geç dalga, 50 pay klip, küçük-maker kenarı:
- Dalgalar KÜÇÜK: medyan 5-10 pay; seviye derinliği medyan 27-53 pay
- Dalgaların yalnız %28-41'i seviyeyi tam tüketiyor → **kuyruk bağlayıcı**
- 0,97+ bandı (hacmin %66'sı) BİZE KAPALI: medyan derinlik 9.877 pay, %3 tüketim
- **Erken gelmek avantaj vermiyor**: seviye ilk göründüğündeki derinlik, dalga
  anındakinden genelde daha büyük (iptaller) → "saatler önce diz" fikri bu hücrede ölü
- Gerçekçi: **$83/gün toplam, dondurulmuş 0,75-0,90 hücresinde $31/gün**;
  iyimser (sıra başı) $400 / $128. Sermaye $77 yeterli ($40/pencere, 5 dk'da döner)
Kod: `data/analysis/pm_late_queue_20260914_v1/kuyruk.py, kuyruk2.py, QUEUE_ALL.parquet`
NOT: tahmin 2 günlük deftere dayanıyor; ek ölçüm günü aralığı daraltır.

## CODEX DENETİMİ SONRASI DÜZELTME (14 Eyl gece) — CANLI YOK
Codex 5 kusur buldu, hepsi haklı; en ciddisi: fiyat seviyesi **gelecekteki
satıştan** seçilmişti (ileri bakış). Düzeltilmiş tek politika (P1: t=265'te
favoride `min(0,90,best_bid)`, 50 pay/pencere, ilerleyen kuyruk, aynı pencerenin
kendi sonucuyla puanlama) → **135 fırsat, 4 dolum (%3), +$12,16, +13,41 kr/pay, 4/4**.
Tek gün, 4 dolum = istatistiksel olarak hiçbir şey.
- t=265'te favori best_bid 165 pencerenin 121'inde >0,98 → 0,90'lık emir 8+ kuruş derinde
- 0,75-0,90'da geç satış olan pencere: %8,5; biz o pencerelerin %29'unu yakaladık
- **KRİTİK: 50 pay × 0,90 = $45 kayıp → $25 stop TEK işlemde patlar.**
  Kenar ~%94,6 kazanma demek → ~18 dolumda 1 tam kayıp → günde 4 dolumla 4-5 günde bir.
  Stopla uyumlu klip (10 pay) günde ~$2 getirir = ölçülemez.
- $31/$83/gün rakamları GEÇERSİZ (başka maker'ın kenarıyla çarpımdı).
KARAR: canlıya geçilmedi. Sıradaki: `data/tape/` (kendi kayıtçımız, price_change +
last_trade_price) için ayrıştırıcı yazıp P1'i biriken her güne uygula; ~2 hafta
sonra 50-60 dolumla karar. Kod: `data/analysis/pm_policy_sim_20260914_v1/`
Denetim: `data/analysis/pm_locked_twap_claim_review_20260914_v1/REPORT_TR.md`

## YÖN DÜZELTMESİ — AKTÖR MODELİ ASIL İŞ (14 Eyl gece, operatör uyarısıyla)
Operatör haklı çıktı: geç-pencere köşesine daralmam hataydı. Aktör dolumlarının
**%93'ü son 45 saniyeden ÖNCE**. Asıl soru "sürekli mi geç mi" değil,
**"dokunuşta mı derinde mi"**.

ÖLÇÜM (17 gün, 23M pay, referans=dolumdan >=1sn önceki son işlem; bayatlık
kontrolü geçti — referansların %99,4'ü <=5sn taze, gradyan taze altkümede aynı):
| nereye yazıyorsun | kr/pay | gün-kümeli GA |
|---|---|---|
| piyasanın ÜSTÜ (kovalama) | **−0,47** | [−0,91,−0,07] |
| dokunuşta (eski politikamız) | +0,50 | [+0,09,+0,92] |
| 2-5 kr altta | +1,03 | [+0,34,+1,72] |
| 5-10 kr altta | +1,91 | [+0,72,+3,30] |
| 10+ kr altta | +6,66 | [+4,00,+9,25] |
Monoton, her kova GA geçiyor, her kovada iki yarı uyuşuyor. **Tek eksi kova
KOVALAMA.** Eski bot dokunuşta durup fiyat kaçınca kovalıyordu = en kötü bileşim.

DİKKAT — bu derinlik DOLUM ANINDA ölçülür. Fiyat yavaşça bize kayarsa emir artık
derin değildir. +1,91 kovası fiyatın SIÇRAYARAK geçtiği dolumlar.

P2 SİMÜLASYONU (`pm_actor_model_20260914_v1/sim2.py`, düzeltilmiş kuyruk motoru,
probe.py ile aynı, Codex tanığı geçiyor): t=S+30'da p=best_bid−DELTA, çift kapağı
0,97, taraf başına 5 pay, asla yeniden fiyatlama yok.
Londra 1 gün / 165 pencere: **dolum oranı %48-64** (geç-pencere köşesi %3'tü),
çift maliyeti 0,59-0,95 (1,00 altında = yapısal güvenlik), azami nakit $4,45/pencere.
DELTA taraması −3,30…+4,49 kr/pay, her birinde artıda pencere ~%50 → **tek gün
işareti belirleyemiyor, gürültü baskın.**
İYİ HABER: %60 dolum oranı × 10 pazar = günde ~1.000 dolan pencere. Geç-pencere
köşesi için 2 hafta gereken örnek, bu modelde 1-2 günde birikiyor.

## P2/P3 SİMÜLASYON SONUÇLARI (14 Eyl gece)
**TAMAMLAYICI EŞLEŞME — kritik veri düzeltmesi.** Tape'te işlem baskılarının **%89'u
BUY** ve baskı genelde tek token'da çıkıyor. Bizim X@p alış emrimiz (a) X'te taker
SELL@p ile VEYA (b) karşı token'da taker BUY@(1−p) ile doluyor (tam set üretimi).
Sadece aynı-token SELL saymak akışın %89'unu kaçırıyordu. Düzeltince Londra işlem
akışı 29.626 → 230.076 (7,8×), dolum oranı %48-64 → **%91-97**.

**EKONOMİNİN AYRIŞTIRMASI (Londra 1 gün, 156 dolan pencere, DELTA=0,05):**
- İki taraf da doldu (eşleşen çift): 95 pencere, 960 pay (%77) → **95/95 ARTIDA, +$52,45**
  Çift maliyeti 0,8896, ödeme 1,00 → çift başına **+11,04 kr, SIFIR RİSK** (aritmetik)
- Tek taraf kaldı (artan envanter): 61 pencere, 290 pay (%23) → 14/61, **−$39,68**
  (pay başına −13,89 kr)
- NET +$12,77 → +1,02 kr/pay
→ **Bu bir tahmin işi değil, ÇİFT TAMAMLAMA işi.** Aktörlerin neden hiç satmadığını
açıklıyor: satmak değil, eksik tarafı tamamlamak gerekiyor.

**P3 ÇİFT TAMAMLAMA (taker'dan eksik tarafı al) — ÖLÇÜLDÜ, ÇALIŞMIYOR.**
Önce bir hata bulundu: tamamlarken o taraftaki kendi bekleyen emrimizi iptal
etmezsek o da dolup dengesizliği TERS yöne geçiriyor (artan 289→359). İptal
eklendi, mekanik düzeldi (289→281). Ama PnL her DELTA'da DÜŞÜYOR:
0,03: +0,05→−0,64 | 0,05: +1,02→+0,44 | 0,08: −0,03→−0,17 | 0,12: +3,76→+3,23.
Sebep: dengesizliğe düştüğümüzde eksik tarafın ask'i zaten bilgiyi fiyatlamış;
tamamlamanın maliyeti, tutmanın beklenen zararından büyük. Piyasa bedava hedge
bırakmıyor. **Bu kol kapandı.**

DURUM: yapı anlaşıldı, DELTA taraması hâlâ gürültülü (−2,21…+3,76, 1 gün).
Karar için çok-pazar tape'i lazım. Kod: `pm_actor_model_20260914_v1/`
(derinlik.py, kontrol.py, sim2.py, sim3.py), `pm_multi_tape_20260914_v1/tape_sim2.py`.

## P6/P7 VE KAYITÇI KUSURU (14 Eyl gece, devam)
**Tamamlayıcı eşleşmenin sonucu:** bizim X@p emrimiz, KARŞI tarafı almak isteyen
taker geldiğinde dolar → topladığımız taraf **talep görmeyen** taraftır. İki emrimiz
aynı akıştan ters yönlerden beslenir: akış iki yönlüyse çift eşleşir (garanti kâr),
tek yönlüyse kaybedeni toplarız. Asıl soru yön değil, **akışın iki yönlü olup olmadığı**.

- **P6 dengesizlik merdiveni** (bir taraf diğerine göre en fazla ADIM kadar öne geçsin):
  ÇÜRÜDÜ. Her derinlikte kötüleştirdi (+1,02→−0,48; +3,73→+1,23). Sebep ölçüldü:
  eşleşmeme, bir tarafın öne geçmesinden DEĞİL, **öbür tarafın hiç dolmamasından**.
  Artan oranı %23,2→%24,9, yani kapak hiçbir şey düzeltmedi.
- **P7 salınım filtresi** (ilk 30 sn dönüş/menzil): ETKİSİZ — 156 pencerenin 155'i
  zaten salınımlı, ayırt edecek varyasyon yok.
- **AYAKTA KALAN TEK ŞEY: en yalın hali.** İki tarafa da dokunuşun 12 kuruş altına
  sabit emir, hiçbir akıllılık yok: **+3,73 kr/pay, 87/150 pencere artıda.**
  Bağımsız 17 günlük derinlik gradyanıyla uyumlu (10+ kr alt: +6,66 [+4,00,+9,25]).
  Denenen 5 eklemenin HEPSİ zarar verdi veya etkisiz kaldı.

**KAYITÇI KUSURU — ölçümü bozuyordu.** İlk multitape sürümü tek ortak WS kullanıyordu;
her yeni pencere abonelik setini değiştirince bağlantı kapanıp açılıyordu →
**110 dk'da 57 kopma**, her kopmada saniyeler kayıp. Parmak izi: eşleşen çift oranı
Londra %67 iken tape'te **%29**. Taze tape'te çıkan −5,08 kr/pay bu yüzden GÜVENİLİR
DEĞİL. DÜZELTİLDİ: her pencere kendi WS bağlantısında yaşıyor (`pencere_akisi`),
ilk 2 dakikada **sıfır kopma**. Yeniden ölçüm temiz veriyle yapılacak.

Fable devri: `data/analysis/HANDOFF_FABLE_20260914_AKTOR.md` (189 satır).

## ⚠️ BAYAT KORUMASI — İDDİA GERİ ÇEKİLDİ (aşağıdaki düzeltmeye bak)
Fable doğruladı + ben bağımsız hesapladım: mo-money/bosona **çift kilitleyici DEĞİL**
(kârlarının %70-75'i tek taraflı envanterden, o envanter KAZANAN tarafta: 0,55'ten
alıp %57,7 kazanıyorlar = yön seçimi). **whiskas** çift kilitleyici ve maker defteri
17 günde **+$23.417 = +$1.377/gün** — yani model çalışıyor, iade onun ÜSTÜNE geliyor.
(Eski "whiskas trading kaybediyor" notu tüm cüzdanın rakamıydı, taker dahil.)

**BULUNAN FARK:** çift tarafında whiskas'ı yeniyoruz (çift maliyeti 0,888 vs 0,962).
Tek kayıp yeri artan envanter: whiskas −0,38 kr/pay (%46,2 kazanma), biz −13,9 (%19,6).

**SEBEP:** emri koyup pencere sonuna kadar hiç çekmiyorduk → fiyat aleyhimize
koşarken batan tarafı topluyorduk. **ÇÖZÜM: BAYAT KORUMASI** — o tarafın best_bid'i
bizim fiyatımızın CEK kuruş altına düşerse o taraftaki dolmamış emri ÇEK.

Doz-cevap (Londra, artan kazanma oranı): iptal yok %19,6 → 10kr %29,6 → 5kr %32,4
→ 3kr %33,9 → 2kr **%43,7**. Kâr rakamı değil TEŞHİS metriği monoton — bu yüzden
gürültü değil.

**OUT-OF-SAMPLE TEKRARLANDI** (Londra BTC 10 Eyl vs taze tape 5 coin 14 Eyl):
| CEK | Londra | Tape |
|---|---|---|
| yok | +1,02 | +1,50/+1,57 |
| **0,05** | **+2,80** | **+3,14/+3,39** |
| 0,03 | +2,11 | +2,27 |
Bağımsız gün + bağımsız pazarlar, aynı sıralama, yakın büyüklük. Bu projede
ilk kez bir bulgu kontrolde ölmedi.

## ⚠️ İPTAL GECİKMESİ = BAĞLAYICI KISIT (ölçüldü)
| iptal gecikmesi | toplam kr/pay |
|---|---|
| 0 ms | +3,14 |
| 200 ms | +2,11 |
| **400 ms (Türkiye gerçeği)** | **+0,30** |
| 800 ms | −1,35 |
| 1500 ms | −2,92 |
**400 ms'de bayat koruması NET ZARARLI** (+0,30 < iptalsiz +1,57): geç yetişiyor,
kötü dolumu yiyoruz ÜSTELİK iyi dolumları da iptal ediyoruz.
→ Kenar **<200 ms iptal gecikmesinde** yaşıyor. Türkiye'den (~179 ms RTT, POST ~367 ms)
erişilemez; **Londra colocation ilk kez GERÇEKTEN gerekli** (operatör onay verdi).
Önceki turlardaki "hız önemli değil" sonucu TAKER yolu içindi; burada mekanizma
iptal olduğu için hız doğrudan kenarın kendisi.

Kod: `pm_actor_model_20260914_v1/sim8.py` (Londra) ·
`pm_multi_tape_20260914_v1/tape_sim3.py` (tape, gecikme parametreli).
Kural DONDURULDU: t=S+30, p=best_bid−0,05, çift≤0,97, 5 pay/taraf, CEK=0,05.

## ✖ DÜZELTME — "tekrarlandı" İDDİASI ÇÖKTÜ (14 Eyl gece geç, iki denetim)
Codex ve Fable bağımsız olarak aynı yere vardı; ben de doğruladım.
**+2,80 / +3,14 ve "kenar <200ms'de yaşıyor" eğrisi ARTEFAKT.** İki kod hatası:
1. İptal tetiği kalıcı kaydedilmiyordu (fiyat toparlanınca sinyal unutuluyordu)
   → Codex aynı 81 markette: iptal yok +1,44 | özgün kod +3,19 | **tetik kalıcı −6,13**
2. İptal, AYNI süpürmeden kaçabiliyordu: "best_bid düştü" mesajı işlem baskısından
   ÖNCE gelebiliyor. Kendi ölçümüm: 265.583 eşleşmede düşüşlerin **%51,3'ü işlem
   baskısından önce**, medyan −19 ms. Fable süpürmeleri izole edip %99,9 / ~100 ms buldu.

**DÜRÜST MOTOR (sim9.py) — üç düzeltme uygulanmış:** olay sırası (iptal etkin =
tetik + 15 ms gözlem + emir gecikmesi), best_bid=0 geçerli tetik, dolum için
iyimser/kötümser sınır.
| dolum sınırı | iptal yok | dürüst iptal 0ms | 200ms | 400ms |
|---|---|---|---|---|
| İYİMSER (fiyatımızdaki baskı doldurur) | +1,02 [−1,64,+3,68] | +2,62 | +2,83 | +2,83 |
| KÖTÜMSER (yalnız altımızdan geçen) | −2,52 [−4,97,−0,38] | −2,39 | −2,74 | −2,74 |
**Bir arm hariç tüm GA'lar sıfırı içeriyor.**

## ★ HIZ GEREKMİYOR — KESİN (bağımsız doğrulandı)
Dürüst motorda iptal faydası 0ms'de +1,59, 200ms'de +1,81, 400ms'de **+1,81** —
gecikmeyle DEĞİŞMİYOR. Fable de aynısını buldu. **Londra colocation masrafı
gereksiz, karar iptal edildi.** Eski "kenar <200ms" sonucu artefaktın sönme eğrisiydi.

## ★ ASIL DARBOĞAZ: DOLUM FİYATI ÇÖZÜNÜRLÜĞÜ (gün sayısı veya hız DEĞİL)
Toplu baskı sorunu ölçüldü (Fable akış verisi, 8,13M bacak): TX'lerin **%9,0'ı çok
fiyatlı ama payların %32,5'ini taşıyor**, fiyat yayılımı ort 1,53 kr / p90 3,00 kr.
İyimser-kötümser sınır aralığı (±2,8 kr) **kovaladığımız etkiden (1-3 kr) BÜYÜK.**
Gün eklemek bunu çözmez.
**VERİ ÇAKIŞMASI SORUNU:** bacak-bazlı gerçek dolumlar 13 Ağu–5 Eyl
(`actor_inventory_ml_20260914_v1/flows/`, sütunlar: tx_hash, log_index, price,
quantity, match_us, available_us); sürekli defter yalnız 9-10 Eyl (Londra PC akışı).
ÖRTÜŞME YOK. Fable'ın `BOOKS.parquet`'i karar-anı anlık görüntüsü (5 seviye,
D/A150/A500), sürekli akış değil.
→ SIRADAKİ İNŞA: kendi tape dönemimiz için **zincir-tarafı bacak-bazlı dolum
toplayıcısı** yaz; tape zaten `cid` (conditionId) kaydediyor. O zaman aynı günlerde
hem sürekli defter hem gerçek dolum fiyatı olur, sınır aralığı kapanır.

Gözlem gecikmesi ölçüldü: match→available medyan **15 ms**, p90 76, p99 521.

## VERİ HATTI TAMAMLANDI (14 Eyl gece yarısı)
**1. Zincir-tarafı bacak toplayıcısı** (`pm_chain_fills_20260914_v1/collect.py`):
data-api `/trades?market=<cid>` her eşleşmenin iki bacağını gerçek fiyat/miktar/tx ile
veriyor. 439.084 bacak, 393 pencere-aile, 10 pazar. ~2 sn/pencere.
**Toplu-baskı hatasının GERÇEK boyutu** (doğru ölçüm: (tx,token,yön) grubu içinde —
sadece `tx`'e göre gruplamak Up/Down bacaklarını karıştırıp %82,7 gibi sahte rakam verir):
**%6,2 grup / payların %16,2'si / yayılım ort 0,95 kr (p90 2,00)**. Yani payların
%83,8'inde WS fiyatı zaten doğru → eski "kötümser sınır" (fiyatımızdaki baskı bizi hiç
doldurmaz) gerçeğe uzaktı, gerçek iyimser sınıra yakın.
**2. `CORRECTED_PRINTS.parquet`**: WS baskı akışı taban (tam kapsam + ms damga), fiyat
zincirden düzeltilmiş. 168.202 olay / 4,91M pay, %45,2 zincir-doğrulanmış fiyat,
hepsi ms damgalı. (Önceki `join_ms.py` tasarımı zinciri taban alıyordu, %50'si blok-saniye
kalıyordu — kuyruk simülasyonu için fazla kaba, terk edildi.)

## ✖ "BINANCE TÜRKİYE'DEN PERP AKIŞI VERMİYOR" — TAMAMEN YANLIŞTI
Operatör itiraz etti, test ettim, iki katmanda da yanılmışım:
- **Coğrafi engel YOK**: Türkiye'den `fapi/v1/aggTrades`, `trades`, `premiumIndex`
  hepsi **HTTP 200**. WS handshake **101**.
- **Perp akışı ALINIYOR**: `@aggTrade` veri vermiyor ama **`@trade` veriyor** (ham hali).
  Stream haritası (fstream.binance.com/ws/, ölçüldü):
  AKIYOR `@trade` `@bookTicker` `@depth5@100ms` | VERİ YOK `@aggTrade` `@markPrice`
  `@kline_1m` `@forceOrder` `@miniTicker` → 2026 USDS-M WS migration'ıyla tutarlı,
  eski host bazı stream'leri artık servis etmiyor.
**DERS: "mesaj gelmiyor" kanıt değildir; HTTP durum kodu kanıttır.** Eski `tape.py`'deki
"aggTrade TR'den gelmiyor" notu da bu yüzden yanlış, düzeltilmeli.
`perp_rec.py` artık 4 akış yazıyor: perp bookTicker+trade, spot bookTicker+aggTrade
→ `data/tape_perp/`. Fable'ın perp kulvarının veri boşluğu KAPANDI.

## GİZLİ SİNYAL: BULUNMADI (operatör sorusu)
Kanıtlanan: 17 günde artan envanter kazanan tarafa düşüyor (0,55'ten %57,7).
Kanıtlanmayan: Codex son 11 günde tersini buluyor (artan −$172/−$9.755, çift
+$22.926/+$28.749); FIFO vs ortalama maliyet seçimi payı değiştiriyor. Fable'ın perp
hipotezi makul + korelasyonlar ölçülmüş ama 49 ajanlık taramada **hiçbir kural
adversaryal incelemeyi geçmedi**; kendi sondası 400 ms'de eksi.


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [🎯 PM GEÇ-PENCERE TASFİYE (09-14): kenar zamanda — son 35 sn favori 0,75-0,90 maker alım +9,58 kr/pay (17 gün, iki yarı ayrı geçti); 240-265 sn TEHLİKE (−3…−23); dalga filtresi ve fark≥0,10 kuralı ÇÜRÜTÜLDÜ; açık risk = kuyruk, defter lazım](project_pm_late_window_liquidation_20260914.md)
