#!/usr/bin/env python3
"""G4 lane; operator launcher activates the frozen, unlimited-time $100 run."""
from pathlib import Path
import runpy
import sys

if __name__ == '__main__':
    sys.argv.insert(1, '--lane-g')
    runpy.run_path(str(Path(__file__).with_name('ab.py')), run_name='__main__')
