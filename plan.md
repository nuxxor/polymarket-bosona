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
- [x] API/veri kapsami ve muhasebe kontrolu.
- [x] Dolum davranisi, gec dolumlar ve sabit kurallarin ayri-gun sonucu.
- [x] Test/lint/gercek veri dogrulamasi ve ileri golge runtime kaniti.
- [ ] Ileri 24 saatlik ekonomik sonuc (sure henuz tamamlanmadi).

Arastirma notu (ilk betimleyici sonuclardan sonra, kesif olarak etiketli):
FIFO eslesme katkisi pozitif, acik kalan kisim negatif. Ek mekanizma
kontrolu: t<=200 gozlenen alislar sabit tutulup, son 100 saniyede yalniz
mevcut acigi kapatan ve FIFO nakit maliyeti toplami <=0.98 olan gozlenen
dolum miktari alinmis olsaydi, pencere bazinda sonuc/risk nasil degisirdi?
Bu aktorun dolumlarina kosullu bir karsilastirmadir; bizim dolum garantimiz
veya gercek bir politika backtest'i olarak sunulmaz. Golgedeki uc sabit
kurali degistirmez; sonuc sonrasi parametre aramasi yapilmaz.

Ilk tur sonucu: 1.842 pencere / 19.761 BUY, API nakit maliyetiyle +8.319,438464
USD islem sonucu (rebate/sabit gider haric). FIFO cift +14.799,083092 / acik
kisim -6.479,644628; maliyet dagitimi strateji becerisi iddiasi degil.
Son 100 saniye +4.603,639828; en buyuk alt katki ayni yone ekleme +2.784,242434.
Sadece gec tamamlama, gozlenen dolumlara kosullu +244,947645 fark; 88 iyi /
276 kotu pencere, en iyi uc haric -814,937663. Ustunluk kaniti yok.

Sabit t=240 kurallari, 19–20 Eylulun 131 fiyat/defter-uygun penceresinde
5 sanal pay ve ask+ucret ile: favori -21,66382; uyum -30,47725;
uyum+uzaklik -19,19185. Tum birincil araliklar sifiri kapsiyor.
Sekiz gunluk defter testi degil; fiyat girdileri 5sn geriden 5.710/19.761
dolumda mevcut. Sonuc/dagilim/model etiketleri birbirine karistirilmadi.

Londra emir vermeyen golge: bosona-gec-shadow, PID 90794, 20 Eylul 23:20
UTC–21 Eylul 23:20 UTC; sonucu bekleme icin +25dk. Uc kural sabit;
ilk 210/240 kararlarinin nedensel zamanlari gercek kayitta dogrulandi,
270 bos defter boslugu olarak kaydedildi. LIVE F/butce degismedi.
Calisan golge sha=1f33a277c694b781ca3b5f30f3f5369b39ae1497cdae4cd76ceeb26d70652086;
yerel analiz/rapor kodu daha sonra ilerledi, golge kurallari ayni kaldi.
FIFO/fazla dolum, ileriyi gormeme, coklu-token defter, bayatlik, ucret,
metin fiyat, risk testleri; Ruff/compile; 5 bagimsiz API piyasa kontrolu;
gercek veri toplamlari ve runtime/source hash kaniti gecti.
Rapor: docs/BOSONA_GEC_ARASTIRMA_20260921.md.
Kanıt ve dondurulmus fiyat verisi: data/analysis/bosona_gec_20260921/.

## Derinlestirme — gec ek alimi kazandiran kosullar
Operator tum erisilebilir metriklerle arastirmayi derinlestirmeyi istedi.
Kapsam salt-okunur arastirma; calisan golge kurallari ve LIVE degismez.
- [x] Mevcut dolum/veri araclarini kullan; yeni girdiler ve eksik kapsami acikla.
- [x] Gec eklemelerde fiyat/sure, boy, onceki envanter/maliyet, ilk giris,
      momentum/donus, oynaklik, TWAP kapanis mekanigi, RSI/hacim ve defter
      baglamini incele. Dolum sonucu ile karar-oncesi girdiyi ayir.
- [x] Pozitif gorunen mekanizmayi kayiplar, es-boy, en iyi uc pencere harici,
      gunler ve zaman gecikmesiyle sına. Coklu arama kesiftir; kor test denmez.
- [x] Bosona dolumu gerektirmeyen mevcut defterli pencerelerde az sayida
      gerekceli kuralin alinabilir fiyat + ucret sonucunu kontrol et.
