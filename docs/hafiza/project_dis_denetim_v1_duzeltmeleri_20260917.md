---
name: project-dis-denetim-v1-duzeltmeleri-20260917
description: Dis denetim canli bot analizimde UC BUYUK HATA buldu, ucu de DOGRULANDI — "ters secim" bulgusu ve v2'nin dayanagi CURUDU
metadata:
  type: project
---

ChatGPT/Astra, `polymarket_bot_20260917.zip` paketini denetledi. Iddialarini
loglardan TEK TEK dogruladim; ucu de DOGRU cikti.

## 1) "TERS SECIM -22,59" BULGUSU CURUDU — GERI CEKILDI
Tek taraf biten 11 pencerenin **9'u BASTAN tek tarafliydi**: karsi tokenin iki
emri de post-only reddedilmis, bot kabul edilen taraftaki emirleri ACIK TUTMUS.
Yani cıplak yonlu pozisyon almisiz. Sadece 2 pencere gercek "iki taraf kabul,
biri dolmadi" vakasi.
```
S=1789658100 kabul=[0] red=[(1,0.37),(1,0.36)]  -> tek tarafli CUNKU RED
S=1789663200 kabul=[1] red=[(0,0.36),(0,0.35)]  -> ayni
... 9 tanesi boyle
```
=> Olctugum sey ters secim DEGIL, **bozuk kotasyon kurulumu**.

## 2) SEVIYE TABLOSU YANLIS SIRALANMIS — SONUC TERS DONUYOR
`b[:SEVIYE]` defterde VAR OLAN ilk iki seviyeyi aliyor (bitisik tik degil), ve
red edilen emirler cikinca kalanlar YENIDEN siralaniyor.
| siralama | seviye 0 | seviye 1 |
|---|---|---|
| yalniz kabul edilenler (BENIM RAPORUM) | -4,25 | -1,64 |
| **ORIJINAL plan (redler dahil, DOGRUSU)** | **+0,11** | **-6,04** |
**Dokunus IYIYDI, bir tik alt KOTUYDU.** Ben tersini raporladim ve
**v2'yi (daha derine koy) bu hatali tabloya dayandirdim.** v2 kotu gitmesi
sasirtici degil.

## 3) "CIFT" GRUBU KIRLI — 10/5 PENCERELER
21 iki-tarafli pencerenin 7'sinde miktarlar esit degil (10/5). Dogru ayrim
m=min(q_Up,q_Down):
| | token-pay | kr/pay |
|---|---|---|
| ESLESMIS | 340 | **+1,08** |
| ESLESMEMIS | 145 | **-12,78** |
| toplam | 485 | -3,06 |
Benim "cift +2,67 / tek taraf -22,59" ayrimim yanlisti.

## KOD HATALARI (denetimden, dogrulandi)
- `iptal()` yanit icerigini KONTROL ETMEDEN True donuyor; `not_canceled`
  yanitinda emir acik kalabilir ama yerelde 'kapali' yazilir ve rezerv sifirlanir.
- `koy()` TUM istisnalari kesin RED sayiyor; POST yaniti kaybolursa emir
  borsada CANLI olabilir -> UNKNOWN durumu ve acik-emir mutabakati gerekli.
- Risk serbest birakma ile PnL guncellemesi AYRI anlarda: cozulen pencere riski
  aninda sifirlanir, kayip 120 sn sonraki mutabakata kadar butcede gorunmez.
- STATE.json yaziliyor ama YUKLENMIYOR; yeniden baslatmada PnL/pencereler sifir.
- Dolum orani paydasi: 103 dolum OLAYI = 101 ayri emir -> %95,4 degil **%93,5**.
- Tek-yazici taramasi 'ladder.py' adini ariyor; farkli dosya adiyla calisan
  ikinci surec yakalanmaz. Atomik kilit degil.

## SONUC — PLAN DEGISTI
v2'nin dayanagi (derinlik) yanlis tablodan geldi. Dogru 1. oncelik:
**pencere acilisinda IKI TARAFIN da kabul edildigini garanti eden durum makinesi.**
Bir taraf reddedilirse kabul edilenleri GERI CEK, ciplak yon alma.
Sonra: emir/islem muhasebesi (order_id, ACK zamanlari, kismi dolum),
sonra tek-taraf yonetimi, en son fiyat/derinlik deneyleri.

**DERS: kendi olcum kodumu da en az strateji kadar denetlemeliyim.
Bugun 5. kez kucuk-ornek/olcum hatasi; bu sefer disaridan yakalandi.**

## DENETIMIN UC NUANSI — UCU DE DOGRULANDI (onemli)
1. **Redleri duzeltmek KARI GARANTI ETMEZ.** En az bir red olan 15 pencere
   -2,46 kr/pay; hic red olmayan 17 pencere **-3,40**. Yani redli pencereler
   daha KOTU DEGIL. Red duzeltmesi OLCUMU temizler, kaybi aciklamaz.
2. **t=120 cikisi KARLI cifti bozardi.** v2 S=1789669200: t=120'de yalniz Up
   vardi, Down 165 ve 173. saniyede doldu, final **+0,70$**. Kor t=120 cikisi
   bu pencereyi kesip zarari kilitlerdi. "Sonunda tek taraf kalanlar" gelecege
   bagli bir secim; onceden bilinemez.
3. **v2'nin kapanis riski gercekten eslesmis ciftti.** S=1789669800 ve
   S=1789670100: her birinde 10 Up + 10 Down, maliyet 9,30 ve 9,00, tam-set
   degeri 10,00 -> brut kilitli **+1,70$**. Dort cozulen pencerenin -24,44'u
   alti pencerenin ekonomisini TEMSIL ETMIYOR.

## GERCEK DURUM
Uc baslik bulgumun ucu de yanlisti. Ama denetim ayni zamanda gosteriyor ki
**bariz hatayi (red) duzeltmek de tek basina kar getirmiyor.** Yani elimizde
kanitlanmis bir kenar YOK; olcum duzenegimizde maddi hatalar VARDI ve simdi
tespit edildi.

## V3 ONCELIK SIRASI (denetimin sirasi, kabul edildi)
1. Once HATA duzeltmeleri — her karsilastirma kolunda bulunmali:
   teyitli iptal (canceled/not_canceled ayri), POST kaybinda UNKNOWN durumu,
   risk serbest birakma ile PnL yazmanin AYNI ana baglanmasi, STATE yukleme,
   order_id + ACK/snapshot zamanlari + orijinal seviye kaydi, gercek tick_size.
2. Iki tarafli kabul durum makinesi (bir taraf reddedilirse kabul edilenleri
   teyitli geri cek, ciplak yon alma).
3. Ilk dolumdan itibaren miktar yonetimi.
4. t=120 KONTROLLU DENEY KOLU olarak (varsayilan cozum DEGIL) — sifir dolumlu
   ve sonradan eslesen pencereler dahil.
5. Fiyat/kuyruk kalitesini MARKOUT ile olc (1/5/30 sn sonraki referans - alis).
6. Merge sermaye yonetimi icin.
Deney birimi PENCERE, emir veya pay degil. 11 pencere 110 bagimsiz sonuc degildir.
