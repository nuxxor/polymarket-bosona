#!/usr/bin/env python3
"""Freeze a finite byte prefix; reuse the checkpoint arithmetic in our output only."""
import argparse
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
R = Path('/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921')
F = R / 'btc15_followup'
S = F / 'status_20260921_1800'
SOURCE = F / 'raw/books_72h'
DEST = HERE / 'new_period'


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def freeze():
    target = DEST / 'raw/book_validation_prefix.json.gz'
    if target.exists():
        return
    started = round(time.time() * 1000)
    status = json.loads((SOURCE / 'status.json').read_text())
    run = json.loads((SOURCE / 'run.json').read_text())
    pid = status['pid']
    proc = Path(f'/proc/{pid}')
    cmd = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode() if proc.exists() else None
    assert cmd is None or 'record_books.py' in cmd
    files = sorted(SOURCE.glob('books_*.jsonl.gz'))
    sizes = {p: p.stat().st_size for p in files}
    rows, manifest = [], []
    for p in files:
        with p.open('rb') as stream:
            data = stream.read(sizes[p])
        copied = DEST / 'raw/source_prefixes' / p.name
        copied.parent.mkdir(parents=True, exist_ok=True)
        copied.write_bytes(data)
        incomplete = False
        count = 0
        last = None
        try:
            with gzip.open(io.BytesIO(data), 'rt') as stream:
                for line in stream:
                    x = json.loads(line)
                    count += 1
                    last = x['received_ms']
                    if last <= status['received_ms']:
                        rows.append(x)
        except EOFError:
            assert p == files[-1] and status['running'], 'closed gzip corrupt'
            incomplete = True
        manifest.append(dict(source=str(p),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),
                             rows=count,last_received_ms=last,open_footer=incomplete))
    assert rows and all(a['received_ms'] <= b['received_ms'] for a,b in zip(rows, rows[1:]))
    target.write_bytes(gzip.compress(json.dumps(dict(rows=rows,status=status),separators=(',',':')).encode(),mtime=0))
    save(DEST / 'raw/run.json', run)
    save(DEST / 'freeze_manifest.json', dict(started_ms=started,cutoff_ms=status['received_ms'],
        inspected_at_ms=round(time.time()*1000),status=status,pid_present=proc.exists(),command=cmd,
        heartbeat_age_ms=started-status['received_ms'],files=manifest,rows=len(rows),
        uncompressed_bytes=sum(len(json.dumps(x,separators=(',',':')).encode())+1 for x in rows),
        capture_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        split='S is known counterexample; S+ is a post-preregistration diagnostic, not blind.'))


def run(offline):
    freeze()
    spec = importlib.util.spec_from_file_location('prior_checkpoint', S / 'check.py')
    checkpoint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checkpoint)
    checkpoint.HERE = DEST
    checkpoint.audit.OFFLINE = offline
    checkpoint.run()
    old = json.loads((S / 'results/book_quality.json').read_text())['asof_ms']
    windows = json.loads((DEST / 'results/windows.json').read_text())
    cutoff = json.loads((DEST / 'freeze_manifest.json').read_text())['cutoff_ms']//1000
    prestart = []
    for w in windows:
        market = json.loads((DEST/'raw/new_period_markets'/f'{w["slug"]}.json').read_text())['data']
        rows = checkpoint.audit.activity('prestart_validation/'+w['slug'], checkpoint.r.base.WALLET,
                                        market=market['conditionId'],start=1,end=cutoff)
        assert all(x['conditionId']==market['conditionId'] for x in rows)
        trades = [x for x in rows if x['type']=='TRADE']
        assert len(trades)==w['fills']
        prestart.append(dict(slug=w['slug'],complete=True,rows=len(rows),
            trades_before_start=[x for x in trades if x['timestamp']<w['S']],
            trade_count=len(trades),published_trade_count=w['fills'],activity_types=sorted({x['type'] for x in rows})))
    save(DEST/'results/prestart_validation.json',prestart)
    fresh = [w for w in windows if w['S'] >= old // 1000 and w['full'] and w['winner'] is not None]
    transition = [w for w in windows if w['S']*1000 < old < w['end']*1000]
    save(DEST / 'results/after_preregistered_split.json',dict(
        old_cutoff_ms=old,fully_new_closed_windows=fresh,previously_open_windows=transition,
        pnl=sum(x['pnl'] for x in fresh),late_pnl=sum(x['late_pnl'] for x in fresh),
        note='Only windows beginning after S cutoff; earlier windows never relabeled unseen.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    run(parser.parse_args().offline)
