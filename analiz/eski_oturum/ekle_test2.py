p='ab.py'; s=open(p,encoding='utf-8').read()
hedef="    ok.append(('tavan degismedi', PX_TAVAN_MAKER==0.40, PX_TAVAN_MAKER))"
satirlar = [
"    # 09-19 15:19-15:23: acilis kapilari 999'a takilip 4 kez pes etti, bot 4 dk",
"    # kapali kaldi. Sinirli tekrar eklendi; EMNIYET korunmali: kapi gecmeden",
"    # baslamak MUMKUN OLMAMALI.",
"    ok.append(('acilis tekrari var (>=3 deneme, artan bekleme)',",
"               ACILIS_DENEME>=3 and ACILIS_BEKLE>0,",
"               f'{ACILIS_DENEME} deneme x {ACILIS_BEKLE}sn artan'))",
"    import inspect as _i, re as _re",
"    _ms=_i.getsource(main) if 'main' in dir() else ''",
"    _kd=_ms.count('_kapi(')",
"    ok.append(('uc acilis kapisi da tekrarli (_kapi ile)', _kd>=4, f'_kapi gecis sayisi {_kd}'))",
"    ok.append(('kapi gecmezse BASLAMIYOR (fail-closed korundu)',",
"               _ms.count(\"log('BASLAMIYOR'\")>=1 and 'return False' in _ms,",
"               'tekrar bitince return False -> BASLAMIYOR'))",
]
assert hedef in s
s=s.replace(hedef, hedef+"\n"+"\n".join(satirlar), 1)
open(p,'w',encoding='utf-8').write(s)
print('testler eklendi')