- [x] Tekrar calistirilabilir kod/veri, oz-test/lint ve gercek sonuc raporu;
      bulunan ipucu ile cozulmeyen karar kurali acikca ayri sunulsun.

Derinlestirme sonucu: 124 saat / 18,65 GB eski tape yeniden okundu; 643.059
nedensel defter kesiti, 339 yeni DB penceresi, eski RTDS fiyatlari ve kapali
Binance mumlariyla 60 metrik tarandi. Bozuk saat/uyusmayan defter dislandi.
Bosona'dan bagimsiz evren 2.286 sozlesme; 2.490 uygun zaman noktasi, 10 kural
x 5 zaman = 50 kesif karsilastirmasi. Farkli zamanlar bagimsiz pencere sayilmaz.

Son 20 saniye ayni yone ekleme: 271 kayit/66 pencere +1.888,805825 USD;
en iyi uc haric +975,726104. Borsa saati eslesen 157 kayit/40 pencerede
+1.190,608631; en iyi uc haric +460,420004. Es-pencere 5 pay normu +27,255466,
8 gunun 7'si pozitif; gercek miktar agirliginda 8/8 pozitif. Ucuz alimin
kazandigi mekanizma salt yuksek isabet degil, odenen fiyata gore yeterli odeme.

Ileri arastirma adayi: t=280, daha ucuz taraf ask<0.50, o yone gore basit
RSI14<40 ve son 10sn momentum>0. 140 uygun/23 secilen sanal alis +19,93476,
en iyi uc haric +7,47245; sonraki donem +11,21198, 10,73325'i tek gunde.
Tarama sonrasi secildi; 23 islem ve duzeltilmemis pozitif bootstrap araliklari
kalici avantaj kaniti degil. Tam momentumu uzatmak fiyat tahminini kotulestirdi;
ogrenilmis katsayi/hata dagilimi ve alim baskisi kurallari da denendi, saklanmadi.

Yeni kural 21 Eylul 00:30–24 Eylul 00:30 UTC icin kaynak ve parametrelerle
data/analysis/bosona_derin_20260921/prospective_protocol.json'a sabitlendi.
Mevcut asil defter/Chainlink kaydedicileri guncel; repo aynasi gecikmeli.
Bu bir ileri veri protokoludur, yeni karar yazicisi veya LIVE bot baslatilmadi.
- [ ] Yeni adayda ileri sonuc: >=3 gun, >=100 uygun pencere VE >=100 secilen
      islem; iki kumeli alt sinir>0, en iyi uc haric pozitif. Ilk 72 saat bu
      sayiya yetmezse yetersiz; parametreler sonuc gorulerek degistirilmez.

Oz-test/Ruff/compile, 3 yeni bagimsiz API piyasa eslemesi, 18 ham-defter
kontrolu, zaman/miktar/ucret kontrolleri gecti. Bellek azaltimi onceki ozellik
ve sekiz kuralin butun sonuclarini byte hash'iyle aynen korudu. Kaynak:
b825c37449e1069c8bcedfa4037d6dd9ee620bdd667da1e4d6b36905fb1a0690.
Rapor: docs/BOSONA_DERIN_20260921.md. LIVE strateji/butce degismedi.

## Ek Londra rebound shadow — 21 Eylul operator talebi
Mevcut uc kuralli golge aynen korunur; rebound icin ayri emir vermeyen
karar yazicisi, dizin, kaynak hash'i ve sure siniri kullanilir. Onceki
00:30 protokolu geriye donuk canli baslangic sayilmaz; gercek ilk pencere
kaydedilir. Birincil t=280; protokoldeki t=240/270 ikincil ve ayni anda
favori karsilastirmasi ayri sanal stratejilerdir. Kurallar degistirilmez.
- [x] Var olan fiyat/RSI/ucret araclarini kullan; veri boslugu ve sifir
      sinyali ayir; >=250ms sonraki alinabilir defter derinligini kaydet.
- [x] Tek yazici, kaynak sabitleme, yeniden baslatmada mukerrer karar
      engeli, bitis/sonuc bekleme ve salt-okunur girisler dogrulansin.
- [x] Oz-test, hedefli lint/compile ve Londra'da gercek karar/kalp atisi;
      mevcut golgenin kaynak ve surecinin korunmasi kanitla dogrulansin.

