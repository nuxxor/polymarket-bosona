---
name: project-prewindow-pair-maker-20260916
description: YENİ KULVAR (09-16) — pencere-ÖNCESİ çift maker'ı: ters seçim için bilgi gerekir, pencere açılmadan bilgi yok; artan envanter yazı-tura (%49,9 vs pencere içi %37,8); 28 cüzdan +0,94 kr/pay GA[+0,55,+1,32] 20 günde; simülasyon 2'şer günde +0,91/+0,37 (GA sıfırı kapsıyor), kapı 10 gün
metadata:
  type: project
---

**2026-09-16.** Paket `data/analysis/pm_prewindow_pair_20260916_v1/` (CONTRACT.md dondurulmuş, sim.py, sim_london.py).

**Mekanizma:** ters seçim bilgi gerektirir; pencere açılmadan önce ortada bilgi yoktur. Zincir defteri (20 gün):
pencere-öncesi dolan tek taraflı envanter 0,490'dan alınmış **%49,9 kazanıyor**; pencere içi aynı şey %37,8 (zehirli).
Kâr tahminden değil mekanikten: iki tokeni 0,50 altına al → merge → 1,00.

**Popülasyon kanıtı:** pencerelerinin ≥%50'sinde iki tarafı da alan 28 cüzdan, TÜM pencerelerinde (tek taraf dahil)
**+0,94 kr/pay GA [+0,55, +1,32]**, 5,95M pay, ~298k pay/gün (cüzdan başına ~10,6k pay/gün ≈ $100/gün).
Çift dolma %69,5, çift maliyeti 0,9815. **Aynı cüzdanlar pencere içinde +0,01** → kenar tamamen pencere öncesinde.
Zaman kovaları (tüm makerlar): 30dk+ önce +0,94 · 10-30dk +1,77 · 5-10dk −2,12 · 1-5dk +1,21 · son 1dk +0,06 ·
pencere içi −0,09…−0,14.

**Yürütülebilir simülasyon (dürüst kuyruk, venue sonucu):** dokunuşa post-only, S−240'ta, açılışta iptal:
tape 10 pazar/2 gün +0,91 [−0,86,+2,78] (çift %35,8, maliyet 0,9875, artan %50,4 kazanma);
Londra BTC5m/2 gün +0,37 [−1,64,+2,44] (çift %69,2, maliyet 0,9895). Kontrol pencere içi S+1: −0,42/+0,02, artan %37,4.
Daha derin (0,47/0,48) KÖTÜ (−2,09 Londra): kenar ucuzlukta değil iki tarafı da almakta. S+60'a taşımak zarar.

**Durum:** yapı doğrulandı, seviye underpowered (2 gün). Kapı CONTRACT.md'de: ≥10 gün tape, pencere-kümeli GA>0,
ex-top3>0, iki yarı>0. Kayıtçılar çalışıyor. Bu, Opus'un S+1 testinden (−2,13) FARKLI rejim; o pencere içi, bu öncesi.
İlgili: [[project-maker-ilk-alim-ters-secim-20260915]], [[project-research-followup-20260915]].

## AYNI GÜN DEVAM (16 Eyl)
- **Popülasyon OOS (survivor-bias'sız):** ilk 10 günde YALNIZ davranışa göre seçilen 37 cüzdan (çift oranı≥%50, ≥5k pay; kâra
  bakılmadı) → son 10 günde **+0,76 kr/pay GA [+0,26, +1,31]**, 3,1M pay, 9/10 gün artı; kontrol (diğer tüm cüzdanlar) +0,14 GA sıfır.
  OOS yapı: çift dolma %60,9, çift maliyeti 0,9808, artan @0,491 kazanma %49,6.
- **Kenar = ÇİFT TAMAMLAMA ORANI.** Küçük pencerelerde (≤100 pay): çift tamamlandıysa +0,73 GA[+0,38,+1,14]; tek kalınca −0,63.
  Boyut kovalarında çift dolma %34 (≤25 pay) → %87 (250-1000 pay); kenar de öyle.
- **Çift tamamlama SATIN ALINAMIYOR (yeni ölçüm):** geride kalanı dokunuşa taşı −1,29 (çift 0,9966); +1 tik −0,53 (çift 1,0025);
  ask'ten al −1,39 GA[−1,58,−1,21] (çift 1,0278). Kovalamak marjdan pahalı — 09-14 pencere-içi P3 sonucuyla aynı.
- **Havuzlanmış yürütülebilir simülasyon (4 gün kitap, Londra+tape): +0,74 kr/pay GA [−0,74,+2,24]**, 8.518 pay/gün → ≈$63/gün
  (25 pay klip, 10 pazar). Popülasyon OOS (+0,76) ile birebir aynı sınıf; GA 4 günle sıfırı kapsıyor, 10 gün kapısı duruyor.

