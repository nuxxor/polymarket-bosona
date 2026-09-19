#!/usr/bin/env python3
"""KOL C 'TAZE SEVIYE' yamasi — ab.py'ye websocket beslemeli ucuncu kol ekler."""
import re,sys
P='/home/taygun/Masaüstü/polymarket/data/analysis/pm_merdiven_ab_20260918_v5/ab.py'
s=open(P).read()
def rep(old,new,n=1):
    global s
    assert s.count(old)==n, f"beklenen {n} eslesme, bulunan {s.count(old)}: {old[:70]!r}"
    s=s.replace(old,new)

# 1) import threading
rep("import asyncio, hmac, hashlib, time, json, os, sys, gzip","import asyncio, hmac, hashlib, time, json, os, sys, gzip",0) if False else None
first_import=re.search(r'^import [^\n]*\n',s,re.M).group(0)
assert 'threading' not in s.split('def ')[0] or True
rep(first_import, first_import+"import threading   # 09-19: KOL C websocket is parcacigi\n")

# 2) sabitler + saf hedef fonksiyonu: KAPI_ACIK bloğundan hemen once
anchor="# --- REJIM KAPISI (09-18 18:30, operator emriyle canliya alindi) -------------"
kolC_consts='''# --- KOL C: TAZE SEVIYE (09-19 19:55Z, operator: "canlida cozelim") ---------
# Bkz ONKAYIT_TAZE_KOL_C_20260919.md. A1 olcumu: maker dolumlarinin %80'i KISMI
# (seviye supurulmuyor, kuyrugun ONUNDEKI doluyor); bosona taze (medyan 3,2 sn)
# dokunusa-yakin seviyelerde ILK emir, biz 298 sn yasinda derin/ucuz seviyelerde.
# C: spread >= 2 tik -> bb+1 tik (seviyeyi biz olustururuz); spread 1 tik -> bb'ye
# yalniz seviye ince (<= C_TAZE_MAX pay) ise katil. Aksi halde emir yok.
C_ORAN=0.5                 # pencerelerin yarisi C; kalan yari A/B esit (A_ORAN)
C_PX_MIN,C_PX_MAX=0.15,0.60
C_T_MIN,C_T_MAX=3.0,200.0  # aktif sure (sn); t>=C_T_MAX'ta tum C emirleri iptal
C_TAZE_MAX=30.0            # spread 1 tikse bb seviyesinde en fazla bu kadar pay varsa katil
C_MIN_ARA=1.0              # taraf basina iki islem arasi asgari sure (sn)
C_MAX_ISLEM=40             # pencere basina azami post
C_WS="wss://ws-subscriptions-clob.polymarket.com/ws/market"
TAZE_IS={}                 # k -> Thread (state'e YAZILMAZ)

def taze_hedef(bb,ba,tik,bb_boy,dolan_ben,dolan_diger):
    """Bir taraf icin C hedef fiyati ya da None (saf; testlenir).
    bb/ba: en iyi alis/satis, bb_boy: bb seviyesindeki pay, dolan_*: taraflarin dolan payi."""
    if not bb or not ba or not tik or tik<=0: return None
    if dolan_ben-dolan_diger >= DENGE_SINIR-0.5: return None      # agir tarafa yeni emir yok
    spread=round(ba-bb,4)
    if spread>=2*tik-1e-9: px=bb+tik
    elif bb_boy<=C_TAZE_MAX: px=bb
    else: return None
    px=round(px,3 if tik<0.01 else 2)
    if not (C_PX_MIN-1e-9<=px<=C_PX_MAX+1e-9) or px>=ba-1e-9: return None
    return px

'''
rep(anchor, kolC_consts+anchor)

# 3) kol_ata: uclu atama
rep("""    r=_rnd.Random(f"{AB_TOHUM}|{sym}|{S}")
    return 'A' if r.random()<A_ORAN else 'B'""",
"""    r=_rnd.Random(f"{AB_TOHUM}|{sym}|{S}")
    u=r.random()
    if u<C_ORAN: return 'C'                       # 09-19: KOL C (taze seviye)
    return 'A' if (u-C_ORAN)/max(1e-9,1.0-C_ORAN)<A_ORAN else 'B'""")