Londra bosona-rebound-shadow 21 Eylul 00:46:37 UTC'de baslatildi.
Atama araligi 21 Eylul 00:50–24 Eylul 00:50 UTC (72 saat); +25dk sonuc
bekleme. Onceki protokolun 00:30 baslangici bu yaziciya geriye yazilmadi.
Ilk gercek veri smoke kontrolu sinyal uretti (RSI49.49, rebound=None,
defter HTTP25ms); zaman disi kontrol oldugu icin deney sonucuna katilmadi.
Ilk planli karar 00:54:00, birincil 00:54:40 UTC; baslangic kontrolunde
henuz planli karar/kar-zarar yoktu. Kalp atislari iki ayri surecte guncel.
Mevcut golge kaynak hash'i 1f33a277... ayni; LIVE emir/butce degismedi.
Yeni yazici sha=19b115c07016d5a950c0dead78c84c46287b68002ac5805a7d850734763fd5e5.
Yerel ve Londra oz-testleri, hedefli Ruff/compile gecti. Sonlu dongu testinde
240/270/280 karar, ucretli sonuc, sifir sinyali ve tekrar baslatmada sifir
mukerrer kayit dogrulandi. Kod/manifest/runtime kaniti: rebound_release/.

## Gecikme karsilastirmasi ve coklu piyasa Bosona arastirmasi
Operator 250ms ile ek beklemesiz, olculen fiyat-alim gecikmesini karsilastirmayi;
BTC/ETH/SOL 5dk/15dk/saatlik islemlerde ayni kurallarin kullanilip
kullanilmadigini arastirmayi istedi. Mevcut iki dondurulmus golge korunur.
- [x] Ayri salt-okunur gozlemci: yeni rebound adayinin ayni kararlari icin nedensel yeni defter
      fiyatini ve olculen gecikmeyi kaydet; 250ms orijinal kayitla eslestir.
      HTTP fiyati gercek emir kabul/dolum gecikmesi diye adlandirilmasin.
- [x] BTC/ETH/SOL sure gruplarinin tam gorunur aktivitesini, sonuc ve
      pencere kurallarini kontrol et; ilk/ek/tamamlama/zaman/fiyat/boy ve
      kazanc dagilimini ayni donem/gunlerle karsilastir. Eksik veri ayri.
- [x] Mevcut shadow kosullariyla uyum verisi varsa olc; sadece dolum
      fiyatindan favori/RSI/iptal stratejisi kesinligi cikarilmasin.
- [x] Test/lint/gercek Londra kaydi ve tekrar uretilebilir rapor; sabit
      altyapi mi, farkli karar kurallari mi oldugunun kanit sinirlarini ver.

Sonuc: 13 Eylul00:00–21 Eylul00:30UTC, 4.062 piyasa /30.111 BUY /dokuz
grup; alis oncesi tarihce icin10Eylul'e donuldu,63.821aktivite. In-scope
token/yon/condition/sure/sonuc dislamasi0. Iki taraf alinmis pencere orani
BTC5m64,6%,ETH5m17,4%,SOL5m8,2%; ilk fiyat medyanlari44/49/75sent.
Gun/fiyat/goreli-zaman eslesmesinde de ayrim surdu: BTC/ETH58,0/18,3%,
BTC/SOL56,4/10,1%. Likidite/gerceklesmeyen emir/ozel hedef eslesmedi;
ayri bot veya kesin degismis kod kaniti degil. ETHsaatlik iki taraf74%.
5/15dkChainlinkTWAP60, saatlikBinance1H;6saatlik sonuc Binance'da eslesti.
BTC5mson20ekleme271/+1888,81 aynen yeniden uretildi; ETH66/+3,03,
SOL13/+24,66; farkli boylar esit-butce karsilastirmasi sayilmadi.
Her varlik1dkRSI/return, kamu ts−5/−10s ile kontrol; gercek emir saati ve
10sChainlink/karar defteri bu vekilden cozulmus sayilmadi. Gece kaymasi
20Eylul'de belirgin, her tam gecede ayni sabit saat davranisi yok.

Londra bosona-latency00:57:08UTC'de basladi; yalniz rebound gunlugunu
okuyor, eski uc kuralli deney korunuyor. Ilk dogal t240karsilastirmasi
01:04UTC: bildirim1ms, erkenquote48ms, eski280ms. Reboundsecim0;
favori5sanalpay erkenmaliyet0,04661USDaz. Tekgozlem kar kaniti degil.
Iki dondurulmus golge hash/PID korunarak ucuncu surec yalniz olcum yapti.
18eniyi/enkotu APItrade kimligi/miktar/brutsonuc ve6Binance sonucu,
butun toplamlar/zamanlar,oz-test,Ruff/compile gecti.
Rapor:docs/BOSONA_COKLU_20260921.md; kanit:data/analysis/bosona_coklu_20260921/.

