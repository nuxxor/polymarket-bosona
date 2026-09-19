# ÖN KAYIT — Ucuz Bant Maker (yalnız kol A, tavan 0.40)
## Yazıldı: 2026-09-19, KODDAN ÖNCE (playbook #52)

## Hipotez
BTC 5dk pazarlarında 0,40 altı fiyatlara maker alış emri koymanın küçük ama
gerçek bir pozitif beklentisi vardır; 0,40 üstünde beklenti negatiftir.

## Dayanak (üç bağımsız kaynak, aynı yöne)
**1. Zincir-kesin defter**, 19 gün, 13,7M maker BUY dolumu, yalnız 1-9 paylık
dolumlar (bizim klip sınıfı), HAVUZLANMIŞ tahminci `E[sonuç|doldu] − fiyat`:
```
0.20-0.30  +1.55      0.40-0.50  -0.45
0.30-0.40  +0.71      0.50-0.60  -0.98
0.10-0.20  +0.43      0.60-0.80  -2.17
```
**2. Kendi 529 dolumumuz** (2.631 pay, 18 Eylül):
```
0.10-0.20  +1.48      0.40-0.50  -0.79
0.20-0.30  +0.99      0.50-0.60  -3.93
0.30-0.40  +0.70      0.60-0.80  -9.56
0.40 ALTI: 1.211 pay  +$11.45  |  0.40 USTU: 1.355 pay  -$50.95
```
**3. İkisinin uyumu:** korelasyon **+0,918**, ortalama mutlak hata 2,05 kr/pay.

### HANGİ TAHMİNCİ — ve neden diğeri reddedildi
PENCERE-EŞİT ağırlıklı tahminci aynı veriden ZIT işaret üretiyordu
(0,60-0,80 için +10,83 vs havuzlanmış −2,17). Kendi gerçekleşenimizle
korelasyonu **−0,931**, yani sistematik olarak tersini söylüyor. Sebebi:
pencere-eşit ağırlık ters seçimi gizler — kaybeden pencerelerde daha çok
dolarsın, eşit ağırlık bunu saymaz. **Havuzlanmış tahminci kullanılacak.**

## Dondurulmuş kural
- **Yalnız kol A.** Kol B (mid takipli) KAPATILDI: hacminin tamamı ≥0,40'ta.
- Izgara: `[0.40, 0.30, 0.22, 0.15, 0.10, 0.06, 0.03]`, klip 5 pay
- `PX_TAVAN_MAKER = 0.40` (0,45'ten indirildi)
- Diğer parametreler 18 Eylül sürümüyle aynı; A_UYUM ve TAMAMLA KAPALI
- Boy deneyi KAPALI, rejim kapısı KAPALI (IPW ile çürüdü: +0,70 GA[−3,65,+4,74])

## Beklenti (önden yazılıyor)
- Kenar: **+1,0 kr/pay** (aralık +0,4 … +1,6)
- Hacim: ~15 pay/pencere
- Pencere σ: $4,05 → günlük σ ≈ $67, günlük beklenen ≈ **+$41**
- **Bir günde anlamlı sonuç ÇIKMAZ.** Altı gün gerekir.

## Durdurma ve değerlendirme
- Kontrol noktası: **300 pencere** (~1 gün). Ara okuma yalnız sağlık kontrolü;
  karar 300'den önce VERİLMEZ.
- Para sınırı: `KESICI = -100` (taban ≈ $440, bakiye $540).
- Sonuç üç kategoriden biri: belirgin artı / belirgin eksi / **BELİRSİZ**.
  GA sıfırı kapsıyorsa BELİRSİZ yazılır; "işaret pozitif, demek ki çalışıyor" YASAK.
- Sıfır dolumlu ve atlanan pencereler de kayda girer.
- Bu belge değişecekse ÖNCE burası yeniden yazılır, sonra kod (playbook #52).

## Bu hipotezi NE ÇÜRÜTÜR
- 300 pencerede kr/pay < 0 ve GA sıfırın altında → hipotez çürük
- 0,40 altı dolumlarda ters seçim imzası (dolum sonrası mid'in sistematik
  aleyhte kayması) → tahminci yanlış demektir

---
## EK (2026-09-19 23:50) — KİRLİ PENCERE HARİÇ TUTULDU
`S=1789774800` sayımın DIŞINDA. Sebep: o pencere açılırken bot bir kod hatasıyla
çöktü (`koy_toplu` 4'lü demet açılımı canlı yolda 3'lü kalmıştı; kuru koşu o satıra
hiç ulaşmıyor). 11 yetim emir borsada kaldı, biri doldu (9,99 pay Up, $2,60),
operatör onu elle $0,22'den kapattı (~−$0,40). Kod düzeltildi ve **canlı yol
artık testli** (sahte client ile 4 senaryo; 57/57).
**Sayım `S>=1789775100`'den başlar.**
