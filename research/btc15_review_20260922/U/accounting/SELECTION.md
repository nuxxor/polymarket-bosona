# BTC15 piyasa seçimi ve saat: küçük bağımsız ek

Bu inceleme yalnız resmî BTC15 evrenini ve karar öncesi arşiv girdilerini okur; model öğrenmez, eşik aramaz. Saat UTC sözleşme başlangıcıdır. Etiket kamu dolumu gözlenmesidir; emir gönderme/iptal veya fırsat yokluğu anlamına gelmez.

## Takvim ve saat

| UTC gün | Resmî pencere | İşlemli | Oran | Tam gün |
|---|---:|---:|---:|---|
| 2026-09-13 | 96 | 56 | 58.33% | True |
| 2026-09-14 | 96 | 54 | 56.25% | True |
| 2026-09-15 | 96 | 93 | 96.88% | True |
| 2026-09-16 | 96 | 93 | 96.88% | True |
| 2026-09-17 | 96 | 87 | 90.62% | True |
| 2026-09-18 | 96 | 95 | 98.96% | True |
| 2026-09-19 | 96 | 84 | 87.50% | True |
| 2026-09-20 | 96 | 36 | 37.50% | True |
| 2026-09-21 | 48 | 0 | 0.00% | False |

**DOĞRULANDI:** sekiz tam gün 768 pencerenin 598'inde işlem var; 21 Eylül 00–12 UTC ayrı 48 pencere, işlem yok. Yarım gün tam günlerin saat oranına katılmadı. Bir tam gün çıkarılınca genel işlem oranı %74.85…%83.63.

| UTC saat | İşlemli /32 | Günler arası oran min–max | Bir gün çıkarılmış oran min–max |
|---|---:|---:|---:|
| 00 | 25/32 | %0–%100 | %75.0–%89.3 |
| 01 | 29/32 | %75–%100 | %89.3–%92.9 |
| 02 | 26/32 | %25–%100 | %78.6–%89.3 |
| 03 | 30/32 | %75–%100 | %92.9–%96.4 |
| 04 | 31/32 | %75–%100 | %96.4–%100.0 |
| 05 | 27/32 | %0–%100 | %82.1–%96.4 |
| 06 | 28/32 | %75–%100 | %85.7–%89.3 |
| 07 | 27/32 | %25–%100 | %82.1–%92.9 |
| 08 | 28/32 | %50–%100 | %85.7–%92.9 |
| 09 | 25/32 | %0–%100 | %75.0–%89.3 |
| 10 | 22/32 | %0–%100 | %64.3–%78.6 |
| 11 | 22/32 | %0–%100 | %64.3–%78.6 |
| 12 | 22/32 | %0–%100 | %64.3–%78.6 |
| 13 | 21/32 | %0–%100 | %60.7–%75.0 |
| 14 | 22/32 | %0–%100 | %64.3–%78.6 |
| 15 | 23/32 | %0–%100 | %67.9–%82.1 |
| 16 | 21/32 | %0–%100 | %60.7–%75.0 |
| 17 | 20/32 | %0–%100 | %57.1–%71.4 |
| 18 | 24/32 | %0–%100 | %71.4–%85.7 |
| 19 | 23/32 | %0–%100 | %67.9–%82.1 |
| 20 | 27/32 | %0–%100 | %82.1–%96.4 |
| 21 | 26/32 | %0–%100 | %78.6–%92.9 |
| 22 | 24/32 | %0–%100 | %71.4–%85.7 |
| 23 | 25/32 | %0–%100 | %75.0–%89.3 |

**GÖZLEMSEL DESTEK / SINIR:** her saat-gün hücresi yalnız dört sözleşmedir. Tam saat tablosu ve gün bırakma oynaklığı, tek bir saati seçerek kural ilan etmeyi desteklemez. Saat ilişkisi gün/rejim, mevcut envanter, defter veya dolmamış emir etkilerini ayırmaz.

## t180 fiyat/oynaklık: gözlenebilirlik paydası

Eski btc15_context t180 sigma değeri USD/√sn; normalize değer sigma/spot×10000. Bu girdinin geçmiş örnek erişim kusuru ana raporda ayrıca düzeltildi; bu ek eski sürümü açıkça sabit tutar. Tarihsel iki token fiyatı t180 veya daha önceki son örnektir; en çok75sn yaşında, 0<p<1. Sonraki örnek, nihai hacim/likidite veya sonuç özellik yapılmaz. Fiyat kayıtlarının yerel tarihsel alınma zamanı bilinmiyor; bunlar olay-zamanlı kamu fiyatları, bid/ask değildir.

| Sekiz tam gün sınıfı | Piyasa | Context / fiyat / ortak | Normalize sigma medyan | Ucuz fiyat medyan | Fiyat yaşı medyan |
|---|---:|---:|---:|---:|---:|
| traded | 598 | 426/598/426 | 0.3681580404016357 | 0.395 | 48.0 |
| no_observed_trade | 170 | 117/170/117 | 0.35900409787357523 | 0.355 | 48 |

t180 sınıfları (816): {'entered_by180': 326, 'later_first_entry': 271, 'no_observed_trade': 218, 'first_at_or_after_end': 1}. t180'den önce zaten girilenlerde aynı andaki sigma/fiyat ilk giriş açıklaması olamaz; piyasa-içi katılım karşılaştırması bile ters zaman yorumuna açıktır. Karar öncesi risk seti için yalnız t180'de henüz girilmemiş sonraki ilk girişler ile gözlenen işlemsizler karşılaştırılabilir. Bitiş sonrası ilk dolumu olan bir piyasa ayrıca ayrıldı.

| t180’de henüz girilmemiş tam gün durumu | Piyasa | Ortak veri | Normalize sigma medyan | Ucuz fiyat medyan |
|---|---:|---:|---:|---:|
| later_first_entry | 271 | 186 | 0.3320896697696807 | 0.415 |
| no_observed_trade | 170 | 117 | 0.35900409787357523 | 0.355 |

**KANIT YETERSİZ:** dağılım farkı karar mekanizması veya nedensel seçim etkisi değildir. Veri mevcudiyeti gün ve sınıfa göre farklıdır; `selection_audit.json.byday_context` bütün paydaları verir. Yeni 21 Eylül sıfır işlemli yarım günü eski tam günlerin kontrol grubuna ekleyip rejim etkisini gizlemedim.

Çalıştırma: `PYTHONDONTWRITEBYTECODE=1 python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/accounting/selection_audit.py`. Gömülü gelecek/bayat fiyat regresyonu,96-slot gün kontrolü ve816/598 mutabakatı her koşuda çalışır. Kaynak SHA256 JSON içinde; kaynaklar ve önceki result.json değişmez.
