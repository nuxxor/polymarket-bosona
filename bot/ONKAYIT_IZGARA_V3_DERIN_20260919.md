# ON KAYIT — IZGARA v3 "DERIN-C" + GEC KURALI TERSINE CEVIRME
Tarih/saat: 2026-09-19 ~15:00 UTC. Kod HENUZ degistirilmedi (playbook #52).

## 1. NEDEN — bu turda olculenler

### (a) 30 hucrelik (fiyat x zaman) haritasi, bizim kisit sinifimiz
Zincir-kesin FILL_PARTY_LEDGER maker ALIS dolumlari; kiyas sinifi =
cuzdan-pencerede HIC >0.40 alim yok (bizim PX_TAVAN_MAKER kisitimiz).
1.406.171 dolum / 21.314.667 pay / 19 gun. Havuzlanmis kr/pay, GUN-KUMELI
esli bootstrap GA95.

TABAN: -0.39 kr/pay.
30 hucrenin HICBIRI artida sifirdan ayrismiyor. 7'si EKSIDE ayrisiyor:
  px 0.16-0.22 @ t60-120  -3.31   px 0.16-0.22 @ t120-180 -3.96
  px 0.16-0.22 @ t240-301 -4.52   px 0.22-0.28 @ t180-240 -3.41
  px 0.22-0.28 @ t240-301 -4.53   px 0.28-0.34 @ t240-301 -6.67
  px 0.34-0.41 @ t120-180 -4.11   px 0.34-0.41 @ t180-240 -3.69
Notr/en iyi bolge: px 0.00-0.10 @ t120-240 (+0.63 / +0.34, GA sifiri iceriyor).

### (b) TAM EV merdiven simulasyonu — secim artefakti YOK
4506 pencere, 19 gun. Her basamak icin: fiyat o seviyeye indiyse dolduk
kabul; ESSIZ BACAK KAYIPLARI DAHIL; gun-kumeli GA. Kuyruk yok sayildi =>
UST SINIR, ama tum politikalar icin AYNI varsayim, sıralama gecerli.
  v2 CANLI [.34 .30 .26 .22 .20 .16]  +0.19 [-0.72,+1.08]  $+0.075/pen  maruz $10.15
  DERIN-A  [.26 .22 .18 .14 .10 .06]  +0.72 [-0.15,+1.55]  $+0.262/pen  maruz $ 6.03
  DERIN-C  [.20 .16 .12 .09 .06 .03]  +0.78 [+0.04,+1.48]  $+0.268/pen  maruz $ 3.89
  COK DERIN[.14 .11 .08 .06 .04 .02]  +0.96 [+0.24,+1.63]  $+0.314/pen  maruz $ 2.53
Basamak marjinal katkisi (v2 tabanindan): 0.34 -> -0.17, 0.30 -> -0.17,
0.26 -> +0.08, 0.22 -> +0.12, 0.20 -> +0.09, 0.16 -> +0.03.

### (c) CURUTULENLER (bu turda, hicbiri uygulanmadi)
- "bosona'yi kopyala: pahali bacak + bedava bacak (0.80/0.02)": TAM EV ile
  -19.74 kr/pay [-20.78,-18.66]. 0.80'e duran ALIS ancak fiyat oraya
  DUSUNCE dolar = ters secimin tanimi. bosona o bacagi taker olarak ya da
  kuyrugun onunde aliyor; maker olarak kopyalanamaz.
- "gec cift kuranlar +6.79 kazaniyor, o yuzden gec kal": SECIM ARTEFAKTI.
  Olen tarafi 0.05'ten ancak ilk bacagin kazaniyorsa alabilirsin.
  Marjinal dolum duzeyinde (t>=200 & px<=0.25): karsi taraf VAR -0.08,
  karsi taraf YOK +0.02 -> SIFIR. Kodda yazili "-14.86 kaybeder" gerekcesi
  de 7 dolumluk gurultuymus; O DA curudu.
- "iki bacak da <=0.40 olan cuzdanlar +13.55 kazaniyor": AYNI ARTEFAKT
  (gidis-donusun tamamlanmis olmasina kosullanma).

### (d) bosona'nin kenari NEREDE (zincir-kesin, 19 gun, 1.78M pay)
  pencere tamamen <=0.40 (BIZIM OYUN):  -3.53 kr/pay
  pencerede >0.40 alim VAR           :  +1.51 kr/pay [+0.43,+2.64]
bosona bizim oyunumuzu oynadiginda O DA kaybediyor. Ama (c)'ye gore o
bolgeyi MAKER olarak kopyalamak -19.74. Yani bu kapi bize kapali; bizim
yapabilecegimiz en iyi sey ulasabildigimiz uzayda en az eksi / en cok arti
hucreye cekilmek = DERIN.

## 2. DEGISIKLIK (uygulanacak)
1. FIYATLAR: [0.34,0.30,0.26,0.22,0.20,0.16] -> [0.20,0.16,0.12,0.09,0.06,0.03]
   Gerekce: (a) + (b). En ust iki basamak olculen marjinal katkisi NEGATIF.
   DERIN-C secildi, COK DERIN degil: COK DERIN simulasyonda daha iyi ama
   gercek dolum orani daha da dusuk olur; 0.20 ust basamagi gercek dolumun
   yogun oldugu yeri koruyor. Bu bir YARGI, onceden yaziliyor.
2. GEC KURALI TERSINE: t>=GEC_KES(200) sonrasi
   ESKI: px <= UCUZ_ESIK(0.25) olan emirleri iptal et  (derin olani keser)
   YENI: px >  GEC_UST(0.10)  olan emirleri iptal et   (ortayi keser)
   Gerekce: (a) haritasinda t240-301 kovasinda 0.16-0.34 bandi -4.5...-6.7
   ile eksi ayrisiyor, 0.00-0.10 notr (-0.19). Eski kural tam tersini
   yapiyordu. Yeni izgarada eski kural TUM emirleri iptal ederdi.
3. PX_TAVAN_MAKER 0.40 DEGISMIYOR (artik baglayici degil, emniyet olarak dursun).
4. Baska hicbir parametre degismiyor. KESICI=-100, KLIP=5, A_ORAN=1.0,
   KAPI_ACIK=False, TAMAMLA_ACIK=False, A_UYUM_ACIK=False, BOY_TESTI=False.

## 3. ONCEDEN YAZILAN BEKLENTI (hedef kaydirmak YASAK)
- Maruziyet pencere basina ~$10 -> ~$4'e DUSECEK. Bu KESIN, mekanik.
- Dolum sayisi DUSECEK: v2'de ~9 pay/pencere gozlendi; v3'te 4-7 bekliyorum.
- kr/pay: simulasyon +0.78 diyor ama kuyrugu yok sayiyor. Canli v2 -1.85 iken
  simulasyon +0.19 diyordu => kuyruk cezasi ~-2.0. Ayni cezayi uygularsak
  v3 canli beklentisi ~-1.2 kr/pay. YANI HALA EKSI BEKLIYORUM.
  BASARI OLCUTU: v3'un 150 pencerelik kr/pay'i v2'nin ayni donemdeki
  degerinden ISTATISTIKSEL OLARAK IYI olmasi ve maruziyetin dusmesi.
  MUTLAK KARLILIK BU DENEYIN HEDEFI DEGIL.
- KILL: 150 pencere sonunda kr/pay v2'den kotuyse VEYA net PnL < -$40 ise
  izgara v3 geri alinir.

## 4. NE OLCULMEYECEK / NE IDDIA EDILMIYOR
- Bu degisiklik kulvari karli yapmaz iddiasinda DEGILIM. (a) haritasi
  ulasabildigimiz uzayda artida ayrisan TEK hucre olmadigini soyluyor.
  Degisiklik "en az zararli + en az sermaye baglayan" noktaya cekilmektir.
- Kalici kar icin gereken sey bu turda da bulunamadi: kuyruk pozisyonu
  (bosona seviyenin %15'i / son boyun %48'i). Bu ayri bir is.

## 5. EK — v2 DENEYI ERKEN KESILDI (protokol notu)
v2 (izgara [.34 .30 .26 .22 .20 .16]) 150 pencerelik deney icin ON KAYITLIYDI.
~20 pencerede kesiliyor. SEBEP v2'nin canli sonucu DEGIL: v2 kesildigi anda
ARTIDAYDI (11/150 skorkartinda +14.20 kr/pay, ve 14:30-14:50Z arasi 4 ust uste
cift: +3.70 / +1.20 / +5.00 / +7.30). Kesme sebebi, bagimsiz CEVRIMDISI
olcumun gelmesi (30 hucrelik harita + TAM EV merdiven simulasyonu, 19 gun,
21.3M pay). Canli 20 pencere gurultudur; 21.3M pay degildir.
"v2 basarisiz oldu" IDDIASI YOKTUR ve ileride de kurulamaz.

## 6. EK — ERKEN IPTAL KOSULU (v3'e ozel, simulasyonun koru noktasi)
Simulasyon "fiyat seviyeye degerse doluruz" varsayar; derin basamaklarda
gercek dolum orani cok daha dusuk olabilir. Eger v3 ILK 30 PENCEREDE
ortalama < 2.0 pay/pencere doldurursa (v2'de ~9 pay/pencere gozlendi),
derin basamaklar pratikte DOLMUYOR demektir: v3 geri alinir ve ara bir
izgara (DERIN-A [.26 .22 .18 .14 .10 .06]) denenir. Bu kosul SIMDI yaziliyor.
