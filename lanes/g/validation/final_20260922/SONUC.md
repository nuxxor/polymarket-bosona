# G1 ilk 30 dakika — 22 Eylül 2026

12:27:27–12:57:26 Türkiye saati, normal süre sonu. Bot kapalı; yeniden başlatılmadı.

| Pencere (TR) | İşlem PnL ($) |
|---|---:|
| 12:30 | +5,15 |
| 12:35 | +3,10 |
| 12:40 | +0,75 |
| 12:45 | −0,198115 |
| 12:50 | −2,345571 |
| 12:55 | +2,75 |
| **Toplam** | **+9,206315** |

63 kabul edilen emir, 36'sında dolum; kısmi dolum nedeniyle 37 dolum artışı.
Son gerçek hesap kontrolü: açık emir 0, bekleyen sonuç 0, risk 0.
İade ve sabit giderler hariç. Eski hesap PnL'si −15,234894; yeni mutabakat
−6,028580. Fark yalnız bu pilot; geçmiş zarar silinmedi.

Üç piyasa WS kopması ve yedi emir reddi kaydedildi. SDK telemetri yazma
hatası yok. Kaynak/state/bütçe değişmedi. İki gözlemci normal süre sonunda
kapandı. İlk küçük pilotun kazancı kalıcı strateji üstünlüğü kanıtı değildir.

Son pencere ilk kontrolde resmî sonuç bekliyordu; `recheck/` ilk kesiti,
`complete/` sonraki tam mutabakatı korur. `check.py` Decimal ile altı
pencerenin miktar, maliyet, ödeme, toplam ve kapanışını tekrar denetler.
