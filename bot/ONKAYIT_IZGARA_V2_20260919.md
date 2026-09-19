# ÖN KAYIT — Izgara v2 (basamaklar 0,16-0,34) + cancel60
## Yazıldı 2026-09-19 13:30 UTC, KODDAN ÖNCE (playbook #52)

## Önceki deneyin durumu
cancel60 (`ONKAYIT_CANCEL60_20260919.md`), 4 pencere sonra **SONLANDIRILDI**:
3,8 pay/pencere (öncesi 17,5), 4 pencerenin 2'si tamamen boş.
Ön kayıttaki çürütme koşulu tetiklendi: *"hacim düşüşü öngörülenden (%63) çok
farklı çıkarsa → replay modeli yanlış."* Gerçek düşüş **%78**.
**Sebep teşhis edildi:** basamaklarımız 60 saniyede dolmayacak kadar derin.

## Hipotez
Basamaklar 0,16-0,34 bandına taşınırsa, aynı klip ve aynı 0,40 tavanıyla,
pencere başına beklenen katkı belirgin biçimde artar.

## Dayanak — 19 günlük zincir defteri, HAVUZLANMIŞ tahminci, 1-9 paylık dolumlar
Yalnız **t<60** kesiti (kenarın olduğu tek zaman dilimi: 0,20-0,40 bandında
t<60 **+2,34** [+0,35,+4,44], t60-150 +0,92, t150-240 +0,20, t240+ −0,19).
```
fiyat        kapsam   kenar      GA95
0.20-0.22     36%     +5.52   [+2.25,+9.23]
0.22-0.24     41%     +5.17   [+1.21,+9.98]
0.26-0.28     57%     +3.60   [+0.67,+6.73]
0.28-0.30     63%     +2.89   [+0.29,+5.64]
0.32-0.34     81%     +1.87   [+0.30,+3.67]
0.38-0.40     92%     -0.03
0.40-0.42     96%     +0.15
```
**Mevcut basamaklarımızın t<60 performansı:**
```
0.40: %95 kapsam, kenar -0.42   <- EN COK DOLAN, ZARARDA
0.30: %69            +2.00
0.22: %40            +5.63      <- EN IYI
0.15: %15            +2.30
0.10: % 6            +0.23
0.06: % 2            -2.76      <- negatif, olu
0.03: % 0            -2.84      <- negatif, olu
```

## Dondurulmuş kural
```python
FIYATLAR = [0.34, 0.30, 0.26, 0.22, 0.20, 0.16]   # 7 basamak -> 6
# ATILAN: 0.40 (kenar -0.42), 0.15/0.10 (dusuk katki), 0.06/0.03 (negatif+olu)
GEC_KES  = 60.0     # degismedi
UCUZ_ESIK= 0.40     # degismedi
PX_TAVAN_MAKER = 0.40  # degismedi
KLIP = 5.0, A_ORAN = 1.0, KESICI = -108.0  # degismedi
```

