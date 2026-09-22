"""Replay the frozen dual capture and verify provenance; no financial operations."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile

import analyze
import run


def main():
    root = Path(__file__).resolve().parent
    analyze.self_check()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)/'ready.json'
        run.write(path, dict(ready=True))
        assert json.loads(path.read_text()) == dict(ready=True)
        try:
            run.write(path, dict(ready=False))
        except AssertionError:
            pass
        else:
            raise AssertionError('ready marker overwritten')
    manifest = json.loads((root/'run1/manifest.json').read_text())['sources']
    for name in ('run.py', 'protocol.json'):
        expected, = [h for p, h in manifest.items() if Path(p).name == name]
        assert sha256((root/name).read_bytes()).hexdigest() == expected
    result = analyze.main(root/'run1')
    assert json.loads(json.dumps(result)) == json.loads((root/'result.json').read_text())
    raw = json.loads((root/'run1/raw_manifest.json').read_text())
    for lane, proof in zip(('A', 'B'), result['integrity']):
        assert proof['raw_sha256'] == raw[lane]['raw_sha256']
    final = json.loads((root/'run1/final_state.json').read_text())
    previous = json.loads((root.parent/'btc5m_m7_transport_20260922/run1/final_state.json').read_text())
    assert final['financial_hashes'] == previous['financial_hashes']
    assert final['open_orders'] == 0 and final['relevant_pids'] == []
    return dict(replay_equal=True, financial_unchanged=True, coverage_gate=result['coverage_gate'],
                raw_hashes={lane:r['raw_sha256'] for lane,r in raw.items()},
                source_hashes={p.name:sha256(p.read_bytes()).hexdigest() for p in root.glob('*.py')},
                full_calibration=False)


if __name__ == '__main__':
    print(json.dumps(main(), indent=2))