## 121 GÜNLÜK ARKA TEST (Telonex quotes arşivi, BTC15m, 26 Nis–24 Ağu; `quotes121.py`, Q121/J121.parquet)
11.548 pencere, 121 gün, pencere öncesi kotasyonlar (ilk kotasyon medyan S−10,9 SAAT önce → saatler öncesinden emir konabiliyor,
kullanıcı haklıydı). **İki fiyatlama gerçeği 5 ay boyunca sabit:**
1. **Çift maliyeti dokunuşta 0,99** — medyan 0,9900, pencerelerin %99-100'ünde <1,00, aylık ortalama 0,9870-0,9900 (Nis/May/Haz/Tem/Ağu).
   Yani iki tarafı da dokunuşta doldurabilirsen pay başına +0,50 kuruş garanti.
2. **Pencere öncesi fiyat ADİL** — 10.881 pencerede Up kazanma %49,5 ±0,94 (50/50'den ayırt edilemiyor); mid kovalarında
   gerçek−fiyat farkı ±0,03 içinde, çoğunlukla −0,01. → artan envanter GERÇEKTEN yazı-tura, ters seçim yok.
3. Dokunuştaki medyan derinlik 150-200 pay → 25 paylık emrimiz kuyruğun ~1/7'si.
**Kâr aritmetiği:** eşleşme oranı f ile beklenen ≈ f×0,50 − (1−f)×0,50 kr/pay (makas 1 kr). Başabaş f≈%50;
popülasyon f≈%61-87 ve dokunuş ALTINA yerleşerek çift maliyetini 0,9808'e indiriyor (+0,96/eşleşen pay) → OOS +0,76.
Benim 4 günlük simülasyonumda f=%56 (25 pay) → aritmetik +0,06…+0,74 aralığı; yani **tek belirsiz değişken DOLUM/EŞLEŞME ORANI**,
kenar veya ters seçim değil. Bunu ancak canlı/gölge ölçer (kitap 121 gün var ama işlem verisi yalnız 4 gün).

## CANLI HAZIRLIK TAMAM (16 Eyl, ÇALIŞTIRILMADI — operatör onayı bekliyor)
`live_runner.py` (paket içinde): `--test` 20/20 birim testi geçti; KURU koşu gerçek kitapla uçtan uca çalıştı
(12 pencere karar, 24 emir, açılışta teyitli iptal, çift maliyeti 0,98-0,99 — 121 günlük arşivle birebir).
Güvenlik: ARM dosyası zorunlu, STOP dosyası, günlük kesici −$25 (gerçekleşen + en kötü durum), bağlı azami nakit $150,
azami 30 açık pencere, çift maliyeti >0,995 ise emir yok, 12 saat azami çalışma, başka yazıcı süreç varsa başlamaz.
probe.py v2 dersleri içeride: iptal teyitsizse bacak AÇIK kalır; POST timeout = BELİRSİZ (risk korunur); restart'ta state yüklenir;
sonuç yalnız Gamma'dan. Kuyruk ölçümü (KURU): önümüzdeki medyan 35-45 pay, bacakların yarısında ≤25 pay.
RUNBOOK.md'de operatör sırası. REVIEW_REQUEST.md bağımsız denetime gönderildi (3 kusurum içinde: 121-gün totolojisi,
tek-taraflı bacakta ±0,9¢ belirsizlik, cüzdan seçim filtresi).

## BAĞIMSIZ DENETİM SONUCU (16 Eyl): **DAHA VERİ — CANLIYA HAZIR DEĞİL**
Rapor: `data/analysis/pm_prewindow_pair_independent_audit_20260916_v1/REPORT_TR.md`. 24 test, 25 dosya Ruff/AST geçti, canlı emir yok.
- **K1 (kendi yakaladığım totoloji) doğrulandı** → 121 gün yalnız fiyatlama olgusu; kâr/ters-seçim kanıtı DEĞİL.
- **Popülasyon OOS yeniden üretildi:** +0,76004 [+0,27255;+1,30505], 3,098M pay, 9/10 gün; eşik taramasında 9/9 kombinasyon artı → K3 tek başına düşürmüyor.
- **BENİM HATAM (kendi hesabımla doğruladım):** "aynı cüzdanlar pencere içinde +0,01" YANLIŞ — o 28 cüzdanlıktı (both≥%50 & ≥20k pay).
  Asıl 37 cüzdanın test dönemi pencere-içi sonucu **+0,41 c/pay** (3,71M pay). → "kenar YALNIZ pencere öncesinde" iddiası GERİ ÇEKİLDİ;
  pencere öncesi daha iyi (+0,76 vs +0,41) ama tekil değil.
- **Simülasyon kuyruk motoru kusuru:** başlangıç defter anlık görüntüleri atlanıp yalnız price_change kullanılmış → tape'te 1.184 bacağın
  başlangıç sırası yanlış, 149'una dolum yazılmış. Ham defter eklenince: tape +0,9106→+0,7093, Londra +0,3677→+0,2806,
  **havuz +0,7387→+0,5725, GA [−0,863; +2,078]**. İptal sıra kredisi kaldırılırsa havuz −1,772 (duyarlılık).
