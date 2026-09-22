#!/usr/bin/env python3
"""Reproduce this audit offline; source repositories are read-only inputs."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
F=Path('/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_followup')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1')
    logs=HERE/'verification'
    logs.mkdir(exist_ok=True)
    tracked=[HERE/'accounting/result.json',HERE/'accounting/collision_result.json',HERE/'accounting/selection_audit.json',HERE/'onchain/results.json',
        HERE/'execution/results.json',HERE/'execution/calibration.json',HERE/'execution/s_candidate_replay.json',
        HERE/'statistics/audit.json',HERE/'statistics/merge_corrected/hypothesis_models.json',
        HERE/'execution/history_policy_sensitivity.json',HERE/'execution/calibration_market_comparison.json',
        HERE/'onchain/postclose_results.json',HERE/'onchain/selection_checks.json',
        HERE/'case_paths.json',HERE/'new_period/results/summary.json',HERE/'new_period/results/windows.json']
    before={str(p.relative_to(HERE)):digest(p) for p in tracked}
    commands=[('accounting/audit.py',),('accounting/collision_check.py',),('accounting/check.py',),('accounting/selection_audit.py',),
        ('onchain/probe.py',),('onchain/check.py',),('onchain/postclose.py',),
        ('execution/audit.py',),('execution/sensitivity.py',),('execution/check.py',),
        ('snapshot.py','--offline')]
    for command in commands:
        with (logs/(command[0].replace('/','_')+'.log')).open('w') as log:
            subprocess.run([sys.executable,str(HERE/command[0]),*command[1:]],cwd=HERE,env=env,
                           stdout=log,stderr=subprocess.STDOUT,check=True)
    spec=importlib.util.spec_from_file_location('reproduced_followup',F/'analyze.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUT=HERE/'statistics/reproduced'
    module.run()
    module.OUT=HERE/'statistics/merge_corrected'
    module.models(json.loads((HERE/'accounting/risk_set_actual_inventory.json').read_text()))
    for filename in ('statistical_audit.py','case_paths.py','provenance.py'):
        with (logs/(filename+'.log')).open('w') as log:
            subprocess.run([sys.executable,str(HERE/filename)],cwd=HERE,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    paths=sorted(HERE.glob('*.py'))
    for folder in ('accounting','execution','onchain'):
        paths.extend(sorted((HERE/folder).glob('*.py')))
    for path in paths:
        ast.parse(path.read_text(),filename=str(path))
    with (logs/'ruff.log').open('w') as log:
        subprocess.run([sys.executable,'-m','ruff','check','--no-cache',*map(str,paths)],cwd=HERE,env=env,
                       stdout=log,stderr=subprocess.STDOUT,check=True)
    after={str(p.relative_to(HERE)):digest(p) for p in tracked}
    changed=[p for p in before if before[p]!=after[p]]
    result=dict(passed=not changed,offline=True,tracked=len(tracked),before=before,after=after,changed=changed,
        syntax_files=len(paths),lint='passed',no_shared_source_writes=True,
        commands=[list(c) for c in commands]+[['F/analyze.py via redirected OUT'],['statistical_audit.py'],['case_paths.py'],['provenance.py']])
    (HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    assert not changed,changed
    print(json.dumps(dict(passed=True,tracked=len(tracked),syntax_files=len(paths),lint='passed')))


if __name__=='__main__':
    main()
