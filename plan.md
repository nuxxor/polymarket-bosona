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
