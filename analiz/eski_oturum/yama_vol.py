p='ab.py'; s=open(p,encoding='utf-8').read()

# 1) parametreler
anc="KAPI_ACIK=False   # 09-19: IPW ile curudu (+0,70 GA[-3,65,+4,74]); kol B de yok"
assert anc in s
s=s.replace(anc, anc + "\n" + "\n".join([
"# --- BTC OYNAKLIK KAPISI: PENCERE ATLAMA (09-19 15:45) --------------------",
"# Eski KAPI_ACIK ayni olcumu yapiyordu ama yanlis EYLEMI: pencereyi atlamak",
"# yerine KOL DEGISTIRIYORDU. Bu kapi pencereyi ATLAR.",
"# OLCUM (zincir, 3.913 pencere / 17 gun, gun-kumeli GA, ORNEK DISI kararli):",
"#   KOL A kapisiz +0,48 [-0,26,+1,28] -> vol5>15 bps: +1,67 [+0,49,+2,75]",
"#   KOL B kapisiz +0,88 [+0,12,+1,59] -> vol5>15 bps: +1,69 [+0,59,+2,62]",
"#   oynaklik kaliciligi Spearman +0,676 (onceki 5dk -> pencere ici menzil)",
"#   ornek disi: EGITIM farki +2,21, TEST farki +2,09 (asiri uyum YOK)",
"# Bkz ONKAYIT_VOL_KAPISI_20260919.md",
"VOL_KAPISI=True",
"VOL_ESIK=15.0     # bps. Olculemezse pencere ACILIR (fail-open; kapi bir RISK",
"                  # kontrolu degil, SECIM kontrolu -- olcemeyince tarafsiz kal).",
]),1)

# 2) pencere_ac icinde kapi
anc2="""def pencere_ac(sym,S,per):
    \"\"\"Iki-tarafli kabul durum makinesi. Tek taraf kabul edilirse GERI CEKER.\"\"\"
    kol=kol_ata(sym,S)"""
assert anc2 in s
s=s.replace(anc2, """def pencere_ac(sym,S,per):
    \"\"\"Iki-tarafli kabul durum makinesi. Tek taraf kabul edilirse GERI CEKER.\"\"\"
    if VOL_KAPISI:
        _v=onceki_oynaklik(S)
        if _v is not None and _v<VOL_ESIK:
            # GOLGE KAYDI: atlanan pencere sonradan kamu veriden degerlendirilecek.
            log('vol_atla',sym=sym,S=S,vol=round(_v,1),esik=VOL_ESIK,
                kol=kol_ata(sym,S),karar='pencere ATLANDI')
            return
        if _v is None: log('vol_olculemedi',sym=sym,S=S,karar='pencere ACILIR (fail-open)')
    kol=kol_ata(sym,S)""",1)

# 3) SURUM logu
s=s.replace("a_oran=A_ORAN,tohum=AB_TOHUM","vol_kapisi=VOL_KAPISI,vol_esik=VOL_ESIK,a_oran=A_ORAN,tohum=AB_TOHUM",1)
open(p,'w',encoding='utf-8').write(s)
print('vol kapisi eklendi')
