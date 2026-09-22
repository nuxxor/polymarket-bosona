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

## Bagimsiz BTC5m politika incelemesi — 21 Eylul 2026

Kapsam: `add159d343948e4b46a5491b9bab4c78fceeeb40` uzerinden bagimsiz
arastirma denetimi. Servis, strateji, emir, butce ve credentials kapsam disi.
Onceki "dolumlardan karar kurali" asamasinin kabul olcutleri uygulanir:
bir kazanc ve bir kayip yolu, muhasebe/cokluk/zaman denetimi, davranis ile
ekonomik sonucun ayrilmasi ve tek ayirici deney. Yeni shadow baslatilmaz.
- [x] Onbellekli alti-pencere kontrolunu izole kopyada yeniden calistir.
- [x] Tarihsel nakit hesabi, ham kayit coklugu ve iki ham tape ornegini denetle.
- [x] Guncel/frozen kaynaklari ayir; scheduler ve causal kontrollerini calistir.
- [x] Yeniden uretilebilir hesaplar, Turkce degerlendirme ve sinirlari teslim et.

Sonuc: docs/BOSONA_BTC5M_INDEPENDENT_REVIEW_20260921.md. Ana yeniden
uretim ve destek kontrolleri data/analysis/bosona_independent_review_20260921/.
Alti-pencere yeniden uretimi, scheduler/causal regresyonlari, 50 politika
toplami ve yeni check.py/Ruff/syntax/hash kontrolleri gecti. Tarihsel
dict tekillestirmesi cokluk kaybediyor; ham coklukla +8313,228464 USD.
En onemli yeni ipucu: eslesen4331dolumun4015'inde pasif role uygun
ucret/karsi-token deseni; kesin orderHash/maker-taker cozumlemesi henuz yok.
Oneri yeni shadow degil, parent-order/rol ayrimini sinayan sabit evrenli
kamu-verisi deneyi. Ekonomik edge veya tam Bosona politikasi dogrulanmadi.

## Uc saat sonra BTC5m shadow durum kontrolu — 21 Eylul
Operator shadow'larin ilerleyisini sordu. Salt-okunur Londra kontrolu;
mevcut kaynak, kurallar, sureler ve butceler degismez. Ana karsilastirma
katilim baslangici14:45UTC–17:40UTC ayni kapanmis pencereler; diger
baslangiclar ve acik/sonucu bekleyen pozisyonlar ayri raporlanir.
- [x] PID/hash/kalpatisi, planli karar kapsami ve hata/veri bosluklarini dogrula.
- [x] Ucretli sanal PnL, katilim, envanter ve FIFO/risk/tekillik kontrolu;
      ayni donem Bosona kamu dolumlari ve resmi sonuclariyla karsilastir.
- [x] Tekrar calistirilabilir dondurulmus kesit ve kisa Turkce okuma;
      yeni kod varsa hedefli lint/compile ve gercek veri tekrarini dogrula.
Sonuc:17:46UTCsnapshot'ta3guncelPID/hashayni. Ortak35kapalipencerede
250mssecici pair+3,70987/add+8,76225;katilim pair-3,81524/add+2,28290.
Secici19/35,katilim35/35islemli;eniyi3haricadd+1,48018/-8,54943.
Herikiinventory945an=944karar+1geckarar;secici120/katilim114baglameksigi.
Reboundana t28028gecerli/5alim/-0,37406. Bosona33/35pencere282BUY,
24581,693057pay/-1671,549952APIcashPnL;tekpencere-1631,824136.
Ilkyonsecici7/19,katilim17/33ayni;buyukboy hamPnLesit-riskkiyasi degil.
46resmisonuc,35piyasadaactivity/tradescoklugu,Decimal/FIFO/ucret/risk/
gecikme/tekillik,kaynakhash,Ruff/compileveaynihashlitekrar gecti.
Kanit:data/analysis/btc5m_status_20260921_1740/{OKUMA.md,check.py,report.json}.
Runtime/kurallar degismedi;kaliciekonomikavantaj/Bosonakopyasi kaniti yok.

## PRO / Ultra / Fable sentezi — 21 Eylul
Operator uc bagimsiz arastirmayi atlamadan okuyup onemli bulgulari ve
olasi mekanizma kirilimini tartismak istedi. Degerlendirme/salt-okunur
kontrol; raporlardaki durdur/deploy onerileri islem talimati sayilmaz.
- [x] PRO'nun paylasilan tam metni, Ultra yerel tam raporu ve Fable'in
      tam artifact'ini oku; kaynak/kapsam farklarini ve tum maddeleri kaydet.
- [x] Mekanizma, muhasebe, surum, veri/kapsam ve istatistik iddialarini
      ayir; karar degistiren noktalari kod/kayit/resmi belgelerle denetle.
- [x] En guclu birlesik hipotezi, celiskileri ve oncelikli tek arastirma
      siralamasini raporla; gozlem/tahmin/dogrulanmamis ayrimi korunsun.
Sonuc: docs/BOSONA_UC_INCELEME_SENTEZI_20260921.md. Uc tam rapor ve
Fable'in kotasyon/iade alt notlari okundu; K1-K13 ve diger bulgular
ayri degerlendirildi. Ultra ana hesaplari izole ciktiyla birebir eslesti;
PRO dort piyasa aritmetigi, gunluk kaynak/manifest hash'leri ve mum
istek/yanit siniri kusuru tekrar kontrol edildi. Yeni check.py Ruff,
syntax ve gercek arsiv kontrolleri gecti. Tum alt bootstrap/tape/onchain
hesaplari tekrar kosulmus sayilmadi. Resmi iade belgelerinde Gold %18
kademesi teyit edildi; iade/rol/gelecek nakit varsayimlari ayrildi.
Oneri: cokluk ve parent/rol kimligi -> ayni giristen tek risk azaltimi
karsilastirmasi -> yeterli veri varsa ihtiyatli kuyruk replay'i.
Yeni canli/shadow, durdurma, strateji/butce veya runtime degisikligi yok.

## Eski shadow'lari kapat ve emir arastirmasini hazirla — 21 Eylul
Operator mevcut shadow'lari durdurma/revize etme secimini ve sonraki yolu
sordu. Secim: mevcut BTC5m politika deneyleri erken sonlandirilir; kaynak
ve gecmis kurallar degistirilmez. Jev ve ham piyasa/aktor kaydedicileri
kapsam disidir. Yeni islem lane'i yerine parent-emir/rol arastirmasi hazirlanir.
- [x] Londra'daki ilgili surecleri ve STOP_SHADOW yolunu dogrula; normal
      kapanisi iste, stop kaydi/surec yoklugu ve arsiv hash'lerini denetle.
- [x] Son gunlukleri koru; erken bitis, son tam pencere ve acik/bekleyen
      sanal pozisyonlari ayir. Durdurma ileri ekonomik kabul degildir.
- [x] Mevcut araclari kullanarak emir/rol arastirmasinin dar ilk veri
      paketini ve kabul kapisini hazirla; gercek veri erisimiyle siniri teyit et.
- [x] Kisa sonuc ve sonraki lane'in hangi bulgudan sonra acilacagini ver;
      degisen yardimci kod varsa test/lint ve gercek calisma kontrolu.
Sonuc: 18:19:02 UTC'de 7 politika shadow'u + 1 latency gozlemcisi normal
STOP_SHADOW ile kapandi; 8 stop kaydi, PID yoklugu ve 18:26 tekrar kontrolu
teyitli. Ham gunluk onegi/son hashleri korundu; kapanista bekleyen sanal
pozisyonlar ayri. Jev ve veri kaydedicilerine mudahale edilmedi.
R1 sonlu kamu-verisi kontrolu hazirlandi ve Londra'da calisti: 1789402200
piyasasinin t256'daki 7 activity / 7 transaction / 297 payi TEK actor
orderHash'e eslendi; 49,72 taker / 247,28 maker. Gercek nakit ve token
transferleri uzlasti. Ilk receipt iki public RPC'de ayni; tum receiptler
arsivlendi. Emir ilk-gonderim/iptal zamani veya genel siklik cozulmedi.
Yerel/Londra sonuc ayni; duplicate log/eksik match/yanlis exchange/tek
birim nakit farki reddi, Ruff/syntax ve kapanis arsiv kontrolleri gecti.
Yeni islem lane'i veya devamli arastirma servisi baslatilmadi; sonraki
adim parent/rol kapsamini buyutup tek risk-azaltimi testine gecmek.
Kanit: docs/BOSONA_SONRAKI_ADIM_20260921.md;
data/analysis/{btc5m_retire_20260921,btc5m_order_identity_20260921}/.

