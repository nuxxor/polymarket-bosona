"""Frozen research sources; output is confined to this version directory."""
import hashlib
import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
R = HERE.parent
U = Path('/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z')
FABLE = R/'fable_review_20260921'
S = R/'btc15_followup/status_20260921_1800'
INPUTS = {}


def read(path):
    raw = path.read_bytes()
    INPUTS[str(path)] = hashlib.sha256(raw).hexdigest()
    return json.loads(raw)


def save(name, value):
    p = HERE/name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True,
                           default=lambda x: str(x) if isinstance(x, Decimal) else list(x))+'\n')


def module(name, path):
    INPUTS[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def protected():
    for path, expected in read(R/'btc15_followup/baseline_hashes.json').items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path


accounting = module('ultra_accounting', U/'accounting/audit.py')
timing = module('ultra_timing', U/'execution/audit.py')
roles = module('fable_roles', FABLE/'code/role_classifier.py')
