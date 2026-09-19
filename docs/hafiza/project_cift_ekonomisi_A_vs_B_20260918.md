---
name: project-cift-ekonomisi-a-vs-b-20260918
description: A kolu çifti 0.584'e kuruyor (0/22 pencere 1.00 üstü), B 0.968'e (12/39 = %31 garantili zarar); ama "çift tavanı" düzeltmesi karşı-olgusal testte ÇÜRÜDÜ ve canlıya girmedi
metadata:
  type: project
---

# ÇİFT EKONOMİSİ: A vs B — ve reddedilen düzeltme (2026-09-18)

Kendi tam verimizden (gecikmesiz, eksiksiz):

| kol | çift maliyeti (pay-ağırlıklı) | medyan | en kötü | 1.00 ÜSTÜ |
|---|---|---|---|---|
| A (derin merdiven, mutlak fiyat) | **0.584** | 0.610 | 0.700 | **0/22 (%0)** |
| B (mid−2/−4 tik takipli) | **0.968** | 0.957 | 1.400 | **12/39 (%31)** |

Çift kârı: A **+21 kr/pay**, B **+1.7 kr/pay**. A'nın çift ekonomisi 12 kat iyi.
Teşhis: A mutlak ucuz noktalarda BEKLER; B mid'i KOVALAR, mid kayınca iki tarafı
farklı anlarda ve ikisi de "o anın favorisi" fiyatından alır, toplam 1.00'i aşar.

Asimetri (yakın izleme, 4 A penceresi): A ya çift kurar ve çok kazanır
(+16.25$, çift 0.473), ya kuramaz ve AZ kaybeder (−1.25$, −2.60$ — çünkü
yalnız ucuz seviyeler dolar). B'de bu asimetri yok.

## REDDEDİLEN DÜZELTME — burası dersin kendisi
"Çift tavanı" (px + karşı_taraf_ortalaması >= 0.99 ise emri koyma) yazıldı,
`ab.py.cift_tavani_REDDEDILDI` olarak duruyor, **canlıya HİÇ girmedi**.

Lehine görünen kanıt güçlüydü:
- çift maliyeti >=1.00 olan 13 pencere: **−6.51 kr/pay, GA95[−9.8,−2.6]** (sıfırı dışlıyor)
- korelasyon **rho −0.451**

Karşı-olgusal test (dolum sırası `dolum` olaylarından yeniden oynatıldı) ÇÜRÜTTÜ:
- toplam +$19.81 ama **12 pencere iyileşti, 15 KÖTÜLEŞTİ**
- **medyan etki 0.00$**
- önyükleme **GA95[−37, +78]** — sıfırı kapsıyor
- kazancın **%170'i en iyi 3 pencereden**; o üçü çıkınca değişiklik net ZARAR

Mekanizma: yüksek çift maliyeti, trend penceresinin **işareti** — sebebi değil.
İkinci bacağı engellemek trendi durdurmaz, sadece bizi eşsiz bırakır.
Dış denetim bunu zaten söylemişti: "çift maliyeti tek başına ölçüt değil"
([[project-essiz-bacak-yapisal-artefakt-20260918]]).

**KURAL: korelasyon + dar GA, bir müdahaleyi haklı çıkarmaz. Karşı-olgusal
replay + önyükleme + medyan etki görülmeden deploy yok.**

İlgili: [[project-rejim-kapisi-20260918]]
