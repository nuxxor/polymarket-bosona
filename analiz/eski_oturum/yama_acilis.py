p='ab.py'; s=open(p,encoding='utf-8').read()

eski = """    if LIVE:
        a=acik_emirler()
        if a is None or a:
            log('BASLAMIYOR',sebep='acik emir var/okunamadi'); return
    if acilis_maruziyeti() is None:
        log('BASLAMIYOR',sebep='acilis maruziyeti okunamadi (fail-closed)'); return
    state_yukle()
    gorulen=set((s,int(S)) for s,S in st.get('pencereler',[]))
    t=mutabakat()
    if LIVE and t is None:
        log('BASLAMIYOR',sebep='baslangic mutabakati eksik'); return"""

yeni = '''    # --- ACILIS KAPILARI: SINIRLI TEKRAR (09-19 15:25) ----------------------
    # HATA: uc kapi da tek denemede pes ediyordu. data-api 999 (hiz limiti)
    # GECICI; 09-19 15:19-15:23 arasi 4 kez ust uste BASLAMIYOR verdi ve bot
    # 4 dakika kapali kaldi, 15:20 penceresi kacti.
    # EMNIYET BOZULMADI: yalnizca kapi GERCEKTEN GECERSE baslar. Denemeler
    # bitince hala gecmiyorsa BASLAMIYOR -- "denedim olmadi, yine de gireyim"
    # yolu YOK.
    def _kapi(ad,fn,gecerli):
        for i in range(ACILIS_DENEME):
            v=fn()
            if gecerli(v): return True
            if i+1<ACILIS_DENEME:
                b=ACILIS_BEKLE*(i+1)
                log('acilis_tekrar',kapi=ad,deneme=i+1,bekle=b); time.sleep(b)
        log('BASLAMIYOR',sebep=ad,deneme=ACILIS_DENEME); return False

    if LIVE:
        if not _kapi('acik emir var/okunamadi', acik_emirler,
                     lambda a: a is not None and not a): return
    if not _kapi('acilis maruziyeti okunamadi (fail-closed)',
                 acilis_maruziyeti, lambda v: v is not None): return
    state_yukle()
    gorulen=set((s,int(S)) for s,S in st.get('pencereler',[]))
    if not _kapi('baslangic mutabakati eksik', mutabakat,
                 lambda t: (t is not None) or (not LIVE)): return'''

assert eski in s, 'acilis blogu bulunamadi'
s=s.replace(eski,yeni,1)

# parametreler
anc="MUTABAKAT_ARA=260.0"
assert anc in s
s=s.replace(anc, anc+"\nACILIS_DENEME=6         # acilis kapilari icin azami deneme (999 gecicidir)\n"
                     "ACILIS_BEKLE=5.0        # bekleme: 5,10,15,20,25 sn (toplam ~75 sn)",1)
open(p,'w',encoding='utf-8').write(s)
print('acilis tekrari eklendi')