## R1 genis orneklem ve risk azaltimi — 21 Eylul
Operator emir kimligi -> risk azaltimi -> kanita gore tek yeni shadow
sirasini onayladi. Bu asamada once mevcut decoder ile genis kamu-verisi
testi; ekonomik/girdi kapilari gecmeden keyfi yeni islem kurali acilmaz.
- [x] Evreni sonuclardan bagimsiz sabitle: tarihsel 1842 gozlenen piyasanin
      her UTC gununden hash sirasiyla 8 (64) temsil ornegi; onceki son20-add
      grubunun 66 piyasasinin tamami ayri tanisal kohort; 14 bilinen vaka/
      cokluk kontrolu ayri. Birlesim137piyasa/2066BUY/2041transaction.
      Takvim2286slot ve eksik/olmayan islem ayrimi korunur; kor test denmez.
- [x] Ham coklugu koruyan girdiler, tam piyasa public activity teyidi,
      receipt/gercek transfer/emir kimligi/rol eslesmesini sayi ve pay
      bazinda raporla. Basarisiz cevap veya desteklenmeyen akis sifir degil.
- [x] Dolum/emir parcalanmasi, gec parent-devami, rol/buyukluk ve
      ilk risk azaltan zaman grubunu incele. Ayni saniyede ilk parent
      belirsizse primer karsilastirma null; sonraki aktor islemleri replay
      edilmez. Tek parent grubunda kapatilan pay, maliyet sinirlari ve
      hold/karsi-alim yerel farki; gun ve piyasa agirliklari ayri.
- [x] Sonuclardan yurutulebilir bagimsiz kural cikiyorsa tek deney tanimi;
      cikmiyorsa somut kalan veri/sinyal ihtiyaci ve sonraki ayirici adim.
      Decoder regresyon/negatif kontrolleri, lint, gercek/cached tekrar;
      kaynak ve veri manifestli Turkce rapor teslim edilir.
Sonuc: 137/137 public condition gecmisi, 2041/2041 receipt, 2066/2066 BUY
ve 96059,619427 pay uzlasti; 8 ikinci-RPC kontrolu ayni. Onchain BUY
nakit/token teyidi tam; MERGE/REDEEM public API kontrolu, harici transfer
yoklugu ve sifir ilk envanter zincir bakiyesiyle ispatlanmis degil.
64-piyasa seciminde maker pay %86,57; 629 dolum 305 parent. Onceki son20
271 add kaydi 120 parent; zaman sirasi varsaymadan 151-165 kayit ayni
emrin devam parcasi. Miktar araligi %20,80-52,96: pay-cogunlugu teyitsiz.
64 piyasada ilk azaltim32, azaltim-yok23, belirsiz9. 15 olayda en ucuz
uygun lotla bile cift maliyeti>1; azaltim payinin %46,07'si. Yerel delta
55 hesaplanabilir pencerede +165,37USD, ex-top3 -153,79; gun araligi
sifiri kesiyor. Bu actor-kosullu sonuc bagimsiz ekonomik kural degil.
Eski shadow'lar 18:50:38 UTC tekrar kapali. Yeni islem/shadow lane'i
baslatilmadi. Sonraki tek adim M1 pasif teklif icin gerceklesebilir
fiyat/kuyruk kontrolu: derinlik + yonlu islem hacmi + nedensel saat;
fiyat-degdi=doldu varsayimi yok, girdi/kapsam kapisi gecmeden yeni
islem politikasinin parametreleri dondurulmayacak. Bu adimin protokolu
raporda; M1 kodu/servisi henuz uygulanmadi. R1 kontrol/lint/syntax,
gercek veri ve byte-identical cached tekrar gecti.
Kanit: docs/BOSONA_EMIR_RISK_SONUCLARI_20260921.md;
data/analysis/btc5m_parent_research_20260921/.

## M1 pasif teklif gerceklesebilirligi — 21 Eylul
Operator R1 sonrasi devam talimatini verdi. Gercek emir yok; eski shadow
ve Jev degismez. Tek sonlu deney: gorunen defterin arkasina konan 5 paylik
pasif teklif icin gerceklesme/veri kapisi. Bu Bosona dolum-replay politikasi
veya kuyruk yeri kanitlanmis bir kar backtest'i degildir.
- [x] Mevcut DB/kaydedici/sema ve yardimcilari incele; degismeyen takvim
      kesimi ve gun basina hash-secimli kucuk evreni sonuclardan once sabitle.
      t30/120/210/280 ayni deneyin bagimsiz gozlem noktalaridir; toplamlari
      tek envanter stratejisinin PnL'si sayilmaz. Ana fiyat bid-1tik, bid
      kontrolu; 5pay,250ms aktivasyon,1sn sonra iptal istegi,+250ms iptal.
- [x] Iki-token ham defter/olay zamanini, LTP transaction coklugunu ve
      gercek maker seviyesi/miktarini denetle. Snapshot sonrasi delta
      tutarliligi, gec/veri boslugu, aynali mint ve rol dogrulamasi; yok=0
      yapilmaz. Kamu L2 kaydi L3/kuyruk sirasi diye sunulmaz.
- [x] Yeterli baglamda iptalden otomatik kuyruk kredisi vermeyen arkadan
      model ve kuyruk-onu duyarliligi; fiyat degmesi dolum degil. Yetersiz
      kayitlarda ekonomi null ve somut veri kaybi; esik sonuca gore degismez.
- [x] Tekrar calistirilabilir veri/kaynak manifesti, para/zaman/kuyruk
      negatif kontrolleri, lint ve gercek veri replay'i; Turkce bulgu ve
      tek sonraki lane icin gecilen/kalan kapilari raporla.
Sonuc:614takvimslotundan gun basina32hashsecim=96piyasa/384baglam.
92piyasadaabonelik;tamgoruntu/deltaayrimiyla267->322hamkesit;304gecerli
baglam(%79,17),%95kapisigecilmedi. Son gun123/128; butun evrenin eksikleri
silinmedi.1089LTP'nin1087'si/%99,91pay tum katilimcilarin onchain nakit ve
token transferleriyle eslesti; iki RPC receipt yoklugu null. Yuvarlanmis
LTPortalamasigercek maker fiyat/miktarina acildi;70mesaj tamVWAPileayni
degil, yuvarlamaileuyumlu. Gercekseviyeler ve mint/direkt yollar ayri.
On hesapta terminalGamma tickini gecmise kullanma sorunu yakalandi:
89/92piyasada.001tick karar aninda dogrulanmis degildi. Bu hesap gecersiz
arsivlendi. V2 sabit .01USD fiyat mesafesi/sent-izgarasi; eski protokol
korunarak gerekce ve revision hash'i kaydedildi. Kor onkayit basarisi denmez.
V2bir-sent-gerisi501uygunteklif:arkada9dolum/45pay/-8,35USD;onde89dolum/
422,14pay/-46,93. 0sentkontrolarkada18dolum/87,13pay/-9,31;onde-22,82.
Bunlar bagimsiz problemin tanisal senaryolari; uygulanabilir botgeliri
veya matematikselPnLalt/ustsiniri degil. Sade maker model kar gostermedi;
Bosona'nin geneli veya makerligin imkansizligi sonucuna varilmadi.
Kontroller:gercekreceipt,bozuklog,erken/gecfiyat,WS tekrar,eski snapshot+
gunceldelta,tektarafbosdefter,kuyruk,Decimalpara ve sonucu ters cevirme;
Ruff/syntax ve tamverinin byte-identical tekrari gecti. 19:22:53UTC'de
eski8PIDyok; yeni shadow/LIVEbaslatilmadi,Jev/butce/kaydedicidegisiklikyok.
Siradaki tek asama: kendi eski D/E/F kabul/iptal/dolum kayitlariyla
yurutme modelini kalibre etmek; bu kalibrasyon henuz uygulanmadi.
Kanit:docs/BOSONA_MAKER_GERCEKLESME_20260921.md;
data/analysis/btc5m_maker_feasibility_20260921/.

