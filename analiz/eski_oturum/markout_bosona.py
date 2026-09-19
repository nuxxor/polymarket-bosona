"""bosona'yi BIZIMLE AYNI yontemle olc: ayni mid tanimi, ayni ufuk, ayni yas
siniri, ayni miktar agirligi. v1 onun sayilarini sabit metin olarak basiyordu."""
import json,urllib.request,time,sys
sys.path.insert(0,'/tmp/claude-1000/-home-taygun-Masa-st--polymarket/b4197893-bd19-4ee9-9e9a-ddd5e06151af/scratchpad')
from markout_v2 import tape_yukle,mid_at,olc,bizim_dolumlar,UFUK,MAX_YAS
UA={'User-Agent':'python-urllib/3'}
BOS='0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed'
def jget(u,t=25):
    with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t) as r: return json.loads(r.read())
LOG='/home/taygun/Masaüstü/polymarket/data/analysis/pm_merdiven_ab_20260918_v5/LOG_ab.jsonl'
dol,_,k=bizim_dolumlar(LOG)
bas=min(x[1] for x in dol)-20000; bit=max(x[1] for x in dol)+20000
print("tape yukleniyor (tek sefer, ikisi icin)...",flush=True)
ser=tape_yukle(bas=bas,bit=bit)
print(f"tape asset: {len(ser)}\n",flush=True)
print("### BIZ (dogrulama)")
olc(dol,ser,"tum dolumlar")
# bosona: ayni zaman araliginda, ayni assetlerde
tr=[];off=0;gor=set()
while off<=8000:
    try: d=jget(f"https://data-api.polymarket.com/trades?user={BOS}&limit=500&offset={off}&takerOnly=false")
    except Exception as e: print("akis dur:",str(e)[:40]); break
    if not d: break
    for x in d:
        kk=(x['timestamp'],x['asset'],x['size'],x['price'],x['side'])
        if kk not in gor: gor.add(kk); tr.append(x)
    if len(d)<500 or min(x['timestamp'] for x in d)*1000<bas: break
    off+=500; time.sleep(0.35)
bd=[(x['asset'],x['timestamp']*1000,x['price'],x['size']) for x in tr
    if x['side']=='BUY' and x['asset'] in ser and bas<=x['timestamp']*1000<=bit]
print(f"\n### BOSONA (ayni tape, ayni yontem)  — ham islem {len(tr)}, olculebilir {len(bd)}")
print("  UYARI: kamu akisi islem zamanini saniye cozunurlukte veriyor; bizim")
print("  dolum anlarimiz ms. Bu asimetri bosona lehine/aleyhine olabilir, gizlenmiyor.")
olc(bd,ser,"bosona BUY")