- **Geç ulaşan işlem:** karardan 2,351 sn ÖNCE olmuş bir işlemden 25 pay dolum yazılmış (saat kusuru).
- **J121 etiketi Gamma değil** (sona yakın orta fiyattan türetilmiş): 313/11.548 uyuşmazlık, 667 pencere gelecek-fiyat güvenine göre dışlanmış.
  §3.3'ün Gamma etiketleri doğru.
- **"Pencere öncesi bilgi yok" DESTEKLENMİYOR:** S−5 kaynak saatinde yön doğruluğu %56,79. K2'deki ±0,9¢ dolum-koşullu sapmayı sınırlamaz.
- **Kapasite:** 25 pay / görünen sıra ≠ dolum ihtimali; medyan başlangıç sırası tape 205, Londra 526. Ham defter düzeltmesinde pay %0,4
  azalırken PnL %23 azaldı → hangi bacağın dolduğu belirleyici. 10 eşzamanlı pencerede tek taraflı kayıp potansiyeli $125;
  gerçekleşmiş PnL'e bakan $25 kesici bunu baştan sınırlamıyor (RUNBOOK'a düzeltme gerek).
- **Sıradaki:** aynı kuralı mevcut 21 günlük arşivde fiyat-seviyesi desteğiyle sına → sözleşme kapıları (≥10 gün) → geçerse 1 hafta kuru gölge.
**DURUM: live_runner.py ARM EDİLMEDİ, çalışmıyor, sıfır gerçek emir. Denetimdeki dosya değişiklikleri benim yazma+kuru koşumdu.**

## DENETİM DÜZELTMELERİ TAMAMLANDI (16 Eyl gece) — CANLI YOK
1. **Kuyruk motoru defter tohumlu:** `parse_books.py` (tape'ten 130,9M `pm:book` satırı) → `BK_PRE.parquet` (8,4M, abonelik
   anlık görüntüsü dahil; ilk filtrem S−245 idi ve onu eliyordu, düzeltildi). `sim3.py` PC+BK'nın EN GÜNCELİNİ kullanıyor.
2. **Geç-ulaşan işlem filtresi:** borsa saati (src) karar anından önce olan işlemler dolum saydırmıyor.
3. **J121 etiketi:** 1.500 pencerelik Gamma örneği → **%97,5 uyum**, Up kazanma %49,56 (vekil %49,70). Çift maliyeti olgusu
   etkilenmiyor; J121 yine de yalnız FİYATLAMA olgusu olarak sınıflı (K1 totolojisi).
4. **Kesici:** `WORST_CAP=25` — açık pozisyonların en kötü durumu; 25 paylık klipte fiilen 2 eşzamanlı tek-taraflı pencere.
   Ayrıca döngü `pnl − risk ≤ LOSS_CAP` olunca da duruyor. live_runner testleri 22/22.
5. **Sözleşmeden kaldırıldı:** "pencere öncesinde bilgi yok" (S−5 yön %56,8) ve "kenar yalnız pencere öncesinde"
   (37 cüzdan içeride de +0,41 — kendi hesabımla doğrulandı).
**Düzeltilmiş sayılar:** benim motorum tape 2 gün +0,90 GA[−1,05,+2,77]; denetçi aynı veride +0,71; havuz +0,57 GA[−0,86,+2,08].
13 pencerede motorlar ayrışıyor (dolum miktarı), yön aynı. İptal-kredisiz stres −0,29…−1,77 (alt sınır değil: seviye
küçülmelerinin %17,7'si işlem eşleşmeli, `calib_cancel.py`).
**Sıradaki:** `daily.sh` ile her gün yeniden ölç; kapı ≥10 gün tape + pencere-kümeli GA>0 + ex-top3>0 + iki yarı>0.
Kayıtçılar çalışıyor. ARM edilmedi, sıfır gerçek emir.


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [🕰️ PENCERE-ÖNCESİ ÇİFT MAKER'I (09-16, YENİ): ters seçim bilgi ister, pencere açılmadan bilgi yok — artan envanter %49,9 kazanıyor (pencere içi %37,8); 28 cüzdan +0,94 kr/pay GA[+0,55,+1,32]/20 gün; dürüst simülasyon 2 günde +0,91 ve +0,37 (GA sıfırı kapsıyor); dokunuşa koy, açılışta iptal; DENETİM 09-16: DAHA VERİ — kuyruk motoru kusuru (ham defter atlanmış) havuzu +0,74→+0,57 GA[−0,86;+2,08] indirdi, 'kenar yalnız pencere öncesi' GERİ ÇEKİLDİ (37 cüzdan içeride de +0,41), 'öncesinde bilgi yok' çürüdü (S−5 yön %56,8); live_runner hazır ama ARM EDİLMEDİ](project_prewindow_pair_maker_20260916.md)
