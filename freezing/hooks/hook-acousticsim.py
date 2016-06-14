
import os
import sys

from PyInstaller.utils.hooks import (
    collect_data_files, collect_dynamic_libs)

hiddenimports = ['cython', 'mock']


from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata('mock')

if sys.platform == 'darwin':
    binaries = [(os.path.expanduser('~/dev/tools/bin/reaper'), '.')]


