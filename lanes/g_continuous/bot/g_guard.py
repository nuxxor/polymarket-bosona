"""A parked source or expired pilot cannot trade via a direct engine invocation."""
from hashlib import sha256
import json
from pathlib import Path
import time

REQUIRED = {'ab.py', 'g.py', 'g_policy.py', 'g_guard.py', 'emir_iz.py', 'f_budget.py',
            'pilot.py', 'protocol.json', 'observer.py', 'stream_iz.py', 'measurement/protocol.json'}


def verify(root, budget):
    root = Path(root)
    if not budget or (budget['end_ms'] is not None and time.time()*1000 >= budget['end_ms']):
        raise ValueError('G pilot budget missing or expired')
    protocol = json.loads((root/'protocol.json').read_text())
    if budget['end_ms'] is None and not (budget.get('continuous') is True and protocol.get('continuous') is True):
        raise ValueError('G unlimited budget requires frozen continuous protocol')
    if protocol.get('experiment') == 'G4' and (budget.get('experiment') != 'G4' or budget['limit'] != 100 or protocol['loss_limit'] != 100):
        raise ValueError('G4 requires its own activated budget')
    run = json.loads((root/'RUN_G.json').read_text())
    if run['budget'] != budget:
        raise ValueError('G activation/budget mismatch')
    manifest = json.loads((root/'G_RELEASE.json').read_text())
    if not REQUIRED <= set(manifest):
        raise ValueError('G release manifest incomplete')
    for name, digest in manifest.items():
        if sha256((root/name).read_bytes()).hexdigest() != digest:
            raise ValueError('G source mismatch')
