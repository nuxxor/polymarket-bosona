p='ab.py'; s=open(p,encoding='utf-8').read()
h="    ok.append(('atlanan pencere GOLGE olarak loglanir (sonradan sinanabilsin)',"
i=s.index(h); j=s.index('\n',s.index('vol_atla olayinda vol+esik var',i))+1
ek="".join([
"    ok.append(('ACILAN pencerenin de vol'+chr(39)+'u loglanir (kill olcutu icin sart)',\n",
"               \"vol=(round(_vol,1)\" in _pa, 'pencere olayinda vol alani var'))\n",
])
s=s[:j]+ek+s[j:]
open(p,'w',encoding='utf-8').write(s)
