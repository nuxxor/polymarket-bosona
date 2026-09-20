# BTC5m muhasebe mutabakati — 2026-09-20

Operator: once muhasebeyi eksiksiz esitle, sonra C deneyini degerlendir.
Bu tur C'nin fiyat/sure kurallari, 5 pay klibi ve -100 zarar siniri degismez.
Gercek emir gonderilmez; canli hesap/state/log dosyalari degistirilmez.

## 1. Muhasebe kaynaklarini uzlastir
- [x] Depodaki JSONL + gzip/backfill kasetlerini tekillestirerek oku.
- [x] Atanan tum pencereleri, sifir dolum / eksik veri / sonucu bekleyen
      ayrimini koruyarak raporla; yerel log, kamu kaseti ve salt-okunur API
      karsilastirmasini pencere ve surum bazinda ver.
- [x] Eski logu yeniden yazma. Farklari miktar, maliyet ve PnL olarak sakla.
- [x] Rebate/masraf dahil olmayan islem PnL'sini net gelir diye adlandirma.

## 2. Kok nedenleri duzelt
- [x] Mutabakatta tekrarli islem cift sayilmasin; eksilen veri veya yarim
      sayfalama basarili sayilmasin. Yeni bir eksik cevap eski sonucu silmesin.
- [x] Kimligi olsun olmasin belirsiz/acik emir varken pencere cozulmesin.
- [x] Sonradan dogrulanan dolum, yerel defter ve toplamda yalniz bir kez
      duzeltme uretsin; restart eski dolumu atlamasin.
- [x] Pencere logunda emir kimligi, tam miktar/maliyet ve duzeltme kaynagi olsun.

## 3. Dogrulama
- [x] Izole oz-test + sahte borsa ile eksik/gec/tekrarli dolum regresyonlari.
- [x] Degisen Python dosyalarinda hedefli lint ve syntax kontrolu.
- [x] Gercek kayitlar uzerinde rapor; mevcut kamu API'sinden salt-okunur kontrol.
- [x] Emir gondermeyen kuru C dongusu ve kaynak hash'i dogrulamasi.

Tamamlanma: her incelenen pencere ya kaynaklari uyumlu olarak ya da somut
fark/eksik kaynakla etiketlenir; sayaclari zorla esitlemek basari degildir.
Ekonomik avantaj ve canli emirlerin uctan uca dogrulanmasi ayri asamadir.

## Dogrulanan cikti ve acik kalan sinir
96 pencere / 304 kamu islemi / 96 resmi sonuc: toplam -15,194433 USD,
C 15 pencere -2,561051 USD (ucret/iade haric). 6 yerel fark ve 3 eski yerel
sonuc eksigi raporda ayri gorunur; orijinal kanitlar degistirilmedi.
121/121 oz-test, muhasebe regresyonlari, lint/syntax, skor karti duzeltme
kontrolu ve gercek kayit raporu gecti. Son kaynakla kuru C: 8 niyet / 8
iptal, sifir WS hatasi, gercek emir yok. Kanit: docs/MUHASEBE_20260920.md.

Depo state'i 71, son log 96 pencere: guncel sunucu state'i alinmadan bu
kopya canliya uygun sayilamaz. Canli dagitim/baslatma yapilmadi. Eski emir
kimlikleri eksikken tarihsel farklar zorla kapatilmaz. STOP-POST omur dongusu
ve strateji deneyleri bu muhasebe asamasinin tamamlandigi iddiasina dahil degil.

## Yeni kapsam: D lane
Operator deney 1'i ayri D kolunda, $10 kesiciyle istedi; canli baslatma
komutunu kendisi calistiracak. Izole worktree:
`/home/taygun/Masaüstü/polymarket-bosona-d` (`lane-d` dali).
Kabul olcutleri ve ilerleme o worktree'in `plan.md` dosyasinda. Ana `ab.py`
otomatik senkronla degistigi icin burada ezilmez; onceki muhasebe yamasi
D'de sabitlenen kaynaga alinir. Gercek emir bu calismada gonderilmez.

D hazirlik/test asamasi tamamlandi; 121/121 + D/muhasebe regresyonlari gecti.
Son kuru D: 56 niyet / 56 iptal; bir WS kopusu sonrasi toparlandi, gercek
emir yok. Deney 4'un salt-okunur fiyat kaydedicisi D worktree'inde calisiyor.
Operator komutlari: ../polymarket-bosona-d/docs/D_LANE.md. Canli baslatilmadi.

