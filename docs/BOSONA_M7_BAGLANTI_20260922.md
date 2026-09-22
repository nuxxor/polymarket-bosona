# M7 coklu-pencere baglanti tanisi

22 Eylul 2026, Londra; emir vermeyen 900 saniyelik sabit sureli kontrol.
Finansal bot, risk/butce, muhasebe ve M7-v3 kaynaklari korunur.

Tam M7 kayitcisinin yaninda ayri surecte JSON ayirmayan/diskte piyasa
verisi yazmayan bir kamu dinleyicisi ayni token listesini alir. Iki
baglantida da ayni olcum: saniyelik tampon zirvesi, tampon nedeniyle
okuma duraklamasi, iki recv cagrisi arasindaki isleme suresi, recv suresi
ve kapanis kodu. Auth/ham hata metni kayda girmez. Kamu kapanisinda
yalniz sayisal kod ve 'slow consumer' sinifi saklanir.

[websockets tampon aciklamasina](https://websockets.readthedocs.io/en/stable/topics/memory.html)
gore gelen frame kuyrugu yuksek siniri asarsa ag okuma durur. Londra'da
kurulu 17.1 kaynagi dogrudan incelendi: high=4096, low=1024; olcum
icin bu alanlar okunuyor, tasima ayarlari degistirilmiyor. Ornekleme
her recv oncesi/sonrasinda; aradaki anlik zirvelerin tam kaydi degil.

Dosyaya yazma gecikmesi recv sonrasini; kamu timestamp-alinma farki
yayin yasini gosterir. Hicbiri borsa emir aktivasyon saati degildir.
Iki baglanti ayni host/ag/sunucu altyapisini paylasir. Bir temiz kosu
kalici kesintisizlik veya kendi gercek dolum kalibrasyonu kaniti degil.

Kanit/kod: data/analysis/btc5m_m7_transport_20260922/.
Protokol kaynak hash'leri ve 900sn sureyle sonuc oncesi donduruldu.
probe.py --self-test izinli alanlar, kuyruk ve gecikme sayaci, timeout
ve kapanis hatasini kontrol eder. check.py gercek M7 ham kaydini mevcut
check_capture.py ile dogrular, olcum sayaclariyla karsilastirir.

## Sonuc

22 Eylul **02:37:54–02:52:54 Turkiye saati**; Londra UTC takviminde
21 Eylul 23:37:54–23:52:54. 900,017 saniye, dort aktif BTC5m penceresi,
603.783 kamu olay kaydi. Snapshot/delta/PONG/sira/son-kayit kontrolleri
gecti; eksik veri sifir veya eksiksiz sayilmadi.

| Okuyucu | Sure | Kamu kapanisi | En yuksek olculen kuyruk | Kuyruk nedeniyle okuma durusu |
|---|---:|---:|---:|---:|
| Tam M7 kayitcisi | 15 dk | 3 | 150 / 4.096 | 0 |
| JSON/disk islemeyen senkron kontrol | yaklasik 15 dk | 5 | 98 / 4.096 | 0 |
| Ek asenkron kontrol | 4 dk | 1 | olculmedi | olculmedi |

Tum kamu kapanislarinda sunucudan alinan kod **1013**, guvenli neden
sinifi **slow consumer**. M7 kullanici kanali: 0 kopus / 90 PONG;
bot kapali oldugundan gercek order/trade bildirimi 0.

Asenkron kontrol ilk iki okuyucudaki kopuslar goruldukten sonra ayri
protokolle eklendi; ana 900 saniyelik kriter degismedi. Ayni dondurulmus
token listesini kullandi. Senkron/asenkron uygulamalar ayni kutuphane
parser'ini, host ve agi paylasiyor; farkli servis saglayici testi degil.

Kayitci toplam CPU 78,89 sn, basit okuyucu 33,89 sn; RAM ornekleri
yaklasik 71,5–72,4 MiB / 37–38 MiB, FD 10 / 5. Kuyruklar ornekleme anlarinda
sinira yaklasmadi. Tam kayitcinin uc kopustan onceki 30 saniyesindeki
gorulen kuyruk zirveleri 27 / 32 / 147. Bu, surekli istemci tampon
birikmesi aciklamasini zayiflatiyor; anlik isletim sistemi veya ag
duraklamasini kesin dislamiyor. Basit ve asenkron kontrol de koptugundan
yalniz M7 JSON/disk islemesi veya senkron recv secimi kok neden olamaz.

Dosyaya yazma p99 1,699 ms, maksimum 9,577 ms. Price-change yayin yasi
medyan 5,741 ms / p99 214,688 ms / maksimum 676,666 ms. Bunlar borsa emir
latency'si degil. Kayit kuyrugu tasmasi, bozuk/veri-disi ret ve yazici
arizasi 0. M7 tum kopmalari kaydedip yeniden abone oldu; kayip olaylari
geri doldurmus sayilmadi. Kac olayin kayboldugu bu veriden kesin sayilamaz.

**Kesintisiz tasima kapisi gecmedi; 1013'un kalici cozumu bulunmadi.**
Bu nedenle islem koduna gerekcesiz hiz/tampon yamasi uygulanmadi. M7-v3
ve finansal kaynak/state/butce hash'leri korunuyor. Son hesap GET'inde
acik emir 0; M4v2 ve bu turun uc gozlem sureci kapali. Herhangi bir
finansal pilot veya yeni butce baslatilmadi.

Sonraki dar aday: ayni kamu akisini iki bagimsiz **tam** kayittan almak.
Bu kosuda iki senkron baglantinin kapali olma araliklari cakismadi.
Ancak bu yalniz close–yeniden-socket-acma araligi; defter/veri tazeligi
kaniti degil. Basit kontrol piyasa olaylarini saklamadigindan bu tur
yedek hatla veri kurtarma sonucu uretilemez. Sonraki testte her iki
akisin snapshot, olay kimligi/coklugu ve kaynak/alinma saati korunmali;
iki akisin dolumlarini ust uste toplamak veya sonradan en iyi goruneni
secerek canli basari yazmak yasak. Ikisi de gecersizse aralik eksik kalir.

Tekrar uretim:

```bash
"/home/taygun/Masaüstü/KararAtlas/base1/bin/python3" "/home/taygun/Masaüstü/polymarket-bosona/data/analysis/btc5m_m7_transport_20260922/check.py" "/home/taygun/Masaüstü/polymarket-bosona/data/analysis/btc5m_m7_transport_20260922/run1"
```

check.py veri butunlugu/kaynak/olcum uzlasmasini denetler; basarili
calismasi tasima kapisinin gectigi anlamina gelmez. Ciktidaki
transport_gate_passed=false ve full_calibration=false korunmalidir.
