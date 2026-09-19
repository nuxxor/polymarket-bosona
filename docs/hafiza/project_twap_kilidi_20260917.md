---
name: project-twap-kilidi-20260917
description: Settlement kapanıştan 30 sn önce kamu verisiyle %100 bilinebiliyor — ama o anda defterde 0,98 altı ask SIFIR; sinyal gerçek, yürütme yok
metadata:
  type: project
---

# TWAP KİLİDİ — SİNYAL %100, ALINACAK MAL SIFIR (2026-09-17)

## Mekanizma (matematiksel, tartışmasız)
Settlement: `TWAP60(S+300) ≥ TWAP60(S)` → Up. `TWAP60(T)` = spot'un `[T−59,T]` ortalaması.
Terminal pencere **`[S+241, S+300]`**. t=S+270'te o pencerenin **yarısı zaten yazılmış**.
Kalan 30 sn'de gereken ortalama: `gerekli = (60·K − bilinen_toplam)/30`, `K = TWAP60(S)`.
`marj_bp = 10000·(P_t − gerekli)/P_t`.

## Doğrulama (kendi tape'imden, kamu Chainlink verisiyle)
| | ön okuma (yalnız defter görüntüsü) | tam sürüm (+ price_change) |
|---|---:|---:|
| sinyal hesaplanabilen pencere | 799 | 787 |
| **\|marj\| ≥ 5bp KESİN** | **597 (%74,7)** | **591 (%75,1)** |
| **SİNYAL İSABETİ** | **597/597 = %100,00** | **581/581 = %100,00** |
| **0,98 altı ask bulunan pencere** | **0/597** | **0/591** |

Kardeş oturumun Ağustos ölçümü de %74 ve iki dönemde %99,7 bulmuştu — kapsam bağımsız doğrulandı.

## YÜRÜTME ÖLÜ — ve nedeni
Kardeş oturumun **+6,40 kr/pay** iddiası `kapasite.py:32` ile **dolum defterinden** okuyor
(`from read_parquet('{P}/{rol}.parquet') where side='buy'`) — yani **başkalarının o an aldığı
baskıları** "biz alsaydık" diye sayıyor. O paylar tükendi, geriye dönük alınamaz.
Karar anı olarak **Chainlink'in bize gerçekten ulaştığı `rcv` + 200 ms** kullanıldığında
defterde 0,98 altı ask **hiç yok**. Tavan kuralı da uyarıyordu: +6,40 = 1 kr tavanının 6 katı.

## Gecikmeler (ayrımı koru: kaynak damgası → yerel alım, "eşleşme → biz" DEĞİL)
- Chainlink `cl`: **~1,5 sn**
- Kamu işlem akışı `last_trade_price`: medyan **50 ms**
- Kimlikli aktör akışı (polling): medyan **169 sn**

## Değeri ne
Sinyal gerçek ve `(Y−m)` artığının bir kısmı için **tahmin modeli gerektirmeyen** mekanizma:
"geleceği tahmin etmek" değil, **çoktan yazılmış sonucu okumak**. `EDGE_HORIZON_V1`'e
pencere-içi zaman kırılımı eklendi: artık pencere sonunda yoğunlaşıyorsa açıklama budur.
Bkz [[project-chainlink-streams-unlocked-20260913]], [[project-098-hucresi-dogrulama-20260916]]


---
**INDEX ÖZETİ (tam, kısaltma öncesi):**
- [🔐 TWAP KİLİDİ (09-17): settlement penceresi [S+241,S+300] → t=270'te sonuç %100 bilinebiliyor (597/597 ve 581/581, pencerelerin %75'i); AMA o anda defterde 0,98 altı ask 0/591 → yürütme YOK; kardeş oturumun +6,40 kr/pay iddiası tükenmiş baskıları sayıyordu](project_twap_kilidi_20260917.md)
