---
name: project-btc5m-maker-kapanis-20260915
description: PM BTC5m maker kulvarı 15 Eyl'de kapatıldı — 40 günde −5,26 kr/pay [−6,12,−4,39], aktör kenarı tahtada görünmeyen dolum-düzeyi seçiminde
metadata:
  type: project
---

**15 Eyl 2026 — KULVAR KAPANDI (park, mezar değil).** Tam rapor:
`data/analysis/KAPANIS_BTC5M_MAKER_20260915.md` (182 satır).

## Hüküm
Kopyalanabilir kısım (iki taraflı çift mekanizması) 40 günde, 3.756 pencerede,
gün-kümeli GA ile **−5,26 kr/pay [−6,12, −4,39]**, 40 günün **1'i** artıda.
Canlı doğrulama: 14 pencere, −6,62 kr/pay (−$5,30). Düzeltilmiş motor −5,96 dedi
→ model canlıyı üretiyor (eski motor +0,40 diyordu, yalancıydı).

## Mekanizma
- Çift TAM eşleşince **+5,51 kr/pay** (2.288 pencere) — aritmetik, kırılmaz
- Tek taraf kalınca **−37,37 kr/pay**, artan envanterin kazanma oranı **%1,8**
- Yapısal: X@p emrimiz ancak X satılırsa ya da karşı token yüksekten alınırsa dolar;
  ikisi de "X kaybediyor" demek → tek taraflı kalmak = kaybeden tarafta kalmak
- **Aktörlerde aynı delik yok:** artanları %45-57 kazanıyor (kalabalık %5-15).
  Aynı Chainlink hücresinde onlar +13…+20 kr, kalabalık +1…+4 → hücre seçimi kenar DEĞİL,
  seçim **dolum düzeyinde**. Karşı taraf kimliği borsadan işlem bitince **2,8-3,2 sn sonra**
  geliyor; özel WS kanalında taker cüzdanı HİÇ yok (4.084 kendi dolumumuzda doğrulandı).
- Aktör kâr yapısı: en iyi %5 pencere = kârın %153'ü; top-%5 hariç **−1,2 kr/pay**

## Kalıcı ölçüt
**Bu borsada 1 kr/payın üstünü gösteren her backtest, aksi kanıtlanana kadar hatalıdır.**
Polymarket'in kendi API'si, 30 gün: bosona 0,67 · mo-money 0,73 · whiskas 0,54 kr/pay.

