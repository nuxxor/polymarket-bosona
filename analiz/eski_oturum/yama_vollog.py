p='ab.py'; s=open(p,encoding='utf-8').read()
eski = """    if VOL_KAPISI:
        _v=onceki_oynaklik(S)
        if _v is not None and _v<VOL_ESIK:"""
yeni = """    _vol=None
    if VOL_KAPISI:
        _v=onceki_oynaklik(S); _vol=_v
        if _v is not None and _v<VOL_ESIK:"""
assert eski in s
s=s.replace(eski,yeni,1)
# pencere olayina vol ekle -> acilan pencerelerin vol'u de kayda gecsin
old="log('pencere',sym=sym,S=S,kol=kol,tokens=[str(tk[0]),str(tk[1])],emir=len(w['emir']),"
assert old in s
s=s.replace(old,"log('pencere',sym=sym,S=S,kol=kol,vol=(round(_vol,1) if _vol is not None else None),"
                "tokens=[str(tk[0]),str(tk[1])],emir=len(w['emir']),",1)
open(p,'w',encoding='utf-8').write(s)
print('acilan pencerelere vol logu eklendi')
