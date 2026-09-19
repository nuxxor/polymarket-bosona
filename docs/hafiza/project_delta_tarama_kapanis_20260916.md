---
name: project-delta-tarama-kapanis-20260916
description: base.py iki-tarafli pasif kotasyon — 6 DELTA x 2 cikis x 24 saat hepsi EKSI; son kaldirac tuketildi
metadata:
  type: project
---

2026-09-16. `base.py` politikasi (t=S+1, p=bb-DELTA, cift kapagi 0,97, 5 pay/taraf,
post-only) durust kuyruk motoruyla tarandi. 2.015 pencere / 5 coin / 4 gun,
PM tam merdiven defteri. Detay: `data/analysis/pm_delta_tarama_20260916_v1/SONUC.md`

- **6 DELTA (0,03..0,15) x 2 cikis varyanti = 12 konfigurasyonun 12'si EKSI**
  (-6,02 … -8,48 kr/pay), hepsinin gun-kumeli GA'si sifiri disliyor, 4/4 gun eksi.
- DELTA=0,15 operatorun %20 R2 esigini asiyor (%22,6) → o satir gecersiz;
  gecerli satirlarda R2 %5,7-%11,3.
- **SAAT KIRILIMI: 0/24 saat artida.** "Yanlis saatte calisiyor" hipotezi curudu.
- t=120 cikis kurali her DELTA'da +0,2..+0,8 kr/pay ama isareti cevirmiyor.
- Basabas cift-tamamlanma %79,8; motor %50,4, canli %62-65 → ikisi de cok altinda.
  Motorun bilinen kotumser yanliligi ([[project-uygunluk-dolum-modeli-20260916]])
  duzeltilse bile bosluk kapanmiyor.

**SAKLANAN BILESEN:** t=120'de tek kalan bacagi satmak — Londra kalibrasyonu ve bu
tarama bagimsiz olarak ayni optimum ani buldu. Gelecekteki kotasyon politikalarinda
kullanilabilir. base.py'de `SATIS_ACIK=False` ile KAPALI durumda.

**Bu kulvarda tek acik aday DEGIL, ayri kulvar:** [[project-bosona-gec-favori-20260916]]
0,98-1,00 bandi (0/1401 kayip, ters secim yok) — rekabet ve tamamlayici likidite
sorulari kapatilmadan para yok.


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [📉 DELTA TARAMASI — base.py KOTASYON POLİTİKASI TÜKENDİ (09-16): 6 DELTA × 2 çıkış × 24 saat = hepsi EKSİ (−6,02…−8,48 kr/pay, GA sıfırı dışlıyor, 0/4 gün, **0/24 saat**); başabaş çift-tamamlanma %79,8 ama motor %50,4 canlı %62-65; saklanacak bileşen = t=120 çıkış kuralı (iki bağımsız veri setinde aynı optimum, base.py`de KAPALI)](project_delta_tarama_kapanis_20260916.md)


---

# MOTOR DÜZELTMESİ SONRASI YENİDEN KOŞUM (2026-09-17)

**Kusur (denetimden):** `tara.py` kuyruk borcunu KALICI sayıyordu — önümüzdeki kuyruk
iptal edilip yok olsa bile hâlâ çıkarılıyordu. Doğru kural: **limitin ALTINDA gerçekleşen
bir işlem, o seviyedeki tarihsel kuyruğun temizlendiğini kanıtlar** (kendi tokende px<p,
tamamlayıcıda px>1−p) → kalan kuyruk 0, emir dolmuştur. Kronolojik işlenir.

## Yan yana sonuç (aynı 1.259-1.267 pencere, 4 gün)
| DELTA | motor | çift% | kr/pay | %95 GA | artıda gün |
|---|---|---:|---:|---|---|
| 0,05 | ESKİ tut | 50,4 | **−8,07** | [−8,48, −6,49] | 0/4 |
| 0,05 | **DÜZ** tut | 60,0 | **−4,19** | [−4,62, −3,65] | 0/4 |
| 0,05 | DÜZ SAT | 44,7 | −3,76 | [−4,69, −3,24] | 0/4 |
| 0,09 | DÜZ SAT | 27,7 | **−4,01** | [−5,07, −3,15] | 0/4 |
| 0,15 | DÜZ SAT | 12,8 | −4,45 | [−5,38, −3,98] | 0/4 |

Denetim "−8,07 → −4,11" bildirmişti; bağımsız uygulamam **−4,19** verdi ⇒ hata ve büyüklüğü DOĞRULANDI.

## HÜKÜM
Düzeltme **+3,9 kuruş** değerinde ama işareti çevirmedi. **12 konfigürasyonun hepsi eksi**,
hepsinin GA'sı sıfırı dışlıyor, **0/4 gün artıda**. Çift tamamlanma %50,4→%60,0 çıktı ama
başabaş **%79,8** — yapısal olarak yetersiz.

⇒ "Bu hükümler bozuk motorla verildi, şüpheli" endişesi KAPANDI. Kulvar gerçekten ölü.
Düzeltilmiş motor `scratchpad/tara_duzeltilmis.py` (DUZ=True/False ile iki davranış).
