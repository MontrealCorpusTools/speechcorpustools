
import os
import sys

from PyInstaller.utils.hooks import (
    collect_data_files, collect_dynamic_libs, copy_metadata)

hiddenimports = ['cython', 'Cython', 'resampy', 'mock']

datas = collect_data_files('resampy')

datas += copy_metadata('mock')

if sys.platform == 'darwin':
    binaries = [(os.path.expanduser('~/dev/tools/bin/reaper'), '.')]


