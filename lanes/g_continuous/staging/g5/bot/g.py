#!/usr/bin/env python3
"""G5/G4_FIXED research; parked until explicit G5 account/budget activation."""
from pathlib import Path
import runpy
import sys

if __name__ == '__main__':
    sys.argv.insert(1, '--lane-g')
    runpy.run_path(str(Path(__file__).with_name('ab.py')), run_name='__main__')
