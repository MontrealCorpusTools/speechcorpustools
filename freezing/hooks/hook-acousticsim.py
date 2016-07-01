
import os
import sys

from PyInstaller.utils.hooks import (
    collect_data_files, collect_dynamic_libs)

hiddenimports = ['cython', 'Cython', 'resampy']

datas = collect_data_files('resampy')

if sys.platform == 'darwin':
    binaries = [(os.path.expanduser('~/dev/tools/bin/reaper'), '.')]


