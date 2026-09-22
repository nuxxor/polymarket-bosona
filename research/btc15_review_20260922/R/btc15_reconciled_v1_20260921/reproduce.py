"""Offline reconstruction twice, content hashes, regressions, syntax and lint."""
import hashlib
import os
import subprocess
import sys

from common import HERE, protected, save


def main():
    os.environ['OPENBLAS_NUM_THREADS'] = '1'
    protected()
    artifacts = ('fills btc15_activity phase_changes risk_set reconciliation input_manifest '
                 'parent_fills parents parent_inputs replay replay_inputs checks ws_quality').split()
    runs = []
    for i in range(2):
        for name in ('reconcile', 'parents', 'replay', 'check'):
            result = subprocess.run([sys.executable, '-B', str(HERE/f'{name}.py')],
                                    capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError(name+': '+result.stdout+result.stderr)
        runs.append({name: hashlib.sha256((HERE/'results'/f'{name}.json').read_bytes()).hexdigest()
                     for name in artifacts})
        print(f'run {i+1}: {len(artifacts)} artifacts', flush=True)
    assert runs[0] == runs[1], 'non-reproducible frozen artifact'
    for path in HERE.glob('*.py'):
        compile(path.read_text(), str(path), 'exec')
    subprocess.run([sys.executable, '-m', 'ruff', 'check', str(HERE)], check=True)
    protected()
    save('results/reproduction.json', dict(passed=True, identical_runs=2, hashes=runs[0],
        sources={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('*.py'))},
        syntax='passed', ruff='passed', original_core_hashes='unchanged',
        note='Offline only. Does not restart the public recorder or claim economic acceptance.'))
    print('Identical hashes, syntax, Ruff and protected sources: PASS')


if __name__ == '__main__':
    main()
