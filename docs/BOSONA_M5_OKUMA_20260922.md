# M5: okuyucu duzeltildi; emir simulatoru henuz kalibre degil

22 Eylul 2026, Turkiye saati. Kapsam M4v2'nin 12 kabul edilen emri,
yerel ana/F okuyucusu ve Londra'da emir yollarini kapatan sonlu veri testi.
Yeni strateji, LIVE baslatma veya butce degisikligi yapilmadi.

Okuyucudaki somut duzeltmeler:

- Ayni saniyedeki tam defter goruntuleri artik atilmiyor. Onceki ham-metin
  filtresi, icinde baska token/delta bulunan karma mesaji da atabiliyordu.
- Ilk snapshot gelmeden delta tek basina gecerli defter olusturmuyor.
  Kopustan sonra bu hazirlik durumu sifirlaniyor.
- Eski kaynak zamanli mesaj yeni defteri geriye goturmuyor; beklemis bir
  mesaja alinma ani verilerek yapay tazelik uretilmiyor. Kaynakta zaman
  yoksa mevcut uyumluluk yolu alinma zamanini kullanir; bu durumda kaynak
  yasi dogrulanmis degildir. Bir saniyeyi asan gelecek kaynak saati reddedilir.
- DURDUR sonrasi okuyucu yeniden baglanmiyor. Belgelenen `type=market`
  aboneligi ve 10 saniyelik uygulama `PING` mesaji kullaniliyor.
  [Resmi protokol](https://docs.polymarket.com/market-data/realtime-data).

**1013 kopmalarinin tum kok nedeni kanitlanmadi.** Ayni tokenlerle
eszamanli 50 saniyelik Londra kontrolunde eski/yeni abonelik ayni
8.107 price_change, 16 book ve 7 trade olayi aldi; ikisi de kopmadi.
Dolayisiyla abonelik bicimini tek neden olarak gostermek yanlis olur.
Duzenlenmis gercek okuyucu, Londra'da 120 saniye / 1.200 karar kontrolu,
1.198 iki-kotasyonlu gorunum, sifir WS hatasi ve sifir emirle tamamlandi.
Bu kisa test kalici kesintisizlik kaniti degildir; tampon siniri buyutulmedi.

Ana/F kaynaklarinin eski surumleri yeni davranis testinde basarisiz,
duzeltilmis halleri basarili: burst, karma mesaj, eski snapshot, snapshot
oncesi delta, yeniden baglanti, kalp atisi ve okuyucu kapanisi. F'nin dokuz
karar/WS senaryosu gecti. Her iki oz-test 120/120: eski snapshot-atlama
kontrolunun yalniz kendi kaynak metnini bulup yesil olabilen bir satiri
kaldirildi; yerine gercek okuyucu dongusu test edildi. Yeni dosyalarin
Ruff kontrolu ve syntax gecti. Eski ortak lint bulgulari ayni (ana4/F3);
deponun tumu temiz ilan edilmiyor.

Emir kalibrasyonu:

| Olcu | M4v2 gercek kayit |
|---|---:|
| Kabul / sifir dolumla iptal / tam dolan emir | 12 / 8 / 4 |
| Zincirde ayri dolum / toplam pay | 5 / 20 |
| Iptal cagrisi / basarili iptal | 9 / 8 |
| Kabul edilen POST medyani | 57,40 ms |
| Butun iptal cagrilari medyani | 23,75 ms |
| SDK gonderiminden terminal durumu ogrenmeye medyan | 3.631,44 ms |

Bes zincir dolumunun tamami maker; 0,50 Up emrinin birisi 1,34+3,66
olarak iki transaction'da doldu. Miktarlar, rol, nakit ve uc piyasanin
tam kamu activity'si korundu. Baslangic veri kesitinde 227.264 olay var;
emirlerin gozlem araliklari icin 530 receipt alindi. Kendi dolumunun
bir ek receipt'i kamu activity ile bulundu: toplam 531. Bu ekleme,
ilk zaman-seciminin bir gercek dolumu disarida biraktigini gizlemiyor.

Kritik saat bulgusu: bir dolumun kamu LTP zamani, botun MATCHED cevabini
almasindan **141,54 ms sonra**. Onceden kullanilan 100 ms tolerans sonucu
kurtarmak icin buyutulmedi; ilgili emir null kaldi. SDK kabul/iptal saati
borsanin kesin aktivasyon/iptal saati degildir. Ilk protokoldeki aksi
yonda okunabilen ifade `clock_qualification.json` ile acikca duzeltildi.

Kalan 11 emirde eski M1 statik kuyruk modeli, gozlenen emir omurleriyle
iki tanisal zaman senaryosunda calistirildi. Gercek 15 paya karsilik
10–15 sanal pay hesapliyor; fakat bu toplama guvenilemez:

- **Iki sifir-dolumlu emre 5'er sanal pay yaziyor.**
- **Gercekte 5'er pay dolan iki emri hic dolduramiyor.**
- Bir dolan emrin sonucu zaman araliginin ucuna bagli.

Dolayisiyla 11 degerlendirilebilir emrin dordunde miktar, iki statik
senaryonun da disinda. Kuyrugun onunde varsaymak 25–35 sanal pay veriyor;
bu da cozum degil. Gozlenen SDK omruyle calisan bu hesaplar bagimsiz bir
strateji veya matematiksel dolum alt/ust siniri sayilmaz. Islem bazinda
%91,7, dolan pay bazinda %75 zaman kapsami da tam kalibrasyon icin yetersiz.

**Karar:** 250 ms sabit gecikmeyi 24/57 ms medyanlarla degistirmek tek
basina yeterli degil. Sonraki dar is, bu dort uyusmayan emirde teklifin
gorunen deftere giris/cikis yolu ile kamu trade yayim saatini ayirmak;
ardindan yalniz bu kanitin destekledigi kuyruk modelini sinamak.
Yeni kâr kurali veya yeni LIVE lane hazir oldugu iddia edilmiyor.

Son muhasebe: M4v2 **+0,20 USD**, iki pencere de resmen sonuclandi.
Eski zarar dahil yerel toplam -15,234894; kamu -15,234895. Acik emir0,
bekleyen pencere0, risk0. Rebate/sabit gider haric. Orijinal remote STATE
yeniden yazilmadi; hesap ayri bellekte uzlastirildi.

Kanıt dizini: `data/analysis/btc5m_m5_20260922/`. `prepare.py` tum 12 emri
ve veri kesitini sabitler; eski M1 decoder/queue ve R1 receipt toplayicisi
yeniden kullanilir. `analyze.py` ve `check.py` mevcut cache ile agsiz
yeniden hesaplanir. Negatif kontroller eksik/tekrarli telemetriyi,
state-dolum farkini, yanlis taraf/fiyat akisini ve null'u sifira cevirmeyi
engeller. Donmus M1/M2/M4/M4v2 kaynaklari degistirilmedi.

```bash
python3 "/home/taygun/Masaüstü/polymarket-bosona/data/analysis/btc5m_m5_20260922/analyze.py"
python3 "/home/taygun/Masaüstü/polymarket-bosona/data/analysis/btc5m_m5_20260922/check.py"
"/home/taygun/Masaüstü/KararAtlas/base1/bin/python3" "/home/taygun/Masaüstü/polymarket-bosona/bot/test_ws_reader.py"
```

Uygulama notu: bir yerel kontrol yanlis `--self-test` argumaniyla kuru
donguye girdi; 61 saniye sonra normal STOP ile kapatildi. Gercek emir veya
kimlik kurulumu yoktu; kuru log/state bu kontrolu icerir. Dogru `--test`
ardindan calistirildi. Bu olay Londra LIVE/kalibrasyon orneklemine katilmadi.