## M2 — Kendi D/E/F emirleriyle yurutme kalibrasyonu
Operator sonraki adimi onayladi. Sonlu salt-okunur arastirma; gercek emir,
butce, Jev veya kaydedici degisikligi ve yeni shadow yok.
- [x] Londra'nin kapanmis D/E/F gunluk/state kesitini hash ile sabitle;
      devreden emirleri bir kez say, kabul edilen dolmamis emirleri koru.
- [x] Gonderim/kabul, iptal ve dolum saatlerinin gercek anlamini kaynaktan
      dogrula. Ogrenilme saati exchange saati sayilmaz; eksik omur aralik
      veya null olur. M1 varsayimlarini gercek olcumlerle karsilastir.
- [x] Yeterli kayitta ayni defter/receipt hacmiyle gercek ve modellenen
      miktari karsilastir. Kendi emrinin deftere eklenmesi cift kuyruk
      yaratmasin; eksik iptal saatinden sahte false-positive uretilmesin.
- [x] Kapsam, uyum/hata ve kalan veri ihtiyaci; runnable kontrol, lint,
      gercek veri tekrar uretimi ve Turkce rapor. Veri kapisi gecmeden
      simulator kalibre veya yeni politika karlı ilan edilmez.
Sonuc:624kabul/170dolmus/454dolmamis; devreden emirler tek sayildi.
59conditiontamgecmisi/203BUY/203receipt/203maker dolumu,840,474039pay ve
385,432141USDnakit gercek transferlerle ve tum emir-state miktarlariyla
uzlasti. Dyerel56/Londra480medyanNIYET->ACK125,5/70ms; E69/F96ms.
ACKsafag/aktivasyon saati degil; dolum_ms ogrenilme saati. WSclock183/203
vepay%89,77gecerli;13gecrapor,1saatceliskisi,6WSeksigi ayri. Kamu saati
ozel exchange saati sayilmadi. Basariliiptalistek/cevapsaaticifti0:
tamkalibrasyonkapisi GECMEDI, confusionmatrix/tamomurtahmini null.
Dolumdanbagimsizherkol12hashsecimi=36emir/36gecerlidefter. Bunlarin
16dolmusundan14tamkullanilabilirzamanliemirde kosullutanisalakis:
548ekreceiptuzlasti; modele gerceksondolum+100ms'yekadarsureverilse de
69,982214gercekpaya35hesapladi;7emirdegercekdolumvarkenmodelsifir.
Bu7/14geneldogrulukorani degil; statikilk-kuyrukvarsayimi yeterli degil.
Iki kismidolumda toplam0,017786fazlahesap. Yuvarlamadanbuyuyenfiyat
bolumu paratutarindadogrulandi; eskiM1donmussonuckaynagi korunuyor.
Test/lint/compile ve ikiraporunbyte-identicaltekrari gecti. 19:47:20UTC
eski8PIDveilgiligolgesureciyok; gercekemir/butce/Jev/kaydedicidegisiklikyok.
Siradaki veri gereksinimi: kendi gercek emirlerinde oid bazli iptalistek/
cevap + gerceklesme kaynak/alınma saatleri. Bu veriler bu tur uretilmis
veya tam simulatorkalibrasyonu tamamlanmis sayilmaz. Yeni shadow yok.
Kanit:docs/BOSONA_KENDI_EMIR_KALIBRASYONU_20260921.md;
data/analysis/btc5m_own_execution_20260921/.

## M3 — Emir yasam dongusu saatlerini olcume hazirlama
Operator eksik iptal saatlerini kapatacak sonraki adimi onayladi.
Ana kaynak ve mevcut F calisma kopyasina yalniz gozlem eklenir; strateji,
butce, state ve donmus M1/M2 kanitlari degismez. Yeni LIVE veya shadow yok.
- [x] Ortak POST, tekil/toplu iptal, durum sorgusu ve dolum ogrenilmesini
      oturum/deneme/oid ile bagla. UTC + monotonic saat; SDK cagrisi
      exchange aktivasyon/iptal saati gibi sunulmaz.
- [x] Kismi/bozuk/teyitsiz yanit, eszamanlilik ve kayit arizasinda mevcut
      emir sonucu korunur. Yalniz izinli alanlar, ham imza/yanit/sir yok.
- [x] Sahte borsayla gercek ortak fonksiyonlari calistir; mevcut hedefli
      F testleri/yeni-modul lint/syntax ve JSONL mutabakati gecsin; ana
      kaynaktaki eski basarisizliklar once/sonra ayrica raporlansin.
- [x] Kaynak/hash ve calistirma kanitini sakla. Hazir olcum altyapisi ile
      henuz toplanmamis gercek iptal verisini ayir; kalibrasyon acik kalir.
Sonuc: ana kaynak + F ortak SDK yolunda oturum/deneme/oid, UTC/monotonic
ve dolum ogrenilme kaydi hazir. F dagitim listesi/hash guncel; butce degismedi.
Her iki kaynakta37MOCKcagri/79olay/3dolumartisi; ag kapali. Dosya arizasi,
timeout/tekrar, gecPOST/iptal, eszamanlilik ve saat sicramasi kontrolleri gecti.
Iki self-test121/121; F muhasebe/D/arsiv/E/F/butce/devir ve lint/syntax gecti.
Ana depoda eski test_muhasebe tekrar-parametresi uyumsuzlugu ve kosullu
collections F821 once/sonra ayni; genel yesil veya LIVE onayi verilmedi.
20:32:44UTC uzak eski8PID/ilgiliLIVE-shadow sureci yok, uzak kaynaklar
degismedi. Yalniz yerel hazirlik; gercekiptalolcumu/tamkalibrasyon yok.
Kanit:docs/BOSONA_EMIR_ZAMAN_KAYDI_20260921.md;
data/analysis/btc5m_order_telemetry_20260921/.

## M4 — Londra olcum pilotunu operator baslatmasina hazirlama
Operator M3 sonrasi sirayla ilerlemeyi onayladi. Gercek para emrini asistan
baslatmaz; Londra'ya park edilmis paket ve tek operator komutu hazirlanir.
Mevcut F stratejisi olcum araci olarak kalir; yeni Bosona politikasi degildir.
Ilk sonlu pilot:30dk,5pay,$10ekrisk; onceki muhasebe aynen devredilir,
yeni butce yalniz operatorun --live komutunda bir kez olusur.
- [x] Uzak kaynak/runtime/hesap durumunu salt okunur kontrol et; uc eski
      bekleyen pencereyi kimlikli dolum+resmi sonuc ile ayri kopyada uzlastir.
- [x] Izole parkli dizine M3 kaynaklari, model, veri yolu, kaynak manifesti
      ve bir kez kullanilan operator komutu. Eski kaynak/state/butce korunur.
- [x] Ag/emir kapali testler, ret/tek-kullanim/sure/butce/hash kontrolleri;
      Londra'da salt-okunur hesap onkontrolu ve gercek piyasa kuru dongusu.
- [x] Operator komutunu ve pilotun sinirlarini teslim et; LIVE baslamadiysa
      gercek iptal/dolum kalibrasyonu ve strateji ileri testi acik kalir.

21:04UTC /22Eyl00:04TR sonuc: izole M4 parkta, salt-okunur hesap
onkontrolu gecti.3eski pencere(+.30,-4,0),duzeltilmis toplam-12.636421;
eski kaynak/state/butce degismedi.Acik emir/disrisk0.500pozisyon kesilmesi
ortak okuyucuda sayfalama+bozukcevap reddi ile duzeltildi.Periyodik
maruziyet okunamazsa normal durus.30dk/5pay/$10 henuz aktive edilmedi.
Yeni G stratejisi yok; F yalniz olcum araci.KamuWS588karar/0emir,
sonkaynak37MOCKcagri/79olay,iki selftest121/121,ilgiliFregresyonlari gecti.
Yeni dosya lint temiz; eskiF3lintbulgusu ayni.Kanit ve operator komutu:
docs/BOSONA_M4_PILOT_20260921.md.Gercekfinansalbaslatmaoperatoradimi;
iptal/dolum kalibrasyonu ve yeni strateji deneyi tamamlanmis degil.

