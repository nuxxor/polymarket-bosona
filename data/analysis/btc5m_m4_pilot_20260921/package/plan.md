# M4 — 30 dakika / 5 pay / $10 olcum pilotu
M3 emir zaman kaydi mevcut F politikasi ustunde olculur. Kar arastirmasi
veya Bosona kopyasi dogrulanmis sayilmaz. Eski F dizini/state/butce korunur.
Park: STOP_F. m4.py varsayilan salt okunur SDK + muhasebe/feed onkontrolu.
Gercek emir baslatma yalniz operator: m4.py --live. Bir kez kullanilabilir,
sure/butce restart ile sifirlanamaz. 30dk/$10 kesici ve eski risk iptalleri.
Asistan --live calistirmaz. Kabul: hash/test + gercek salt-okunur onkontrol
ve kamu WS karar dongusu. Operator LIVE sonrasinda saat/oid/miktar ve
dolmayan emirlerin tamamlanmis omru incelenir; once basari iddiasi yok.

M4 hesap onkontrolunde ilk500 pozisyonda kesilme bulundu. Ortak maruziyet
okuyucusu offset ile tum sayfalari, dust ve arsiv aktifleri dahil okur.
Eksik/bozuk/tekrarli sayfa risk=0 degildir; periyodik kontrol basarisizsa
normal durus/iptal yoluna girilir. F politikasi/butcesi degismedi.