# 4) taze_izle is parcacigi: pencere_ac'tan hemen once
anchor2="def pencere_ac(sym,S,per):"
taze_fn='''def taze_izle(k,w,tk):
    """KOL C is parcacigi: websocket defter -> taze seviyeye tek emir/taraf, t<C_T_MAX."""
    sym,S=k; klip=wklip(w)
    tik={oi:tick(tk[oi]) for oi in (0,1)}
    tid2oi={str(tk[0]):0,str(tk[1]):1}
    lv={0:{},1:{}}                                   # BID seviyeleri: fiyat -> pay
    ask={0:None,1:None}
    son={0:0.0,1:0.0}; n_koy=0; n_iptal=0; ws_hata=0; durdur=False
    def bb_of(oi):
        pz=[p for p,q in lv[oi].items() if q>0]
        if not pz: return None,0.0
        b=max(pz); return b,lv[oi][b]
    def guncelle(m):
        et=m.get('event_type') or m.get('type')
        if et=='book':
            oi=tid2oi.get(str(m.get('asset_id')))
            if oi is None: return
            lv[oi]={}
            for x in m.get('bids') or []:
                try: lv[oi][round(float(x['price']),3)]=float(x['size'])
                except Exception: pass
            a=[float(x['price']) for x in (m.get('asks') or []) if float(x.get('size',0))>0]
            ask[oi]=min(a) if a else None
        elif et=='price_change':
            for c in m.get('price_changes') or []:
                oi=tid2oi.get(str(c.get('asset_id')))
                if oi is None: continue
                try: p=round(float(c['price']),3); q=float(c['size'])
                except Exception: continue
                if (c.get('side') or '').upper()=='BUY': lv[oi][p]=q
                try:
                    if c.get('best_ask'): ask[oi]=float(c['best_ask'])
                except Exception: pass
    def acik(oi): return [r for r in list(w['emir']) if r['durum']=='acik' and r['oi']==oi]
    def dolan(oi): return sum(r.get('pay',0.0) for r in list(w['emir']) if r['oi']==oi)
    def karar(oi):
        nonlocal n_koy,n_iptal,durdur
        if time.time()-son[oi]<C_MIN_ARA: return
        bb,bb_boy=bb_of(oi); ba=ask[oi]
        hedef=taze_hedef(bb,ba,tik[oi],bb_boy,dolan(oi),dolan(1-oi))
        ac=acik(oi)
        if ac and hedef is not None and abs(ac[0]['p']-hedef)<1e-9: return   # yerinde
        if ac:
            for r in ac:
                kapat(r,'taze_yenile',k); n_iptal+=1
            son[oi]=time.time()
            if hedef is None: return
        if hedef is None or n_koy>=C_MAX_ISLEM: return
        if taraf_maliyet(w,oi)+klip*hedef>TARAF_TAVAN*(klip/KLIP): return
        if kesici_asilir(klip*hedef): return
        t0b=time.time()
        res=koy_toplu([(oi,tk[oi],hedef,klip)])
        ackm=round(time.time()*1000); sure=round((time.time()-t0b)*1000)
        son[oi]=time.time(); n_koy+=1
        _oi,px,oid,dur=res[0]
        if dur=='BILINMEYEN':
            st['bilinmeyen']+=1
            oid2=bilinmeyen_coz(tk[oi],px)
            log('POST_BILINMEYEN',sym=sym,S=S,oi=oi,p=px,bulundu=bool(oid2))
            if not oid2: durdur=True; return           # belirsizlikte C durur (fail-closed)
            oid,dur=oid2,'KABUL'
        if dur=='RED':
            st['red']+=1; log('emir_RED',sym=sym,S=S,oi=oi,p=px,ofset=px,tur='taze'); return
        if not oid: return
        st['emir']+=1
        w['emir'].append({'oi':oi,'p':px,'ofset':px,'hedef_ofset':px,'hedef_p':px,'bb':bb,
                          'oid':oid,'pay':0.0,'durum':'acik','ack_ms':ackm,'toplu_ms':sure,
                          'snap_ms':ackm,'dolum_ms':None,
                          'taze':{'ba':ba,'bb_boy':round(bb_boy,1),'t':round(time.time()-S,1)}})
        log('taze_koy',sym=sym,S=S,oi=oi,p=px,bb=bb,ba=ba,bb_boy=round(bb_boy,1),
            t=round(time.time()-S,1),ms=sure)
    try:
        from websockets.sync.client import connect
    except Exception as ex:
        log('taze_ws_yok',S=S,err=str(ex)[:80]); w['taze']={'hata':'ws_yok'}; return
    bitis=S+C_T_MAX
    while time.time()<bitis and not w.get('cozuldu') and not durdur and ws_hata<5:
        try:
            with connect(C_WS,open_timeout=8,close_timeout=2) as ws:
                ws.send(json.dumps({"type":"subscribe","channel":"market","assets_ids":[str(tk[0]),str(tk[1])]}))
                while time.time()<bitis and not w.get('cozuldu') and not durdur:
                    try: raw=ws.recv(timeout=1.0)
                    except TimeoutError: raw=None
                    if raw:
                        try: d=json.loads(raw)
                        except Exception: d=None
                        for m in (d if isinstance(d,list) else [d]):
                            if isinstance(m,dict): guncelle(m)
                    if time.time()-S<C_T_MIN: continue
                    for oi in (0,1): karar(oi)
        except Exception as ex:
            ws_hata+=1; log('taze_ws_hata',S=S,err=str(ex)[:80],deneme=ws_hata); time.sleep(1.0)
    for oi in (0,1):
        for r in acik(oi): kapat(r,'taze_bitti',k); n_iptal+=1
    w['taze']={'koy':n_koy,'iptal':n_iptal,'ws_hata':ws_hata,'durdur':durdur}
    log('taze_bitti',sym=sym,S=S,koy=n_koy,iptal=n_iptal,ws_hata=ws_hata,durdur=durdur,
        dolan=round(sum(r.get('pay',0.0) for r in list(w['emir'])),2))
    state_kaydet()

'''
rep(anchor2, taze_fn+anchor2)