Sonraki operator pilotu: D yerelde 15:06–15:26 UTC calisti; operator durdurdu.
Guncel D ve son muhasebe /home/ubuntu/polymarket-bosona-d yoluyla Londra
eu-west-2a'ya tasindi. Londra 240dk baslatma komutu D worktree'indeki
londra_d_baslat.sh; canli baslatmayi operator yapacak. $10 butce ve teyitsiz
emir kaydi korundu; yeni acilis kapisi eski emirler dogrulanmadan ilerlemez.

## Yeni kapsam: E lane, Londra'da park edilmis hazirlik
Operator D calisirken deney 2'yi ayri E olarak hazirlayip Londra'ya kurmayi,
baslatmadan bekletmeyi istedi. Izole worktree:
`/home/taygun/Masaüstü/polymarket-bosona-e` (`lane-e` dali).
E, D'nin tamamlayici fiyat bandina ek olarak gecerli tamamlayici emri
giris filtresi degistigi icin iptal etmez. Kabul olcutleri ve dogrulama
E worktree'inin `plan.md` dosyasinda. D'nin kaynagi ve canli sureci korunur;
E `STOP_E` ile park edilir, bu gorev E'yi canli baslatmaz.

## Salt okunur D/E ve Bosona karsilastirmasi — 20 Eylul 18:04 UTC
Operator kisa yanit istedi: E/D farki, Up/Down pay oraninin gerekcesi ve
D baslangicindan bu yana Bosona'nin ayni donemdeki gorunur performansi.
Kabul: koddan gercek pay/tamamlama kurali; yerel pilot ve Londra baslangici
ayri; ortak piyasalar, kapanmis PnL ve acik pozisyon ayrimi; kamudan
iptal/kuyruk/gorunmeyen emir cikarilamaz. Emir/kaynak/runtime degistirilmez.

Sonuc: D emir boyu tum kapanmis ornekte 5 pay; miktar farki yon tahmininden
uretilmiyor. E, D'nin gecerli tamamlayici emrini korur; canli ustunluk
olculmedi. 15:10–17:55 UTC BTC5m kohortu: 220 kamu trade/activity kimligi
eslesti, 32 Gamma sonucu ve MERGE/REDEEM odemeleri pay bazinda eslesti.
Bosona 32 pencerede brüt +153.238745, API USDC maliyetiyle +107.607915;
25 ortak pencerede D +1.31920351, Bosona +620.574078 (brüt +652.430298).
Yalniz Londra 21 ortak pencerede D +2.82000343, Bosona +679.921506.
Iadeler/sabit giderler ve sonraki acik pencereler haric; tum hesap sonucu
degil. Bosona 10420.87, D 412.68 pay; 0.60 ustu pay orani %73.53 / %16.96.
Gorunmeyen iptal/kuyruk davranisi tahmin edilmedi. Emir/kod degistirilmedi.
Kanit: data/referans/d_bosona_20260920_1808.json. Sonuc/kimlik/odeme/miktar
assert kontrolleri gecti; dosya JSON olarak tekrar okundu.

## Siradaki arastirma: Bosona'nin dolumlarindan karar kurali — 21 Eylul
Operator, gerceklesen islemler ve kazanc uzerinden bir sonraki adimi istedi.
Bu tur salt-okunur tespit ve deney tasarimi; LIVE kaynak/butce/start degismez.
- [x] F sessizligini runtime ile ayir: 22:49 UTC kontrolde LIVE yazici yok;
      22:00:35 UTC hata cikisi, hemen oncesinde uc SSL dogrulama hatasi.
      Bu kayit SSL'nin fatal cagrinin kesin kok nedeni oldugunu kanitlamaz.
- [x] 21:00–22:30 UTC Bosona BTC5m dolumlarini tam piyasa gecmisi ve resmi
      sonucla karsilastir: 14 piyasa / 127 kayit / 5097.890825 pay.
      Onceki 128 sayisina 22:30:44 islemi dahildi. Dolum kaydi emir sayisi degil.
      46 kayit / paylarin %49.13'u t>200; F t=200'de islemi kesiyor.
      Gec dolumlar hem eslesmeyi artiriyor hem yeni yon riski aciyor;
      zaman sinirini kaldirmak tek basina kar kaniti degil.
- [x] JSON yeniden okuma, miktar/sinif/toplam sonuc assert kontrolleri.
      Kanit: data/referans/bosona_f_siradaki_adim_20260921.json.

