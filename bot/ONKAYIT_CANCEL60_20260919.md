# ÖN KAYIT — cancel60 (GEC_KES=60, UCUZ_ESIK=0.40)
## HAZIRLIK — operatör onayı bekliyor, KOD DEĞİŞTİRİLMEDİ

## Önceki deneyin kapanışı
`ONKAYIT_UCUZ_BANT_20260919.md` — **142/300'de ERKEN SONLANDIRILDI.**
```
142 pencere | 2074 pay | -$38.35 | -1.85 kr/pay
sifirdan 0.82 sigma | onkayit beklentisi +1.00'in 1.27 sigma altinda
borsa PnL -51.11 = kesici butcesinin %51'i
```
**Sonuç kategorisi: BELİRSİZ** (GA sıfırı kapsıyor) ama **bütçe projeksiyonu
kesiciyi aşıyordu** (300 pencerede ~−$108 vs kesici −$100). Bot 12 saatlik
MAX_SAAT sınırına takılıp kendi durdu; devam kararı verilmedi.
İstatistiksel olarak "çürüdü" DEMİYORUZ; "bu bütçeyle tamamlanamadı" diyoruz.

## Yeni hipotez
Doldurulmamış TÜM emirleri **t=60 saniyede** iptal etmek, mevcut t=200/≤0,25
kuralından daha iyidir.

## Dayanak (GPT Ultra derin incelemesi, bağımsız)
`data/analysis/btc5m_maker_deep_review_20260919_v1/REPORT.md`
```
tam replay 4.378 pencere / 19 gun:
  mevcut politika : -0,645 kr/pay  -$442,96
  cancel60        : +2,061 kr/pay  +$523,36
  fark            : +$966,32  [$361,36 , $1.623,99]
  2.310 iyilesen / 1.014 kotulesen / 1.054 ayni | medyan +$0,70 | en iyi-3 %1,96
```
Playbook #47 kontrol listesini GEÇİYOR (medyan pozitif, en iyi-3 küçük,
iyileşen > kötüleşen, GA sıfırı dışlıyor).

**Ve replay modeli canlıda doğrulandı:** mevcut politika için −0,645 tahmin etti,
canlıda 142 pencerede −1,85 çıktı. Aynı yön, aynı büyüklük mertebesi.

## ÇEKİNCELER — raporun kendisi bunları saklamadı, biz de saklamıyoruz
1. Kapsam %95'e çıkarılınca cancel60 **−1,102 [−3,469,+1,030]** oluyor.
   Mutlak kârlılık popülasyon kısıtına DAYANIKLI DEĞİL.
2. Aile geneli işaret-çevirme **p=0,129** (anlamsız). O ailenin kazananı cancel**200**.
3. Geliştirme döneminin ikinci yarısında eşleşmiş kazanç **negatif** (−$21,88):
   ön kayıtlı kararlılık kapısını GEÇEMİYOR.
4. Kendi 24 dolumumuzla karşı-olgusal: +$19,65 **[−$4,50,+$43,50]**, sıfırı kapsıyor.

Bu yüzden bu bir **DENEY**, terfi değil. Beklenti replay'in +2,06'sı DEĞİL.

## Dondurulmuş kural
```python
GEC_KES     = 60.0     # 200.0 -> 60.0
UCUZ_ESIK   = 0.40     # 0.25 -> 0.40  (yani t=60'ta TUM acik emirler iptal)
```
Diğer HER ŞEY aynı: ızgara [0.40…0.03], klip 5, tavan 0,40, yalnız kol A,
kapı kapalı, A_UYUM/TAMAMLA kapalı, DENGE_SINIR 10, TARAF_TAVAN 10.

## Beklenti (önden yazılıyor)
- Replay +2,06 der; **biz +0,5 ile +1,5 kr/pay bekliyoruz** (replay bir
  sabit-akış yer değiştirme modeli, gerçek kuyruk önceliği değil).
- Hacim DÜŞECEK: replay'de 68.685 → 25.392 pay (%63 azalma). Daha az dolum,
  daha az rebate ($113 kayıp öngörülüyor), ama işlem kenarı daha iyi.
- Rebate: `0.014·q·p·(1−p)` → 0,24 kr/pay @0,22, 0,336 @0,40.

## Durdurma ve değerlendirme
- Kontrol noktası: **200 pencere** (300 değil — bütçe daha kısıtlı).
- Para sınırı: **taban ~$430** (bakiye ~$490, yani bu deney için $60 alan).
  **DÜZELTME (12:45, koddan ÖNCE):** `KESICI` KÜMÜLATİF sayaca bakar ve sayaç
  biten deneyden **−48,06** taşıyor. `KESICI=−60` yazmak cancel60'a yalnız
  **$12** alan bırakırdı — 200 pencerelik kontrol noktasına ulaşmadan durur,
  deney tanımı gereği tamamlanamazdı. Doğrusu:
  **`KESICI = −108`** (−48,06 mevcut − 60 yeni ≈ taban $430).
  Sayaç SIFIRLANMIYOR: geçmiş zararı unutan bir kesici 09-18'de gerçek bir
  kayıp yaşatmıştı (playbook #46).
- Sonuç üç kategori: belirgin artı / belirgin eksi / **BELİRSİZ**.
- Bu deneyin bütçesinin %60'ı (yani sayaç **−84**'e inerse) 100 pencereden önce
  tükenirse DUR ve yeniden değerlendir.
- Sıfır dolumlu ve atlanan pencereler kayda girer.

## Neyin çürüteceği
- 200 pencerede kr/pay < 0 ve GA sıfırın altında
- Hacim düşüşü öngörülenden (%63) çok farklı çıkarsa → replay modeli yanlış
- Dolum başına maruziyet artarsa → t=60 iptali beklenmedik bir şey yapıyor
