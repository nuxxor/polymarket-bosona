#!/usr/bin/env python3
"""F lane; varsayilan kuru, canli icin operator --live vermeli."""
from pathlib import Path
import runpy
import sys

if __name__=='__main__':
    sys.argv.insert(1,'--lane-f')
    runpy.run_path(str(Path(__file__).with_name('ab.py')),run_name='__main__')
