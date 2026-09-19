p='ab.py'; s=open(p,encoding='utf-8').read()
hedef="    ok.append(('tavan degismedi', PX_TAVAN_MAKER==0.40, PX_TAVAN_MAKER))"
yeni = hedef + "\n" + "\n".join([
"    # 09-19 15:15 CANLI HATA: kol B sabit derin izgaraya cevrildi ama yenile()",
"    # hala mid takip ediyordu -> B'nin 12 derin emrini silip mid'e Down@0.40",
"    # koydu ve 0.40'tan 5 pay doldu. Iki kolun tek farki IZGARA olmali.",
"    _w={'kol':'B','emir':[],'per':300,'son_yenileme':0.0}",
"    _once=dict(_w)",
"    yenile(('btc',int(time.time())-30),_w)",
"    ok.append(('yenile() KAPALI: cagrilinca hicbir sey yapmaz',",
"               _w=={'kol':'B','emir':[],'per':300,'son_yenileme':0.0},",
"               'pencere sozlugu degismedi' if _w==_once else _w))",
])
assert hedef in s
s=s.replace(hedef,yeni,1)
open(p,'w',encoding='utf-8').write(s)
print('test eklendi')