## Jev ve ileri shadow ara performans — 21 Eylul gunduz
Operator gecen surede Jev ve iki shadow'un gercek kayitli sonuclarini istedi.
Salt-okunur anlik kesit: strateji, sure, butce veya surec degistirilmez.
- [x] Londra kaynak/hash/surec ve kayit kapsamlarini dondur; fiili calisma
      suresi, planli bitis, eksik veri ve sonucu bekleyenleri ayir.
- [x] Jev surum/birincil nihai karar ve iki golgenin birincil/ikincil
      zamanlarini ayri hesapla; ucretli sanal PnL, isabet, adet, maliyet ve
      gecikme eslesmesini resmi sonucla dogrula. Olmayan sureyi sifir sayma.
- [x] Bagimsiz toplam/zaman/kaynak kontrolleri, tekrar calistirilabilir
      rapor ve kullaniciya kisa karsilastirma; ekonomik kabul esikleri korunur.

Kesim21Eylul10:15UTC: eski shadow10s55dk/131atama, yeni9s25dk/113atama.
Jev gece boyunca calismadi; iki saatlik pilot20Eylul23:47UTC'de normal
kapandi. V2 17atama/11nihaiislem/10kazanan, ucretli sanal+12,53070USD;
ayni11pencerede favori+4,68269. V1ayri:1islem/-1,26384.
Ilk golge ana t240:40gecerli, favori+6,63001, uyum+4,62804,
siki-3,35196. 91veriboslugu; sifir islem sayilmadi.
Yeni golge ikincil t240:32gecerli,9rebound/1kazanan/-3,31884;
ayni32favori+9,11713. ANA t280veikincil t270gecerlikarar0:
t280103defterboslugu+10eski mum. Kendi hazirlik dongumuz t245'te30sn
cache esigini gecemiyor; t260'ta hazirlik araligi bitmis oluyor.
Gercek donmus kod blogunda ve25gec baglam hatasinda kok neden dogrulandi.
Onceki smoke/zaman testleri bu mum yenileme hatasini yakalamamis;
ana ekonomik deney uygulanmis sayilamaz. Bu salt-okunur raporda fix/deploy
yapilmadi; duzeltme yeni kaynak/surumle ayri ileri donem gerektirir.
31eslesmede fiyat medyani31/278ms;9rebound isleminde hizli fark+0,05453.
98resmi piyasa sonucu,18bagimsiz Decimal toplam,17dosyahash ve3Jevhash,
oz-test/Ruff/compile/gercek analiz ve ayni hash'li tekrar gecti.
Surec/hash/bitisler korundu; ekonomik kabul esikleri hala acik.
Rapor:docs/SHADOW_SONUC_20260921.md; kanit:data/analysis/shadow_status_20260921_1016/.

## Iki shadow ile ayni donem Bosona karsilastirmasi — 21 Eylul
Operator Jev haric iki golgenin ilerleyisini ve gercek baslangiclarindan
beri Bosona'nin performans/davranis benzerligini istedi. Salt-okunur arastirma;
calisan strateji/kaynak/butce/sure degismez. Bilinen t270/280 olcum hatasi
gecerli test veya Bosona'dan sapma diye sayilmaz.
- [x] Guncel Londra kayitlarini ve ayni kesime kadar resmi sonuclari dondur;
      eski/yeni shadow sureleri, gecerli/eksik/bekleyen sonuc ayri olsun.
- [x] Bosona'nin gorunur aktivitesini tam sayfalama/tekillik ile al; BTC5m
      ortak piyasa kohortu ve diger piyasalar ayri. Onceki alimlar, MERGE,
      acik miktar ve ucret/iade belirsizligi dogru muhasebelensin.
- [x] Ayni pencerelerde yon, zaman, fiyat, ekleme/tamamlama, boy ve PnL
      karsilastirmasi; sinyal yok ile veri yok ayri. Gorunmeyen emirlerden
      sonuc uydurma; ham dolar farkini strateji ustunlugu sayma.
- [x] Tekrar calistirilabilir rapor, hedefli test/lint/gercek API ve toplam
      dogrulamasi; kopyalamaya ne kadar yaklasildigi ve acik kalan fark net.