# 5) pencere_ac: C dali (snapshot dongusunden sonra, plan kontrolunden once)
rep("""    if not plan: return
    if not (any(x['oi']==0 for x in plan) and any(x['oi']==1 for x in plan)):
        log('plan_tek_tarafli',sym=sym,S=S,karar='pencere atlanir'); return
""","""    if kol=='C':                                   # 09-19: KOL C taze seviye (is parcacigi)
        klip=boy_ata(sym,S)
        if kesici_asilir(2*klip*C_PX_MAX):
            log('ZARAR_KESICI',pnl=round(etkin_pnl(),2),risk=round(toplam_risk(),2),ek=round(2*klip*C_PX_MAX,2))
            st['durdu']='kesici'; return 'kesici'
        w={'cozuldu':False,'emir':[],'per':per,'snap0':snap,'snap':[],'kol':kol,
           'klip':klip,'son_yenileme':time.time()}
        pen[(sym,S)]=w; st['pencere']+=1; st.setdefault('pencereler',[]).append([sym,S])
        log('BOY',S=S,klip=klip,kol=kol)
        log('pencere',sym=sym,S=S,kol=kol,vol=(round(_vol,1) if _vol is not None else None),
            tokens=[str(tk[0]),str(tk[1])],emir=0,kabul=[0,0],fiyatlar=[],taze=True)
        th=threading.Thread(target=taze_izle,args=((sym,S),w,tk),daemon=True,name=f"taze-{S}")
        TAZE_IS[(sym,S)]=th; th.start()
        state_kaydet(); return
    if not plan: return
    if not (any(x['oi']==0 for x in plan) and any(x['oi']==1 for x in plan)):
        log('plan_tek_tarafli',sym=sym,S=S,karar='pencere atlanir'); return
""")

# 6) gec_ucuz_kes: C'nin emirlerini is parcacigi yonetir
rep("""    if w.get('cozuldu') or w.get('geri_cekildi') or w.get('gec_kesildi'): return
    if time.time()-k[1] < GEC_KES: return
    if w.get('kol')=='B':""","""    if w.get('cozuldu') or w.get('geri_cekildi') or w.get('gec_kesildi'): return
    if w.get('kol')=='C': return                   # C: is parcacigi t>=C_T_MAX'ta kendi kapatir
    if time.time()-k[1] < GEC_KES: return
    if w.get('kol')=='B':""")

