p='ab.py'; s=open(p,encoding='utf-8').read()
hedef="    ok.append(('tavan degismedi', PX_TAVAN_MAKER==0.40, PX_TAVAN_MAKER))"
satirlar=[
"    # --- BTC OYNAKLIK KAPISI (09-19) ---",
"    ok.append(('vol kapisi ACIK, esik 15 bps', VOL_KAPISI is True and VOL_ESIK==15.0,",
"               f'{VOL_KAPISI} / {VOL_ESIK}'))",
"    ok.append(('eski kol-degistiren kapi KAPALI (karismasin)', KAPI_ACIK is False, KAPI_ACIK))",
"    import inspect as _i2",
"    _pa=_i2.getsource(pencere_ac)",
"    ok.append(('kapi pencereyi ATLIYOR (kol degistirmiyor)',",
"               \"log('vol_atla'\" in _pa and 'return' in _pa.split(\"vol_atla\")[1][:200],",
"               'vol_atla sonrasi return var'))",
"    ok.append(('olculemezse pencere ACILIR (fail-open)',",
"               \"_v is None\" in _pa and 'fail-open' in _pa,",
"               'vol None -> acilir'))",
"    ok.append(('atlanan pencere GOLGE olarak loglanir (sonradan sinanabilsin)',",
"               \"esik=VOL_ESIK\" in _pa and 'vol=round' in _pa, 'vol_atla olayinda vol+esik var'))",
]
assert hedef in s
s=s.replace(hedef, hedef+"\n"+"\n".join(satirlar),1)
open(p,'w',encoding='utf-8').write(s)
print('testler eklendi')