Kesim21Eylul12:00UTC/15:00TR. Ilkshadow152atama/46gecerli ana t240:
favori+2,43761, uyum-3,44569, siki-7,93189. Yeni134atama/38gecerli
ikincil t240:10islem/1kazanan/-5,95631; ana t280gecerlikarar0.
Bilinen mum yenileme sorunu ve defter eksigi bu tur giderilmedi.
Bosona ayni ilk-baslangic kohortunda322sonuclupiyasa/+2053,442069;
BTC5m89pencere/535dolum/38965,62pay/+984,655319. Yeni-baslangic
BTC5m78pencere/+805,206345. 3sonucu dogrulanmamis saatlik ve devreden
70alis ayri;282,1514USDhesap-geneli iadeler kohorta dagitilmadi.
BTC5m eniyi3haric-92,548175, herpencere5toplampay normu+0,768051.
Yakin zaman +/-15sn yon uyumu favori8/16, rebound2/5; +/-5/30sn de
kontrol edildi. Ayni32pencere favori+0,81094/Bosona5paynormu+2,879092;
rebound7ortakpencere-4,11772/Bosona5paynormu+5,233032.
Bosona ilk-alimmedyan90sn/42sent,44/89iki taraf; shadowt240tek5pay.
Son20ekleme+73,5538yalniz1pencere/10dolum/88-91sent; ucuz-taraf
kuralinin genel taklit olduguna kanit yok. Kamu ts/emir saati ayri tutuldu.
120piyasada bagimsiz/trades kimlik-cokluk-miktar-brutsonuc,322piyasada
MERGE/REDEEMsiniri,8rawhash,15Decimalgolgetoplam,321eskikaydin taze
activityeslesmesi,oz-test/Ruff/compile/gercekanaliz gecti. API429sonrasi
dogrulama tekil1snaralikli yapildi; veri eksigi sifira cevrilmedi.
Rapor:docs/SHADOW_BOSONA_20260921.md; kanit:data/analysis/shadow_bosona_20260921_1200/.
Jev, iki calisan golge ve LIVE kaynak/sureclerine mudahale edilmedi.

## Envanter odagi ve yeni ileri shadow — 21 Eylul
Operator siradaki arastirma odagini uygulamayi ve Londra'da yeni shadow
baslatmayi onayladi. Gercek emir yok; Jev/LIVE ve eski deney kanitlari korunur.
- [x] Mum yenileme hatasini kokten duzelt; gercek hazirlik dongusunu
      t240/270/280 boyunca test et. Duzeltilmis rebound ayri surum/manifest.
- [x] Bosona ilk/ek/tamamlama fiyat-miktar-maliyet ayrimini mevcut tum
      kazanc/kayip verisinde incele; kesin karar kuralindan hipotezi ayir.
- [x] Kendi envanterini izleyen, FIFO acik maliyete gore tamamlama yapan
      az sayida sabit kurali ileri teste kaydet. Yeni risk, ekleme ve
      tamamlama ayri; esit risk limitli kontrol, ucret/derinlik/gecikme,
      eksik veri/karar yok/sonuc bekleyen ayrimi ve yeniden baslatma korunur.
- [x] Test/lint/compile ve Londra kaynak-hash/gercek karar dongusu teyidi;
      raporda fiili baslangic, sure ve henuz bilinmeyen ekonomik sonuc.
Basari yeni donemde ucret sonrasi dolar, acik risk/dusus ve Bosona ile ayni
piyasalardaki davranis benzerligidir; yalniz islem sayisi veya tek kazanan
yeterli degil. Esik aramasi yapilmaz; ileri >=3 gun ve >=100 islem olmadan
kalici avantaj iddiasi yok. Gecmis kesif temiz bir kor test diye sunulmaz.

