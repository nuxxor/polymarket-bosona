"""Use the existing unauthenticated collector for own public fills and receipts."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
from pathlib import Path
import importlib.util
import json
import sys
import time

OUT = Path(__file__).resolve().parent


def main():
    helper=Path(sys.argv[1]) if len(sys.argv)>1 else OUT.parent/'btc5m_parent_research_20260921/collect.py'
    spec=importlib.util.spec_from_file_location('public_collect',helper)
    api=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api)
    api.OUT=OUT
    wallet=json.loads((OUT/'public_wallet.json').read_text())['address']
    markets=json.loads((OUT/'markets.json').read_text())
    for folder in ('full_activity','receipts'):
        (OUT/folder).mkdir(exist_ok=True)
    started=round(time.time()*1000)
    failures=[]
    assert all(api.rpc(url,'eth_chainId',[])=='0x89' for url in api.RPCS)
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs={}
        for i,item in enumerate(markets.items(),1):
            try:
                api.market_activity(item,wallet)
                rows=api.read(OUT/'full_activity'/f'{item[0]}.json')['rows']
                for tx in {r['transactionHash'] for r in rows if r['type']=='TRADE'}:
                    if tx not in jobs:
                        jobs[tx]=pool.submit(api.receipt,tx)
            except (OSError,ValueError,AssertionError) as error:
                failures.append(dict(market=item[0],error=type(error).__name__))
            if i%10==0 or i==len(markets):
                print('markets',i,'/',len(markets),'transactions',len(jobs),flush=True)
        for job in as_completed(jobs.values()):
            try:
                job.result()
            except (OSError,ValueError,AssertionError) as error:
                failures.append(dict(tx=next(t for t,f in jobs.items() if f is job),error=type(error).__name__))
    api.save(OUT/'fetch_manifest.json',dict(started_ms=started,finished_ms=round(time.time()*1000),failures=failures,
        helper_sha256=sha256(helper.read_bytes()).hexdigest(),source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        files={str(p.relative_to(OUT)):sha256(p.read_bytes()).hexdigest() for folder in ('full_activity','receipts') for p in (OUT/folder).glob('*.json')}))
    print('finished; failures',len(failures),flush=True)


if __name__=='__main__':
    main()
