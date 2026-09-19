---
name: project-btc5m-maker-kapanis-20260919
description: BTC 5dk maker kulvarı PARK — sinyal çözüldü (Chainlink marjı ≥3bps, 1006 pencerede 0 hata) ama arzın tamamı 24.000 paylık kuyruğun önündekine gidiyor; bağlayıcı kısıt sermaye değil KUYRUK ÖNCELİĞİ
metadata:
  type: project
---

# BTC 5dk MAKER KULVARI — ⚠️ PARK KARARI GERİ ÇEKİLDİ (2026-09-19)

> **ÜSTÜ ÇİZİLDİ.** Operatör park kararını reddetti ve haklı çıktı: aynı zincir
> defterinde BİZİM KLİP BOYUMUZDA kazanan 132 cüzdan var (bkz
> [[project-kucuk-klipli-kazananlar-20260919]]). "Kenar boy/kuyruk önceliği ister"
> sonucu çürüdü. Aşağıdaki ölçümler GEÇERLİ (bizim uygulamalarımızın neden
> başarısız olduğunu doğru anlatıyorlar), ama KULVAR HÜKMÜ geçersiz.

İki bağımsız inceleme (PRO denetimi + Fable çok-ajanlı tur, 280 ajan) ve kendi
ölçümlerim aynı yere çıktı. Kulvar kapanmadı, **park edildi**; tetikler altta.

## NE ÇÖZÜLDÜ
1. **Yön çözüldü.** Chainlink TWAP-60 marjı ≥3 bps kapısı: t=270'te
   **1.006 pencerede 0 hata** (kapısız hata %2,7). Sonuç pencere bitmeden bilinebiliyor.
2. **Arz ölçüldü.** Kilitli tarafta 0,99'da pencere başına **130-350 pay** satılıyor.
3. **Erişimin neden olmadığı ölçüldü.** O arzın önünde **medyan 24.000 pay** var.
   Defterdeki en büyük cüzdan (4,1M pay, +0,56 kr/pay, %100 isabet) kuyruğun başı.
   İyimser kuyrukta 0,99 bid pencerelerin %74'ünde dolar (+1,00 kr/pay, %100 isabet);
   **pesimist (gerçekçi) kuyrukta %1,2.**

## BAĞLAYICI KISIT SERMAYE DEĞİL
Operatöre "3-4 bin dolar ihtimali %35-40'a çıkarır" dedim, **geri çektim**.
24.000 paylık kuyruğun arkasında $4k ile $540 aynı yerde. Kuyruk önceliği parayla
değil, **seviye açıldığı anda orada olmakla** alınır → WS emir yolu + <150 ms.
Bu bir altyapı sorusu, bahis değil.

## ÖLEN KULVARLAR (bu turda, kanıtla)
- **Derin merdiven (kol A):** 0,20-0,40 bandında SABIT BOYLA giren birinin
  gerçeği **−5,28 kr/pay** (4.430 pencere, pencere-eşit ağırlık). A'nın gerçekleşen
  −5,37'si bununla birebir. Bozuk değil; bandın gerçeği bu.
- **Mid takipli (kol B):** hacminin %39-53'ü ≥0,45'te, orada ortalama maker bile
  kaybediyor (0,60-0,70 −1,97 GA[−3,47,−0,59]; 0,70-0,80 −2,33).
- **Rejim kapısı:** hacim çeyreği önden bilinemiyor (Spearman: önceki hacim −0,004,
  önceki salınım +0,026, saat +0,008); 4 kapının OOS'u da negatif. Üst çeyreğin
  %88'i gidiş-dönüş penceresi → öngörülemeyen eksenin vekili.
- **Geç-favori TAKER:** 4 ay/33.509 gözlem, isabet = ask fiyatı.
- **Boy:** 1.526-2.544 pencere gerek; $40 tavan 1-2 pencere alır.
- **Hızlı iptal:** kalabalık kuralı dolumların %94'ünden önce tetikleniyor —
  stratejiyi düzeltmiyor, kaldırıyor.

## BENİM ÇÜRÜYEN 6 HİPOTEZİM (hepsi kendi verimle, hiçbiri canlıya girmedi)
1. "Ölçekli ızgara" — sakin pencerede A DAHA ÇOK doluyor, tersi
2. "Çift tavanı 1,00" — karşı-olgusal: 12 iyi/15 kötü, medyan 0, GA[−37,+78]
3. "Ucuza tamamlama" — 0,85 tavanında 0/32 pencere uygun
4. "bosona aynı pencerede hem derin hem yakın" — hacminin %2,6'sı derin
5. "Giriş −1,38'de kaybediyoruz" — poll keşif zamanı artefaktı; gerçek +0,16 GA[−0,02,+0,35]
6. "Ucuz bantta kenar var (+1,85)" — PAY-ağırlıklı; pencere-eşit −5,28

## TETİKLER (bunlar olursa yeniden aç)
- WS tabanlı <150 ms emir/iptal yolu çalışır hale gelirse → 0,99 erişim ölçümü tekrarlanır
- BTC **15dk** ailesinde bosona'nın geometrisi (mid−1,6 kr, büyük boy) gölgede
  200 dolum üretirse — 15m'de kenarı +3,21 GA[+0,51,+5,87] (2 gün, kamu akışı)
- Likidite ödülü BTC 5m'de fonlanırsa (`clobRewards != null`)
- Kuyruk önünde duran 4,1M paylık cüzdan çekilirse

İlgili: [[project-takeronly-hatasi-20260918]], [[project-rejim-kapisi-20260918]],
[[project-cift-ekonomisi-a-vs-b-20260918]], [[project-olcek-kaniti-20260918]]