Sonuc: mum cache yasina degil son yayimlanmis kapali dakikaya gore yenilenir.
Gercek scheduler testi t225.6 cache fazini ve HTTP cevap gecikmesini kapsar;
eski 30sn kuralina donunce test bilerek basarisiz olur. Kaynaklar donduruldu.
Bosona1842eski/89yeniBTC5m: ilk-alimmedyani43/90sn ve44/42sent. Yeni159
tamamlama kaydinin93'u FIFO pozitif. TWAP-olasilik>=3sent eski-ekleme
filtresi eniyi3haric-462,12; guclu yon modeli sayilmadi, stratejiye eklenmedi.
Yeni inventory_v1 mevcut rebound giris kosulunu t30..200'de kullanir;
FIFO<=.98 tamamlama t290'a kadar; kontrol/ekleme kolu, bagimsiz hizli/250ms
portfoyleri. 5payklip/10acikpay/$15alis/$5en-kotu-sonuc SINIRLARI SANALDIR.
Yeni risk her seferinde yeniden filtrelenir; envanter/masraf gunlukten kurulur.
Londra bosona-inventory PID98339 ve bosona-rebound-v2 PID98340, 12:45:32UTC
basladi; atamalar21Eylul12:50–24Eylul12:50UTC, +25dksonuc takibi.
Ilk envanter penceresi27planlikarar:9gecerli giris baglami/0sinyal,
14fiyat-baglami+4deftereksigi, sanalalim0. Reboundv2 t240gercekkarar/quote;
t270/280bosdefter, fakat sonmum239.999 ve taze: eski mum hatasi giderilmis,
butun veri kapsam sorunu cozulmus degil. Henuz ekonomik ustunluk yok.
Yerel/Londra full-loop, acik envanterle restart, eski bug regresyonu, FIFO,
ucret/risk/fiyat kaymasi, kaynakfreeze/lock, Ruff/compile gecti. Bes uretim
kaynagi manifestle birebir. Eski iki golge/Jev PID ve hashleri korundu.
Rapor:docs/BOSONA_ENVANTER_SHADOW_20260921.md;
kanit:data/analysis/bosona_inventory_20260921/. Ileri kar/benzerlik sonucu acik.

## Aktif odak yeniden yalniz BTC5m — 21 Eylul 13:21UTC
Operator Jev ve diger piyasa arastirmasini bu oturumun odagindan cikardi.
BTC5m yeni shadow saglik kontrolu: PID/kalp atisi/kaynak, veri kapsami,
ilk envanter dongusu ve ucretli sanal sonuc teyidi. Salt-okunur; strateji
ve dondurulmus deney kurallari bu durum kontrolunde degistirilmez.

13:21:11UTC kesiti: yeniPID98339/98340 ayni, kaynakmanifestleri ayni,
kalpatislari guncel. Envanter167karar/63gecerligirisbaglami;68eski fiyat
baglami/36deftereksigi. 16:15TRpenceresinde5Up+5Down: ucretlidelay250
maliyet2,62118/payout5/sanaldenge+2,37882; hizli+2,42977. Iki politika
ayni davranmis, ekleme henuz yok. Resmi sonuc kesitte bekliyor. 16:20TR
penceresindeayrica5Up/2,48736USD acik; bu risk toplamsonuca dahil edilmeden
yalnizdenge kazanci toplamkar diye sunulmaz. Reboundv2 18deneme/1t240karar,
14bosdefter/3eski fiyat; ana t280gecerlikarar0. Mumlar71baglamhatasinin
hepsinde guncel;71/71fiyat-tazelik ihlali,57yalnizgecmis orneklerde.
Eski ornek yasmedyani3064ms/max7302ms;3000mskural gevsetilmedi.
FIFO/Decimal/risk/tekillik/gecikme/resmi sonuc-pending ayrimi, Ruff/compile
gecti. Kod/runtime degismedi. Kanit: inventory arastirma dizini/status_1321/.

## BTC5m shadow veri yolu duzeltmesi — 21 Eylul
Operator eski/eksik fiyat ve defter engellerini fixlemeyi istedi. Yeni,
ayri dondurulmus shadow surumu; Jev/LIVE ve eski deney kayitlari korunur.
- [x] Gecmis fiyatlari karar anina kadar alinmis olay zamanlariyla sec;
      gelecekte alinacak veri kullanma, 3000ms guncel tazelik limitini koru.
- [x] Tek tarafli defterde yalniz gercek kotasyonla yon siralamasini belirle;
      gerekli alis derinligi olmayan islemi yapma. Diger tarafin eksigi
      gecerli islemi engellemesin; eksik kontrol islemi sifir PnL sayilmasin.
- [x] Causal zaman/eksik derinlik/regresyon ve gercek scheduler testleri,
      Ruff/compile, eski kayitlarla kapsam replay'i ve Londra yeni kaynak
      hash'i/karar dongusu/ana t280 teyidi. Ekonomik ustunluk iddiasi yok.