Operator M4 komutunu calistirdi: 21Eyl21:09:08 UTC /22Eyl00:09:08 TR
LIVE basladi. Tek yazici PID160500, kaynak0b632c67fd49, olcum oturumu
8996eec4bbef4981ae441012dc85bc13. F politikasi ayni; M4 olcum paketidir.
Yeni butce10USD, anchor-12.636421, kesici-22.636421; bitis21:39:05UTC
/00:39:05TR. Eski624emir/56dolum baslangic tarihcesidir, yeni sonuc degil.
Ilk kontrolde risk0, yeni emir0; LIVE telemetri yaziliyor, errors0.
Asistan yalniz salt-okunur teyit yapti. Kanit:M4 dizininde
operator_live_verified.json. Pilot sonu/tam kalibrasyon henuz bekleniyor.

## M4 ilk sure kontrolu /22Eyl00:30TR
Operator durum sordu.00:22:15TR hata kapanisi; PID yok.3pencere,
6POST/2kabul/4ret; bir0payiptal,bir4.997273Down@.56dolum.
Salt-okunur ozel arsiv+resmi sonuc+kamu mutabakati:newPnL-2.798473,
toplam-15.434894yerel/-15.434895kamu;acikemir0,pending0,risk0.
OrijinalSTATE/PnL yeniden yazilmadi; ayri kopyada uzlastirildi.
Duruş Errno24 Too many open files: log yazarken. F modelinin her iki
SQLite okuyucusu with connect ile baglantiyi kapatmiyor; normal/SQL
hata yollarinda eski kaynak4/4sizinti,contextlib.closing yamasi4/4kapali.
Yama yerelF/model/hash ile hazir; donmusM4 ve Londrakaynaklari ayni.
Yeni butce/restart yok. Telemetri35istek/35cevap/errors0; iki kabul
28/31ms, bir basariliiptal32ms.Bu kucuk ornek tamkalibrasyon degil.

## M4 duzeltme ve tek devam —22Eyl operator talebi
SQLite baglantilarini kapatan mevcut yerel duzeltme izole Londra devam
paketine uygulanir; eski M4 kaynak/log/state/butce dondurulmus kalir.
Eski10USD anchor/kesici ayni, kalan~7.20USD; yeni para butcesi yok.
Baslangic30dk'dan hata kapanisina kadar gecen sure cikarilir, kalan
~17dk operator baslatmasinda tek sefer tanimlanir. Gercek finansal
restart operator komutudur; asistan salt-okunur test ve dagitim yapar.
Kabul:eski/yeni kaynagin kaynak-sizintisi testi;Londra3.14te tekrarlayan
gercekDBokumalari;Fregresyon/lint/hash;tam hesap mutabakati;tekdevam
butcesi/statekimligi/suregecmisi korunarak komut teslimi.

Operator ayni turda kapsam degistirdi: yeniden10USD butceye acik onay
verdi. Onceki devam tasarimi uygulanmadi. M4v2 ayri parkli pakette
30dk/5pay/yeni10USD; onceki-2.798473USD kayip ve tum gecmis korunur.
Mevcut m4.py onkontrol/tek-kullanim kodu kullanilir; yeni devam
altyapisi yazilmaz. Kaynak hesap ilkM4, sabit state hash'i ile aktarilir.

M4v2 kabul sonucu: izole Londra paketinde duzeltilmisf_model,
16manifestgirdisi teyitli.Python3.14te eski100okumaFD4->205,
yeni1000okumaFD4->4;GCye bagimli kapanis giderildi.Normal/SQLhata
4yol ve Fkarar/risk/WSregresyonu gecti.Hesap-15.434894USD;
acikemir/risk0.EskiM4kaynak/state/butce/logkorundu.Yeni30dk/5pay/
10USDonayli,operatoraktivasyonubekliyor;butce/livehenuzyok.
Komut/kanit:docs/BOSONA_M4_V2_20260922.md.

## M4v2 operator LIVE ve10dkpolling
Operator komutu calistirdi,10dk izleme istedi.Salt-okunur30sn aralikli
surec/FD/butce/mutabakat/emir/telemetri/veri izleme; strateji/risk
ayarlari degistirilmez.LIVE22Eyl00:42:11TR; PID161495, bitis01:12:08TR.
Yeni anchor-15.4349/kesici-25.4349/limit10; eski zarar korunuyor.
Ilk poll00:44:05TR:FD6,acikemir/risk0,hata0.10dk gozlem bu ilk
olcumden itibaren tamamlanacak, tek anlik kontrol yeterli sayilmaz.

M4v2 polling tamam:00:44:05–00:54:05TR600sn,20snapshot; ilk gozlemci
kurulum araligi68sn, sonra~30sn. PID161495tumkontrollerdecanli;FD6–7,
yenidenbirikim/Errno24/telemetriyazmahatasi yok.4kabul/4CANCELED,
heremir0dolum;gercekGETacikemir0,risk0,yeniPnLsentduzeyinde0USD.
Bir1013slowconsumerWSkopmasi sonrasinda kararlar devam etti.
4POSTmedyan56.57ms/4iptal33.11ms;SDKcagrisi,exchangeaktivasyonsaatidegil.
Butce/stratejisabit,planlibitis01:12:08TR;10dkizleme tamamlandi,
30dkpilot/tamkalibrasyon/stratejikarinin kaniti tamamlanmis degil.
Kanit:M4v2dizininde poll_summary.json,20hamkesit,telemetri ve
poll_final_account.jsonl.Salt-okunurhesapta1sifirdolumluacikpencere
sonucubekliyor;bekleyenpozisyonriski degil.

## M4v2 planli bitis —22Eyl01:12TR
01:12:10.971TR sebep=sure ile kapandi;01:12:21UTC+3kontrolundePIDyok.
Salt-okunurborsaGETacikemir0;12kabulun4'u5'erpayMATCHED,8'iCANCELED.
14POST/2post-onlyret;toplam20pay,ikiayripencerede5Up@.50+5Down@.48.
Herpencere4.90maliyet/5odeme:+.10USD.01:12sonrasihesapta+.10USD
sonuclanmis,sondengeli+.10USDresmisonucubekliyor;toplamterminal
katki+.20USD(rebate/sabitgiderharic),eskiM4zarariniicermez.
Public-15.334895/yerel-15.334894sonuclanmismutabakatiuyumlu.
624telemetri/309istek/309cevap,0yazmahatası;Errno24/Tracebackyok.
5WS1013slowconsumerkopmasi:tekrarlayansorun,sifirhataliisletimdegil.
BiriptalLIVEceliskisi271msicindeCANCELEDolarakcozuldu;soniptal
already-matchedsonucunda5paykaybedilmedenislendi.Songettumemirlerkapali.
Kaynak/butce/stratejidegismedi;restartyok.Planli30dkpilotbitti,
kalibrasyonveWSkoknedenincelemesisonrakiis;stratejiedgekanıtidegil.
Kanit:data/analysis/btc5m_m4_v2_20260922/final_0112;check.pygercek
sonkayitlarvehesaptaassert/lintgecti.OrijinalcalisanSTATEdegistirilmedi.

## M5 — WS kok neden kontrolu ve M4v2 emir kalibrasyonu
Operator sonraki adimi onayladi. Kapsam: yerel ortak WS okuyucusunu
incele/test et, dogrulanan kusuru cerrahi duzelt; donmus M4/M4v2 kaynak
ve canli hesap degismez. Gercek emir/restart/yeni butce yok.
- [x] Yogun akis ve yeniden baglanmada defter/veri tazeligi davranisini
      yeniden uret; ilgili F/ortak testler, lint ve Londra salt-okunur WS
      olcumuyle sonucu ve kalan neden belirsizligini ayir.
- [x] M4v2 tum12kabul ve dolmayan emirleri koruyarak POST/iptal/dolum
      saat araliklarini cikar; ayni pencerelerde gercek veriyle mevcut
      simulatoru karsilastir, eksik defter/receipt/saat bilgisini null tut.
