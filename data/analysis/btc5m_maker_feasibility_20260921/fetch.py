"""Bounded public receipt fetch; reuses the R1 collector and its cache."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
from pathlib import Path
import importlib.util
import json
import shutil
import sys
import time

OUT = Path(__file__).resolve().parent


def main():
    helper = Path(sys.argv[1]) if len(sys.argv)>1 else OUT.parent/'btc5m_parent_research_20260921/collect.py'
    spec = importlib.util.spec_from_file_location('public_collect',helper)
    collector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)
    collector.OUT = OUT
    transactions = json.loads((OUT/'transactions.json').read_text())
    assert len(transactions)==len(set(transactions))
    assert all(len(tx)==66 and int(tx[2:],16)>=0 for tx in transactions)
    (OUT/'receipts').mkdir(exist_ok=True)
    for tx in transactions:
        old = helper.parent/'receipts'/f'{tx}.json'
        new = OUT/'receipts'/f'{tx}.json'
        if old.exists() and not new.exists():
            shutil.copyfile(old,new)
    assert all(collector.rpc(url,'eth_chainId',[])=='0x89' for url in collector.RPCS)
    failures, started = [], time.time()
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs = {pool.submit(collector.receipt,tx):tx for tx in transactions}
        for i, job in enumerate(as_completed(jobs),1):
            try:
                job.result()
            except (OSError,ValueError,AssertionError) as error:
                failures.append(dict(tx=jobs[job],error=type(error).__name__,reason=str(error)[:160]))
            if i%100==0 or i==len(jobs):
                print('receipts',i,'/',len(jobs),'failed',len(failures),flush=True)
    result = dict(started_ms=round(started*1000),finished_ms=round(time.time()*1000),failures=failures,
        helper_sha256=sha256(helper.read_bytes()).hexdigest(),source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        transactions_sha256=sha256((OUT/'transactions.json').read_bytes()).hexdigest(),
        files={str(p.relative_to(OUT)):sha256(p.read_bytes()).hexdigest() for p in (OUT/'receipts').glob('*.json')})
    (OUT/'fetch_manifest.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    main()