Sonuc: r.decide iki yeni shadow icin karar anina kadar gelen fiyatlari
olay-zamani gecmisiyle seciyor. Ortak defter okuyucu gercek None kotasyonlari
koruyor; alinamayan kontrol kolunun maliyet/sonucu null. 167eski karar
replay'inde63->114gecerli;68fiyat hatasinin51'i giderildi,17'si gercek bosluk.
Eski gecerli karar kaybi yok; tazelik3000ms ve risk/strateji esikleri ayni.
Yeni inventory_v2 PID112062 ve rebound_v3 PID112442 Londra'da, ayri
polymarket-bosona-inventory-v2 dizininde donduruldu. Atamalar21Eylul13:50UTC
baslangicli72saat; eski98339/98340 surec/kaynaklari ayni kaldi.
Ilk tam pencerede envanter27/27planlikarar,19gecerli/8gercek fiyat boslugu,
6tek-tarafli-defterde gecerli karar/12sanal dolum(dort bagimsiz kol toplami).
Reboundt240/270/280ucunde gecerli karar ve sanal islem var; favori2dolum,
1eksik-satis null, sifirPnLdegil. Yerel/Londra full-loop/causal/eksik derinlik,
FIFO/risk/ucret/gecikme/restart/freeze, Ruff/compile, kaynak/hash ve gercek
gunluk mutabakati gecti. Kaynak akisi6sn sustugunda karar atlama suruyor;
bu gercek veri kaybi esitigi gevsetilerek gizlenmedi. Net kazanc kaniti yok.
Kanit: data/analysis/btc5m_feed_fix_20260921/{replay.json,runtime_verified.json}.

## BTC5m shadow ara kontrol ve Bosona benzerligi — 21 Eylul 14:20UTC
Operator kendi shadow'larinin duzeldiginin guncel teyidini ve Bosona'ya
benzer hareket edip etmedigini kisa istedi. Salt-okunur runtime/kamu veri
kontrolu; kurallar, butce, sure ve calisan kaynaklar degismez.
- [x] Yeni surumlerin PID/hash/kalpatisi, kapsam, tekillik, ucret ve risk
      dogrulamasi; eski kontrol surumleriyle yeni donem karistirilmaz.
- [x] 13:50–14:20UTC alti ayni BTC5m penceresinde kendi ilk/ek/tamamlama
      islemlerini Bosona'nin taze kamu dolumlariyla karsilastir. Gercek
      dolum coklugu korunur; sifir dolum, veri eksigi ve bekleyen ayri.
- [x] Resmi sonucla sanal PnL ve tekrar calistirilabilir kontrol; gozlenen
      benzerlik ile cozulemeyen karar kurali ayri ve kisa raporlanir.

Sonuc: yeniPID112062/112442vehashlerayni; envanter162/162planlikarar,
144gecerlibaglam/18gercek fiyatboslugu/0schedulerhatasi. Rebound17/18
gecerli, ana t2805/6;10tektaraflideftergecerli,alinamayanfavori10keznull.
6resmisonuc/134BosonaBUY,activity/trades cokluklarivekimlikleribirebir.
250ms kontrol3islemlipencere/7dolum/-0,39053;eklemelikol3pencere/10dolum/
+0,23117USD. Hizli kontrol-0,24764/eklemeli+0,02529. Ucretlisanal;esikicinyetersiz.
Bosona6/6pencere,134dolum,-158,631739APIcashPnL(iade/sabitgiderharic);
kendi3/6pencere. Ilkyon3ortakta2ayni; +/-15sntekyon4yakineslesmede2ayni.
IlkalimmedyanBosona71sn/29sent,kendi150sn/16sent(farkliislemlicohort).
Kendi eklemelikolda3ilk/3ek/4tamamlama var; islem yonetim davranisi eklendi,
ayni karar modeline yaklasma veya ekonomik ustunluk kaniti henuz yok.
Hash/FIFO/risk/ucret/gecikme/tekillik/6resmisonuc/bagimsizDecimal toplam,
APIgercekcokluk,Ruff/compileveonbellektentekrar gecti. Runtime degismedi.
Kanit:data/analysis/btc5m_status_20260921_1420/{report.json,check.py,runtime.json}.

## Her BTC5m penceresine katilim shadow'u — 21 Eylul
Operator Bosona gibi her pencerede bulunmayi istedi. Mevcut secici ileri
deney dondurulmus kalir; ayri Londra shadow'unda ilk-giris seciciligi
kaldirilir. Gercek emir yok. Yon kurali Bosona'nin cozulmus modeli degil.
- [x] Ilk sanal alim: t30..200, 10sn aralikla ilk alinabilir 5pay defterini
      ara; ucretli maliyeti en dusuk alinabilir taraf (esitlikte Up).
      Ilk giriste RSI/momentum/50sent bariyeri yok; gereken veri taze,
      kimligi dogru ve 5pay satis derinlikli defter. Eksik veri dolum degil.