- [x] Son muhasebeyi ayri salt-okunur kopyada dogrula; tekrar
      calistirilabilir rapor/test ve somut kalibrasyon kapisi sonucu.

M5 sonuc: yerel ana/F okuyucuda snapshot-atlama, snapshot oncesi delta,
eski mesajdan yapay tazelik ve DURDUR sonrasi yeniden baglanma duzeltildi;
belgelenen heartbeat eklendi. Eski kaynak yeni davranis testinde kaldi,
yeni ana/F gecti; F9senaryo, iki120/120oztest, yeni kod lint/syntax gecti.
Londra emirsiz120sn/1200karar/sifirWS hatasi;1013'un tum nedenleri veya
kalici kesintisizlik kanitlanmadi. Eski/yeni abonelik50sn'de ayni veriyi
aldi; yalniz abonelikbicimi kok neden degil.
12kabul/8iptal/4dolmus emir,5zincirdolumu/20pay;531receipt,3tamactivity.
SDKPOSTmedyan57.40ms/iptal23.75ms;borsaaktivasyonsaati degil.
BirLTPsaatiMATCHEDcevabindan141.54mssonra:100mstolerans degismedi,
1emirnull. Diger11emirde gercek15pay/statikmodel10-15pay;2sahte5pay,
2kacirilan5pay,4emirduzeyindeuyusmazlik. Toplamtutmasikalibrasyondegil.
Sonhesap+.20USDtamsonuclu;acikemir/bekleyen/risk0,remoteSTATEdegismedi.
M5inceleme/yerelfix/tanisalkarsilastirma tamam;tamkalibrasyonkapisi
GECMEDI. Sonraki dar odak4uyusmayanemirde defter/saat/gerceklesme yolu.
YeniLIVE/butceyok. Rapor:docs/BOSONA_M5_OKUMA_20260922.md.

## M6 — Dort emir uyusmazliginin kok nedeni
Operator uyusmazliklari cozmeyi onayladi. Donmus M1/M2/M4/M5 korunur;
yeni LIVE, shadow veya butce yok. Mevcut decoder ve ham M5 kesiti kullanilir.
- [x] Iki sahte dolum ve iki kacirilan dolumda gercek fiyat/rol, defter
      degisimleri ve SDK/kaynak/alinma saatlerini tek tek uzlastir;
      besinci saat-celiskili dolumu ayrica kontrol et.
- [x] Kanitlanan model kusurunu en kucuk yeni arastirma revizyonunda
      gider; bilinmeyen kuyruk/saat bilgisini uydurma. Tum12emir kontrolu
      ve onceki donmus sonuclarla farklar acik olsun.
- [x] Runnable negatif kontroller, hedefli lint ve gercek veri tekrarini
      dogrula; cozulmus neden ile kalan kalibrasyon kapisini ayri raporla.

M6 sonuc: ayni12emir/20pay/5zincirdolumu,eskiM5korundu.Iki sahte dolumda
send-100msderinlik0ikenACKaninda321.99/341.52paygorunuyor.ACKderinligi
eksi5payduyarliligindebunlar0dolum;4uyusmazlik2yeiniyor.Ama bir baska
0dolumkontrolu0-0yerine0-5oluyor;bu kalibre/tamdogru modeldegil.
Iki kacirilandolumda663/518.40sabitderinlik,ilkuygunLTPkaynakzamanindan
oncealinmisgoruntude15/49payakadarazaliyor.Sabitkuyrukyeterlidegil;
azalmayidolum/iptalsaymakvemesajsonrasiikinci kez dusmekyanlisolabilir.
Bir33.33paysame-priceeslesmeyleuyumluL2azalmasiLTPden464msonce;
MATCHEDcevabiLTPden141.54msonce.Baska20paysame-priceeslesmeye4azalma
adayivar;eniyakinizamani secipgeriyedolumyazilmadi.Saat-nullkorundu.
YeniM6taniaraci/12kontrol/causal-mirror-belirsizliktesti,M1/M5regresyon,
Ruff/syntaxvebyte-identicaltekrargecti.01:48:38TRM4v2PIDyok;kaynak/
state/butcehashlerikorundu.Tamkalibrasyonacik:ayniLondrasaatindeizinli
alanli kendiorder/tradeWS+kamuL2/LTPbirlikteolcumu gerekiyor.Bu tur
yeni dinleyici/pilot/butcebaslatilmadi;kesinolcumolmayan12tahminnull.
Kanit:docs/BOSONA_M6_UYUSMAZLIKLAR_20260922.md;
data/analysis/btc5m_m6_20260922/{diagnose.py,check.py,report.json}.

## M7 — Ayni Londra saatinde hesap ve kamu olay kaydi
Operator M6 sonrasi olcum adimini onayladi. Ayri salt-okunur dinleyici;
gercek emir, pilot/restart ve yeni butce yok. Mevcut SDK telemetrisiyle
UTC/monotonic saat ve oid/trade kimligi uzerinden birlesebilir kayit.
- [x] Mevcut saat/kimlik yardimcilarini yeniden kullan; kendi order/trade
      olaylari ve BTC5m book/price_change/LTP icin izinli alan kaydi.
      API owner/anahtar, ham auth/istisna metni ve imza kayda girmesin.
- [x] Kaynak/alinma/yazma saatleri, baglanti oturumu, ping-pong, eksik
      veri/kopma, kuyruk tasmasi, durus ve piyasa gecisi ayri izlenebilsin.
      Yeniden baglanti kaybolan olaylari tamamlamis sayilmasin.
- [x] Sahte WS ile parcali/tekrarli/gec olaylar, sir-sizintisi ve ariza
      kontrolleri; Ruff/syntax. Londra'da emir vermeyen gercek sonlu
      iki-kanal/piyasa-gecisi kontrolu ve kaynak/hash/cikti dogrulamasi.
- [x] Parkli paket ve tekrar calistirma komutu; henuz gercek kendi
      dolum olayi alinmadiysa bunu tam kalibrasyon saymadan raporla.

M7 sonuc: ayri izinli-alan dinleyici ve ayni UTC/mono/saat-kimlik kaydi
hazir. Parcali/tekrarli/gec olay, sir/tasma/yazici/STOP testleri; son kod
Ruff/syntax ve yerel/Londra iki-kanal kontrolleri gecti.
Gercek360+120+120sn:374923kamuolayi,hesapGETacik0,gercekuserolay0.
Ilkiki kosuda birer kopus(ikincide1013);son120sn tamkayit+ayribasitdrain
0kopus.Surekliislemeyetersizligigorulmedi;1013koknedeni ayirtedilmedi.
Ilkkosu ikipencereama kopus;sonkosu temizama tekpencere.Kesintisiziki-
pencere kapisi ve gercekdolumkalibrasyonu GECMEDI.Kritergevsetilmedi.
Listeendpoint varolanoncekipiyasayibosdondu;dogrudansluglookupile
iki satirlikduzeltme,eksikpencereatlamayok.35dkevreni10piyasa20token
teyit;35dkWSkosusu yapilmadi.Sonruntimehash4ae34533bf79;paketparkli
/home/ubuntu/polymarket-bosona-m7-v3.M4v2kaynak/state/butcehashayni,
finansalPIDyok;dinleyicilerbitmis.Yenifinansalpilot/restart/butceyok.
Rapor:docs/BOSONA_M7_OLCUM_20260922.md.Sonraki kalibrasyonkapisi acik.

## M7 devam — coklu pencere tasima tanisi
Operator elektrik sonrasi saglik kontrolunun ardindan bu adimi onayladi.
M7-v3 kaynagi ve finansal bot/state/butce korunur; emir/restart yok.
- [x] Sonuc oncesi 900sn ayni evrenli tam kayit + ayri basit dinleyici
      kontrolunu sabitle. Kutuphane tamponu, okuma duraklamasi, mesajlar
      arasi isleme suresi ve guvenli kapanis sinifini olc; ham auth yok.
- [x] Londra'da sonlu gercek akis ve en az iki aktif piyasa gecisi;
      kopus/eksik veri basari sayilmasin. Kanitlanan kusur varsa dar yama
      ve eski/yeni testi; neden belirsizse kosudan kesin cozum uretme.
