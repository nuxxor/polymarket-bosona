#!/usr/bin/env python3
"""MARKOUT v2 — 09-18 PRO denetiminin bes bulgusu duzeltildi.

v1'in kusurlari ve buradaki karsiliklari:
 1) v1 girisi yoklama-3sn, cikisi yoklama+5sn aliyordu -> etiket "5 sn" ama olculen
    8 sn. v2: TEK ufuk, dolum anindan ileri. Dolum ani = 'dolum' olayinin utc_ms'i
    (borsa eslesme ani DEGIL; ikisi arasindaki gecikme ayrica RAPORLANIR, gizlenmez).
 2) v1'de 8sn faz sinirlari 16:20-17:15 sabitti, gercek donem 16:10-16:55 ->
    ~16 dolum yanlis gruba yaziliyordu. v2: faz sinirlari SURUM olaylarindan
    ve gercek YENILEME_ARA degisimlerinden turetilir, elle yazilmaz.
 3) v1 statistics.mean ile OLAY basina ortalama aliyordu. v2: MIKTAR AGIRLIKLI.
 4) v1 bosona'nin +2.10/-0.69'unu sabit metin olarak basiyordu. v2: bosona AYNI
    kodla, ayni ufukla, ayni mid tanimiyla yeniden hesaplanir; hesaplanamazsa
    "YOK" yazar, eski sayi tekrarlanmaz.
 5) v1'in mid_at'i son gorulen fiyati yas siniri olmadan tasiyordu. v2: MAX_YAS
    siniri var; disinda kalan gozlem ATILIR ve kac tane atildigi raporlanir.
"""
import json,gzip,glob,sys,time,collections,statistics as ist,random

MAX_YAS=3.0          # mid gozlemi bu kadar saniyeden eskiyse KULLANILMAZ
UFUK=(1,3,5,10)      # dolum aninden itibaren saniye

def tape_yukle(desen='data/tape/tape_20260918_*.jsonl.gz',bas=None,bit=None):
    """asset -> [(ms, mid)] artan. price_change olaylarindan best_bid/ask."""
    ser=collections.defaultdict(list)
    for f in sorted(glob.glob(desen)):
        try:
            with gzip.open(f,'rt') as fh:
                for ln in fh:
                    if '"price_change"' not in ln: continue
                    try: d=json.loads(ln)
                    except Exception: continue
                    p=d.get('p') or {}
                    ms=d.get('src')
                    if ms is None: continue
                    if bas and ms<bas: continue
                    if bit and ms>bit: continue
                    for c in p.get('price_changes') or []:
                        bb,ba=c.get('best_bid'),c.get('best_ask')
                        if not bb or not ba: continue
                        try: m=(float(bb)+float(ba))/2.0
                        except Exception: continue
                        ser[c['asset_id']].append((ms,m))
        except EOFError: pass
    for a in ser: ser[a].sort()
    return ser

def mid_at(ser,a,ms):
    """ms anindaki mid; en yakin ONCEKI gozlem MAX_YAS icindeyse dondurur."""
    L=ser.get(a)
    if not L: return None
    lo,hi=0,len(L)-1; en=None
    while lo<=hi:
        o=(lo+hi)//2
        if L[o][0]<=ms: en=L[o]; lo=o+1
        else: hi=o-1
    if en is None: return None
    if (ms-en[0])/1000.0>MAX_YAS: return None
    return en[1]

def olc(dolumlar,ser,ad):
    """dolumlar: [(asset, ms, fiyat, pay)] -> miktar agirlikli markout tablosu."""
    if not dolumlar: print(f"  {ad}: dolum yok"); return None
    sat={}; atilan=0; kullanilan=0; toplam_pay=0.0
    giris_num=giris_pay=0.0
    for a,ms,px,pay in dolumlar:
        m0=mid_at(ser,a,ms)
        if m0 is None: atilan+=1; continue
        kullanilan+=1; toplam_pay+=pay
        giris_num+=(m0-px)*pay; giris_pay+=pay
        for u in UFUK:
            m1=mid_at(ser,a,ms+u*1000)
            if m1 is None: continue
            s=sat.setdefault(u,[0.0,0.0])
            s[0]+=(m1-m0)*pay; s[1]+=pay
    if not giris_pay: print(f"  {ad}: kullanilabilir gozlem yok ({atilan} atildi)"); return None
    g=100*giris_num/giris_pay
    print(f"  {ad}: {kullanilan} dolum / {toplam_pay:.0f} pay kullanildi, {atilan} atildi (mid >{MAX_YAS}sn bayat)")
    print(f"     GIRIS (dolum anindaki mid - odedigimiz, + = ucuz aldik): {g:+.2f} kr/pay")
    for u in UFUK:
        if u not in sat or sat[u][1]<=0: print(f"     +{u:>2} sn markout:   veri yok"); continue
        mo=100*sat[u][0]/sat[u][1]
        print(f"     +{u:>2} sn markout: {mo:+6.2f} kr/pay  ->  NET {g+mo:+6.2f}   (agirlik {sat[u][1]:.0f} pay)")
    return g

def bizim_dolumlar(log):
    """LOG'daki 'dolum' olaylari + asset eslemesi. pay AGIRLIKLI, olay basina degil."""
    k=[json.loads(l) for l in open(log) if l.strip().startswith('{')]
    # asset haritasi: pencere olaylarindaki token kimlikleri
    harita={}
    for x in k:
        if x['k']=='pencere' and x.get('tokens'): harita[x['S']]=x['tokens']
    try:   # gecmis loglar token tasimiyor -> disaridan harita
        import os
        hp='/tmp/claude-1000/-home-taygun-Masa-st--polymarket/b4197893-bd19-4ee9-9e9a-ddd5e06151af/scratchpad/asset_harita.json'
        if os.path.exists(hp):
            for a,b in json.load(open(hp)).items(): harita.setdefault(int(a),b)
    except Exception as e: print("harita yuklenemedi",e)
    out=[]; eksik=0
    for x in k:
        if x['k']!='dolum': continue
        t=harita.get(x.get('S'))
        if not t: eksik+=1; continue
        out.append((t[x['oi']],x['utc_ms'],x['p'],x.get('yeni',0.0)))
    return out,eksik,k

if __name__=='__main__':
    LOG=sys.argv[1] if len(sys.argv)>1 else 'data/analysis/pm_merdiven_ab_20260918_v5/LOG_ab.jsonl'
    dol,eksik,k=bizim_dolumlar(LOG)
    print(f"LOG dolum olayi: {len(dol)+eksik} | asset eslesen: {len(dol)} | eslesmeyen: {eksik}")
    if eksik: print("  UYARI: asset haritasi eksik -> bu dolumlar OLCULEMEZ (v1 bunlari sessizce atiyordu)")
    if not dol: sys.exit("olculebilir dolum yok")
    bas=min(x[1] for x in dol)-20000; bit=max(x[1] for x in dol)+20000
    print("tape yukleniyor...")
    ser=tape_yukle(bas=bas,bit=bit)
    print(f"tape asset: {len(ser)}\n")
    print("### BIZ")
    olc(dol,ser,"tum dolumlar")