## Beklenti (önden yazılıyor)
Üst-sınır hesabı pencere/taraf başına **+0,176$ → +0,517$** (2,9 kat) diyor.
**Bu rakama İNANILMIYOR.** "Kapsam" = o fiyatta işlem gören pencere oranıdır;
bizim emrimizin dolacağını GARANTİ ETMEZ (kuyruk önceliği modellenmiyor).
Güvenilen şey **sıralama ve yön**, mutlak büyüklük değil.
- Beklenti: **+1,0 … +3,0 kr/pay** (mevcut ölçülen −1,85'ten iyi olmalı)
- Hacim: 3,8 pay/pencere'den **8-14**'e çıkmalı (basamaklar daha erişilebilir)
- **Hacim 6'nın altında kalırsa hipotez yanlış** → basamaklar hâlâ çok derin

## Durdurma ve değerlendirme
- Kontrol noktası: **150 pencere**.
- Kesici **−108** (değişmedi; sayaç −48 taşıyor, bu deneye ~$60 alan).
- Sayaç **−84**'e inerse 75 pencereden önce DUR, yeniden değerlendir.
- Sonuç üç kategori: belirgin artı / belirgin eksi / **BELİRSİZ**.
- Sıfır dolumlu pencereler kayda girer.

## Neyi çürütür
- 150 pencerede kr/pay < 0 ve GA sıfırın altında
- Hacim < 6 pay/pencere → basamak yerleşimi teşhisi yanlış
- 0,16-0,22 basamakları hiç dolmazsa → "kapsam" ölçüsü bizim için geçersiz

---
## EK (13:45 UTC) — SAYAÇ SIFIRLANDI, KESİCİ YENİDEN HESAPLANDI

**Sorun:** `st['pencereler']` hiç budanmıyordu ve 210 pencereye (dünkü 14:45'e
kadar) çıkmıştı. Mutabakat her turda 23 saatlik işlem geçmişini (6.676 işlem,
14 sayfa) çekmek zorunda kalıyor, data-api **999 hız limiti** veriyor ve bot
`BASLAMIYOR: baslangic mutabakati eksik` ile fail-closed oluyordu.
Bu, sayfalama tavanı hatasının **üçüncü** tekrarı (500 → 2.000 → yine yetmedi);
tavanı yükseltmek bir koşu bandı, geçmiş her gün büyüyor.

**Yapılan:**
1. Mutabakat artık tüm geçmişi sayfalamıyor; takip edilen en eski pencerenin
   gerisine geçince duruyor (kod düzeltmesi, 66/66 test).
2. **STATE arşivlendi ve sayaç sıfırlandı** (`STATE_ab.json.arsiv_20260919`).
   Kapanan deneylerin sonuçları LOG'da ve hafızada zaten kayıtlı; sayaç
   sıfırlamak geçmişi silmiyor, yalnız mutabakat yükünü kaldırıyor.
3. **KESICI = −100**, çünkü sayaç artık sıfırdan başlıyor:
   `bakiye $530,45  −  taban $430  =  $100 alan`.
   (Playbook #46'nın uyardığı "geçmişi unutan kesici" riski, tabanın MUTLAK
   değerden hesaplanmasıyla karşılanıyor — bakiye ölçüldü, varsayılmadı.)

**Kontrol noktası yine 150 pencere. Sayaç −60'a inerse 75 pencereden önce DUR.**

---
## EK 2 (17:20 UTC) — cancel60 GERİ ALINDI, KODDAN ÖNCE

**Bulgu:** cüzdan-pencere düzeyinde ölçüm (19 gün, 473.070 kayıt, yalnız ≤0,40
alan sınıf) şunu diyor:
```
SON DOLUM ZAMANI      kr/pay
  hepsi t<60 (BIZ)    -0,65
  t60-150             -1,73
  t150+               +0,31   <- tek pozitif
DOLUM SAYISI
  1 dolum/pencere     -0,77   (255.997 kayit)
  2-3 dolum           +0,51
ORTALAMA FIYAT
  0,25-0,33 (BIZ)     +0,77   <- BANDIMIZ DOGRU
```
**Bizim tam profilimiz (5-9 pay + hepsi t<60 + ort 0,25-0,33): −2,47
[−6,11,+0,85]**, 9.784 kayıt. Canlı sonucumuz −1,85 ile örtüşüyor.
→ **Uygulama bozuk değil, PROFİL kaybettiriyor.**

**Neden yanıldım:** `GEC_KES=60`'ı DOLUM düzeyindeki bir ölçüme dayandırmıştım
("0,20-0,40 bandında t<60 kenarı +2,34"). O soru "şu dolumun kenarı ne?" idi.
Bu ölçüm ise "işi t=60'ta biten katılımcı ne kazanır?" diye soruyor.
İkisi zıt cevap veriyor ve **strateji kararı için doğru birim cüzdan-pencere**,
çünkü biz o birimde çalışıyoruz.

**Değişiklik:** `GEC_KES = 60 → 200`, `UCUZ_ESIK = 0,40 → 0,25`
(yani 18 Eylül'deki orijinal davranış: t=200'den sonra yalnız ≤0,25 iptal).
Izgara v2 KALIYOR (bandımız doğru ölçüldü). Tavan 0,40 KALIYOR.

**Beklenti:** −2,47'lik hücreden çıkıp "t150+ / 2-3 dolum" hücresine doğru
gitmek. Kıyas +0,31 … +0,51. Rebate (+0,27) ile toplam +0,6 … +0,8.
**Kontrol noktası yine 150 pencere.**