- [x] Test/lint, gercek kayit tekrari, kaynak/runtime hash ve finansal
      dosyalarin korunmasi. Tasima kapisi ile gercek dolum kalibrasyonu
      ayrilsin; tek temiz kosu kalici kesintisizlik kaniti degildir.

Sonuc:900,017sn/dortaktifpencere/603783kamuolayi.Kayitci3/basitsenkron5/
ek240snasenkron1kamu1013slowconsumerkopusu;user0kopus90PONG.Kuyruk
max150/98(sinir4096),paused0;CPU78,89/33,89sn;FD10/5,RAMstabil.
Surekliistemcibirikmesikanitiyok;JSON/diskveya senkronI/Otekaciklamadegıl.
Sunucu/ag/kutuphaneortakyolkoknedenisinirli;kalicicozumvekesintisizlik
kapisiGECMEDI.Gerekcesizkaynak/tamponyamasi uygulanmadi;M7v3degismedi.
Eszamanlikapaliaralikyok;tamveri-yedeklemehenuzyok.Ikibagimsiztamkamu
kaydi sonrakidaraday,bu turbaslatilmadi.Cokluk/saat/tazelik ayrıdoğrulanmalı.
Kontrol/negatiftest/Ruff/syntax/hashvegercekkayituzlasmasigecti.Finansal
kaynak/state/butceayni,sonGETacik0,finansal/gozlemPIDyok.Kalibrasyonacik.
Kanit:docs/BOSONA_M7_BAGLANTI_20260922.md;
data/analysis/btc5m_m7_transport_20260922/{protocol.json,probe.py,check.py,result.json}.

## M7 — Iki bagimsiz tam kayitla kopus kapsami
Operator 15dk cift tam kayit testini onayladi. Ayni M7-v3, iki ayri
Londra sureci ve ayni onceden sabitlenen piyasa listesi; finansal emir yok.
- [x] 900sn protokol/kaynak hashlerini sonuc oncesi sabitle; iki tam
      kaydi ayri sakla, mevcut kayitciyi yeniden kullan.
- [x] Kopus ve snapshotla toparlanma boyunca diger kayitta gercek,
      alinma-anina gore guncel iki-token defterini ve LTP coklugunu denetle.
      Ortak olaylari iki dolum sayma; eksik veri/tazelik/kapsam ayri.
- [x] Hedefli kontrol/lint/syntax, Londra gercek kosu/ham kayit tekrari,
      finansal hash/GET ve sonlu surec kapanisi; sonucu ve sinirini kaydet.
Kabul: iki aktif piyasa gecisi, kayit kaybi yok, gozlenen her kopus-
toparlanma kontrol aninda guncel yedek defter; kopus yoksa test belirsiz.
Bu kamu kapsami testidir; kendi dolumu veya kalici kesintisizlik kaniti degil.

Sonuc:900sn/dortaktifpencere;A3/B2kamu1013kopusu.100msgriddekopus-
toparlanma28/28kontrolde yedek iki-token defteri guncel;66LTPmesaji
diger kayitta korundu, ekonomik dolum olarak birlestirilmedi.9.001
kontrolunyalnizbaslangictaki1'inde ikisi de hazirdegil.22/76geri kaynak
zamaniguncellemesi yeni snapshot'a kadar gecersiz. Hamcokluk,saat,
hash,tekrarhesap/test/lintgecti. Dar kapsama kapisi gecti; kalici1013
cozumu/upstreamtamligi/kendigercekdolumkalibrasyonu acik. Finansal
hashlerayni,GETacik0,kayitcisurecleribitmis. Rapor:
docs/BOSONA_M7_CIFT_KAYIT_20260922.md.

## G hazirligi — Operator uyurken devam, finansal baslatma haric
Operator olcum kusurlarini giderip G adayini, yalniz canli baslatma kendisine
kalacak sekilde hazirlamayi istedi. Mevcut M7 cift kayit testi tamamlanir;
gercek para emri, yeni aktive butce veya finansal restart yapilmaz.
- [x] Olcum kopus/kuyruk/saat sinirlarini kapat veya gercek belirsizligi
      fail-closed kontrole cevir; bilinmeyen dolumu sanal gercekmis sayma.
- [x] Dogrulanmis parent/rol ve envanter bulgularindan tek kucuk G
      deneyini tanimla; yeni politika hipotezini Bosona'nin cozulmus
      sinyali veya kanitlanmis kar diye sunma. Eski kanitlar korunur.
- [x] Mevcut emir/mutabakat/risk altyapisini tekrar kullanarak izole
      G paketi; kaynak ve risk dondurma, operator baslatma komutu,
      salt-okunur hesap kontrolu ve emir gondermeyen gercek dongu.
- [x] Ilgili regresyonlar, hedefli lint ve gercek runtime hash/kayit
      teyidi; hazirlik ve yalniz gercek dolumla sinanabilecek kabuller ayrilsin.
Kabul: finansal baslatma operatora kalir; acik teknik engel varsa canli
hazir onayi verilmez. G'nin karli veya tam Bosona kopyasi oldugu varsayilmaz.


Sonuç: G1 ayrı Londra paketi `/home/ubuntu/polymarket-bosona-g-v2/bot` içinde
parkta. F emir/mutabakat motoru yeniden kullanıldı; yön sinyali yerine
pasif teklif + net envanter yönetimi hipotezi sabitlendi. Gerçek tick,
snapshot/kaynak saati, muhasebe çokluğu, belirsiz rezerv ve telemetry
kontrolleri eklendi. Mutabakat geçersizken mevcut teklifi koruma hatası
önce yeniden üretildi, sonra G_emniyet iptal kontrolüyle kapatıldı.

Yerel/Londra hedefli testler, lint/syntax, tek kullanımlık bütçe/hash
kapıları ve sahte SSH başlatma testi geçti. Son kaynakla 480,117 saniye
iki gerçek piyasa kuru koşusu: 120 teklif niyeti, 0 ekonomik dolum,
870 karar; normal süre sonu ve tüm kuru emirler kapalı. Kaynak hash
`d45ee6731e35b1b189770fe308f7ab8f0cb6814bfb18667f6aa7606c2c4bdd1a`.
Çift gözlemci gerçek başlangıç testi 4,41 saniyede hazır; 45 saniye
sonunda iki süreç normal kapandı. Emir telemetrisi sahte SDK kontrolü
37 çağrı/79 olay; saat, eşzamanlılık ve yazma arızası kontrolleri geçti.

Son gerçek hesap GET: açık emir 0, risk 0; 79 pencere/638 emir nihai
−15,234894 PnL ile uzlaştı. Eski M4v2 kaynak/state/bütçe hashleri aynı.
G için RUN_G/STATE_g/BUDGET_G/LOG_g yok, STOP_G var; finansal süreç yok.
`londra_g_baslat.sh` yalnız operatör çalıştırınca 30dk/5pay/yeni$10 açar.
G'nin kârlılığı, kendi gerçek dolum kuyruk kalibrasyonu, upstream tamlık
ve 1013 kök nedeni açık; bunlar çözülmüş diye kabul edilmedi. İki arşiv
otomatik canlı book failover değildir. Teknik hazırlık tamam; ilk küçük
LIVE ölçüm operatöre bırakıldı. Kanıt ve sınırlar:
`docs/BOSONA_G_HAZIRLIK_20260922.md`, `lanes/g/validation/`.


## G1 operatör LIVE başlangıç teyidi — 22 Eylül 2026
Operatör londra_g_baslat.sh komutunu kendisi çalıştırdı. Bu tur salt okunur
başlangıç/ilk işlem kontrolü; kaynak, strateji, süre ve bütçe değiştirilmez.
- [x] Londra'da tek LIVE yazıcı, beklenen kaynak hash'i, yeni $10 bütçe,
      30 dakika/5 pay ve önceki muhasebenin korunmasını doğrula.
- [x] İki kayıtçıda güncel dosya, kamu/hesap PONG, gerçek özel order/trade
      olayları ve SDK telemetrisinde sıfır yazma hatasını doğrula.
- [x] İlk gerçek pencere/teklif/dolum kaydı; belirsiz iptal kapanışı ve
      kaydedilmiş net pozisyon sınırı. Başlangıç teyidi pilot sonucu değildir.