Onerilen sonraki deneyin kabul olcutleri (bu tur uygulanmadi):
- BTC5m'de ilk alim, ayni yone ekleme, karsi tarafi tamamlama ve yeniden
  risk acma olaylarini kazanan/kaybeden tum pencerelerde esle; FIFO maliyet
  dagilimi muhasebe secimidir, gizli karar kuralinin kaniti degildir.
- Ilk odak son 100 saniye: dolum ONCESINDE mevcut fiyat/ref, kalan sure,
  envanter ve spread ile gorunur ayrimi ara. Gec gelen kamu kaydi ileri
  karar girdisi olmaz; eksik/gecikmeli defter ve yon belirsizligi etiketlenir.
- Bulunan az sayida kurali sonraki ayrilmis gunlerde/golgede sabitle ve
  olc. Yalniz kazananlari secme; benzer kosullardaki kayiplari da kapsa.
  Fiyat degdi diye maker dolumu varsayma; dolum belirsizligini ayri raporla.
- Basari: yeni donemde islem benzerligiyle birlikte masraf/iade dahil net
  sonuc, acik risk ve dusus. Daha cok islem tek basina basari sayilmaz.

## Aktif uygulama — 21 Eylul, Bosona gec dolum arastirmasi
Operator yukaridaki sirayi onayladi. Kabul: tekrar calistirilabilir dolum
muhasebesi, zaman-sizintisiz fiyat birlestirmesi, ayri gun raporu ve emir
vermeyen ileri golge kaydi. F/LIVE kodu ve butcesi degistirilmez.
On kayit (yeni sonuclari incelemeden):
- 13–17 Eylul kesif, 18–20 Eylul kronolojik kontrol; onceki arastirmalarda
  gorulen gunler oldugu icin bu kontrol tamamen kor test sayilmaz.
- BTC5m, kapanistan >=20 dakika gecmis tum bulunan pencereler; eksik
  kaynak sifir islem sayilmaz. Ilk alim/ekleme/tamamlama/yeniden acilis;
  FIFO muhasebesi ve toplam odeme-maliyet bagimsiz uzlasir. MERGE gelirini
  ikinci kez kar sayma. Kaybedenler ve en iyi uc pencere harici sonuc dahil.
- Uc sabit kural: piyasa favorisi tabani; spot ve TWAP referansla favori
  yonunde uyumlu; ayni uyum + TWAP uzakligi kalan sure oynakligindan >=1
  standart sapma. Esik taramasi yok. Birincil karar t=240, t=210/270 ikincil.
- Dolum-oncesi betimleyici girdiler kamu ts−5sn; −10sn duyarliligi.
  Politika deneyi her uygun pencerede sabit zamanda, aktor dolumu gerektirmez.
  Taze veri <=3sn; baslangic referansi karar oncesi alinmis exact TWAP.
- Sanal 5 pay icin alinabilir ask derinligi ve ucret hesaplanir; maker
  dolumu uydurulmaz. Bu taker karsilastirmasidir, Bosona maker kopyasi degil.
- Sonraki 24 saatlik golge: ayni kurallar sabit, gercek emir/anahtar yok.
  Pozitif iddia icin >=3 ayri gun, >=100 pencere, gun/pencere kumeli alt
  guven siniri >0 ve en iyi uc pencere harici pozitif sonuc gerekir.
  Az veri UNDERPOWERED; negatif sim tek basina tum stratejiyi curutmez.
- [ ] API/veri kapsami ve muhasebe kontrolu.
- [ ] Dolum davranisi, gec dolumlar ve sabit kurallarin ayri-gun sonucu.
- [ ] Test/lint/gercek veri dogrulamasi ve ileri golge runtime kaniti.

Arastirma notu (ilk betimleyici sonuclardan sonra, kesif olarak etiketli):
FIFO eslesme katkisi pozitif, acik kalan kisim negatif. Ek mekanizma
kontrolu: t<=200 gozlenen alislar sabit tutulup, son 100 saniyede yalniz
mevcut acigi kapatan ve FIFO nakit maliyeti toplami <=0.98 olan gozlenen
dolum miktari alinmis olsaydi, pencere bazinda sonuc/risk nasil degisirdi?
Bu aktorun dolumlarina kosullu bir karsilastirmadir; bizim dolum garantimiz
veya gercek bir politika backtest'i olarak sunulmaz. Golgedeki uc sabit
kurali degistirmez; sonuc sonrasi parametre aramasi yapilmaz.
