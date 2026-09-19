# ON KAYIT — KOL C "TAZE SEVIYE" (2026-09-19 19:55Z, koddan ONCE yazildi)

## Hipotez (A1 olcumunden, 15:15Z-19:36Z, 33.139 maker dolumu)
Maker dolumlarinin %80'i KISMI: seviye supurulmuyor, kuyrugun ONUNDEKI doluyor.
bosona 41 dolumda %88 kismi, onunde medyan 578 pay, seviye yasi medyan 3,2 sn (p25 0,3 sn),
fiyat medyan 0,47, t medyan 83 sn -> TAZE olusan dokunusa-yakin seviyede ILK emir onun.
Biz: 21 dolum, seviye yasi medyan 298 sn, fiyat 0,20 -> eski/derin/ucuz seviyelerde.
HIPOTEZ: "seviyeyi biz olusturursak (spread icine 1 tik) ya da taze/ince seviyeye aninda
katilirsak, kuyruk onunde kismi dolum aliriz ve dolum kalitesi (kr/pay) A/B'den iyi olur."

## Kural (degistirilmez; degisiklik = yeni on kayit)
- Atama: pencere basina tohumlu rastgele: C %50, kalan A/B esit (%25/%25). A ve B KONTROL.
- C penceresinde baslangic izgarasi YOK. Websocket (CLOB market kanali) ile iki token'in
  BID seviyeleri canli tutulur. Her taraf icin hedef:
    spread >= 2 tik  -> bb + 1 tik (seviyeyi BIZ olustururuz = kuyruk basi garantili)
    spread == 1 tik  -> bb, ANCAK bb seviyesinde <= 30 pay varsa (taze/ince kuyruk)
    aksi halde       -> emir yok
  Fiyat bandi 0,15-0,60. Aktif sure t in [3, 200) sn; t>=200'de tum C emirleri iptal.
  Taraf basina tek acik emir, 5 pay (KLIP). Hedef degisince iptal+yeniden koy;
  taraf basina islemler arasi >= 1 sn; pencere basina en fazla 40 post.
- Risk: TARAF_TAVAN $10/taraf, DENGE_SINIR 10 pay (agir tarafa yeni emir yok; mevcut
  denge_koru da calisir), KESICI -100 degismedi, post-only.
- Maliyet muhasebesi, dolum yoklamasi, cozumleme: mevcut altyapi (w['emir']).

## Olcutler ve kill kosulu (cuzdan-pencere birimi, pencere-bootstrap GA)
- Birincil: C kr/pay vs (A+B) kr/pay, ayni saat diliminde.
- Mekanizma: C dolumlarinin kismi orani ve seviye yasi (bacak_anatomisi.py, BIZ satiri);
  beklenti: kismi >= %80 ve yas medyan < 10 sn. Bu saglanmazsa hipotezin ON KOSULU yok.
- KILL: 60 dolumlu C penceresi sonunda C kr/pay <= (A+B) kr/pay - 2 -> C kapanir.
- Hiz: ayni kural Londra'dan calistirilirsa kismi oran/yas farki = gecikme payi.

## Beklenen zarar profili (durust)
0,45 ustu maker alimlari zincirde ortalama negatif (-2 kr/pay). C bunu BILEREK test eder;
kayip bu banttan gelirse "kuyruk onu" tek basina yetmiyor demektir ve rapor edilir.

## v1.1 (20:42Z, KURU KOSU sonrasi, canli PnL gorulmeden) — kural netlestirmesi
Kuru kosu (20:35Z penceresi): dokunus her 2-3 sn'de bir tik oynuyor; "hedef degisince
iptal+yeniden koy" 100 sn'de 40 postu bitirdi. Ayrica aynali defterde Up@0,50 + Down@0,50
birbirini keser (post-only RED).
- Acik emir, dokunusun EN FAZLA 1 TIK altindaysa yerinde kalir (kuyrugun onundeyiz);
  2+ tik geride kalinca iptal edilir; hedef varsa ve acik emir yoksa yeni emir konur.
- Iki tarafin fiyat toplami >= 1 - tik ise ikinci taraf beklenir (kendi kendini kesme yok).
- Pencere basina post tavani 40 -> 60 (yenileme kurali gevsedigi icin kullanim dusecek).

## v1.2 (20:53Z, KURU KOSU 2 sonrasi) — altyapi, kural degismedi
Kuru kosu 2 (20:50Z, fiyat 60 sn'de 0,50->0,15 coktu): 33 post mesru (hedef surekli 2+ tik kaydi).
Websocket sunucusu "1013 slow consumer" verdi: karar mantigi okuma dongusunun icindeydi.
- Okuyucu ayri is parcacigi (yalniz okur, kilitle defteri gunceller); karar dongusu 0,2 sn'de bir.
- Kural, bant, tavanlar AYNI.

## v2 (22:00Z, 6 canli C penceresi sonrasi; operator onayi) — CIFT ONCELIK
Olcum: 6 pencere +$0,29 (2/6 arti). Dolumlar taze seviyede (yas 3,4 sn, onde 27 pay, %57 kismi)
-> mekanizma on kosulu SAGLANDI. Zarar cift degil, 2:1 tek tarafli maruziyet: dusen taraf iki
seviyede 10 pay doluyor, karsi taraf <=5. Kurulan ciftler kucuk arti kilitledi.
- C_DENGE=5: ilk taraf 1 klipte durur; karsi taraf dolana kadar ayni tarafa yeni emir yok.
- RED nedeni yanit metniyle loglanir (RED_NEDEN). Red orani %50 (22/44) — teshis icin.
- Diger kurallar ayni. KILL kosulu ayni (60 dolumlu C penceresi, C <= A+B - 2).

## v3 (23:00Z, Londra'ya gecis sonrasi; 9 canli C penceresi) — TAMAMLAYICI BACAK TAVANI + OKUYUCU
Gozlem: savrulmali pencerelerde iki taraf da kendi tepesinde doluyor -> ciftler 1,00-1,13 (kilitli zarar).
Ornek 22:25Z: 0,51+0,56 / 0,59+0,54 / 0,58+0,42 (1,07/1,13/1,00), 22:55Z: 0,97/1,00/1,00.
bosona zincir verisi: cift <0,85 +10,0 kr/pay, 0,85-0,95 +2,45, 0,95-1,00 +0,83, >1,00 negatif.
- C_CIFT_TAVAN=0,98: karsi taraf DOLDUYSA (dolan_diger > dolan_ben) bu bacak "tamamlayici"dir:
  hedef = min(taze hedef, 0,98 - karsi tarafin ort dolum fiyati). Bant altina duserse emir yok.
  Ilk bacak (dengedeyken) kural AYNI (taze seviye). Yani: ilk bacak taze seviyede, ikinci bacak ancak karli cift verecek fiyatta.
- Okuyucu: 'book' anlik goruntusu asset basina en fazla 1/sn islenir, JSON cozumu kilit disinda
  (Londra'da da her pencere basinda "1013 slow consumer" kopmasi oluyordu: 1-2 sn kor nokta).
- Degismeyen: bant 0,15-0,60, C_DENGE 5, post tavani, KILL kosulu.
Beklenti: cift kurulma sikligi DUSER, kurulan ciftlerin toplami <=0,98 olur; tek tarafli maruziyet ayni kalir.