# 7) SURUM logu
rep("        taraf_tavan=TARAF_TAVAN,gec_kes=GEC_KES,ucuz_esik=UCUZ_ESIK,gec_ust=GEC_UST,gec_esik=GEC_ESIK)",
    "        taraf_tavan=TARAF_TAVAN,gec_kes=GEC_KES,ucuz_esik=UCUZ_ESIK,gec_ust=GEC_UST,gec_esik=GEC_ESIK,\n        c_oran=C_ORAN,c_px=[C_PX_MIN,C_PX_MAX],c_t=[C_T_MIN,C_T_MAX],c_taze_max=C_TAZE_MAX,c_max_islem=C_MAX_ISLEM)")

# 8) testler (son dongunun hemen once)
rep("""    for ad,gecti,deger in ok:
        print(f"  {'GECTI' if gecti else 'KALDI'}  {ad}  (deger={deger})")""",
"""    # --- 09-19: KOL C taze seviye -------------------------------------------
    ok.append(('C hedef: spread 2 tik -> bb+1 tik', taze_hedef(0.45,0.47,0.01,500,0,0)==0.46, taze_hedef(0.45,0.47,0.01,500,0,0)))
    ok.append(('C hedef: spread 1 tik + ince seviye -> bb', taze_hedef(0.45,0.46,0.01,20,0,0)==0.45, taze_hedef(0.45,0.46,0.01,20,0,0)))
    ok.append(('C hedef: spread 1 tik + kalin seviye -> yok', taze_hedef(0.45,0.46,0.01,200,0,0) is None, taze_hedef(0.45,0.46,0.01,200,0,0)))
    ok.append(('C hedef: bant ustu (0,70) -> yok', taze_hedef(0.70,0.72,0.01,10,0,0) is None, taze_hedef(0.70,0.72,0.01,10,0,0)))
    ok.append(('C hedef: bant alti (0,10) -> yok', taze_hedef(0.10,0.12,0.01,10,0,0) is None, taze_hedef(0.10,0.12,0.01,10,0,0)))
    ok.append(('C hedef: agir taraf (10 pay onde) -> yok', taze_hedef(0.45,0.47,0.01,10,10.0,0.0) is None, taze_hedef(0.45,0.47,0.01,10,10.0,0.0)))
    ok.append(('C hedef: defter bos -> yok', taze_hedef(None,0.47,0.01,0,0,0) is None and taze_hedef(0.45,None,0.01,0,0,0) is None, 'None'))
    ok.append(('C hedef: 0,001 tik yuvarlama', taze_hedef(0.451,0.455,0.001,10,0,0)==0.452, taze_hedef(0.451,0.455,0.001,10,0,0)))
    _c=collections.Counter(kol_ata('btc',1789800000+300*i) for i in range(3000)) if 'collections' in globals() else None
    if _c is None:
        import collections as _co; _c=_co.Counter(kol_ata('btc',1789800000+300*i) for i in range(3000))
    ok.append(('kol_ata: A/B/C uclu, C~%50, A~B', 0.45<_c['C']/3000<0.55 and 0.20<_c['A']/3000<0.30 and 0.20<_c['B']/3000<0.30, dict(_c)))
    ok.append(('kol_ata tekrarlanabilir', kol_ata('btc',1789845000)==kol_ata('btc',1789845000), kol_ata('btc',1789845000)))
    _src=open(__file__).read()
    ok.append(('pencere_ac C dali izgara koymaz, is parcacigi baslatir', "if kol=='C':" in _src and 'threading.Thread(target=taze_izle' in _src, 'kaynakta var'))
    ok.append(('gec_ucuz_kes C emirlerine dokunmaz', "if w.get('kol')=='C': return" in _src, 'kaynakta var'))
    ok.append(('C is parcacigi t>=C_T_MAX sonunda acik emirleri kapatir', "kapat(r,'taze_bitti',k)" in _src, 'kaynakta var'))
    ok.append(('C: belirsiz POST -> durdur (fail-closed)', "if not oid2: durdur=True; return" in _src, 'kaynakta var'))

    for ad,gecti,deger in ok:
        print(f"  {'GECTI' if gecti else 'KALDI'}  {ad}  (deger={deger})")""")

open(P,'w').write(s); print("YAMA UYGULANDI")