- [x] Sonraki ekleme/reopen secici kalir; FIFO<=.98 tamamlama, 20sn ekleme
      bekleme,5payklip/10acikpay/$15alis/$5pencere riski ayni. Ilk alim
      istisnasi tekrar acilisa sizmaz; 250ms yeni quote ve fiyat limiti ayni.
- [x] Manifestte profil/hash dondurulsun; restart profil degisimini ve
      mukerrer ilk alimi reddetsin. Verisiz/ret olan pencere ayrica gorunsun.
- [x] Gercek scheduler'da secici modelin sifir sinyal verdigi ard arda
      pencerelere katilimi, geciken veri/ret sonrasi tekrar denemeyi test et;
      mevcut kontrollerin regresyonu, Ruff/compile ve Londra ilk dongu teyidi.
Birincil olcum: mevcut secici 250ms eklemeli kola gore ayni atanmis
pencerelerde katilim, ucretli net dolar ve acik risk. Katilim kar kaniti
sayilmaz; herpencere kaydi zorunlu, herpencere dolum garantisi verilmez.

Sonuc: --participate profili ilk alimi ayirdi; varsayilan secici davranis
regresyon testinde ayni. Yerel/Londra full-loop iki ard arda sessiz pencerede
secici0giris,katilim2/2giris; t30stale/t40kaymafiyatreddi/t50giris,acik
envanterlerestart,profilfreezeveistisnaninilkislemlesinirlanmasi gecti.
Gecmis6karardefterinde6/6girisniyeti (uygulama/PnLreplaydegil).
Londra ayri polymarket-bosona-participation-v1,tmuxbosona-participation,
PID123275. Atama21Eylul14:45UTC/17:45TR–24Eylul14:45UTC,+25dksonuclar.
Ilk gercekpencere:30.082sn hizli/30.325sn gecikmeli, herbagimsizkolda
5Down/ucretlimaliyet2,38694. Eski secici sinyalNoneiken girdi;ilk5kararda
schedulerhatasi0. Gercek defter/ucret/risk/tekillik/gecikme/kaynakhash teyit.
EskiPID112062/112442vekaynaklarayni. Ruff/compile/diffcheck gecti.
Kanit:data/analysis/btc5m_participation_20260921/. Ekonomik sonuc acik.

## Bagimsiz BTC5m arastirma promptu ve repo yayini — 21 Eylul
Operator ayni Ingilizce promptu Astra Ultra, Fable ve PRO'ya kendisi
vermek, mevcut kod/kanitlari commit ve push etmek istedi. Oncelik
Bosona'nin BTC5m karar kuralini cozmek; yeni deney veya runtime degisikligi yok.
- [x] Tarihli kanitlar, kaynak/veri haritasi, mevcut secici ve katilim
      deneyleri, ters kanitlar ve muhasebe/causal/uygulama sinirlari ile
      tek, bagimsiz elestiriye acik Ingilizce Markdown promptu hazirla.
- [x] Prompt yollarini ve sayilarini kontrol et; dahil edilen onceki
      katilim degisikliginin scheduler/regresyon ve hedefli lint kontrollerini calistir.
- [x] Yayina girecek 11 dosyanin kapsami, boyutu, credential kaliplari ve
      JSON/JSONL yapisi kontrol edildi; sir dosyasi yok, ilgisiz dosya eklenmedi.
Yayin adimi: yalniz bu dosyalari commit/push et; son kabul kontrolunde
uzak refs/heads/main ile yerel HEAD ayni olmali.
Kabul: docs/BOSONA_BTC5M_INDEPENDENT_REVIEW_PROMPT.md erisilebilir,
uc inceleyiciye ayni kanit ve acik sorulari verir; GitHub commit'i teyitlidir.
Dogru calisma kaniti: gercek scheduler'in bes test senaryosu, eski mum
hatasini yakalayan mutasyon, FIFO/risk/ucret/restart/causal regresyonlar
gecti; uc Python dosyasinda Ruff/compile ve prompt yol kontrolu gecti.
Mevcut tarihli Londra runtime kanitlari dahil; bu gorev runtime'i degistirmedi.
