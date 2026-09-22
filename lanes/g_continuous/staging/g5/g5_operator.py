"""Parked G5 verifier; --operator-start is reserved for a later operator launch."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g4_operator as transition  # noqa: E402

transition.HERE = Path(__file__).resolve().parent
transition.EXPERIMENT = 'G5'

if __name__ == '__main__':
    try:
        transition.main()
    except Exception as error:
        print('G5_OPERATOR_FAILED: '+type(error).__name__, flush=True)
        raise SystemExit(1) from None
