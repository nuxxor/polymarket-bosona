# G1 — süre sınırı olmadan operatör başlangıcı

```bash
bash "/home/taygun/Masaüstü/polymarket-bosona/londra_g_sinirsiz_baslat.sh"
```

Aynı G1 politikası, 5 pay, yeni başlangıçtan $10 zarar kesici. Önceki
+$9,206315 muhasebede kalır. Başlangıçta hesap yeniden mutabıklaştırılır;
son kontrolde anchor −6,028580 ve buna göre kesici −16,028580 olurdu.
Bu toplam geçmiş PnL tabanıdır; yeni koşunun kaybı anchor'a göre ölçülür.
Sabit bitiş saati yok; kâr zirvesinden kayan stop değildir.

Operatör komutu öncesi hesap ve iki kayıtçı kontrol edilir; bot bu hazırlıkta
canlı başlatılmadı. RUN işareti tekrar bütçe açılmasını engeller. Otomatik
restart yok. Strateji politika hash'i önceki pilotla birebir aynı.

Kayıtçılar A/B ayrı süreçte, 15dk parçalar ve ilk B'de ek5dk ile
piyasa listesini yeniler. gzip level1; eski kayıtlar silinmez. İki kayıtçı
başlangıçta zorunlu, çalışırken en az biri güncel olmalı. Disk2GiB rezervi,
belirsiz muhasebe veya veri arızası botu durdurabilir. Süresiz çalışma,
fiziksel disk veya API geçmiş sınırının kalkması demek değildir.

Durdurma (normal emir kapatma yolu):
```bash
ssh -T -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -i "/home/taygun/İndirilenler/polymarket-test-key2.pem" ubuntu@18.135.99.14 'touch /home/ubuntu/polymarket-bosona-g-continuous/bot/STOP_G'
```

Dört test grubu, hedefli Ruff/syntax, sahte SSH, Londra hesap GET,
120s gerçek kuru koşu, çift kayıtçı başlangıç/rotasyon ve gzip okuma geçti.
Kanıt: validation/proof.tar.gz. Eski pilotun kaynak/state/bütçesi korunur.

## İlk başlangıç sonrası düzeltme

Operatör13:33TR'de başlattı.13:42'de pozisyon API'sinin HTTP hatası,
`maruziyet_teyitsiz` güvenlik kapanışını tetikledi. Süre/kesici kapanışı değil.
Aynı kaynak paketinin düzeltmesinde yalnız ağ hataları üç kez denenir;
ilk hata yeni teklifi kapatır ve mevcut G iptal yolunu devreye sokar.
Geçerli hesap ve mutabakat dönmeden teklif açılmaz. Kalıcı hata yine durdurur.

Aynı başlatma komutu artık RUN mevcutsa `--resume` kullanır. İlk bütçenin
anchor/cutoff/id ve RUN dosyaları aynen korunur; eski state arşivlenir,
yalnız yeni salt-okunur mutabakat sonucu devam state'ine aktarılır.
Kayıtçıların bitmiş parçaları silinmeden arşivlenir. Otomatik restart yok.

Kayıt kullanılabilirliği eski G1 gibi ayrı kapıdır; ayrıştırılmamış mesajlar
olay tamlığı hesabında eksik sayılır ve güvenli hata sınıfıyla kaydedilir.
Süreç/yazma/PONG/kuyruk taşması/disk kapıları korunur. Yeni gerçek testte
iki kayıtçıda birer kamu kopuşu ve birer enum reddi gözlendi;70/70 sağlık
örneği geçerliydi. Bu sıfır veri kaybı değildir. Eski kayıtları koruyan gerçek
kayıtçı yeniden başlangıcı ayrıca test edildi.

Son doğrulama13:53TR: önceki ilk30dk+$9,206315ayrı; yenioturumiki
pencere−$0,3992. Açıkemir/risk0. Orijinal10USD bütçeden kalan yaklaşık9,60USD.
Süre yok; devam komutu yeni10açmaz. Kaynak1c46c9bb8070; politika aynı.
Kanıt:validation/fix2_proof.tar.gz. Paket son kontrolde parkta.