## Elenen 16 fikir (tekrar denenmemeli — detay raporda)
dalga filtresi · model-fark kuralı · TWAP vetosu · taker ile çift tamamlama · aşağı takip ·
gerçekleşen-maliyet bütçesi · dengesizlik merdiveni · salınım filtresi · çok seviyeli merdiven ·
klip boyutu · bayat emir iptali · Kalshi kapısı · artanı satmak · favori eğimi · derinlik ·
hız/Londra colocation (iptal faydası 0/200/400 ms'de birebir aynı, iki bağımsız ölçüm)

## Yeniden açma tetikleri
1. Dolum-düzeyi kimlik/akış gerçek zamanda erişilebilir olursa
2. Borsa kuralları değişirse (ücret, %20 maker iade payı, asgari 5 pay)
3. Aktör kenarı yeniden büyürse (şu an 0,54-0,73 kr/pay, Ağustos başı 3,4'tü)
4. El değmemiş **81 günlük** Telonex defteri işlenirse (40'ı işlendi, aynı motor hazır)

Kayıtçılar DURDURULMADI: `data/tape` (5,8 GB), `data/tape_multi` (9,3 GB),
`data/tape_perp` (841 MB) + Chainlink WS + pencere-öncesi defter.
İlgili: [[project-pm-late-window-liquidation-20260914]]

## EK (15 Eyl akşamı) — kapsam düzeltmesi + 4 ölçüm
**KAPSAM: bu kapanış MAKER ÇİFT POLİTİKASINI kapatır, taker yolunu DEĞİL.**
17. Karşı taraf tiplemesi (emrin ne zaman konduğu = kimin koyduğu): sinyal GERÇEK
   (kalabalık: seyrek-işlemciden +0,58 [+0,36,+0,79] / bottan −0,77 [−0,95,−0,59]),
   ama bekleyen emirde karşı tarafı SEÇEMİYORUZ → uygulanamaz.
18. Kendi RPC/mempool 2,8 sn'yi yenmez: eşleşme zincir DIŞINDA, mempool'daki şey
   uzlaşma; kimliği erken öğrenirsin ama seçme hakkı doğmaz.
19. Çift taker arbitrajı YOK: ask toplamının medyanı 1,0100; 404k saniyede 33 sahte fırsat.
20. Geç-pencere favorisi TAKER kuralı: btc5m 17 günde 3 hücre GEÇTİ (+5,02/+5,60/+2,33)
   ama **btc15m 40 günde DÜŞTÜ** (−2,06/−2,51/−3,28) ve yön TERS → artefakt.

**Codex düzeltmeleri:** "%45 kazanma" genellenemez (20 krş alımlarda %13-27, GA sıfırı
kapsıyor); ama kontrollü aktör avantajı GERÇEK: mo-money +2,25 [1,49;3,01] ·
bosona +2,03 · whiskas +1,56 → **kopyalanamayanın gerçek boyutu ~2 kr/pay.**
**whiskas'ın %75'i TAKER** (maker +$21,7k / taker +$21,3k) — saf maker modeli yarısını kaçırıyor.
`0x3725…` whiskas değil, almach.

**İKİ AYRI AÇIK:** seçim açığı ~2 kr (kopyalanamaz) + yapısal açığımız 5,26 kr
(kendi tasarımımız). Seçimi mükemmel kopyalasak −5,26 → −3,3; ikinci açık daha büyük.
**Ölçülmemiş:** whiskas taker seçim kuralı · Codex ML dolum filtresi (+1 kr) ·
envantere göre maker-bekle/taker-al kararı.

## KESİN KAPANIŞ (15 Eyl) — kayıtçılar DURDURULDU
21. **Temiz taker testi + rejim düzeltmesi:** 40 günlük btc15m testimin 37 günü ESKİ
uzlaşma rejimiydi (TWAP 14 Ağu'da başladı) → elemem GEÇERSİZDİ. Ayrılınca:
eski −3,82 / **TWAP +8,45 [+1,75,+12,00]**. Ama dondurulmuş kuralı temiz test edince
(14-15 Eyl, TWAP rejimi, **defterdeki gerçek ask**, taker ücreti): **−11,78 kr/pay**
(149 işlem, ort 0,826, isabet %71,7). → Hücre tarihsel kayıtta gerçek ama **mekanik
hasat edilemiyor**; tarihsel +5,60 SEÇEREK alanların sonucu.
DERS: "−5,26 + 2 = −3,3" gibi farklı dönem/politika sonuçlarını toplamak geçersiz.

**DURUM:** Tüm kayıtçılar durduruldu (tape 6,6 GB · multi 12 GB · perp 1,3 GB kaldı).
Bot kapalı, açık emir 0, teminat $251,20. 21 fikir ölçüldü, hepsi sebebiyle kayıtlı.
**Yeniden açmak için yeni FİKİR değil yeni VERİ gerekiyor:** karar anında karşı tarafı
veya dolum kalitesini gösteren bir kanal. O çıkmadan ölçülecek yeni şey yok.


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [🔒 PM BTC5m MAKER KULVARI KAPANDI (09-15): 40 günde −5,26 kr/pay [−6,12,−4,39], 40 günün 1'i artıda; çift eşleşince +5,51 ama artan envanter %1,8 kazanıyor; aktör kenarı tahtada GÖRÜNMEYEN dolum-düzeyi seçiminde (kimlik 2,8-3,2 sn geç gelir); 16 fikir elendi; ÖLÇÜT: >1 kr/pay gösteren backtest hatalıdır](project_btc5m_maker_kapanis_20260915.md)
