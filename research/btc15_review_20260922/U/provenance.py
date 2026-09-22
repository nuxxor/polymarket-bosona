#!/usr/bin/env python3
"""Verify declared public research inputs; never walk secret/config directories."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import time

HERE=Path(__file__).resolve().parent
R=Path('/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921')
F=R/'btc15_followup'
S=F/'status_20260921_1800'


def sha(p):
    digest=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):
            digest.update(block)
    return digest.hexdigest()


def check(root, entries):
    changed,missing=[],[]
    for name,details in entries.items():
        p=root/name
        assert not (p.name.startswith('.env') or p.suffix=='.session'),p.name
        expected=details['sha256'] if isinstance(details,dict) else details
        if not p.is_file():
            missing.append(name)
        elif sha(p)!=expected:
            changed.append(dict(path=str(p),expected=expected,actual=sha(p)))
    return dict(checked=len(entries),changed=changed,missing=missing)


def main():
    def read(p):
        return json.loads(p.read_text())
    manifests={
        'R':check(R,read(R/'artifact_manifest.json')['files']),
        'F':check(F,read(F/'results/manifest.json')['static_files']),
        'S':check(S,read(S/'manifest.json')),
        'protected':check(Path('/'),read(F/'baseline_hashes.json')),
    }
    sources=[]
    for original,v in read(R/'source_manifest.json').items():
        current=Path(original)
        frozen=Path(v['copy'])
        sources.append(dict(original=original,frozen=str(frozen),declared_sha256=v['sha256'],
            frozen_sha256=sha(frozen),current_main_sha256=sha(current),
            frozen_matches=sha(frozen)==v['sha256'],main_matches_frozen=sha(current)==sha(frozen)))
    files=[R/'plan.md',F/'plan.md',Path('/home/taygun/Masaüstü/polymarket-bosona/plan.md'),
           R/'BOSONA_NONBTC5_ULTRA_FABLE_PROMPT.md',R/'RAPOR.md',F/'RAPOR.md',S/'OKUMA.md']
    files += list(R.glob('*.py')) + list(F.glob('*.py')) + [S/'check.py']
    result=dict(checked_ms=round(time.time()*1000),python=platform.python_version(),
        packages={name:importlib.metadata.version(name) for name in ('numpy','scipy','scikit-learn','ruff')},
        manifests=manifests,sources=sources,input_files={str(p):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files},
        note='Historical manifests may precede later documentation; distinguish core data/code from plan changes.')
    assert not manifests['protected']['changed'] and not manifests['protected']['missing']
    assert all(x['frozen_matches'] for x in sources)
    (HERE/'provenance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(manifests=manifests,source_versions=sources),ensure_ascii=False))


if __name__=='__main__':
    main()
