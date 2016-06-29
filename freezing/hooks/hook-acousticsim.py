
import os
import sys

from PyInstaller.utils.hooks import (
    collect_data_files, collect_dynamic_libs)

hiddenimports = ['cython']

if sys.platform == 'darwin':
    binaries = [(os.path.expanduser('~/dev/tools/bin/reaper'), '.')]