LIVE başlangıcı 09:27:27 UTC /12:27:27 TR; PID171437, kaynakd45ee6731e35.
Yeni bütçeanchor−15,2349 /kesici−25,2349; planlı bitiş12:57:23TR.
İlk12:30TRpenceresinde gerçek kabul ve dolumlar geldi. Bir iptal LIVE
cevabından499ms sonra CANCELED teyidiyle çözüldü; bir emir reddi kaydedildi.
İki özel hesap akışında order/trade olayları var, rejected0; SDK errors0.
638eskiemir/59eskidolumsayacı yeni pilot sonucu değildir. Başlangıç ve ilk
pencere kanıtı:lanes/g/validation/operator_live_20260922/.
30dksonucu, nihai PnL ve gerçek-dolum kalibrasyonu henüz tamamlanmadı.


## G1 süre sonu kontrolü — 22 Eylül 2026
Operatör 30 dakikanın dolduğunu sordu. Salt okunur kapanış ve pilot PnL
kontrolü: eski hesap, kaynak ve bütçe korunur; yeniden başlatma yok.
- [x] Süre sonu kaydı, LIVE süreç yokluğu ve gerçek GET açık emir kontrolü.
- [x] Altı atanan pencerenin miktar/maliyet/sonuç hesabı; bekleyen resmî
      sonuç kesin kâr sayılmaz, mümkün terminal sonuç aralığı ayrı verilir.
- [x] Ayrı mutabakat kopyası, kaynak/state korunması ve tekrar hesap kanıtı.

Sonuç:12:57:26TR sebep=sure ile normal kapanış. Gerçek GET açık emir0,
LIVE yazıcı0. Son iki pencere yalnız ayrı salt-okunur kopyada çözüldü;
resmî API son pencereyi yaklaşık13:08TR'de Up olarak teyit etti.
Altı pencere: +5,15/+3,10/+0,75/−0,19811460/−2,34557066/+2,75 USD.
Pilot toplam +9,20631474USD;4artı/2eksi. İade/sabit gider hariç işlem
sonucu; önceki −15,234894 geçmiş korunur, yeni toplam −6,028580.
63kabul/36dolmuşparentemir/37dolumartışı;3WSkopuşu,7ret,SDKerrors0.
Kapanıştan sonra açık emir/bekleyen sonuç/risk0. İki gözlemci40dksonunda
exit0 ile bitti. Kaynak/state/bütçe değiştirilmedi, restart yapılmadı.
İlk salt-okunur kontrol sonresmîsonuçbeklediği için tamamlanmadı;
recheck kopyası bu belirsizliği, complete kopyası sonraki kesin sonucu
korur. Decimal/kimlik/durum kontrolleri ve hedefli Ruff geçti.
Kanıt:lanes/g/validation/final_20260922/{check.py,complete/result.json}.
Bu küçük pilot kalıcı ekonomik avantaj veya tam kuyruk kalibrasyonu değildir.


## G1 süre sınırsız devam — operatör komutu hazırlanıyor
Operatör süreyi sınırsız, payı5 ve zarar sınırını10USD istedi. Açık tercih:
yeni başlangıç bakiyesinden10USD; önceki +9,206315USD ayrı korunur.
Önce operator komutu teslim edilir; finansal başlatmayı kullanıcı yapar.
Ardından araştırma devam eder. İlk G kaynağı/state/bütçe/kanıt korunur.
- [x] İzole aynı G1 politikası; gerçek süresiz mod, yeni $10 tek kullanım
      bütçesi ve devreden tam muhasebe. Tekrar komut bütçeyi sıfırlamaz.
- [x] Kayıtçıların40dk ve sabit piyasa listesi sınırını kaldır: sonlu
      parçalar halinde piyasa yenileme, sıkıştırılmış kayıt ve arıza kapısı.
- [x] Para/süre/kayıt rotasyonu/STOP testleri; hedefli lint ve Londra'da
      emirsiz gerçek başlangıç/rotasyon/hesap teyidi, kaynak hash dondurma.
- [x] Park edilmiş paket ve terminal komutu teslimi; gerçek LIVE yok.
Kabul: sahte çok uzun süre kullanılmaz;10USD sınırı ve eski PnL korunur.
Kayıt/mutabakat/kaynak/disk güvenliği nedeniyle duruş korunur. Strateji
parametreleri sonuç görülerek değiştirilmez; araştırma komut tesliminden sonra.


Sonuç: ayrı /home/ubuntu/polymarket-bosona-g-continuous/bot parkta.
Kaynak b462c0081318d2e7b4db4ab355daa7caeeacb06d825a16d7c50767591c293387;
G politika hash'i fbac759df25c ile aynı. Süre end_ms=null; yalnız G'nin
sabit continuous protokolünde izinli. Bütçe operatör başlatırken mutabık
PnL'den yeni10USD; eski +9,206315 sonuç ledger'da korunur. Tekrar çalıştırma
RUN işaretiyle reddedilir; otomatik bütçe yenileme/restart yok.
Londra dört hedefli test grubu geçti; Ruff/syntax ve sahteSSH başlatma geçti.
Gerçek kuru koşu120,318s:17teklif niyeti/56karar/0ekonomik dolum; süre sonu.
İki gerçek kayıtçı2,912s'de hazır:100sağlık örneğinin tamamı geçerli,
A4/B3parça,23.829JSONsatırı,iki normal çıkış. Gzip tekrar okundu;
red/gap/overflow0. İlk testte /tmp küçük tmpfs olduğundan2GiB disk kapısı
haklı olarak durdu; test gerçek bot dosya sistemine taşındı, kapı gevşetilmedi.
Son GET:85pencere/701emir,−6,028580mutabıkPnL,açıkemir/risk0.
Orijinal Gstate hash'i aynı. Yeni RUN/STATE/BUDGET/LIVElog yok, STOP var.
Komut:londra_g_sinirsiz_baslat.sh. Disk2GiBrezerv/API geçmiş kapsamı/
mutabakat/kayıt arızası duruşları korunur; süresiz garanti edilen uptime değildir.
Kanıt:lanes/g_continuous/validation/proof.tar.gz.

## G1 ilk gerçek pilot — komut teslimi sonrası araştırma
Süresiz operatör komutu teslim edildi. Bu aşama yalnız bitmiş pilotun
salt-okunur analizi; yeni paket stratejisi/bütçesi değiştirilmez.
- [x] Altı piyasanın gerçekleşmiş kârı ile son pozisyonun iki sonuçtaki
      ödeme aralığını ayır; bir muhasebe ayrımını nedensel edge sayma.
- [x] 63 kabul / 36 dolmuş parent'ı iki özel hesap akışı ve son mutabakatla
      eşleştir; tekrar status güncellemelerini ekstra dolum sayma.
- [x] Emir kabul/yerel dolum gözlemi gecikmesini ayır, pasif yürütme kanıtı
      ile bilinmeyen kuyruk konumunu ayır; tekrar çalıştırılır rapor üret.

Sonuç: ilk30dk gerçek pilotta63/63parent miktarı A/B özel kaset ve son
muhasebeyle uzlaştı.36dolmuşparent,40trade×parent,37SDKdolumgözlemi;
status tekrarları çoğaltılmadı.40/40kendi emri maker_orders içinde ve
trader_side=MAKER; tümPOSTpost-only. MedyanPOST43,57ms; privateilkreceipt
ile SDKmiktargözlemi farkı medyan132,28ms. Kuyruk gecikmesi diye sunulmaz.
Son envanter ödeme tabanları toplam−5,797970; gerçekleşenödeme tabanın
15,004285üstünde,+9,206315sonuç. Bu karşıolgusal strateji veyaFIFOgetirisi
değildir. Altıpencere5Up; kalıcıedgeyok. Herkasette6bilinmeyenmessage;
private miktarların uzlaşması tümolaytamlığıkanıtı değildir.
Rapor:docs/BOSONA_G_ILK_CANLI_OKUMA_20260922.md. Tekrarhesap/assert veRuff geçti.

