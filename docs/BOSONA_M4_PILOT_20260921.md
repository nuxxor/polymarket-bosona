# M4 — Londra'da parkli emir olcum pilotu

Durum: 21 Eylul 2026 21:04 UTC / 22 Eylul 00:04 TR kontrolunde hazir ve parkta.
Bu yeni G stratejisi degildir. Mevcut F politikasi degismedi; M3 saat kayitlari
ve tam pozisyon sayfalama guvenlik duzeltmesiyle izole pakete kondu.
Amac emir kabul/iptal cevaplari, ogrenilen dolumlar ve dolmayan emirlerin
omru icin gercek veri toplamaya hazirliktir. F'nin veya yeni Bosona
politikasinin karli oldugu kanitlanmadi. F ornegi tum maker davranislarini
kalibre etmez; 30 dakikada emir/dolum olmayabilir. Veri yoksa basari yoktur.

## Yapilanlar ve gercek kontroller
- Eski Londra F kaynak/state/butce aynen korundu. Yeni yol:
  `/home/ubuntu/polymarket-bosona-m4`. STOP_F var; yeni STATE_f,
  BUDGET_F, RUN_M4 ve LIVE LOG_f yok. Ilgili LIVE yazici yok.
- Salt-okunur SDK ile acik emir 0. Uc bekleyen eski pencere, kimlikli
  arsiv dolumlari + resmi sonuc ile bellek kopyasinda uzlasti:
  1789941000 +0.30; 1789941300 -4.00; 1789941600 0.00 USD.
  Onceki yerel -8.936421 -> duzeltilmis -12.636421 USD.
  Kamu nakit/pay mutabakati gecti, dis risk 0. Eski dosya yazilmadi.
- Ilk500 pozisyonda kesilme bulundu ve ortak okuyucuda giderildi.
  Dust/arsiv aktifleri dahil offset sayfalama; eksik/bozuk/tekrarli
  yanit risk=0 sayilmaz. Periyodik hesap hatasi normal durus yoluna girer.
  API limit/offset kaynagi: https://docs.polymarket.com/api-reference/core/get-current-positions-for-a-user
- M4 salt-okunur onkontrolu gecti; Chainlink/TWAP60 gozlem yasi 2071ms,
  alinma yaslari 965/904ms. Bu anlik kontrol, gelecekte tazelik garantisi degil.
- Gercek kamu WS kuru dongusu: 1 pencere, 588 kalite karari; veri_eksik222,
  maker_degil181, favori_degil183, marj_yok2. Gercek emir/dolum0, WS hata0.
  Veri eksikligi basarili bekleme sayilmadi. F filtresi gevsetilmedi.
- Son kaynakla Londra sahte SDK:37cagri/79olay/3dolum gozlemi; ag kapali.
  Ariza uyarisi testin bilerek yazilamaz dosya senaryosundan gelir.
- M4 tek-kullanim, hash, salt-okunur varsayilan, butce/sure ve bozuk
  pozisyon sayfalama kontrolleri gecti. Iki selftest121/121; F D/arsiv/E/F,
  muhasebe ve butce regresyonlari gecti. Baslatma betigi sahte SSH basari/
  hata ve bash syntax kontrolunden gecti. Yeni dosyalar Ruff temiz.
  F ortak kaynakta once/sonra ayni 3 eski F401/F811/F841 bulgusu var;
  ana kaynaktaki eski muhasebe-test uyumsuzlugu M3 raporunda kayitli.
  Tum depo testleri temiz iddiasi yok; dokunulan mantikta yeni lint yok.

## Operator ve sonraki adim
Operator icin hazir komut:
```bash
bash "/home/taygun/Masaüstü/polymarket-bosona/londra_m4_baslat.sh"
```
Bu komut GERCEK emir surecini baslatir. Asistan calistirmadi.
Once onkontrol yeniden yapilir; herhangi bir uyumsuzlukta baslamaz.
30dk / 5pay / $10 ek risk butcesi operator adiminda bir kez olusur;
eski toplam silinmez. Tekrar komut sureyi veya butceyi sifirlamaz.
$10 bir risk kesici ayaridir, kesin gerceklesmis kayip garantisi degildir.
Baslatma-istendi mesaji LIVE teyidi degildir; console.log ve LIVE basladi
ayrica okunmalidir. Yeni kanit gelince emir/dolum/saat mutabakati yapilir.
Sonra maker simulatorde yanlis dolumlari azaltip tek yeni politika sinanir;
sirf bu olcumun bitmesi yeni strateji veya kar kaniti olusturmaz.

Kanit: data/analysis/btc5m_m4_pilot_20260921/{deployment_check.json,
preflight.json,preflight_emir_iz.jsonl,public_smoke.jsonl,tests.json,
lint_baseline.json,m4_release_final.tar.gz}. Paket kaynak hash'i:
0b632c67fd49cc4087f7bb339495651e7f53001e9755b87d6aabf4bc202294c1.

## Operator baslatmasi teyidi

22 Eylul 00:09:08 TR LIVE basladi; PID160500, kaynak0b632c67fd49.
00:10:25 TR kontrolunde ilk yeni pencerede42karar, yeni emir/dolum0.
Telemetri LIVE ve errors0. Yeni butce10USD, onceki toplam korunuyor;
planli kesim00:39:05 TR. Operator baslatti, asistan salt-okunur teyit etti.
Kanit:operator_live_verified.json. Pilotun sonucu henuz belli degil.
