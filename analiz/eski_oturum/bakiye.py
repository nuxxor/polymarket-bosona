import re,sys,json
sys.path.insert(0,'/home/taygun/Masaüstü/polymarket')
env={}
for line in open('/home/taygun/Masaüstü/polymarket/.env.live'):
    if re.match(r'^\s*[A-Za-z_][A-Za-z_0-9]*=',line):
        k,v=line.split('=',1); env[k.strip()]=v.strip().strip('"').strip("'")
from py_clob_client_v2.client import ClobClient
from py_clob_client_v2.clob_types import BalanceAllowanceParams, AssetType
c=ClobClient(env.get('PM_CLOB_HOST','https://clob.polymarket.com'),chain_id=137,
             key=env['PM_PRIVATE_KEY'],signature_type=2,funder=env['PM_FUNDER'])
c.set_api_creds(c.derive_api_key())
b=c.get_balance_allowance(BalanceAllowanceParams(asset_type=AssetType.COLLATERAL))
print("ham:",b)
try: print("pUSD bakiye: $%.2f"%(int(b['balance'])/1e6))
except Exception: pass