## Süresiz G — operatör başlangıcı sonrası API duruşu ve aynı bütçeden devam
Operatör komutu13:33TR'de çalıştırdı. Yenianchor−6,0286/kesici−16,0286,
end_ms=null doğrulandı.13:42'de pozisyonGETHTTPError nedeniyle
maruziyet_teyitsiz güvenlikkapanışı; süre veya zarar kesici değil.
- [x] Normal kapanışı ve kaynak/state/bütçe/ledger yedeğini koru; finansal
      yazıcı yokken yalnız hazırlık kodunu güncelle. Kendiliğinden restart yok.
- [x] Ağ hatası üç denemeyle sınırlı; ilk hatada MUTABAKAT_OK=False ile
      yeni teklifler durur/mevcutGiptalyolu işler. Kalıcı hata kapalı kalır.
- [x] Açık --resume operatöryolu: orijinal BUDGET/RUN/id/anchor/cutoffaynı;
      taze hesap kontrolü, state arşivi, eski kayıt parçaları korunarak devam.
- [x] Rejected mesaj sayacı kullanılabilirlik ile tamlık ölçüsüne ayrıldı;
      eskiG1 kullanılabilirlikanlamı korundu. Süreç/yazma/PONG/disk/taşma
      kapıları sürer. Rejectenumclasskaydı eksikölçümü görünür tutar.
- [x] Dört test grubu izole kaynakla Londra'da geçti, resume bütçe byte
      eşitliği/tükenmiş bütçe reddi/APIretry ve teklifkapısı sınandı;
      hedefli lint/syntax ve sahteSSHkomutu geçti.
- [x] Gerçek recorderA4/B3parça,70/70health,iki normalexit; A/Bbirerpublicgap
      vebirerprivateenumreddi kayıtlı. Sıfırkayıpdenmedi. Eski arşiv korunarak
      recorderrestart2,206s'de iki kanal hazır oldu. Finansal restart yok.
- [x] Son gerçek --resume (LIVEolmayan) kontrol:87pencere/716emir,
      PnL−6,427780, açıkemir/risk0. Yeniikisonuç−2,00/+1,6008USD;
      yenioturumnet−0,3992. Aynı kesicidekalan9,60082USD.
Son kaynak1c46c9bb8070b8e48a2b3d88cf6e27146c01ae8f33a2ae1e18530c4b39f2c40a;
Gpolicyfbac759df25caynı. Orijinalfinansaldosyalarınhashlerideğişmedi.
LondraSTOPparkta,writer0. londra_g_sinirsiz_baslat.sh mevcutRUNvarsa
aynıbütçeli--resume çağırır; yeni10açmaz. Kanıt:lanes/g_continuous/validation/fix2_proof.tar.gz.
İlk testprodklasöründeki aktive bütçeyi okuduğu için varsayılan−10 testinin
beklentisi tutmadı; kaynaklar izole edilip tümgruplar tekrar geçti. Resmî
sonuçbekleyen ilk iki preflight reddi korunur; son kontrol tamamlandı.

## Süresiz G — operatör devam teyidi 22 Eylül 13:56 TR
Operatör aynı komutu yeniden çalıştırdı. Bu tur yalnız salt-okunur
başlangıç teyidi; kaynak/strateji/bütçe değişikliği veya restart yapılmadı.
- [x] Tek LIVE süreçPID175171,13:56:05TRbasladi; kaynak1c46c9bb8070
      ve politika hash'i dondurulmuş paketle eşleşti.
- [x] BUDGET/RUNbytehashleri ilk süresiz başlangıçla aynı. Anchor−6,0286,
      kesici−16,0286,5pay,end_ms=null. Yeni10açılmadı; stbudgetidaynı.
- [x] A/B kayıtçılarında güncel yazma ve gerçek kamu/hesapPONG;
      rejected/overflow0,SDKerrors0. Eski kayıtlar arşivde korunmuş.
- [x] Başlangıç muhasebesi−6,4278; yaklaşık9,6008USDkalanbütçe.
      Henüz yeni pencere/teklif/dolum yok; sonraki giriş14:00TRpenceresi.
Kabul: bu başlangıçsağlığıkontrolüdür; sonraki ekonomikperformans veya
kesintisiz uptime garantisi değildir. Kanıt:
lanes/g_continuous/validation/operator_resume_20260922/status.json.

## G1 sabit politika — canlı sağlık, ekonomi ve aynı pencere Bosona karşılaştırması
Operatör bu araştırmayı başlatmayı onayladı. İlk G pilotu, süresiz ilk koşu
ve13:56TRdevam ayrı raporlanır. Canlı politika/boy/bütçe değiştirilmeyecek.
- [ ] Güncel LIVE kaynak/bütçe/kayıt sağlık kanıtı; API tekrarları, iptal,
      dolum, belirsiz rezerv ve mutabakat sorunlarını ayrı değerlendir.
- [ ] Bütün atanan pencerelerde net tradeUSD, iki sonuçtaki ödeme, net
      envanter yolu ve parent bazlı gerçek dolum ölçümü; açık sonuç null.
- [ ] Bosona'nın aynı condition'lardaki pencere öncesi dahil tam kamu
      çokluğunu koru; eksik/işlemsiz ayrımı, token kimliği ve nakit/envanter
      kontrolü. Maker/parent yalnız doğrulanan exchange receipt kapsamı.
- [ ] Yön/zaman/fiyat/boy/azaltma-ekleme benzerliğini karşılaştır; farklı
      büyüklükteki toplamUSD farkını üstünlük sayma, parçaları karar sayma.
- [ ] Salt-okunur iki saatlik ileri veri/sağlık takibini başlat, ilk gerçek
      kesiti ve tekrar çalıştırılabilir kontrol/raporu doğrula. Bot durursa
      bunu kaydet; otomatik canlı restart veya yeni bütçe açma yok.
Kabul: ilk küçük örnek kalıcıedgekanıtı değildir. Tek iyileştirme ancak
verinin açıkladığı sorun varsa önerilir; yeni eşik taraması yapılmaz.


## 22 Eylül 2026 — Public GitHub yayını

- Operatör ana reponun public GitHub deposuna commit/push edilmesini istedi.
- Kapsam: mevcut kod, test, protokol ve seçilmiş araştırma özetleri. Ayrı BTC15 analiz dizinleri bu repo yayınına eklenmedi.
- Yayın ayrı worktree içinde hazırlanır; ortak çalışma ağacı/index ve çalışan bot/kaydediciler değiştirilmez.
- Yeni kimlik dosyaları, özel hesap olayları, canlı state/log ve ham arşivler hariçtir. Mevcut public Git geçmişi yeniden yazılmaz.
- Kabul: Git geçmişi + yayın ağacında secret taraması, syntax/mock testleri, diff kontrolü; uzak main commit ve PUBLIC görünürlüğü doğrulanır.
- Yayın kontrollerinin sonuçları ve mevcut sınırlamalar: `docs/YAYIN_KONTROLU_20260922.md`. Secret taraması yeni içerikte temiz; 8 çevrimdışı kontrol geçti. Eski muhasebe testi, lint ve arşiv sınırlamaları raporda açıkça kayıtlı.


## 22 Eylül 2026 — Eksik BTC15 araştırması ve PRO/ULTRA inceleme promptu

Operatörün konusu yalnız Bosona BTC15'tir. Önceki ana repo yayını ayrı BTC15 araştırma dizinini içermiyordu; bu yayında eksik BTC15 rapor/kod/kanıt paketi ve ortak İngilizce prompt eklendi. Diğer stratejiler, ana yerel çalışma ağacı/index, çalışan süreçler ve bütçeler değiştirilmez.

- Paket: `research/btc15_review_20260922/`; kapsam ve ham veri/yeniden üretim sınırları README'de.
- Prompt: `docs/BOSONA_BTC15_PRO_ULTRA_PROMPT.md`; iki inceleyici aynı kanıtla, bağımsız olarak BTC15 hipotezlerini ve tek sonraki deneyi değerlendirecek.
- Kabul: özgün kopya hash'leri, BTC15 miktar/nakit/rol/geç-ekleme toplamları, prompt yolları ve secret taraması; aynı public depoya normal commit/push, uzak commit teyidi.
- Bu bir araştırma teslimidir; yeni analiz sonucu, kârlı strateji, tam ham veri yeniden üretimi veya deploy iddiası değildir.
